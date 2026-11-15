"""v0.8.1 dogfood (agent-led, long technical report): compare regression.

Fixtures are synthetic, written in another domain (logistics and purchasing);
no text of the dogfooded document is used.

* DF-04: ``compare`` checked omissions only per sentence and against the
  stems of the whole candidate, while additions were also checked per clause.
  Dropping a factual trailing clause (", gerando ..." with a concrete result)
  whose words occur elsewhere, or that leaves enough of its sentence, was
  no_deterministic_issues: a false green.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402

DROPPED = [
    ("A contagem foi feita em três armazéns, contra o inventário do sistema, gerando planilhas auditáveis "
     "dos lotes. Os dois turnos terminaram no prazo.",
     "A contagem foi feita em três armazéns, contra o inventário do sistema. Os dois turnos terminaram no prazo."),
    ("O levantamento mostra que os fornecedores atrasam, prejudicando a reposição das gôndolas.",
     "O levantamento mostra que os fornecedores atrasam."),
    # the dropped words occur two sentences later in the candidate, outside the neighbours a
    # split may use: the old check measured coverage against the whole candidate and saw them
    ("O caixa lança a venda no livro, emitindo o recibo ao cliente. A loja fecha às dez. "
     "O gerente confere o cofre. O recibo emitido é guardado pelo cliente.",
     "O caixa lança a venda no livro. A loja fecha às dez. "
     "O gerente confere o cofre. O recibo emitido é guardado pelo cliente."),
]
KEPT = [
    # split into two sentences: the clause is in the next sentence
    ("O levantamento mostra que os fornecedores atrasam, prejudicando a reposição das gôndolas.",
     "O levantamento mostra que os fornecedores atrasam. Isso prejudica a reposição das gôndolas."),
    # gerund made finite
    ("A contagem foi feita em três armazéns, gerando planilhas auditáveis dos lotes.",
     "A contagem foi feita em três armazéns e gerou planilhas auditáveis dos lotes."),
    # an editorial formula removed, as the planner asks (shape of holdout h4-ac-003)
    ("Nos dias de hoje, as balanças foram aferidas no depósito.", "As balanças foram aferidas no depósito."),
    # an opening connective removed (the real replay's false alarm before this control)
    ("Dessa forma, conclui-se que a meta do trimestre foi cumprida com folga no orçamento.",
     "Conclui-se que a meta do trimestre foi cumprida com folga no orçamento."),
    # clause moved to the front of the sentence
    ("As entregas saíram no horário, apesar da chuva forte na rodovia.",
     "Apesar da chuva forte na rodovia, as entregas saíram no horário."),
]


class ClauseOmission(unittest.TestCase):

    def test_a_dropped_clause_is_never_a_green(self):
        for original, candidate in DROPPED:
            with self.subTest(original=original[:40]):
                report = compare(original, candidate)
                self.assertNotEqual(report["status"], "no_deterministic_issues")
                self.assertIn("possible_omission", [i["code"] for i in report["issues"]], report["issues"])

    def test_control_a_kept_clause_is_not_an_omission(self):
        for original, candidate in KEPT:
            with self.subTest(original=original[:40]):
                report = compare(original, candidate)
                self.assertNotIn("possible_omission", [i["code"] for i in report["issues"]], report["issues"])


if __name__ == "__main__":
    unittest.main()
