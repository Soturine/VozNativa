"""v0.8.1 dogfood (agent-led, long technical report): marker lexicon forms.

Fixtures are synthetic, in another domain; no text of the dogfooded document is used.

* DF-05: the causal and evidential lexicons listed finite forms ("gera",
  "gerou", "indica") but not the gerunds ("gerando", "indicando"), and had
  "por isso" without "por essa razão". In the real run, rewrites the planner
  itself asks for (", gerando X" -> " e gerou X"; ", indicando X" -> ", o que
  indica X"; "Por isso" -> "Por essa razão") changed the counts and were
  flagged major or critical, so good candidates were discarded; and deleting
  a causal gerund clause changed no count at all.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402

MARKERS = {"causality_changed", "causality_moved", "modality_changed", "modality_moved"}

EQUIVALENT = [
    ("A rede caiu na sexta, gerando atraso nas entregas.", "A rede caiu na sexta e gerou atraso nas entregas."),
    ("A chuva fechou a estrada, provocando filas no porto.", "A chuva fechou a estrada e provocou filas no porto."),
    ("O fornecedor atrasou. Por isso, o estoque acabou.", "O fornecedor atrasou. Por essa razão, o estoque acabou."),
    ("O fornecedor atrasou. Por isso, o estoque acabou.", "O fornecedor atrasou. Por esse motivo, o estoque acabou."),
    ("A margem foi de 3% a 9%, indicando incerteza na previsão.",
     "A margem foi de 3% a 9%, o que indica incerteza na previsão."),
    ("As vendas caíram em março, sugerindo efeito do feriado.",
     "As vendas caíram em março, o que sugere efeito do feriado."),
]
CAUSE_REMOVED = [
    ("A rede caiu na sexta, gerando atraso nas entregas.", "A rede caiu na sexta. Houve atraso nas entregas."),
    ("A margem foi de 3% a 9%, indicando incerteza na previsão.", "A margem foi de 3% a 9%. Há incerteza na previsão."),
]


def codes(original, candidate):
    return {i["code"] for i in compare(original, candidate)["issues"]}


class GerundAndPhraseForms(unittest.TestCase):

    def test_an_equivalent_form_is_not_a_marker_change(self):
        for original, candidate in EQUIVALENT:
            with self.subTest(candidate=candidate[:45]):
                self.assertEqual(codes(original, candidate) & MARKERS, set())

    def test_removing_the_causal_or_evidential_link_is_seen(self):
        for original, candidate in CAUSE_REMOVED:
            with self.subTest(candidate=candidate[:45]):
                self.assertTrue(codes(original, candidate) & MARKERS, compare(original, candidate)["issues"])

    def test_control_a_causal_link_removed_from_a_finite_verb_was_already_seen(self):
        self.assertTrue(codes("A rede caiu e gerou atraso nas entregas.",
                              "A rede caiu. Houve atraso nas entregas.") & MARKERS)


if __name__ == "__main__":
    unittest.main()
