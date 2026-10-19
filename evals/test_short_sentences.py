"""Regression tests for false greens found in the pre-push qualification audit."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare



class ShortSentences(unittest.TestCase):
    def test_negation_flip_in_a_short_sentence_fails(self):
        for original, candidate in (("Não vou.", "Vou."), ("nn posso", "posso"), ("Não vi ninguém.", "Vi alguém.")):
            self.assertEqual(compare(original, candidate)["status"], "fail", original)

    def test_short_rewording_without_flip_does_not_fail(self):
        self.assertNotEqual(compare("Não vou.", "Eu não vou.")["status"], "fail")


if __name__ == "__main__":
    unittest.main()
