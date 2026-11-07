"""v0.7.0.dev1 CP5B (backlog B-M2): oracles for the sentence-level checks of
``compare.py`` that round C of mutation left uncovered.

Round C (evals/assurance/runs/2026-11-07-h07-cp5b, compare.py rows 76 and
429-583, all 271 selected mutants) showed that no test asserted *where* a moved
marker came from and went to, that no test fed a low-similarity pair to the
alignment filter, and that the abstentions of the tense and predicate checks
(ambiguous profile, short stem, weak ending, window edge) were untested. The
checks are called directly with a hand-built alignment ``(i, j, similarity)``
so each oracle is about one rule, not about ``_align``. Each test names the
lines (of c909f1d / ecf3dd2, same blob) whose survivors it is meant to kill.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import ledger  # noqa: E402
from voznativa.compare import (ALIGN_MIN_SIMILARITY, _event_anchors, _moved_signal_issues,  # noqa: E402
                               _predicate_issues, _tense_issues)


def doc(*sentences):
    led = ledger.build(" ".join(sentences), ())
    assert [e.sentence.text for e in led.entries] == list(sentences), [e.sentence.text for e in led.entries]
    return led


def moved(src, out, alignment):
    from voznativa.compare import _bucket
    return _moved_signal_issues(src, out, alignment, _bucket(src.signal_counts()), _bucket(out.signal_counts()))


def same(n, sim=0.9):
    return [(i, i, sim) for i in range(n)]


FRAME = "Vale ressaltar que o prazo acabou."
NEUTRAL = "O relatório chegou ontem à sede."
MUST_PAY = "A empresa deve pagar a multa."
PAYS = "A empresa paga a multa."
DELIVERS = "O fornecedor entrega o material."
MUST_DELIVER = "O fornecedor deve entregar o material."
SIGNS = "O gerente assina o termo."
MUST_SIGN = "O gerente deve assinar o termo."
CHECKS = "A equipe confere o estoque."
MUST_CHECK = "A equipe deve conferir o estoque."


class MovedMarkerLocation(unittest.TestCase):
    """c909f1d lines 435-453."""

    def test_fixture_markers(self):
        self.assertEqual(dict(doc(MUST_PAY).entries[0].signal_counts()), {"modality.necessity": 1})
        self.assertEqual(dict(doc(PAYS, NEUTRAL, FRAME).signal_counts()), {"metadiscourse.framing": 1})

    def test_the_issue_names_the_first_sentence_that_lost_and_the_first_that_gained(self):
        # A new first sentence shifts the candidate (j = i + 1), an unchanged sentence comes first,
        # and the marker leaves two sentences and lands in two others: every index is distinguishable.
        src = doc(NEUTRAL, MUST_PAY, DELIVERS, MUST_SIGN, CHECKS)
        out = doc("Uma frase nova abre o texto.", NEUTRAL, PAYS, MUST_DELIVER, SIGNS, MUST_CHECK)
        issues = moved(src, out, [(i, i + 1, 0.9) for i in range(5)])
        self.assertEqual([(i["code"], i["severity"], i["removed_from"], i["added_to"]) for i in issues],
                         [("modality_moved", "critical", MUST_PAY, MUST_DELIVER)])

    def test_a_net_increase_with_a_relocation_is_not_a_move(self):
        # modality: 1 -> 2 (reported as a count change elsewhere); negation moves after it in label order.
        src = doc(MUST_PAY, DELIVERS, SIGNS, "O gerente não assina o termo.", CHECKS)
        out = doc(PAYS, MUST_DELIVER, MUST_SIGN, SIGNS, "A equipe não confere o estoque.")
        self.assertEqual([i["code"] for i in moved(src, out, same(5))], ["negation_moved"])

    def test_a_net_decrease_with_a_relocation_is_not_a_move(self):
        src = doc(MUST_PAY, MUST_DELIVER, SIGNS, "O gerente não assina o termo.", CHECKS)
        out = doc(PAYS, DELIVERS, MUST_SIGN, SIGNS, "A equipe não confere o estoque.")
        self.assertEqual([i["code"] for i in moved(src, out, same(5))], ["negation_moved"])

    def test_informational_categories_never_move_and_do_not_stop_the_check(self):
        # negation_concord (informational by category) travels with the negation; metadiscourse
        # (informational, sorted before modality) stays put while modality moves.
        src = doc(FRAME, "Ele não fez nada.", "Ela fez tudo.", MUST_PAY, DELIVERS)
        out = doc(FRAME, "Ele fez tudo.", "Ela não fez nada.", PAYS, MUST_DELIVER)
        self.assertEqual(sorted(i["code"] for i in moved(src, out, same(5))), ["modality_moved", "negation_moved"])

    def test_a_pair_below_the_similarity_threshold_is_ignored(self):
        src, out = doc(MUST_PAY, DELIVERS), doc(PAYS, MUST_DELIVER)
        self.assertEqual(moved(src, out, [(0, 0, 0.3), (1, 1, 0.9)]), [])
        self.assertEqual(moved(src, out, [(0, None, 0.0), (1, 1, 0.9)]), [])

    def test_a_pair_exactly_at_the_threshold_counts(self):
        src, out = doc(MUST_PAY, DELIVERS), doc(PAYS, MUST_DELIVER)
        self.assertEqual(len(moved(src, out, [(0, 0, ALIGN_MIN_SIMILARITY), (1, 1, 0.9)])), 1)

    def test_an_ignored_pair_does_not_end_the_check(self):
        src = doc(NEUTRAL, MUST_PAY, DELIVERS)
        out = doc(NEUTRAL, PAYS, MUST_DELIVER)
        self.assertEqual(len(moved(src, out, [(0, 0, 0.3), (1, 1, 0.9), (2, 2, 0.9)])), 1)
        self.assertEqual(len(moved(src, out, [(0, None, 0.0), (1, 1, 0.9), (2, 2, 0.9)])), 1)


HIRED = "A empresa contratou João."
WILL_HIRE = "A empresa contratará João."


class TenseOracles(unittest.TestCase):
    """c909f1d lines 464-491."""

    def test_the_message_names_both_tenses(self):
        issues = _tense_issues(doc(HIRED), doc(WILL_HIRE), same(1))
        self.assertEqual(issues[0]["message"],
                         "verb 'contratar': pretérito perfeito -> futuro do presente")

    def test_a_periphrasis_is_named_by_its_construction(self):
        issues = _tense_issues(doc("Ele terminou o relatório."), doc("Ele está terminando o relatório."), same(1))
        self.assertEqual(issues[0]["message"], "verb 'terminar': pretérito perfeito -> progressive@pres_ind")

    def test_a_pair_below_the_threshold_is_ignored_and_does_not_end_the_check(self):
        src, out = doc(HIRED, "O gerente assinou o termo."), doc(WILL_HIRE, "O gerente assinará o termo.")
        self.assertEqual(_tense_issues(src, out, [(0, 0, 0.3)]), [])
        self.assertEqual(_tense_issues(src, out, [(0, 0, ALIGN_MIN_SIMILARITY)])[0]["lemma"], "contratar")
        self.assertEqual([i["lemma"] for i in _tense_issues(src, out, [(0, 0, 0.3), (1, 1, 0.9)])], ["assinar"])
        self.assertEqual([i["lemma"] for i in _tense_issues(src, out, [(0, None, 0.0), (1, 1, 0.9)])], ["assinar"])

    def test_the_same_construction_on_both_sides_is_no_change(self):
        # Construction labels are built at run time: equal strings, distinct objects (line 487, `!=` vs `is not`).
        self.assertEqual(_tense_issues(doc("Ele está terminando o relatório."),
                                       doc("Ele está terminando o relatório hoje."), same(1)), [])

    def test_a_verb_with_two_tenses_on_either_side_abstains(self):
        two = "A empresa contratou João e contratará Maria."
        one = "A empresa contratava João e Maria."
        self.assertEqual(_tense_issues(doc(two), doc(one), same(1)), [])
        self.assertEqual(_tense_issues(doc(one), doc(two), same(1)), [])


FUTURE_SEND = "A empresa enviará o contrato amanhã."
LIGHT = "A empresa vai até o contrato amanhã."


class PredicateOracles(unittest.TestCase):
    """c909f1d lines 504-568."""

    def test_short_stems_abstain(self):
        # "pagar" has a three-letter stem: below PREDICATE_MIN_STEM, no anchor.
        self.assertEqual(_event_anchors("A empresa pagou a conta."), {})
        self.assertEqual(_event_anchors("A empresa enviou o contrato."), {"envi": {"enviar"}})

    def test_a_token_that_may_be_a_light_verb_abstains(self):
        # "conseguia": conseguir (light) or the guessed "conseguer". One stem, but not only content verbs (line 520).
        self.assertEqual(_event_anchors("Ele conseguia o contrato."), {})

    def test_the_issue_reports_the_first_lemma_of_the_anchor(self):
        # "vendia" -> {vender, vendir}: the message and the record name the first in sorted order (line 568).
        issues = _predicate_issues(doc("A loja vendia o carro."), doc("A loja ia até o carro."), same(1))
        self.assertEqual([(i["code"], i["lemma"]) for i in issues], [("predicate_missing", "vender")])

    def test_a_weak_ending_token_does_not_end_the_sentence(self):
        self.assertEqual(_event_anchors("Durante a semana a empresa enviou o contrato."), {"envi": {"enviar"}})

    def test_a_pair_below_the_threshold_is_ignored_and_does_not_end_the_check(self):
        src = doc("O gerente assinará o termo.", FUTURE_SEND)
        out = doc("O gerente vai até o termo.", LIGHT)
        self.assertEqual([i["lemma"] for i in _predicate_issues(src, out, [(0, 0, 0.3), (1, 1, 0.9)])], ["enviar"])

    def test_the_window_does_not_wrap_to_the_last_sentence(self):
        # j = 0: the neighbours are 0 and 1 only. The verb's stem in the last sentence
        # (index -1 in Python) must not count as a counterpart.
        src = doc(FUTURE_SEND)
        out = doc(LIGHT, "O prazo segue o mesmo.", "Nada foi enviado ontem.")
        self.assertEqual([i["code"] for i in _predicate_issues(src, out, [(0, 0, 0.9)])], ["predicate_missing"])


if __name__ == "__main__":
    unittest.main()
