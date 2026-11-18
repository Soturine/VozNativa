"""v0.10 CP5/CP6: discourse relations, coordinated actions, calibrated false alarms.

Defect tests (marked) fail on v0.9.0; controls keep the checks alive (no check was switched off).
"""
import unittest

from voznativa.compare import compare


def codes(original, candidate):
    report = compare(original, candidate)
    return report["status"], {(i["code"], i["severity"]) for i in report["issues"]}


def flagged(original, candidate):
    return compare(original, candidate)["status"] in ("review_required", "fail")


class Relations(unittest.TestCase):
    def test_profile_families(self):
        from voznativa import discourse
        self.assertEqual(discourse.profile("Embora chova, saímos; mas voltamos porque esfriou."),
                         {"counter": 2, "causal": 1})
        self.assertEqual(discourse.profile("Como o pavilhão alagou, a feira foi adiada."), {"causal": 1})
        self.assertEqual(discourse.profile("Como sempre, a feira abriu cedo. Assim como ontem."), {})
        self.assertEqual(discourse.profile("Choveu; ainda assim, colhemos."), {"counter": 1})
        self.assertEqual(discourse.profile("Logo depois da chuva, colhemos."), {})

    def test_defect_concession_to_cause(self):
        status, found = codes("Embora o lote tenha chegado atrasado, a feira abriu no horário.",
                              "Como o lote chegou atrasado, a feira abriu no horário.")
        self.assertIn(("relation_changed", "major"), found)

    def test_defect_contrast_to_consequence_without_lexicon_marker(self):
        _, found = codes("O caminhão quebrou na estrada. Contudo, a entrega chegou ao laticínio.",
                         "O caminhão quebrou na estrada. Assim, a entrega chegou ao laticínio.")
        self.assertIn(("relation_changed", "major"), found)

    def test_defect_invented_causal_between_juxtaposed_facts(self):
        _, found = codes("A ponte foi fechada. Os ônibus mudaram de rota.",
                         "A ponte foi fechada; assim, os ônibus mudaram de rota.")
        self.assertIn(("relation_invented", "major"), found)

    def test_defect_cause_kept_with_another_connective_is_not_a_failure(self):
        report = compare("A feira foi adiada porque o pavilhão alagou.", "Como o pavilhão alagou, a feira foi adiada.")
        self.assertNotEqual(report["status"], "fail")
        demoted = [i for i in report["issues"] if i["code"] == "causality_changed"]
        self.assertTrue(all(i["severity"] == "info" for i in demoted))

    def test_controls_same_family_swaps(self):
        pairs = [("O mercado abriu cedo, porém a padaria só abriu às dez.",
                  "O mercado abriu cedo, mas a padaria só abriu às dez."),
                 ("O orçamento foi aprovado. Entretanto, a obra só começa em março.",
                  "O orçamento foi aprovado. No entanto, a obra só começa em março."),
                 ("A biblioteca fechou mais cedo para que a equipe fizesse o inventário.",
                  "A biblioteca fechou mais cedo a fim de que a equipe fizesse o inventário.")]
        for original, candidate in pairs:
            self.assertFalse(flagged(original, candidate), candidate)

    def test_control_causal_direction_still_checked(self):
        # same family, but cause and effect traded places: the direction check is untouched
        self.assertTrue(flagged("A estrada alagou porque choveu.", "Choveu porque a estrada alagou."))

    def test_control_purpose_to_cause_still_flagged(self):
        self.assertTrue(flagged("A prefeitura podou as árvores para que a fiação não fosse danificada.",
                                "A prefeitura podou as árvores porque a fiação foi danificada."))


class Coordination(unittest.TestCase):
    def test_defect_dropped_participle_and_verb(self):
        for original, candidate in (("O relatório foi revisado e enviado à diretoria.", "O relatório foi revisado."),
                                    ("A equipe recolheu e pesou as redes.", "A equipe recolheu as redes.")):
            _, found = codes(original, candidate)
            self.assertIn(("coordinated_action_dropped", "major"), found, candidate)

    def test_controls_coordination_kept(self):
        for original, candidate in (("O relatório foi revisado e enviado à diretoria.",
                                     "O relatório foi revisado e, em seguida, enviado à diretoria."),
                                    ("O pedido foi embalado e despachado.", "O pedido foi embalado e depois despachado."),
                                    ("Entregou o seu e meu ingresso.", "Entregou o ingresso.")):
            _, found = codes(original, candidate)
            self.assertNotIn(("coordinated_action_dropped", "major"), found, candidate)


class CalibratedFalseAlarms(unittest.TestCase):
    """v0.9 CP7 arms: four false alarms of compare (a-01, a-07, a-09, a-11)."""

    def test_defect_scheduled_present(self):
        self.assertFalse(flagged("A feira de troca de sementes vai ser no sábado, das 9h às 13h.",
                                 "A feira de troca de sementes é no sábado, das 9h às 13h."))

    def test_control_present_without_future_anchor_still_flagged(self):
        self.assertTrue(flagged("O prédio vai ser grande.", "O prédio é grande."))

    def test_defect_future_to_past_with_foi(self):
        _, found = codes("O mutirão de limpeza vai ser no domingo.", "O mutirão de limpeza foi no domingo.")
        self.assertIn(("tense_changed", "major"), found)

    def test_defect_code_marking_added(self):
        status, found = codes("Copie o arquivo para a pasta data e rode o script.",
                              "Copie o arquivo para a pasta `data` e rode o script.")
        self.assertNotEqual(status, "fail")
        self.assertIn(("code_marking_added", "info"), found)

    def test_control_code_content_changed_still_fails(self):
        self.assertEqual(compare("Rode `make build` antes.", "Rode `make test` antes.")["status"], "fail")

    def test_defect_inteira_toda(self):
        self.assertFalse(flagged("A chuva caiu a tarde inteira.", "A chuva caiu a tarde toda."))

    def test_defect_inteira_to_partial(self):
        self.assertTrue(flagged("A chuva caiu a tarde inteira sobre o quintal.",
                                "A chuva caiu parte da tarde sobre o quintal."))

    def test_defect_concessive_infinitive_is_same_time(self):
        self.assertFalse(flagged("Embora a reunião tenha começado tarde, todos os pontos foram votados.",
                                 "Apesar de a reunião ter começado tarde, todos os pontos foram votados."))


if __name__ == "__main__":
    unittest.main()
