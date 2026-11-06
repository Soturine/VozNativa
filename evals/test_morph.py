"""v0.7.0 CP9L: verb morphology with abstention, and its use as a semantic signal.

Measured against UD gold in evals/linguistics/runs/morph-2026-11-06.json;
these tests pin the contract: unique analyses where the form decides,
abstention where it does not, no analysis of nouns after determiners or of
names, morphological tense kept apart from event time, voice kept apart from
tense, and no agent invented."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402
from voznativa.morph import TENSES, analyse_word, constructions, tense_profile, verbs  # noqa: E402


def labels(sentence: str, lemma: str = "terminar") -> set:
    return tense_profile(sentence).get(lemma, set())


class AddendumExamples(unittest.TestCase):
    """The ten contrastive sentences of the linguistic addendum."""

    def test_unique_analyses(self):
        expected = {
            "Ana terminou o trabalho.": {"pret_perf"},
            "Ana terminava o trabalho.": {"pret_imp"},
            "Ana tinha terminado o trabalho.": {"compound_perfect@pret_imp"},
            "Ana terminará o trabalho.": {"fut_pres"},
            "Ana terminaria o trabalho.": {"fut_pret"},
            "Ana está terminando o trabalho.": {"progressive@pres_ind"},
            "Ana vai terminar o trabalho.": {"periphrastic_future@pres_ind"},
            "Se Ana terminasse, poderia sair.": {"imp_sub"},
        }
        for sentence, label in expected.items():
            self.assertEqual(labels(sentence), label, sentence)

    def test_ambiguous_forms_abstain(self):
        # Without a lexicon "terminara" may be preterite or pluperfect; "terminar" after
        # "quando" may be future subjunctive or infinitive: no forced answer.
        self.assertEqual(labels("Ana terminara o trabalho."), set())
        self.assertEqual(labels("Quando Ana terminar, poderá sair."), set())
        v = next(v for v in verbs("Quando Ana terminar, poderá sair.") if v.form == "terminar")
        self.assertEqual(v.tenses, {"fut_sub", "inf"})
        self.assertFalse(v.unique)

    def test_conditional_vs_future_in_the_same_frame(self):
        self.assertEqual(tense_profile("Se Ana terminasse, poderia sair.")["poder"], {"fut_pret"})
        self.assertEqual(tense_profile("Quando Ana terminar, poderá sair.")["poder"], {"fut_pres"})


class UDMapping(unittest.TestCase):
    def test_traditional_names_map_to_the_treebank_annotation(self):
        # Checked empirically on Bosque/GSD/PetroGold (ADR-0002), not assumed.
        self.assertEqual(TENSES["fut_pret"][1], {"VerbForm": "Fin", "Mood": "Cnd"})
        self.assertEqual(TENSES["imp_sub"][1], {"VerbForm": "Fin", "Mood": "Sub", "Tense": "Imp"})
        self.assertEqual(TENSES["fut_sub"][1], {"VerbForm": "Fin", "Mood": "Sub", "Tense": "Fut"})
        self.assertEqual(TENSES["pret_mqp"][1]["Tense"], "Pqp")
        self.assertEqual(TENSES["pret_perf"][1]["Tense"], "Past")

    def test_person_and_number(self):
        a = [x for x in analyse_word("terminamos") if x["tense"] == "pret_perf"][0]
        self.assertEqual((a["Person"], a["Number"]), ("1", "Plur"))


class NotEverythingIsAVerb(unittest.TestCase):
    def test_nouns_after_determiners_and_names_are_skipped(self):
        forms = {v.form for v in verbs("O contrato da Ana está na mesa e a casa é nova.")}
        self.assertNotIn("contrato", forms)
        self.assertNotIn("Ana", forms)
        self.assertNotIn("casa", forms)
        self.assertIn("está", forms)

    def test_frequent_lookalikes(self):
        self.assertEqual(analyse_word("quando"), [])
        self.assertEqual(verbs("A cadeira da sala quebrou.")[0].form, "quebrou")


class NoInventedAgent(unittest.TestCase):
    def test_agentless_passive_and_indeterminate_subject(self):
        for sentence in ("O documento foi aprovado.", "Venderam o imóvel."):
            for c in constructions(sentence):
                self.assertNotIn("agent", c)
        self.assertEqual(constructions("O documento foi aprovado.")[0]["construction"], "passive")


class TenseAsASemanticSignal(unittest.TestCase):
    def codes(self, a, b):
        return {i["code"] for i in compare(a, b)["issues"]}

    def test_tense_mood_and_aspect_changes_are_signalled(self):
        for a, b in (("A empresa contratou João em março.", "A empresa contratará João em março."),
                     ("Ana terminou o trabalho.", "Ana está terminando o trabalho."),
                     ("Ana terminou o trabalho.", "Ana terminaria o trabalho.")):
            self.assertIn("tense_changed", self.codes(a, b), b)
            self.assertEqual(compare(a, b)["status"], "review_required", "a signal, never a proof")

    def test_controls_do_not_fire(self):
        for a, b in (("Ana terminou o trabalho ontem.", "Ontem, Ana terminou o trabalho."),
                     ("O documento foi aprovado por Maria.", "Maria aprovou o documento."),   # voice, not tense
                     ("A gente terminou o trabalho.", "Nós terminamos o trabalho."),           # ambiguous form
                     ("Ana terminara o trabalho.", "Ana terminou o trabalho.")):               # abstention
            self.assertNotIn("tense_changed", self.codes(a, b), b)


if __name__ == "__main__":
    unittest.main()
