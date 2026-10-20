"""Claims inserted inside a sentence (v0.3.0 M1.2; known regression ho-007)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare


def codes(original, candidate):
    return {i["code"] for i in compare(original, candidate)["issues"]}


class InsertedClauses(unittest.TestCase):
    def test_inserted_achievement_clause_needs_review(self):
        report = compare("Trabalhei dois anos como analista de suporte antes de virar desenvolvedor.",
                         "Trabalhei dois anos como analista de suporte, onde conquistei o prêmio de destaque, "
                         "antes de virar desenvolvedor.")
        self.assertIn("possible_addition", {i["code"] for i in report["issues"]})
        self.assertNotIn(report["status"], {"no_deterministic_issues", "identical"})

    def test_reordering_clauses_is_not_an_addition(self):
        self.assertNotIn("possible_addition", codes(
            "Trabalhei dois anos como analista de suporte antes de virar desenvolvedor.",
            "Antes de virar desenvolvedor, trabalhei dois anos como analista de suporte."))

    def test_auxiliary_verbs_are_not_new_content(self):
        # Found by the unit suite: "sai" -> "será publicado" was flagged as a new clause.
        report = compare("O relatório sai na sexta-feira.", "O relatório será publicado na sexta-feira.")
        self.assertEqual(report["status"], "no_deterministic_issues", report["issues"])


if __name__ == "__main__":
    unittest.main()
