import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analyze import analyze
from semantic_guard import extract, guard


class FoundationTests(unittest.TestCase):
    def test_analyzer_counts_sentences(self):
        result = analyze("Oi. Tudo bem?")
        self.assertEqual(result["sentences"], 2)

    def test_extracts_protected_values(self):
        values = [item["text"] for item in extract("TC-072 ficou em 17% em 2026-09-30.")]
        self.assertIn("TC-072", values)
        self.assertIn("17%", values)
        self.assertIn("2026-09-30", values)

    def test_semantic_guard_detects_loss(self):
        result = guard("O sistema usa PostgreSQL 17 e teve 17% de falhas.", "O sistema usa PostgreSQL e teve 17% de falhas.")
        self.assertFalse(result["ok"])
        self.assertTrue(any(item["text"] == "17" for item in result["missing"]))


if __name__ == "__main__":
    unittest.main()
