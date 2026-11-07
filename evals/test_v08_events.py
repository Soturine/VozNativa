"""v0.8 CP6 (V08-GAP-04): recipients, converse events and missing antonym classes.

The frozen sets in evals/events/ were written and hashed before this code;
their before/after runs are in evals/v08/runs/. These tests pin the
behaviour on general constructions (not the sets' sentences) and the controls
that keep the new rules from becoming false alarms."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import evaluation  # noqa: E402
from voznativa.compare import compare  # noqa: E402
from voznativa.events import converse, frames  # noqa: E402

NEW = {"recipient_dropped", "recipient_changed", "agent_recipient_swapped", "event_converted"}


def codes(a, b):
    report = compare(a, b)
    return report["status"], {i["code"]: i["severity"] for i in report["issues"]}


class Frames(unittest.TestCase):

    def test_recipient_and_agent(self):
        (f,) = frames("A tesoureira repassou o relatório aos auditores.")
        self.assertEqual((f.agent, f.recipient, f.confidence), ("tesoureira", "auditores", "high"))

    def test_what_is_not_a_recipient(self):
        for sentence in ("Enviei o arquivo às 14h.", "Ela entregou o trabalho à noite.",
                         "Trabalhou muito para entregar o relatório.", "O técnico entregou a peça.",
                         "Ele mandou a partir de hoje."):
            with self.subTest(sentence=sentence):
                self.assertTrue(all(f.recipient is None for f in frames(sentence)), frames(sentence))

    def test_purpose_after_a_transfer_verb_is_not_a_recipient(self):
        (f,) = [x for x in frames("A empresa enviou o técnico para avaliar o equipamento.") if x.stem == "envi"]
        self.assertIsNone(f.recipient)
        # ...while "para" + a noun phrase still is one, even when the noun ends like an infinitive.
        (g,) = frames("A empresa enviou o laudo para o diretor.")
        self.assertEqual(g.recipient, "diretor")

    def test_a_bare_article_is_a_preposition_only_before_a_name_after_the_object(self):
        (f,) = frames("O síndico pagou a conta a Marcos.")
        self.assertEqual(f.recipient, "marcos")
        (g,) = frames("O síndico pagou a conta.")
        self.assertIsNone(g.recipient)

    def test_an_auxiliary_or_preposition_is_not_the_agent(self):
        self.assertIsNone(frames("Vou mandar a planilha para a gerente.")[0].agent)
        self.assertIsNone(frames("Ficou tarde para entregar a peça.")[0].agent)

    def test_converse_pairs_are_symmetric_and_not_synonyms(self):
        self.assertTrue(converse("compr", "vend") and converse("vend", "compr"))
        self.assertTrue(converse("envi", "receb"))
        self.assertFalse(converse("compr", "adquir"))
        self.assertFalse(converse("assin", "receb"), "assinar/receber is not a converse pair")


class Recipients(unittest.TestCase):

    def test_dropped_and_changed(self):
        status, found = codes("O hospital entregou os exames ao paciente.", "O hospital entregou os exames.")
        self.assertEqual((status, found.get("recipient_dropped")), ("review_required", "major"))
        status, found = codes("O hospital entregou os exames ao paciente.", "O hospital entregou os exames ao médico.")
        self.assertEqual(found.get("recipient_changed"), "major")

    def test_moved_passive_and_inflected_recipient_are_fine(self):
        source = "O hospital entregou os exames ao paciente."
        for candidate in ("O hospital entregou ao paciente os exames.",
                          "Os exames foram entregues ao paciente pelo hospital.",
                          "Ao paciente, o hospital entregou os exames."):
            with self.subTest(candidate=candidate):
                self.assertFalse(NEW & set(codes(source, candidate)[1]))
        inflected = codes("A loja enviou a nota ao fornecedor.", "A loja enviou a nota aos fornecedores.")[1]
        self.assertFalse(NEW & set(inflected), inflected)

    def test_swap_of_giver_and_receiver(self):
        status, found = codes("A gerente enviou o contrato ao advogado.", "O advogado enviou o contrato à gerente.")
        self.assertEqual(found.get("agent_recipient_swapped"), "major")

    def test_new_codes_are_never_critical(self):
        pairs = [("O hospital entregou os exames ao paciente.", "O hospital entregou os exames."),
                 ("A gerente enviou o contrato ao advogado.", "O advogado enviou o contrato à gerente."),
                 ("A rede comprou a fábrica.", "A rede vendeu a fábrica.")]
        for a, b in pairs:
            for code, severity in codes(a, b)[1].items():
                if code in NEW:
                    self.assertEqual(severity, "major", code)


class Converse(unittest.TestCase):

    def test_same_subject_is_flagged(self):
        status, found = codes("A rede comprou a fábrica em 2024.", "A rede vendeu a fábrica em 2024.")
        self.assertEqual((status, found.get("event_converted")), ("review_required", "major"))

    def test_roles_swapped_is_the_same_event(self):
        found = codes("A rede comprou a fábrica do grupo.", "O grupo vendeu a fábrica para a rede.")[1]
        self.assertNotIn("event_converted", found)

    def test_a_synonym_is_not_a_converse(self):
        found = codes("A rede comprou a fábrica.", "A rede adquiriu a fábrica.")[1]
        self.assertFalse(NEW & set(found))


class NewAntonymClasses(unittest.TestCase):

    def test_true_antonyms_fail(self):
        for a, b in (("A prefeitura contratou dez médicos.", "A prefeitura demitiu dez médicos."),
                     ("O país exportou milho em 2025.", "O país importou milho em 2025."),
                     ("O alarme ligou às 3h.", "O alarme desligou às 3h."),
                     ("O tribunal deferiu o recurso.", "O tribunal indeferiu o recurso.")):
            with self.subTest(a=a):
                status, found = codes(a, b)
                self.assertEqual((status, found.get("polarity_flipped")), ("fail", "critical"))

    def test_words_that_only_look_like_the_classes(self):
        # contrat* would catch "contrato", import* would catch "importante": explicit forms only.
        for a, b in (("É importante revisar o contrato hoje.", "Revise o contrato hoje."),
                     ("O contrato foi assinado ontem.", "O contrato foi rescindido ontem."),
                     ("Importa pouco o horário.", "O horário importa pouco.")):
            with self.subTest(a=a):
                self.assertNotIn("polarity_flipped", codes(a, b)[1])


class FrozenEventSets(unittest.TestCase):
    """Regression floor on the frozen sets (development, and the holdout's first run)."""

    @classmethod
    def setUpClass(cls):
        spec = json.loads((ROOT / "evals" / "v08" / "datasets" / "events.json").read_text(encoding="utf-8"))
        cls.metrics = evaluation.run(spec, ROOT, recorded_at="t")["metrics"]

    def test_development(self):
        m = self.metrics["development"]["semantic_risk"]
        self.assertGreaterEqual(m["sensitivity"]["k"], 14)
        self.assertLessEqual(m["false_alarm_rate"]["k"], 2)

    def test_holdout_first_run_does_not_regress(self):
        m = self.metrics["prospective_holdout"]["semantic_risk"]
        self.assertGreaterEqual(m["sensitivity"]["k"], 11)
        self.assertLessEqual(m["false_alarm_rate"]["k"], 3)


if __name__ == "__main__":
    unittest.main()
