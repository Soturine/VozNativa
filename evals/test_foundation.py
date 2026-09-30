import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze import analyze
from semantic_guard import extract, guard
from voice_profile import profile
from region_consistency import inspect


class FoundationTests(unittest.TestCase):
    def test_analyzer_counts_sentences(self):
        result = analyze("Oi. Tudo bem?")
        self.assertEqual(result["sentences"], 2)

    def test_extracts_non_overlapping_protected_values(self):
        values = [item["text"] for item in extract("TC-072 ficou em 17% em 2026-09-30.")]
        self.assertIn("TC-072", values)
        self.assertIn("17%", values)
        self.assertIn("2026-09-30", values)
        self.assertNotIn("17", values)
        self.assertNotIn("2026", values)

    def test_semantic_guard_detects_number_loss_even_with_same_digits_elsewhere(self):
        original = "O sistema usa PostgreSQL 17 e teve 17% de falhas."
        candidate = "O sistema usa PostgreSQL e teve 17% de falhas."
        result = guard(original, candidate)
        self.assertFalse(result["ok"])
        self.assertTrue(any(item["text"] == "17" for item in result["missing"]))

    def test_semantic_guard_respects_multiplicity(self):
        result = guard("Foram 10 casos e mais 10 casos.", "Foram 10 casos.")
        self.assertFalse(result["ok"])
        lost = next(item for item in result["missing"] if item["text"] == "10")
        self.assertEqual(lost["expected_count"], 2)
        self.assertEqual(lost["actual_count"], 1)

    def test_voice_profile_is_observational(self):
        result = profile(["vc fez o deploy? sim, fiz o deploy."])
        self.assertEqual(result["locale"], "pt-BR")
        self.assertIn("vc", result["lexicon"]["abbreviations"])
        self.assertIn("deploy", result["lexicon"]["foreign_terms"])
        self.assertFalse(result["inference_policy"]["infer_identity"])

    def test_regional_overfit_guard(self):
        result = inspect("uai uai uai uai trem")
        self.assertEqual(result["regional_overfit"], "high")
        self.assertEqual(result["note"], "baseline heuristic; not a dialect classifier")


if __name__ == "__main__":
    unittest.main()
