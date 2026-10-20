"""PT-BR number words, durations and the digit/word boundary (v0.3.0 M1.3)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare
from voznativa.spans import extract


def keys(text):
    return [s.key for s in extract(text) if s.type != "entity"]


class NumberWords(unittest.TestCase):
    def test_compounds(self):
        self.assertEqual(keys("vinte e três pessoas"), ["number:23"])
        self.assertEqual(keys("cento e vinte currículos"), ["number:120"])
        self.assertEqual(keys("duzentos e cinquenta convidados"), ["number:250"])
        self.assertEqual(keys("dois mil e trezentos"), ["number:2300"])
        self.assertEqual(keys("meia dúzia de pães"), ["number:6"])
        self.assertEqual(keys("uma dúzia"), ["number:12"])

    def test_ranges_and_articles_are_not_compounds(self):
        self.assertEqual(keys("entre três e quatro pessoas"), ["number:3", "number:4"])
        self.assertEqual(keys("Um carro chegou."), [])

    def test_words_and_digits_with_currency(self):
        self.assertEqual(keys("mil e quinhentos reais"), ["money:BRL:1500"])
        self.assertEqual(keys("3 mil reais"), ["money:BRL:3000"])
        self.assertEqual(keys("5 milhões de reais"), ["money:BRL:5000000"])
        self.assertEqual(keys("17 por cento"), ["percent:17"])

    def test_equivalence_and_change(self):
        self.assertEqual(compare("Tem trinta e oito alunos.", "Tem 38 alunos.")["status"], "no_deterministic_issues")
        self.assertEqual(compare("Tem trinta e oito alunos.", "Tem 83 alunos.")["status"], "fail")
        self.assertEqual(compare("Custa dois mil e trezentos reais.", "Custa R$ 2.300.")["status"],
                         "no_deterministic_issues")


class Durations(unittest.TestCase):
    def test_durations_compare_in_seconds(self):
        self.assertEqual(keys("meia hora"), ["quantity:1800:s"])
        self.assertEqual(keys("leva 2 horas"), keys("leva 120 minutos"))
        self.assertEqual(compare("O teste leva meia hora.", "O teste leva 30 minutos.")["status"],
                         "no_deterministic_issues")

    def test_minutos_is_not_a_million(self):
        # Pre-existing v0.2.0 bug: "mi" (milhão) matched the start of "minutos".
        self.assertEqual(keys("120 minutos"), ["quantity:7200:s"])
        self.assertEqual(keys("3 mi de usuários"), ["number:3000000"])

    def test_clock_time_needs_a_preposition(self):
        self.assertEqual(keys("chego às 18 horas"), ["time:18:00"])
        self.assertEqual(keys("dura 18 horas"), ["quantity:64800:s"])


if __name__ == "__main__":
    unittest.main()
