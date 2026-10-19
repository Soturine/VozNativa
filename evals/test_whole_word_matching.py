"""Regression tests for false greens found in the pre-push qualification audit."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare
from voznativa.project import ground


class WholeWordMatching(unittest.TestCase):
    def test_entity_inside_another_word_does_not_count_as_present(self):
        report = compare("A Ana comprou banana.", "Alguém comprou banana.")
        self.assertEqual(report["status"], "fail")
        self.assertIn("span_missing", {i["code"] for i in report["issues"]})

    def test_entity_moved_to_sentence_start_is_still_present(self):
        report = compare("O deploy é feito pelo GitHub Actions.", "GitHub Actions faz o deploy.")
        self.assertNotIn("span_missing", {i["code"] for i in report["issues"]})

    def test_value_is_not_supported_by_a_longer_number(self):
        self.assertEqual(ground("São 17 casos.", facts=["Relatório de 2017."])["status"], "fail")
        self.assertEqual(ground("São 17 casos.", facts=["Foram 17 casos."])["status"], "no_deterministic_issues")


if __name__ == "__main__":
    unittest.main()
