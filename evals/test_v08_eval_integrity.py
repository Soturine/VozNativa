"""v0.8 CP5: what an evaluation record can and cannot prove.

* ``results_sha256`` is an integrity digest, not a signature: a forger who
  edits the results recomputes it and ``verify_run`` passes. ``replay_run``
  re-executes the run with the code and inputs of its revision and catches it.
* ``independent: true`` is a claim: an independent split needs evidence whose
  checkable parts are checked (the freezing commit holds the file with the
  MANIFEST hash; an attestation file exists; the author is not the developer).
* Paths that leave the repository through a link are refused.
* A case shared between a holdout and another source contaminates the holdout.

Each test drives real git repositories in temporary directories."""
import copy
import json
import os
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

NEG = {"id": "n1", "category": "negation", "original": "O deploy não deve ser feito hoje.",
       "candidate": "O deploy deve ser feito hoje.", "expect": {"status": ["fail"]}}
SAME = {"id": "s1", "category": "identity", "original": "O relatório sai amanhã cedo para o cliente.",
        "candidate": "O relatório sai amanhã cedo para o cliente.", "expect": {"status": ["identical"]}}


def git(repo, *args):
    done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=repo,
                          capture_output=True, text=True)
    if done.returncode:
        raise AssertionError(done.stderr)
    return done.stdout.strip()


class Repo:
    def __init__(self, with_package=False):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "core.autocrlf", "false")
        (self.root / "s").mkdir()
        if with_package:
            # From the imported package, so the test also runs against an installed wheel.
            from voznativa.paths import references_dir
            shutil.copytree(Path(evaluation.__file__).parent, self.root / "voznativa",
                            ignore=shutil.ignore_patterns("__pycache__", "_bundled"))
            shutil.copytree(references_dir(), self.root / "references")

    def write_suite(self, name, rows, manifest_entry):
        path = self.root / "s" / name
        path.write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"))
        manifest = self.root / "s" / "MANIFEST.json"
        data = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {"suites": {}}
        data["suites"][name] = dict(manifest_entry, sha256=sha256_lf(path))
        manifest.write_text(json.dumps(data), encoding="utf-8")
        return f"s/{name}"

    def commit(self, message="c"):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", message)
        return git(self.root, "rev-parse", "HEAD")

    def close(self):
        self.tmp.cleanup()


def spec_of(*sources):
    return {"kind": "voznativa.eval_dataset", "schema_version": 1, "id": "t", "sources": list(sources)}


class IndependenceNeedsEvidence(unittest.TestCase):

    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.close()

    def independent_spec(self, path):
        return spec_of({"path": path, "adapter": "semantic_suite", "split": "external_independent_holdout"})

    def assert_invalid(self, path, fragment):
        record = evaluation.run(self.independent_spec(path), self.repo.root, recorded_at="t")
        self.assertEqual(record["status"], "INVALID")
        self.assertTrue(any(fragment in p for p in record["problems"]), record["problems"])

    def test_a_bare_flag_is_not_enough(self):
        path = self.repo.write_suite("h.jsonl", [NEG], {"independent": True, "frozen": True})
        self.assert_invalid(path, "without independence_evidence")

    def test_missing_fields_and_the_developer_as_author(self):
        path = self.repo.write_suite("h.jsonl", [NEG], {"independent": True, "frozen": True,
                                                        "independence_evidence": {"prepared_by": "Maria"}})
        self.assert_invalid(path, "independence_evidence.custodian missing")
        path = self.repo.write_suite("h.jsonl", [NEG], {"independent": True, "frozen": True,
                                                        "independence_evidence": {
                                                            "prepared_by": "VozNativa developer", "custodian": "x",
                                                            "frozen_commit": "HEAD", "attestation": "s/MANIFEST.json"}})
        self.repo.commit()
        self.assert_invalid(path, "names the engine's developer")

    def test_the_freezing_commit_must_hold_the_same_file(self):
        (self.repo.root / "ATTESTATION.md").write_text("custódia: Maria\n", encoding="utf-8")
        path = self.repo.write_suite("h.jsonl", [NEG], {"independent": True, "frozen": True})
        first = self.repo.commit("freeze")
        evidence = {"prepared_by": "Maria (revisora externa)", "custodian": "Maria", "frozen_commit": first,
                    "attestation": "ATTESTATION.md"}
        path = self.repo.write_suite("h.jsonl", [NEG], {"independent": True, "frozen": True,
                                                        "independence_evidence": evidence})
        record = evaluation.run(self.independent_spec(path), self.repo.root, recorded_at="t")
        self.assertEqual(record["status"], "COMPLETE", record["problems"])
        self.assertIn("DECLARED", record["inputs"][0]["independence"])
        # The cases changed after the freezing commit (and the MANIFEST hash was updated to hide it).
        path = self.repo.write_suite("h.jsonl", [NEG, SAME], {"independent": True, "frozen": True,
                                                              "independence_evidence": evidence})
        self.assert_invalid(path, "does not have the MANIFEST sha256")
        evidence = dict(evidence, frozen_commit="0" * 40)
        path = self.repo.write_suite("h.jsonl", [NEG], {"independent": True, "frozen": True,
                                                        "independence_evidence": evidence})
        self.assert_invalid(path, "does not contain")
        evidence = dict(evidence, frozen_commit=first, attestation="../fora.md")
        path = self.repo.write_suite("h.jsonl", [NEG], {"independent": True, "frozen": True,
                                                        "independence_evidence": evidence})
        self.assert_invalid(path, "attestation")


class PathsStayInside(unittest.TestCase):

    def test_a_link_out_of_the_root_is_refused(self):
        with tempfile.TemporaryDirectory() as outside, tempfile.TemporaryDirectory() as root:
            target = Path(outside) / "fora.jsonl"
            target.write_text(json.dumps(NEG) + "\n", encoding="utf-8")
            link = Path(root) / "dentro.jsonl"
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"this system cannot create a symlink here: {error}")
            record = evaluation.run(spec_of({"path": "dentro.jsonl", "adapter": "semantic_suite",
                                             "split": "development"}), Path(root), recorded_at="t")
        self.assertEqual(record["status"], "INVALID")
        self.assertTrue(any("resolves outside" in p for p in record["problems"]), record["problems"])

    @unittest.skipUnless(os.name == "nt", "directory junctions are a Windows feature")
    def test_a_windows_junction_out_of_the_root_is_refused(self):
        # A junction needs no privilege on Windows (a symlink does), and escapes the same way.
        with tempfile.TemporaryDirectory() as outside, tempfile.TemporaryDirectory() as root:
            (Path(outside) / "fora.jsonl").write_text(json.dumps(NEG) + "\n", encoding="utf-8")
            done = subprocess.run(["cmd", "/c", "mklink", "/J", str(Path(root) / "j"), outside], capture_output=True)
            if done.returncode:
                self.skipTest(f"mklink /J failed: {done.stderr!r}")
            try:
                record = evaluation.run(spec_of({"path": "j/fora.jsonl", "adapter": "semantic_suite",
                                                 "split": "development"}), Path(root), recorded_at="t")
            finally:
                os.rmdir(Path(root) / "j")      # remove the junction, never what it points to
        self.assertEqual(record["status"], "INVALID")
        self.assertTrue(any("resolves outside" in p for p in record["problems"]), record["problems"])

    def test_the_inside_check_itself(self):
        with tempfile.TemporaryDirectory() as root:
            r = Path(root)
            self.assertTrue(evaluation._inside(r, r / "a" / "b.jsonl"))
            self.assertFalse(evaluation._inside(r, r / ".." / "x.jsonl"))
            self.assertFalse(evaluation._inside(r, Path(tempfile.gettempdir()) / "x.jsonl"))


class Leakage(unittest.TestCase):

    def test_a_development_case_copied_into_a_holdout_invalidates_the_run(self):
        repo = Repo()
        try:
            dev = repo.write_suite("dev.jsonl", [NEG], {"independent": False})
            hold = repo.write_suite("hold.jsonl", [dict(NEG, id="h1"), SAME], {"independent": False, "frozen": True})
            spec = spec_of({"path": dev, "adapter": "semantic_suite", "split": "development"},
                           {"path": hold, "adapter": "semantic_suite", "split": "prospective_holdout"})
            record = evaluation.run(spec, repo.root, recorded_at="t")
            self.assertEqual(record["status"], "INVALID")
            self.assertTrue(any("holdout contaminated" in p for p in record["problems"]))
            self.assertEqual(record["leakage"]["same_pair"], 1)
            spec["sources"][1]["split"] = "frozen_regression"     # reported, not blocking, for a regression set
            record = evaluation.run(spec, repo.root, recorded_at="t")
            self.assertEqual(record["status"], "COMPLETE")
            self.assertEqual(record["leakage"]["cross_split"], 1)
        finally:
            repo.close()

    def test_near_duplicates_need_six_words(self):
        rows = [{"id": "a", "source": "x", "split": "development", "text": "Ana revisa o contrato e Bruno assina hoje"},
                {"id": "b", "source": "y", "split": "prospective_holdout",
                 "text": "Ana revisa o contrato e Bruno assina hoje!"},
                {"id": "c", "source": "z", "split": "development", "text": "Sim."},
                {"id": "d", "source": "w", "split": "prospective_holdout", "text": "Não."}]
        found = evaluation.leakage(rows)
        self.assertEqual([(l["a"], l["b"], l["kind"]) for l in found["links"]], [("a", "b", "exact")])
        rows[1]["text"] = "Ana revisa o contrato e Bruno assina hoje cedo"       # 6 of 7 trigrams shared
        found = evaluation.leakage(rows)
        self.assertEqual(found["links"][0]["kind"], "near")
        self.assertAlmostEqual(found["links"][0]["score"], 0.857, places=3)
        rows[1]["text"] = "Ana revisa o contrato e Bruno assina hoje à tarde"    # 6 of 8: below 0.8
        self.assertEqual(evaluation.leakage(rows)["links"], [])
        rows[1]["text"] = "Ana revisa o contrato e Bruno assina hoje cedo"
        self.assertEqual(len(found["holdout_contaminated"]), 1)

    def test_the_repository_dataset_reports_its_known_leak(self):
        record = evaluation.run(json.loads((ROOT / "evals" / "v08" / "datasets" / "gate-and-planner.json")
                                           .read_text(encoding="utf-8")), ROOT, recorded_at="t")
        pairs = {(p["a"], p["b"]) for p in record["leakage"]["pairs"] if p["same_pair"]}
        self.assertIn(("relations:rel-agent-001", "holdout:ho-022"), pairs)


class ReplayIsNotTheDigest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo = Repo(with_package=True)
        path = cls.repo.write_suite("dev.jsonl", [NEG, SAME], {"independent": False})
        cls.spec = spec_of({"path": path, "adapter": "semantic_suite", "split": "development"})
        cls.revision = cls.repo.commit()
        cls.record = evaluation.run(cls.spec, cls.repo.root, recorded_at="t")

    @classmethod
    def tearDownClass(cls):
        cls.repo.close()

    def test_a_clean_run_reproduces(self):
        self.assertEqual((self.record["revision"], self.record["dirty"]), (self.revision, False))
        result = evaluation.replay_run(self.record, self.repo.root)
        self.assertEqual(result["status"], "REPRODUCED", result)
        self.assertIn("not a signature", result["note"])

    def test_a_forger_passes_verify_but_not_replay(self):
        forged = copy.deepcopy(self.record)
        forged["results"][0]["semantic_risk"] = "missed"
        forged["results"][0]["status"] = "no_deterministic_issues"
        forged["results_sha256"] = evaluation.results_digest(forged["results"])
        forged["metrics"] = evaluation.metrics(forged["results"])
        self.assertEqual(evaluation.verify_run(forged), [], "integrity alone cannot catch a careful forger")
        self.assertEqual(evaluation.replay_run(forged, self.repo.root)["status"], "DIFFERENT")

    def test_records_that_cannot_be_replayed_say_so(self):
        dirty = dict(self.record, dirty=True)
        self.assertEqual(evaluation.replay_run(dirty, self.repo.root)["status"], "NOT_REPLAYABLE")
        unknown = dict(self.record, revision="0" * 40)
        self.assertEqual(evaluation.replay_run(unknown, self.repo.root)["status"], "NOT_REPLAYABLE")
        no_spec = {k: v for k, v in self.record.items() if k != "dataset_spec"}
        self.assertEqual(evaluation.replay_run(no_spec, self.repo.root)["status"], "NOT_REPLAYABLE")
        other_spec = copy.deepcopy(self.record)
        other_spec["dataset_spec"]["id"] = "outro"
        self.assertEqual(evaluation.replay_run(other_spec, self.repo.root)["status"], "NOT_REPLAYABLE")

    def test_inputs_changed_since_the_revision(self):
        changed = copy.deepcopy(self.record)
        changed["inputs"][0]["sha256_lf"] = "0" * 64
        result = evaluation.replay_run(changed, self.repo.root)
        self.assertEqual(result["status"], "DIFFERENT")
        self.assertEqual(result["inputs"], ["s/dev.jsonl"])

    def test_the_record_states_its_limits(self):
        self.assertIn("not a signature", self.record["authenticity"])


if __name__ == "__main__":
    unittest.main()
