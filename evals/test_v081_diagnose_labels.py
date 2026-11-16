"""v0.8.1 dogfood of a second academic document (PDF only): diagnose regressions.

Fixtures are synthetic, in another domain (logistics); no text of the document is used.

* DF-06: ``repeated_word`` read a one-letter label followed by the conjunction
  or article ("os lotes C, E e G", "o lote A a ser enviado") as a repeated
  word, with ``auto_fix``: ``--mode PROOFREAD`` deleted the conjunction.
* DF-07: ``acronym_redefined`` (major, internal contradiction) compared the
  six words before the parenthesis. The same expansion with a different lead
  ("Implantação do Sistema de Gestão de Estoques (SGE)") and a parenthesis
  that is not an acronym definition at all ("Rotina de cálculo de frete
  (SQL)") were reported as contradictions.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.diagnose import diagnose, proofread  # noqa: E402
from voznativa.router import route  # noqa: E402


def found(text):
    return {(d["class"], d["type"]) for d in diagnose(text, route(text, genre="academic"))["diagnostics"]}


LABELS = [
    "Os lotes C, E e G chegaram ao depósito na segunda remessa.",
    "O lote A a ser enviado saiu do armazém central ontem.",
    "As caixas dos corredores A a C foram conferidas pela equipe.",
]


class OneLetterLabels(unittest.TestCase):

    def test_a_label_before_the_conjunction_is_not_a_repeated_word(self):
        for text in LABELS:
            with self.subTest(text=text[:30]):
                self.assertNotIn(("formal_error", "repeated_word"), found(text))

    def test_proofread_never_deletes_the_conjunction_after_a_label(self):
        for text in LABELS:
            with self.subTest(text=text[:30]):
                context = route(text, genre="academic")
                result = proofread(text, diagnose(text, context), "PROOFREAD")
                self.assertEqual(result["text"], text)

    def test_control_a_real_repetition_is_still_fixed(self):
        self.assertIn(("formal_error", "repeated_word"), found("O pedido foi enviado para o o cliente ontem."))
        self.assertIn(("formal_error", "repeated_word"), found("Compramos caixas e e fitas para a expedição."))


class AcronymExpansions(unittest.TestCase):

    def test_the_same_expansion_with_a_different_lead_is_not_a_contradiction(self):
        text = ("O Sistema de Gestão de Estoques (SGE) registra as entradas. "
                "A seção seguinte descreve a Implantação do Sistema de Gestão de Estoques (SGE) nos armazéns.")
        self.assertNotIn(("internal_contradiction", "acronym_redefined"), found(text))

    def test_a_parenthesis_that_does_not_spell_the_acronym_is_not_a_definition(self):
        text = ("A Rotina de cálculo de frete (SQL) lê as tabelas. "
                "A Rotina de conferência dos pedidos (SQL) gera o relatório.")
        self.assertNotIn(("internal_contradiction", "acronym_redefined"), found(text))

    def test_control_two_different_expansions_are_still_a_contradiction(self):
        text = ("O Centro de Distribuição (CD) recebeu a carga. Depois, o Controle de Despesas (CD) "
                "aprovou o frete.")
        self.assertIn(("internal_contradiction", "acronym_redefined"), found(text))


if __name__ == "__main__":
    unittest.main()
