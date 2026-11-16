"""v0.8.1 dogfood of a second academic document (PDF only): compare regression.

Fixtures are synthetic, in another domain; no text of the document is used.

* DF-08: an entity that span extraction finds inside a token (flattened math
  such as "C ∈Rm×n" from a PDF gives the entity "×n") was then looked up as a
  whole word, which it never is. Any edit anywhere in such a document was
  ``span_missing`` (critical) plus ``span_added``, so the long-form global
  validation reverted every unit and returned the original (real run: 13 of
  13 changed units reverted).
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402

KEEP = "A matriz de custos C ∈Rm×n reúne os fretes por rota. "


def codes(a, b):
    return {(i["code"], i.get("text")) for i in compare(a, b)["issues"]}


class EntityInsideAToken(unittest.TestCase):

    def test_an_unchanged_token_is_not_a_lost_or_added_entity(self):
        a = KEEP + "O relatório saiu ontem pela manhã."
        b = KEEP + "O relatório saiu ontem de manhã."
        found = codes(a, b)
        self.assertNotIn(("span_missing", "×n"), found)
        self.assertNotIn(("span_added", "×n"), found)
        self.assertNotEqual(compare(a, b)["status"], "fail")

    def test_control_removing_the_token_is_still_critical(self):
        a = KEEP + "O relatório saiu ontem."
        b = "A matriz de custos reúne os fretes por rota. O relatório saiu ontem."
        self.assertEqual(compare(a, b)["status"], "fail")

    def test_control_a_lost_named_entity_is_still_critical(self):
        a = "A transportadora Rodomar entregou a carga em Campinas."
        b = "A transportadora entregou a carga em Campinas."
        self.assertIn(("span_missing", "Rodomar"), codes(a, b))


if __name__ == "__main__":
    unittest.main()
