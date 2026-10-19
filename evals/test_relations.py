"""Relations between entities, causes and polarity (qualification audit gaps)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare


def codes(original, candidate):
    return {i["code"] for i in compare(original, candidate)["issues"]}


class EntityBinding(unittest.TestCase):
    def test_swapped_agents_fail(self):
        report = compare("A Ana vai revisar o contrato e o Bruno vai assinar.",
                         "O Bruno vai revisar o contrato e a Ana vai assinar.")
        self.assertEqual(report["status"], "fail")
        self.assertIn("entity_binding_changed", {i["code"] for i in report["issues"]})

    def test_reordered_clauses_and_passive_do_not_fire(self):
        self.assertNotIn("entity_binding_changed", codes("A Ana revisa o código e o Bruno faz o deploy.",
                                                         "O Bruno faz o deploy e a Ana revisa o código."))
        self.assertNotIn("entity_binding_changed", codes("A Acme comprou a Beta em 2024.",
                                                         "Em 2024, a Beta foi comprada pela Acme."))



class CausalDirection(unittest.TestCase):
    def test_reversed_direction_fails(self):
        for original, candidate in (("A falha no DNS causou a queda da API.", "A queda da API causou a falha no DNS."),
                                    ("O build quebrou porque o token expirou.", "O token expirou porque o build quebrou.")):
            report = compare(original, candidate)
            self.assertEqual(report["status"], "fail", original)
            self.assertIn("causal_direction_reversed", {i["code"] for i in report["issues"]})

    def test_causative_fazer_is_a_causal_connector(self):
        # Blind holdout hr-004 (first run): this valid rewrite failed.
        report = compare("O servidor reiniciou porque houve um vazamento de memória.",
                         "Um vazamento de memória fez o servidor reiniciar.")
        self.assertNotEqual(report["status"], "fail", report["issues"])
        from voznativa.signals import profile
        self.assertEqual(profile("Ela fez o relatório para entregar amanhã.").get("causality.causal", 0), 0)

    def test_same_direction_with_other_connector_or_voice_passes(self):
        for original, candidate in (("O build quebrou porque o token expirou.", "O token expirou, por isso o build quebrou."),
                                    ("A falha no DNS causou a queda da API.", "A queda da API foi causada pela falha no DNS.")):
            report = compare(original, candidate)
            self.assertNotEqual(report["status"], "fail", (candidate, report["issues"]))



class Polarity(unittest.TestCase):
    def test_antonym_flip_fails(self):
        for original, candidate in (("A receita aumentou 8%.", "A receita diminuiu 8%."),
                                    ("O pedido foi aprovado.", "O pedido foi recusado."),
                                    ("A atualização habilita o cache.", "A atualização desabilita o cache.")):
            self.assertIn("polarity_flipped", codes(original, candidate), original)

    def test_synonyms_and_lone_removals_do_not_fail(self):
        self.assertNotIn("polarity_flipped", codes("A receita aumentou 8%.", "A receita cresceu 8%."))
        self.assertNotEqual(compare("A falha no login foi corrigida.", "O bug no login foi corrigido.")["status"], "fail")

    def test_prefix_entries_do_not_swallow_exact_entries(self):
        from voznativa.signals import profile
        self.assertEqual(profile("A maioria aprovou.").get("quantifier.partial"), 1)



class Attribution(unittest.TestCase):
    def test_swapped_attributions_fail(self):
        report = compare("A Ana disse que o prazo é sexta-feira; o Bruno disse que o orçamento acabou.",
                         "O Bruno disse que o prazo é sexta-feira; a Ana disse que o orçamento acabou.")
        self.assertIn("attribution_swapped", {i["code"] for i in report["issues"]})
        self.assertEqual(report["status"], "fail")

    def test_moving_the_source_to_the_end_passes(self):
        report = compare("Segundo o IBGE, o desemprego caiu para 6,2%.", "O desemprego caiu para 6,2%, segundo o IBGE.")
        self.assertEqual(report["status"], "no_deterministic_issues", report["issues"])


class RelationsSuite(unittest.TestCase):
    def test_relations_dev_suite_passes(self):
        from voznativa.evals import run
        report = run(ROOT / "evals" / "semantic" / "relations.jsonl")
        self.assertEqual(report["failures"], [], report["by_category"])


if __name__ == "__main__":
    unittest.main()
