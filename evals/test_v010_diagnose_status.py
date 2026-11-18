"""v0.10 CP4: contextual status of diagnostics and new high-confidence rules.

Defect tests fail on v0.9.0 (no status field; "daqui há", "seje/esteje", "menas" not diagnosed);
controls pass on both.
"""
import unittest

from voznativa.diagnose import diagnose, proofread
from voznativa.planner import plan
from voznativa.router import route


def _diag(text, **kw):
    return diagnose(text, route(text, **kw))["diagnostics"]


def _types(diags, status=None):
    return {d["type"] for d in diags if status is None or d.get("status") == status}


class NewRules(unittest.TestCase):
    def test_daqui_ha_is_an_error_in_any_written_register(self):
        formal = _diag("A próxima reunião será daqui há duas semanas.", genre="corporate")
        chat = _diag("Daqui há pouco a gente conversa", genre="whatsapp", register="colloquial")
        for diags in (formal, chat):
            d = [x for x in diags if x["type"] == "daqui_ha"][0]
            self.assertEqual((d["status"], d["action"], d["fix"].lower()), ("ERROR_CONFIRMED", "auto_fix", "daqui a"))
        fixed = proofread("Volto daqui há dois dias.", diagnose("Volto daqui há dois dias.", route("x")), "PROOFREAD")
        self.assertEqual(fixed["text"], "Volto daqui a dois dias.")

    def test_daqui_a_and_ha_tempo_are_not_flagged(self):
        for text in ("Daqui a duas semanas o mercado reabre.", "Moro neste bairro há doze anos.",
                     "Há dois dias não chove."):
            self.assertNotIn("daqui_ha", _types(_diag(text, genre="news")), text)

    def test_nonstandard_subjunctive_and_menas(self):
        diags = _diag("Espero que o relatório seje entregue, mesmo com menas pessoas.", genre="corporate")
        self.assertEqual(_types(diags, "ERROR_CONFIRMED"), {"nonstandard_subjunctive", "menas"})
        fix = {d["type"]: d["fix"] for d in diags}
        self.assertEqual((fix["nonstandard_subjunctive"], fix["menas"]), ("seja", "menos"))
        self.assertEqual(_types(_diag("Caso o portão esteje fechado, use a entrada lateral.", genre="corporate"),
                                "ERROR_CONFIRMED"), {"nonstandard_subjunctive"})

    def test_controls_for_new_rules(self):
        for text in ("Espero que o relatório seja entregue.", "Vieram menos pessoas.", "Os sejos da casa.",
                     "Tem que entregar até sexta.", "Ele tem razão."):
            self.assertEqual(_types(_diag(text, genre="corporate"), "ERROR_CONFIRMED"), set(), text)


class Statuses(unittest.TestCase):
    def test_every_diagnostic_has_status_and_recommendation(self):
        diags = _diag("Os resultado mostram que fazem dois anos de queda. Tem muita gente na fila.", genre="news")
        self.assertTrue(diags)
        for d in diags:
            self.assertIn("status", d)
            self.assertEqual(d["recommend_edit"], d["status"] == "ERROR_CONFIRMED")
        self.assertEqual(diagnose("x", route("x"))["schema_version"], 2)

    def test_informal_variants_are_acceptable_not_errors(self):
        cases = {"Tem muita gente na fila da lotérica hoje kkk": "ter_existential",
                 "Me manda o endereço pra mim passar aí depois": "para_mim_infinitive",
                 "Os menino chegaram cedo hoje rs": "plural_agreement"}
        for text, kind in cases.items():
            d = [x for x in _diag(text, genre="whatsapp", register="colloquial") if x["type"] == kind][0]
            self.assertEqual(d["status"], "ACCEPTABLE_VARIANT", text)
            self.assertFalse(d["recommend_edit"])

    def test_same_form_differs_by_context(self):
        formal = [x for x in _diag("A gente fomos ao mercado ontem.", genre="corporate")
                  if x["type"] == "a_gente_plural"][0]
        chat = [x for x in _diag("A gente vamos chegar mais tarde", genre="whatsapp", register="colloquial")
                if x["type"] == "a_gente_plural"][0]
        self.assertEqual((formal["status"], chat["status"]), ("ERROR_CONFIRMED", "CONTEXT_DEPENDENT"))
        self.assertEqual(formal["action"], "suggest")          # no automatic fix: "a gente" vs "nós"

    def test_ter_existential_is_a_style_preference_in_formal_text(self):
        d = [x for x in _diag("Tem muita gente esperando o resultado do concurso.", genre="news")
             if x["type"] == "ter_existential"][0]
        self.assertEqual(d["status"], "STYLE_PREFERENCE")

    def test_para_mim_formal_is_context_dependent_not_error(self):
        d = [x for x in _diag("É difícil para mim aceitar essa proposta.", genre="corporate")
             if x["type"] == "para_mim_infinitive"][0]
        self.assertEqual(d["status"], "CONTEXT_DEPENDENT")

    def test_literary_dialect_is_a_choice(self):
        text = "— Nós vai pescar amanhã cedo se Deus quiser, que daqui há pouco chove — disse o velho."
        statuses = {d["status"] for d in _diag(text, genre="literary")}
        self.assertNotIn("ERROR_CONFIRMED", statuses)

    def test_planner_edits_only_confirmed_errors(self):
        text = "Volto daqui há dois dias para conferir o estoque."
        ctx = route(text, genre="corporate")
        ops = [s["op"] for s in plan(text, ctx)["sentences"]]
        self.assertIn("point_edit", ops)
        chat = "Tem muita gente na fila da lotérica hoje kkk"
        self.assertEqual({s["op"] for s in plan(chat, route(chat, genre="whatsapp", register="colloquial"))
                          ["sentences"]}, {"keep"})


if __name__ == "__main__":
    unittest.main()
