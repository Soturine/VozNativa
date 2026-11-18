"""v0.9 CP4: meaning changes with every value intact, grammar errors and technical terms.

Synthetic sentences (school, farm, condominium, clinic), written for these
tests and different from the frozen prospective sets in evals/v09/. Each
defect test fails on v0.8.1 (17d1f10); each control passes on both.

* V09-GAP-01 qualifier dropped / changed / added (major, never critical);
  ornamental adjectives are not qualifiers;
* V09-GAP-02/03/04 event class changed, fact status changed (intention,
  attempt, request, proposal), aspect changed (passou a, voltou a, deixou de);
  synonyms in one class are not changes;
* V08-GAP-20 attribution in the passive with an agent is the same attribution;
* V09-GAP-08 high-confidence grammar errors in diagnose, as point edits in
  the plan; clitic pronouns, invariable nouns, numerals and auxiliaries are
  not errors; informal text gets suggestions, not fixes;
* V09-GAP-10 a text that uses three technical terms is in the tech domain;
* V09-GAP-11 acronyms with inner letters are definitions.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402
from voznativa.diagnose import _expansion, diagnose  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.planner import plan  # noqa: E402
from voznativa.router import route  # noqa: E402


def codes(original, candidate):
    report = compare(original, candidate)
    return report["status"], {i["code"] for i in report["issues"] if i["severity"] != "info"}


class Qualifiers(unittest.TestCase):

    def test_operational_qualifier_dropped_changed_added(self):
        for original, candidate, code in (
            ("A matrícula online da escola abre na segunda-feira.", "A matrícula da escola abre na segunda-feira.",
             "qualifier_dropped"),
            ("A limpeza da caixa d'água é trimestral no condomínio.", "A limpeza da caixa d'água é anual no condomínio.",
             "qualifier_changed"),
            ("O valor da reforma do telhado é R$ 7.400,00.", "O valor aproximado da reforma do telhado é R$ 7.400,00.",
             "qualifier_added"),
            ("A irrigação do pomar foi testada em campo em agosto.",
             "A irrigação do pomar foi simulada em agosto.", "qualifier_changed"),
        ):
            with self.subTest(code=code, candidate=candidate):
                status, found = codes(original, candidate)
                self.assertEqual(status, "review_required", found)
                self.assertIn(code, found)

    def test_ornament_and_moved_qualifier_are_not_changes(self):
        for original, candidate in (
            ("A diretora fez uma ótima apresentação do projeto da horta.",
             "A diretora fez uma apresentação do projeto da horta."),
            ("A matrícula online da escola abre na segunda-feira.",
             "Na segunda-feira abre a matrícula online da escola."),
            ("No final do semestre, o total de faltas foi baixo.", "No final do semestre, o total de faltas ficou baixo."),
            # "manual" and "final" as nouns, rewritten away: not qualifiers (killed a CP7 mutant that survived)
            ("Consulte o manual da bomba antes da limpeza.", "Consulte as instruções da bomba antes da limpeza."),
            ("O resultado sai no final de maio.", "O resultado sai no fim de maio."),
        ):
            with self.subTest(candidate=candidate):
                status, found = codes(original, candidate)
                self.assertFalse(found & {"qualifier_dropped", "qualifier_changed", "qualifier_added"}, found)


class EventsStatusAspect(unittest.TestCase):

    def test_different_event_class_is_major(self):
        for original, candidate in (
            ("O síndico assinou a ata da assembleia.", "O síndico leu a ata da assembleia."),
            ("A clínica cancelou as consultas de sexta.", "A clínica confirmou as consultas de sexta."),
            ("O conselho aprovou o regimento da escola.", "O conselho revisou o regimento da escola."),
        ):
            with self.subTest(candidate=candidate):
                status, found = codes(original, candidate)
                self.assertNotEqual(status, "no_deterministic_issues")

    def test_same_class_synonyms_are_not_changes(self):
        for original, candidate in (
            ("O síndico assinou a ata da assembleia.", "O síndico rubricou a ata da assembleia."),
            ("A cooperativa enviou as mudas ao viveiro.", "A cooperativa encaminhou as mudas ao viveiro."),
            ("A escola solicitou a vistoria do prédio.", "A escola pediu a vistoria do prédio."),
        ):
            with self.subTest(candidate=candidate):
                status, found = codes(original, candidate)
                self.assertFalse(found & {"event_changed", "fact_status_changed", "predicate_missing"}, found)

    def test_fact_status_changed(self):
        for original, candidate in (
            ("A clínica comprou dois desfibriladores.", "A clínica quer comprar dois desfibriladores."),
            ("O condomínio trocou o portão da garagem.", "O condomínio tentou trocar o portão da garagem."),
        ):
            with self.subTest(candidate=candidate):
                self.assertIn("fact_status_changed", codes(original, candidate)[1])

    def test_aspect_and_cessation(self):
        self.assertIn("aspect_changed", codes("A feira acontece aos domingos.",
                                              "A feira voltou a acontecer aos domingos.")[1])
        status, found = codes("A van escolar deixou de passar na rua 9.", "A van escolar passa na rua 9.")
        self.assertEqual(status, "fail")
        self.assertIn("negation_changed", found)
        self.assertEqual(codes("A van escolar deixou de passar na rua 9.",
                               "A van escolar não passa mais na rua 9.")[0], "no_deterministic_issues")


class PassiveAttribution(unittest.TestCase):

    def test_passive_with_agent_keeps_the_source(self):
        status, found = codes("A enfermeira informou os pacientes sobre a vacina.",
                              "Os pacientes foram informados pela enfermeira sobre a vacina.")
        self.assertNotIn("attribution_changed", found)

    def test_passive_without_agent_loses_the_source(self):
        self.assertIn("attribution_changed", codes("A enfermeira informou os pacientes sobre a vacina.",
                                                   "Os pacientes foram informados sobre a vacina.")[1])


def grammar(text, genre=None):
    return [(d["class"], d["type"], d.get("fix")) for d in diagnose(text, route(text, genre=genre))["diagnostics"]
            if d["type"] in ("plural_agreement", "impersonal_fazer", "existential_haver", "crase")]


class Grammar(unittest.TestCase):

    def test_high_confidence_errors(self):
        self.assertEqual(grammar("As vacina chegaram ao posto na terça-feira."),
                         [("formal_error", "plural_agreement", None)])
        self.assertEqual(grammar("Fazem cinco meses que a quadra está fechada."),
                         [("formal_error", "impersonal_fazer", "Faz")])
        self.assertEqual(grammar("Houveram três reuniões sobre a horta."),
                         [("formal_error", "existential_haver", "Houve")])
        self.assertEqual(grammar("A vacinação continua à partir das 8h."), [("formal_error", "crase", "a")])

    def test_houveram_before_a_plural_noun(self):
        # v0.9 CP8 dogfood: "Houveram atrasos ..." was not diagnosed (only "houveram muitas ..." was),
        # the plan had no grammar reason for it and a real rewrite was accepted with the error kept.
        self.assertEqual(grammar("Houveram falhas na entrega das cestas."),
                         [("formal_error", "existential_haver", "Houve")])
        for text in ("Os sócios houveram por bem adiar a assembleia.", "Eles houveram de partir cedo.",
                     "Os técnicos houveram terminado antes da chuva."):
            with self.subTest(text=text):
                self.assertEqual(grammar(text), [])

    def test_controls_are_not_errors(self):
        for text in ("A enfermeira os chamou pelo nome.", "Ele as lista toda semana na reunião.", "Os ônibus e os lápis ficaram na sala.",
                     "As duas turmas e os três professores chegaram.", "Os pais haviam saído antes da chuva.",
                     "Os alunos fazem três provas por bimestre.", "O kit foi entregue à mulher da portaria, à vista.",
                     "Os lotes C, E e G foram enviados."):
            with self.subTest(text=text):
                self.assertEqual(grammar(text), [])

    def test_informal_text_gets_a_suggestion_not_a_fix(self):
        found = grammar("kkk fazem dois anos q a gente nao se ve", genre="whatsapp")
        self.assertEqual([c for c, _, _ in found], ["possible_contextual_error"])

    def test_the_plan_acts_on_a_grammar_error(self):
        text = "As vacina chegaram ao posto na terça-feira."
        result = plan(text, route(text))
        self.assertEqual(result["decision"], "edit")
        self.assertEqual(result["sentences"][0]["reasons"][0]["id"], "grammar_plural_agreement")
        self.assertEqual(plan("As vacinas chegaram ao posto na terça-feira.",
                              route("As vacinas chegaram ao posto na terça-feira."))["decision"], "no_change")


class TechnicalTerms(unittest.TestCase):

    def test_three_technical_terms_establish_the_domain(self):
        text = ("O sistema do laboratório foi reescrito. O backend recebe as leituras, o deploy acontece a cada "
                "release e os logs ficam no servidor.")
        found = [f["text"] for f in detect(text, "academic")["findings"] if f["id"] == "anglicism_out_of_domain"]
        self.assertEqual(found, [])

    def test_one_term_alone_is_still_suggested(self):
        text = "O sistema do laboratório foi reescrito. O backend recebe as leituras do sensor."
        found = [f["text"] for f in detect(text, "academic")["findings"] if f["id"] == "anglicism_out_of_domain"]
        self.assertEqual(found, ["backend"])


class Acronyms(unittest.TestCase):

    def test_inner_letters(self):
        self.assertEqual(_expansion("o Sound Navigation And Ranging", "SONAR"), "sound navigation ranging")

    def test_no_spelling_is_no_definition(self):
        self.assertIsNone(_expansion("Rotina de cálculo de frete", "SQL"))


if __name__ == "__main__":
    unittest.main()
