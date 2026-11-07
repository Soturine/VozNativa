"""v0.8 CP7 (V08-GAP-13): sentence alignment ties.

Two source sentences with the same content stems ("O orçamento pode passar
de R$ 1.000,00." / "O orçamento não pode passar de R$ 1.000,00.") both
aligned to the first of them in the candidate, so the negated one lost its
negation in the alignment and a candidate that only appended a sentence
failed with critical negation_moved / modality_moved. Found on the
repository's own docs (17k words) and reproduced here in nine short
paragraphs: it needs two pairs of twins in opposite orders, not size.

The guards are unchanged; only ties are decided differently (nearest
position). On the code before the fix (c353058) three tests here fail: the
append (false red), the twins' alignment, and the swap of the twins, which
passed silently (a false green). The GuardsStillFire controls pass on both
versions: no detection was given up. A first version that preferred an
identical surface text made three of those controls fail and was rejected."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import ledger  # noqa: E402
from voznativa.compare import _align, compare  # noqa: E402

# As in the README's quickstart, quoted inside a longer document: two sentences
# that differ only by "não" have the same content stems.
POSITIVE = "O orçamento pode passar de R$ 12.000,00."
NEGATIVE = "O orçamento não pode passar de R$ 12.000,00."
# A second pair of twins in the opposite order: the false negation_moved needed a
# negated sentence aligned to its positive twin (lost) *and* a positive one aligned
# to its negated twin (gained), as in the 17k-word document of the finding.
DEPLOY_NEG = "O deploy não deve ser feito antes das 18h."
DEPLOY_POS = "O deploy deve ser feito antes das 18h."
PARTS = [
    "# Relatório do trimestre",
    "A equipe revisou as metas e publicou o resumo na sexta-feira.",
    POSITIVE,
    "O fornecedor confirmou a entrega para o dia 14/11/2025.",
    NEGATIVE,
    "A auditoria encontrou dois problemas no estoque.",
    DEPLOY_NEG,
    "A janela de manutenção foi marcada para o sábado.",
    DEPLOY_POS,
]
DOC = "\n\n".join(PARTS) + "\n"


class TiesInAlignment(unittest.TestCase):

    def test_appending_a_sentence_is_not_a_moved_negation(self):
        report = compare(DOC, DOC + "\nUma frase nova no fim.\n")
        codes = {i["code"] for i in report["issues"]}
        self.assertNotEqual(report["status"], "fail", codes)
        self.assertFalse({"negation_moved", "modality_moved"} & codes, codes)

    def test_identical_sentences_align_to_themselves(self):
        src = ledger.build(DOC)
        out = ledger.build(DOC + "\nUma frase nova no fim.\n")
        alignment = {i: j for i, j, _ in _align(src, out)}
        for i, entry in enumerate(src.entries):
            self.assertEqual(alignment[i], i, entry.sentence.text)

    def test_a_higher_similarity_still_wins_over_position(self):
        src = ledger.build("Ana revisou o contrato de aluguel. O banco aprovou o crédito.")
        out = ledger.build("O banco aprovou o crédito. Ana revisou o contrato de aluguel.")
        self.assertEqual([(i, j) for i, j, _ in _align(src, out)], [(0, 1), (1, 0)])


class GuardsStillFire(unittest.TestCase):

    def critical(self, candidate):
        report = compare(DOC, candidate)
        return report["status"], {i["code"] for i in report["issues"] if i["severity"] == "critical"}

    def test_negation_removed_from_the_negated_twin(self):
        status, codes = self.critical(DOC.replace(NEGATIVE, POSITIVE))
        self.assertEqual(status, "fail")
        self.assertIn("negation_changed", codes)

    def test_negation_added_to_the_positive_twin(self):
        status, codes = self.critical(DOC.replace(POSITIVE, NEGATIVE, 1))
        self.assertEqual(status, "fail")
        self.assertIn("negation_changed", codes)

    def test_negation_removed_elsewhere_and_modality_changed(self):
        self.assertEqual(self.critical(DOC.replace("A auditoria encontrou", "A auditoria não encontrou"))[0], "fail")
        self.assertEqual(self.critical(DOC.replace(POSITIVE, "O orçamento deve passar de R$ 12.000,00."))[0], "fail")

    def test_a_negation_really_moved_between_sentences(self):
        candidate = DOC.replace(NEGATIVE, POSITIVE).replace("A auditoria encontrou", "A auditoria não encontrou")
        self.assertEqual(self.critical(candidate)[0], "fail")

    def test_the_twins_swapped_is_not_silent(self):
        swapped = DOC.replace(POSITIVE, "@@").replace(NEGATIVE, POSITIVE).replace("@@", NEGATIVE)
        self.assertNotEqual(compare(DOC, swapped)["status"], "no_deterministic_issues")


if __name__ == "__main__":
    unittest.main()
