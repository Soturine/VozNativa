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


if __name__ == "__main__":
    unittest.main()
