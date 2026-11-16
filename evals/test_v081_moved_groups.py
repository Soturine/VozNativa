"""v0.8.1 dogfood of a second academic document (PDF only): compare regression.

Fixtures are synthetic, in another domain; no text of the document is used.

* DF-09: ``*_moved`` (same total, a marker lost by one aligned sentence and
  gained by another) counted sentence pairs one by one. A split sentence
  whose marker went to the new, unaligned sentence counted as "lost"; a
  citation left after the period (". [17].") is a sentence of its own, aligned
  by the number to the merged candidate sentence, whose marker it then
  "gained". Two such legitimate edits far apart in one long document were a
  critical ``causality_moved``, so the global validation reverted units
  (real run: 6 units reverted, 5 of them unrelated).
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402

FILLER = ("O turno da manhã conferiu as caixas do corredor central. A balança do depósito foi aferida "
          "na terça. O motorista entregou as notas ao almoxarife. A empilhadeira voltou da oficina "
          "revisada. O gerente aprovou a escala de férias do setor. A planilha de estoque foi enviada "
          "ao financeiro.")
SPLIT_SRC = "A demanda caiu no inverno de forma acentuada, relacionada ao feriado prolongado na região."
SPLIT_OUT = "A demanda caiu no inverno de forma acentuada. Essa queda está relacionada ao feriado prolongado na região."
MERGE_SRC = "As tarifas subiram no porto, associadas à greve dos estivadores. [17]."
MERGE_OUT = "As tarifas subiram no porto, associadas à greve dos estivadores [17]."


def codes(a, b):
    return {i["code"]: i["severity"] for i in compare(a, b)["issues"]}


class MovedCountsGroups(unittest.TestCase):

    def test_a_split_and_a_citation_merge_far_apart_are_not_a_move(self):
        a = f"{SPLIT_SRC} {FILLER} {MERGE_SRC}"
        b = f"{SPLIT_OUT} {FILLER} {MERGE_OUT}"
        self.assertNotIn("causality_moved", codes(a, b))
        self.assertNotEqual(compare(a, b)["status"], "fail")

    def test_each_edit_alone_was_already_fine(self):
        for a, b in ((SPLIT_SRC, SPLIT_OUT), (MERGE_SRC, MERGE_OUT)):
            with self.subTest(a=a[:30]):
                self.assertNotIn("causality_moved", codes(f"{a} {FILLER}", f"{b} {FILLER}"))

    def test_control_a_real_distant_move_is_still_critical(self):
        a = f"A transportadora não pagou o frete de março. {FILLER} A seguradora pagou a multa do atraso."
        b = f"A transportadora pagou o frete de março. {FILLER} A seguradora não pagou a multa do atraso."
        self.assertEqual(codes(a, b).get("negation_moved"), "critical")

    def test_control_a_real_move_between_neighbours_is_still_critical(self):
        a = "A transportadora não pagou o frete. A seguradora pagou a multa."
        b = "A transportadora pagou o frete. A seguradora não pagou a multa."
        self.assertEqual(codes(a, b).get("negation_moved"), "critical")


if __name__ == "__main__":
    unittest.main()
