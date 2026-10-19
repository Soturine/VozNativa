"""Benchmark runner: tiers kept apart, frozen cases usable by every compared system."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.benchmark import invariant_preserved, load_cases, run
from voznativa.providers import EMULATE_MIN_WORDS
from voznativa.review import content_hash

CASES = ROOT / "benchmarks" / "cases" / "ptbr-v1.jsonl"


class FrozenCases(unittest.TestCase):
    def test_cases_fit_every_system_including_emulate(self):
        for case in load_cases(CASES):
            self.assertGreaterEqual(len(case["text"].split()), EMULATE_MIN_WORDS, case["id"])

    def test_invariants_hold_on_the_source_itself(self):
        for case in load_cases(CASES):
            for phrase in case.get("must_preserve", []):
                self.assertTrue(invariant_preserved(phrase, case["text"], case["text"]), (case["id"], phrase))


class Runner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.outputs = Path(self.tmp.name)
        case = load_cases(CASES)[0]
        self.case = case
        good = self.outputs / "sys-a"
        good.mkdir()
        candidate = case["text"].replace("Prezados, boa tarde.", "Boa tarde, pessoal.")
        (good / f"{case['id']}.txt").write_text(candidate, encoding="utf-8")
        bound = {"original_sha256": content_hash(case["text"]), "candidate_sha256": content_hash(candidate)}
        judgment = {"kind": "llm", "judge_id": "fake-llm", "verdict": "equivalent", **bound,
                    "claims": [{"source": "x", "status": "preserved"}], "added_claims": []}
        (good / f"{case['id']}.judgment-1.json").write_text(json.dumps(judgment), encoding="utf-8")
        claimed = {**judgment, "kind": "human", "judge_id": "someone"}
        (good / f"{case['id']}.judgment-2.json").write_text(json.dumps(claimed), encoding="utf-8")
        bad = self.outputs / "sys-b"
        bad.mkdir()
        (bad / f"{case['id']}.txt").write_text(case["text"].replace("22h", "23h"), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_tiers_are_reported_separately(self):
        report = run(CASES, self.outputs)
        a = report["systems"]["sys-a"]
        row = next(r for r in a["results"] if r["id"] == self.case["id"])
        self.assertIn(row["deterministic_status"], {"no_deterministic_issues", "review_required"})
        self.assertEqual(row["judgments"][0]["kind"], "llm")
        self.assertEqual(a["judgments_by_kind"], {"llm": 1, "human": 1})
        # The unsigned human file is recorded but proves nothing.
        self.assertEqual(row["judgments"][1]["authenticity"], "unsigned")
        self.assertEqual(a["human_judgments_verified"], 0)
        self.assertEqual(report["scoring"]["detectors"], "not used")

    def test_missing_outputs_and_failures_lower_the_rate(self):
        report = run(CASES, self.outputs)
        b = report["systems"]["sys-b"]
        self.assertEqual(b["missing_outputs"], len(load_cases(CASES)) - 1)
        self.assertEqual(b["hard_pass"], 0)
        self.assertEqual(b["hard_pass_rate"], 0.0)

    def test_manifest_is_recorded_or_warned(self):
        self.assertTrue(run(CASES, self.outputs)["warnings"])
        manifest = self.outputs / "manifest.json"
        manifest.write_text(json.dumps({"benchmark_version": "ptbr-v1"}), encoding="utf-8")
        report = run(CASES, self.outputs, manifest)
        self.assertEqual(report["manifest"]["benchmark_version"], "ptbr-v1")
        self.assertEqual(report["warnings"], [])
        self.assertEqual(len(report["cases_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
