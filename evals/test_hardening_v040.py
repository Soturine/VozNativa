"""v0.4.0 M0: regression tests for defects confirmed in the v0.3.0 audit.

Each class names the defect it pins down. Frozen suites are read, never edited.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.evals import check, run

SEMANTIC = ROOT / "evals" / "semantic"


class Ho007IsAClassificationDivergence(unittest.TestCase):
    """ho-007 asks for span_added; the engine catches the inserted clause as
    possible_addition. It was detected, so it must not be reported as a
    missed detection, and the strict count must not hide it either."""

    def test_detected_but_classified_under_another_code(self):
        case = next(c for c in map(json.loads, (SEMANTIC / "holdout.jsonl").read_text(encoding="utf-8").splitlines())
                    if c["id"] == "ho-007")
        result = check(case)
        self.assertIn(result["status"], {"fail", "review_required"})
        self.assertIn("possible_addition", result["codes"])
        self.assertFalse(result["passed"])
        self.assertEqual(result["failure_kind"], "classification_divergence")

    def test_suite_reports_strict_and_status_counts_apart(self):
        report = run(SEMANTIC / "holdout.jsonl", require_frozen=True)
        self.assertEqual(report["passed"], 23)          # the frozen expectation still fails
        self.assertEqual(report["status_passed"], 24)   # but nothing was missed
        self.assertEqual(report["failure_kinds"], {"classification_divergence": 1})

    def test_missed_detection_is_a_false_green(self):
        case = {"id": "x", "category": "value", "original": "O prazo é sexta.", "candidate": "O prazo é sexta.",
                "expect": {"status": ["fail"]}}
        self.assertEqual(check(case)["failure_kind"], "false_green")
        case = dict(case, candidate="O prazo não é sexta.", expect={"status": ["no_deterministic_issues"]})
        self.assertEqual(check(case)["failure_kind"], "false_red")


if __name__ == "__main__":
    unittest.main()
