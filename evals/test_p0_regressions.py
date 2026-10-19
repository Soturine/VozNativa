"""Regression tests for the P0 false greens found in the v0.1.0 audit.

Each test reproduces a case where the v0.1.0 guard or benchmark runner
accepted a candidate that changed protected content (false green) or
rejected one that preserved it (false red). They target the legacy script
API on purpose: the scripts must keep working after the package refactor.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from semantic_guard import extract, guard
from benchmark_runner import score_case, summarize


def values(text):
    return [item["text"] for item in extract(text)]


class MoneyAndNumbers(unittest.TestCase):
    def test_brazilian_money_is_one_span(self):
        self.assertIn("R$ 1.500,00", values("Custa R$ 1.500,00 por mês."))

    def test_money_value_change_is_detected(self):
        self.assertFalse(guard("Custa R$ 1.500,00.", "Custa R$ 1.900,00.")["ok"])

    def test_money_spacing_variant_is_preserved(self):
        self.assertTrue(guard("Custa R$ 149,90.", "O valor é R$149,90.")["ok"])

    def test_thousands_separator_is_one_number(self):
        self.assertIn("1.000.000", values("Temos 1.000.000 de usuários."))

    def test_number_swap_between_entities_is_not_silently_accepted(self):
        # Same multiset of numbers, different binding. A bag-of-spans check
        # cannot prove this is safe, so it must not report ok.
        self.assertFalse(guard("17 casos e 71 erros.", "71 casos e 17 erros.")["ok"])

    def test_percent_with_space(self):
        self.assertTrue(guard("Subiu 17 %.", "Subiu 17%.")["ok"])

    def test_semver_is_one_span(self):
        self.assertIn("20.11.1", values("Use Node 20.11.1 agora."))


class DatesAndTimes(unittest.TestCase):
    def test_written_date_is_one_span(self):
        self.assertIn("18 de outubro de 2026", values("Até 18 de outubro de 2026."))

    def test_written_date_change_is_detected(self):
        self.assertFalse(guard("Até 18 de outubro de 2026.", "Até 30 de outubro de 2026.")["ok"])

    def test_written_and_numeric_date_are_equivalent(self):
        self.assertTrue(guard("Até 18 de outubro de 2026.", "Até 18/10/2026.")["ok"])

    def test_time_change_is_detected(self):
        self.assertFalse(guard("chego 18:30", "chego 18:00")["ok"])

    def test_time_formats_are_equivalent(self):
        self.assertTrue(guard("chego 18h30", "chego às 18:30")["ok"])


class AdditionsAndStructure(unittest.TestCase):
    def test_added_number_is_detected(self):
        result = guard("O teste falhou.", "O teste falhou 3 vezes em 2025.")
        self.assertFalse(result["ok"])
        self.assertTrue(result["added"])

    def test_url_trailing_punctuation_is_not_part_of_url(self):
        self.assertTrue(guard("Veja https://x.com.", "Acesse https://x.com")["ok"])

    def test_inline_code_is_protected(self):
        self.assertFalse(guard("Rode `npm run build` antes.", "Rode o build antes.")["ok"])


class BenchmarkRunner(unittest.TestCase):
    CASE = {
        "id": "x",
        "text": "O serviço pode retornar HTTP 409 em PostgreSQL 17.",
        "must_preserve": ["PostgreSQL 17", "pode", "HTTP 409"],
    }

    def test_invariants_use_word_boundaries(self):
        result = score_case(self.CASE, "O serviço poderia retornar HTTP 4090 em PostgreSQL 170.")
        self.assertFalse(result["explicit_invariants_ok"])
        self.assertIn("HTTP 409", result["explicit_missing"])
        self.assertIn("PostgreSQL 17", result["explicit_missing"])

    def test_negated_invariant_is_not_preserved(self):
        result = score_case(self.CASE, "O serviço não pode retornar HTTP 409 em PostgreSQL 17.")
        self.assertFalse(result["explicit_invariants_ok"])

    def test_missing_outputs_count_against_pass_rate(self):
        rows = [
            {"id": "a", "protected_ok": True, "explicit_invariants_ok": True},
            {"id": "b", "missing_output": True},
        ]
        self.assertEqual(summarize(rows)["hard_pass_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
