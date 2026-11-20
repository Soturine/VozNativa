"""v0.10.5: three false greens/false reds found by the fire trial on real PT-BR text (Machado de Assis, laws).

Metamorphic pairs built on real texts (oracle = the transformation, not the engine) showed them; the sentences
below are invented, in other domains, with the same shape. Defect tests fail on v0.10.0; controls pass on both.
"""
import unittest

from voznativa.compare import compare


def flagged(a, b):
    return compare(a, b)["status"] in ("review_required", "fail")


def codes(a, b):
    return {i["code"] for i in compare(a, b)["issues"] if i["severity"] != "info"}


class NegationHead(unittest.TestCase):
    """V105-GAP-05: negative concord let a polarity change pass as info."""

    def test_defect_head_removed_leaves_n_word_after_the_verb(self):
        for a, b in (("O depósito não recebeu nenhuma caixa.", "O depósito recebeu nenhuma caixa."),
                     ("A diretora não aprovou nada naquela reunião.", "A diretora aprovou nada naquela reunião."),
                     ("O barco não saiu nem voltou.", "O barco saiu nem voltou."),
                     ("O técnico não visitou nunca a usina.", "O técnico visitou nunca a usina.")):
            self.assertIn("negation_head_changed", codes(a, b), b)

    def test_defect_head_added_absorbs_an_inner_n_word(self):
        self.assertTrue(flagged("Ele era só um aprendiz, mas nem por isso desistia.",
                                "Ele não era só um aprendiz, mas nem por isso desistia."))

    def test_controls_concord_paraphrases(self):
        for a, b in (("A falha não afetou nenhum cliente.", "Nenhum cliente foi afetado pela falha."),
                     ("A falha não afetou nenhum cliente.", "A falha não afetou cliente algum."),
                     ("Nunca vi isso.", "Não vi isso nunca."),
                     ("Ninguém respondeu.", "Não respondeu ninguém.")):
            self.assertNotIn("negation_head_changed", codes(a, b), b)


class SentenceDropped(unittest.TestCase):
    """V105-GAP-06: a whole sentence deleted passed when its words occurred elsewhere in the text."""

    TEXT = ("O mercado abriu cedo. A banca de peixe chegou atrasada. O peixe da banca vinha do porto. "
            "A feira terminou às duas.")

    def test_defect_sentence_removed_between_kept_neighbours(self):
        candidate = "O mercado abriu cedo. O peixe da banca vinha do porto. A feira terminou às duas."
        self.assertIn("sentence_dropped", codes(self.TEXT, candidate))

    def test_control_paraphrase_of_the_middle_sentence(self):
        candidate = ("O mercado abriu cedo. A banca de peixe atrasou a chegada. O peixe da banca vinha do porto. "
                     "A feira terminou às duas.")
        self.assertNotIn("sentence_dropped", codes(self.TEXT, candidate))

    def test_control_split_sentence_is_carried(self):
        candidate = ("O mercado abriu cedo. A banca de peixe chegou. Chegou atrasada. O peixe da banca vinha do porto. "
                     "A feira terminou às duas.")
        self.assertNotIn("sentence_not_carried", codes(self.TEXT, candidate))


class HardWraps(unittest.TestCase):
    """V105-GAP-07: joining hard-wrapped lines inside a paragraph read as critical changes."""

    def test_defect_quote_across_a_line_break(self):
        original = "Ela escreveu: «Volto na\nsegunda com as chaves da oficina.» E saiu."
        joined = "Ela escreveu: «Volto na segunda com as chaves da oficina.» E saiu."
        self.assertFalse(flagged(original, joined))

    def test_defect_multiword_connective_across_a_line_break(self):
        original = "A ponte fechou. O ônibus mudou de rota, uma vez\nque o desvio era mais curto."
        joined = "A ponte fechou. O ônibus mudou de rota, uma vez que o desvio era mais curto."
        self.assertNotIn("relation_invented", codes(original, joined))

    def test_control_a_blank_line_still_ends_a_quote(self):
        original = "Ela disse: «Volto na\n\nsegunda.» E saiu."
        self.assertTrue(flagged(original, "Ela disse: «Volto na sexta.» E saiu."))


class DigitsGluedToLetters(unittest.TestCase):
    """Fire trial: '7a companhia' (old ordinal), 'L1' (a term), '#petr4', '@perfil10': the digit names the referent."""

    def test_defect_old_style_ordinal_changed(self):
        self.assertTrue(flagged("O 3o pelotão chegou cedo.", "O 10o pelotão chegou cedo."))

    def test_defect_alphanumeric_term_changed(self):
        self.assertTrue(flagged("O efeito da L1 na escrita foi medido.", "O efeito da L2 na escrita foi medido."))
        self.assertTrue(flagged("Alta de #vale3 hoje.", "Alta de #vale5 hoje."))
        self.assertTrue(flagged("Resposta de @loja22 ontem.", "Resposta de @loja12 ontem."))

    def test_defect_old_ordinal_respelled_is_the_same_value(self):
        # false red on v0.10.0: "3º" was a new ordinal span with no counterpart
        self.assertFalse(flagged("O 3o pelotão chegou cedo.", "O 3º pelotão chegou cedo."))

    def test_controls_equivalent_forms(self):
        self.assertFalse(flagged("Saiu às 18h30 após 10km.", "Saiu às 18:30 após 10 km."))
        self.assertFalse(flagged("Use o formato mp3 e o Python3.", "Use o Python3 e o formato mp3."))


if __name__ == "__main__":
    unittest.main()


class LegalProvisionHead(unittest.TestCase):
    """V105-GAP-15: after the paragraph sign or an item marker with no period ("§ 3° Pendendo…", "I - Enquanto…"),
    the first word of a legal provision was read as a proper name, so any plain-language rewrite of a paragraph
    or item that changed its first word was a critical span loss. Found in the fire trial (law, plain language);
    red on v0.10.0. The regulation below is invented."""

    BASE = "Art. 4. O sócio paga a taxa anual.\n"

    def spans(self, a, b):
        return {i["code"] for i in compare(a, b)["issues"] if i["code"].startswith("span_")}

    def test_defect_first_word_after_markers_is_not_an_entity(self):
        for lead in ("§ 2° ", "§ 2º ", "§2. ", "§§ 3 ", "II - ", "IV – ", "c) "):
            a = self.BASE + lead + "Havendo atraso, a carteirinha fica suspensa.\n"
            b = self.BASE + lead + "Quando houver atraso, a carteirinha fica suspensa.\n"
            self.assertEqual(self.spans(a, b), set(), lead)

    def test_control_entity_inside_the_provision_is_still_protected(self):
        a = self.BASE + "§ 2° Havendo atraso, a Federação Paulista suspende a carteirinha.\n"
        b = self.BASE + "§ 2° Havendo atraso, a Federação suspende a carteirinha.\n"
        self.assertIn("span_missing", self.spans(a, b))


class PresentPluralToImperfect(unittest.TestCase):
    """V105-GAP-22: "criam" -> "criavam" (and "falam" -> "falavam") passed with no signal: the present 3rd plural
    is not analysed, so the imperfect looked like a new verb. Found in the prospective holdout (P05). Invented text."""

    def test_defect_present_plural_to_imperfect_is_flagged(self):
        for a, b in (("Os sócios criam que a sede era segura.", "Os sócios criavam que a sede era segura."),
                     ("Os vizinhos falam que a praça era bonita.", "Os vizinhos falavam que a praça era bonita."),
                     ("Os alunos comem cedo e saem às sete.", "Os alunos comiam cedo e saem às sete."),
                     ("Os homens as criam representantes dos deuses.", "Os homens as criavam representantes dos deuses.")):
            self.assertIn("verb_form_changed", codes(a, b), b)

    def test_controls_same_tense_and_unrelated_words(self):
        for a, b in (("Os sócios criavam que a sede era segura.", "Os sócios criavam que a sede era firme."),
                     ("Os vizinhos falam que a praça é bonita.", "Os moradores falam que a praça é bonita."),
                     ("A equipe criava peças e vendia na feira.", "A equipe criava peças e as vendia na feira."),
                     ("Os alunos falam, enquanto todos comentavam em voz baixa.",
                      "Os alunos conversam, enquanto vizinhos falavam em voz baixa.")):
            self.assertNotIn("verb_form_changed", codes(a, b), b)


class PrivativeDeterminer(unittest.TestCase):
    """V105-GAP-29: emphatic determiners can repeat an existing privative."""

    def test_emphatic_determiner_in_same_phrase_is_not_a_polarity_change(self):
        for a, b in (("Remova o item sem nenhum argumento.", "Remova o item sem argumento."),
                     ("O serviço funciona sem tarifa.", "O serviço funciona sem nenhuma tarifa.")):
            self.assertNotIn("negation_changed", codes(a, b))

    def test_actual_changes_still_trigger_even_in_a_neighbouring_sentence(self):
        self.assertIn("negation_changed", codes("Remova o item sem nenhum argumento.",
                                               "Remova o item com um argumento."))
        a = "Remova o item sem nenhum argumento. O sistema registra a operação."
        b = "Remova o item sem argumento. O sistema não registra a operação."
        self.assertIn("negation_changed", codes(a, b))
