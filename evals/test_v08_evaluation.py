"""v0.8 CP4: Evaluation Core (voznativa/evaluation.py, `voznativa evaluate`).

What a run must never do: count a NOT_RUN arm or an unreadable source as
passed, accept a frozen file that changed, call a developer-written suite an
independent holdout, pool splits into one number, keep the texts of the cases,
or let an edited record verify."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import evaluation  # noqa: E402
from voznativa.evals import sha256_lf  # noqa: E402

SPEC = json.loads((ROOT / "evals" / "v08" / "datasets" / "gate-and-planner.json").read_text(encoding="utf-8"))
NEG = {"id": "n1", "category": "negation", "genre": "technical", "original": "O deploy não deve ser feito hoje.",
       "candidate": "O deploy deve ser feito hoje.", "expect": {"status": ["fail"], "codes": ["negation_changed"]}}
SAME = {"id": "s1", "category": "identity", "genre": "technical", "original": "O deploy é hoje.",
        "candidate": "O deploy é hoje.", "expect": {"status": ["identical"]}}
LOOSE = {"id": "l1", "category": "loose", "genre": "technical", "original": "O deploy é hoje.",
         "candidate": "O deploy acontece hoje.", "expect": {"status": ["no_deterministic_issues", "review_required"]}}


def spec_of(*sources, id_="t"):
    return {"kind": "voznativa.eval_dataset", "schema_version": 1, "id": id_, "sources": list(sources)}


class Workspace:
    """A temporary repository-like root with suites and their MANIFEST."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "s").mkdir()

    def suite(self, name, rows, frozen=False, independent=False):
        path = self.root / "s" / name
        path.write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"))  # LF
        manifest = self.root / "s" / "MANIFEST.json"
        data = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {"suites": {}}
        data["suites"][name] = {"role": "dev", "independent": independent, "frozen": frozen,
                                **({"sha256": sha256_lf(path)} if frozen else {})}
        manifest.write_text(json.dumps(data), encoding="utf-8")
        return f"s/{name}"

    def close(self):
        self.tmp.cleanup()


class SpecValidation(unittest.TestCase):

    def setUp(self):
        self.ws = Workspace()
        self.path = self.ws.suite("a.jsonl", [NEG])

    def tearDown(self):
        self.ws.close()

    def assert_invalid(self, spec, fragment):
        record = evaluation.run(spec, self.ws.root, recorded_at="t")
        self.assertEqual(record["status"], "INVALID")
        self.assertEqual(record["results"], [])
        self.assertTrue(any(fragment in p for p in record["problems"]), record["problems"])

    def test_malformed_specs(self):
        good = {"path": self.path, "adapter": "semantic_suite", "split": "development"}
        self.assert_invalid(dict(spec_of(good), kind="other"), "unsupported dataset kind")
        self.assert_invalid(spec_of(), "non-empty list")
        self.assert_invalid(spec_of(dict(good, adapter="magic")), "adapter must be")
        self.assert_invalid(spec_of(dict(good, split="training")), "split must be")
        self.assert_invalid(spec_of(good, dict(good)), "listed twice")
        self.assert_invalid(spec_of(dict(good, path="s/missing.jsonl")), "not found")

    def test_paths_must_stay_inside_the_root(self):
        good = {"adapter": "semantic_suite", "split": "development"}
        self.assert_invalid(spec_of(dict(good, path="../a.jsonl")), "stay inside")
        self.assert_invalid(spec_of(dict(good, path=str(self.ws.root / self.path))), "stay inside")

    def test_a_developer_suite_cannot_be_an_independent_holdout(self):
        self.assert_invalid(spec_of({"path": self.path, "adapter": "semantic_suite",
                                     "split": "external_independent_holdout"}), "not independent")

    def test_a_frozen_file_that_changed_invalidates_the_run(self):
        frozen = self.ws.suite("f.jsonl", [NEG, SAME], frozen=True)
        spec = spec_of({"path": frozen, "adapter": "semantic_suite", "split": "frozen_regression"})
        self.assertEqual(evaluation.run(spec, self.ws.root, recorded_at="t")["status"], "COMPLETE")
        target = self.ws.root / frozen
        target.write_text(target.read_text(encoding="utf-8").replace("hoje", "amanhã"), encoding="utf-8")
        self.assert_invalid(spec, "frozen file")

    def test_line_endings_do_not_change_the_frozen_hash(self):
        frozen = self.ws.suite("crlf.jsonl", [NEG], frozen=True)
        target = self.ws.root / frozen
        target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
        spec = spec_of({"path": frozen, "adapter": "semantic_suite", "split": "frozen_regression"})
        self.assertEqual(evaluation.run(spec, self.ws.root, recorded_at="t")["status"], "COMPLETE")


class BadCasesNeverPass(unittest.TestCase):

    def setUp(self):
        self.ws = Workspace()

    def tearDown(self):
        self.ws.close()

    def test_unreadable_source_makes_the_run_incomplete_but_runs_the_others(self):
        good = self.ws.suite("good.jsonl", [NEG])
        bad = self.ws.root / "s" / "bad.jsonl"
        bad.write_text('{"id": "x", "original": "a"}\nnot json\n', encoding="utf-8")
        spec = spec_of({"path": good, "adapter": "semantic_suite", "split": "development"},
                       {"path": "s/bad.jsonl", "adapter": "semantic_suite", "split": "development"})
        record = evaluation.run(spec, self.ws.root, recorded_at="t")
        self.assertEqual(record["status"], "INCOMPLETE")
        self.assertEqual([r["id"] for r in record["results"]], ["good:n1"])
        self.assertTrue(record["problems"])

    def test_missing_fields_duplicates_and_bad_expectations(self):
        for rows, fragment in (([{"id": "a", "original": "x"}], "missing or non-text"),
                               ([NEG, NEG], "duplicate case ids"),
                               ([dict(NEG, expect={"status": []})], "non-empty list")):
            with self.subTest(fragment=fragment):
                path = self.ws.suite("c.jsonl", rows)
                record = evaluation.run(spec_of({"path": path, "adapter": "semantic_suite", "split": "development"}),
                                        self.ws.root, recorded_at="t")
                self.assertEqual(record["status"], "INCOMPLETE")
                self.assertTrue(any(fragment in p for p in record["problems"]), record["problems"])
        path = self.ws.suite("r.jsonl", [{"id": "r", "original": "a", "candidate": "b", "expect": "maybe"}])
        record = evaluation.run(spec_of({"path": path, "adapter": "risk_sample", "split": "development"}),
                                self.ws.root, recorded_at="t")
        self.assertEqual(record["status"], "INCOMPLETE")

    def test_arms_that_did_not_run_are_never_counted(self):
        path = self.ws.suite("a.jsonl", [NEG])
        record = evaluation.run(spec_of({"path": path, "adapter": "semantic_suite", "split": "development"}),
                                self.ws.root, recorded_at="t")
        self.assertTrue(record["arms_not_run"])
        self.assertTrue(all(a["evidence"] == "NOT_RUN" for a in record["arms_not_run"]))
        self.assertEqual(record["system_under_test"]["evidence"], "ENGINE_EXECUTED")


class Metrics(unittest.TestCase):

    def test_denominators_and_intervals(self):
        ws = Workspace()
        try:
            missed = dict(NEG, id="n2", candidate="O deploy não deve ser feito hoje!")      # risky by label, clean
            missed["expect"] = {"status": ["fail"]}
            path = ws.suite("m.jsonl", [NEG, missed, SAME, LOOSE])
            pred = ws.suite("p.jsonl", [{"id": "p1", "expect": "clean", "original": "Ana chegou.",
                                         "candidate": "Ana não chegou."}])
            spec = spec_of({"path": path, "adapter": "semantic_suite", "split": "development"},
                           {"path": pred, "adapter": "risk_sample", "split": "adversarial"})
            record = evaluation.run(spec, ws.root, recorded_at="t")
        finally:
            ws.close()
        dev = record["metrics"]["development"]["semantic_risk"]
        self.assertEqual(dev["counts"], {"detected": 1, "missed": 1, "false_alarm": 0, "correct_clear": 1,
                                         "abstained": 0, "not_applicable": 1})
        self.assertEqual((dev["sensitivity"]["k"], dev["sensitivity"]["n"]), (1, 2))
        self.assertEqual((dev["false_alarm_rate"]["k"], dev["false_alarm_rate"]["n"]), (0, 1))
        self.assertEqual(dev["sensitivity"]["wilson95"], evaluation.wilson(1, 2))
        adv = record["metrics"]["adversarial"]["semantic_risk"]
        self.assertEqual(adv["counts"]["false_alarm"], 1, "a clean label flagged by the gate is a false alarm")
        self.assertEqual(set(record["metrics"]), {"development", "adversarial"}, "splits are never pooled")

    def test_the_record_keeps_hashes_not_texts(self):
        record = evaluation.run(SPEC, ROOT, recorded_at="t")
        dumped = json.dumps(record, ensure_ascii=False)
        self.assertNotIn("O deploy não deve ser feito antes das 18h.", dumped)
        # Non-empty first (Assertiva CP14, vacuous all() confirmed by a negative control).
        self.assertEqual(record["status"], "COMPLETE")
        self.assertGreater(len(record["results"]), 200)
        self.assertTrue(all("original_sha256" in r or "text_sha256" in r for r in record["results"]))

    def test_the_declared_axes_are_the_ones_measured(self):
        # CP15 (Derivanta Engine: AXES was named only at its definition): the axis names are a
        # contract of the record, so the declared tuple must match what the run measures.
        record = evaluation.run(SPEC, ROOT, recorded_at="t")
        per_row = {k for row in record["results"] for k in row if k in evaluation.AXES}
        self.assertEqual(per_row, set(evaluation.AXES))
        for split, metrics in record["metrics"].items():
            with self.subTest(split=split):
                measured = set(metrics) - {"cases", "semantic_risk_by_kind"}
                self.assertTrue(measured)
                self.assertLessEqual(measured, set(evaluation.AXES), measured)


class RepositoryDataset(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.record = evaluation.run(SPEC, ROOT, recorded_at="fixed")

    def test_complete_and_reproducible(self):
        self.assertEqual(self.record["status"], "COMPLETE", self.record["problems"])
        again = evaluation.run(SPEC, ROOT, recorded_at="fixed")
        self.assertEqual(again["results_sha256"], self.record["results_sha256"])
        self.assertEqual(again["metrics"], self.record["metrics"])

    def test_no_source_is_called_independent(self):
        self.assertEqual(len(self.record["inputs"]), len(SPEC["sources"]))   # not vacuous (CP14)
        self.assertTrue(all(not i["independent"] for i in self.record["inputs"]))
        self.assertNotIn("external_independent_holdout", self.record["metrics"])
        self.assertIn("Nenhum número acima é validação independente", evaluation.render(self.record))

    def test_nothing_is_auto_accepted_without_identity(self):
        # Unconditional (Assertiva CP14, FALSE_GREEN_CANDIDATE confirmed by a negative control): with the
        # semantic_risk metric removed, the old `if` asserted nothing and passed.
        gate_splits = {"development", "frozen_regression"}
        self.assertTrue(gate_splits <= set(self.record["metrics"]))
        for split in gate_splits:
            self.assertEqual(self.record["metrics"][split]["semantic_risk"]["auto_accepted_without_identity"], 0, split)

    def test_known_misses_are_visible_not_hidden(self):
        # The predicate sample had 4 known misses (16/20, docs/releases/v0.8/AS_IS.md); CP6 detects pr-17 (recipient
        # omitted), so 3 remain (17/20). The core must show them, not hide them.
        misses = [r["id"] for r in self.record["results"] if r.get("semantic_risk") == "missed"]
        self.assertEqual(sorted(m for m in misses if m.startswith("cases-h07:")),
                         ["cases-h07:pr-09", "cases-h07:pr-10", "cases-h07:pr-13"], misses)


class Verification(unittest.TestCase):

    def setUp(self):
        self.record = evaluation.run(SPEC, ROOT, recorded_at="fixed")
        self.assertEqual(evaluation.verify_run(self.record), [])

    def test_an_edited_result_is_detected(self):
        edited = copy.deepcopy(self.record)
        row = next(r for r in edited["results"] if r.get("semantic_risk") == "missed")
        row["semantic_risk"] = "detected"
        self.assertTrue(any("results_sha256" in p for p in evaluation.verify_run(edited)))
        edited["results_sha256"] = evaluation.results_digest(edited["results"])     # a careful forger
        self.assertTrue(any("metrics do not follow" in p for p in evaluation.verify_run(edited)))

    def test_inflated_metrics_and_promoted_arms_are_detected(self):
        edited = copy.deepcopy(self.record)
        edited["metrics"]["frozen_regression"]["semantic_risk"]["counts"]["missed"] = 0
        self.assertTrue(evaluation.verify_run(edited))
        edited = copy.deepcopy(self.record)
        edited["arms_not_run"][0]["evidence"] = "ENGINE_EXECUTED"
        self.assertTrue(evaluation.verify_run(edited))
        edited = copy.deepcopy(self.record)
        edited["problems"] = ["x"]
        self.assertTrue(evaluation.verify_run(edited))


class Cli(unittest.TestCase):

    def run_cli(self, *args):
        done = subprocess.run([sys.executable, "-B", "-m", "voznativa", "evaluate", *args], capture_output=True,
                              cwd=ROOT)
        return done.returncode, done.stdout.decode("utf-8"), done.stderr.decode("utf-8")

    def test_run_report_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, report = Path(tmp) / "run.json", Path(tmp) / "run.md"
            code, stdout, err = self.run_cli("evals/v08/datasets/gate-and-planner.json", "--out", str(out),
                                             "--report", str(report))
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(stdout)["status"], "COMPLETE")
            self.assertIn("frozen_regression", report.read_text(encoding="utf-8"))
            self.assertEqual(self.run_cli("--verify", str(out))[0], 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            data["results"][0]["status"] = "identical"
            out.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(self.run_cli("--verify", str(out))[0], 1)

    def test_invalid_spec_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "spec.json"
            spec.write_text(json.dumps(spec_of({"path": "../x.jsonl", "adapter": "semantic_suite",
                                                "split": "development"})), encoding="utf-8")
            code, stdout, _ = self.run_cli(str(spec))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
