"""v0.8.1 dogfood (agent-led, long technical report): regressions for defects found there.

Fixtures are synthetic; no text of the dogfooded document is used.

* DF-01: the long-form call budget (``Limits.max_provider_calls``, CLI
  ``--max-calls``) counted only the writer; every judge vote was a provider
  call outside it, so the budget did not bound the cost of a run with a judge.
* DF-02: in long form the writer reached ``rewrite`` through the budget
  wrapper, so a writer judging itself was not ``same_agent`` and a
  self-judged document was accepted (the one-unit path already refused it).
* DF-03: units are rewritten one by one; a term respelled in some units only
  (in the real run "backend" -> "back-end", suggested by the anglicism finding;
  the fixture uses "email" -> "e-mail") left the
  document with two spellings of one term, and no guard saw it.

DF-04 (compare) is in test_v081_compare_omission.py.
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import engine  # noqa: E402
from voznativa.document import Limits  # noqa: E402
from voznativa.router import route  # noqa: E402

FENCE = re.compile(r"<<<TEXTO#(\w+)\n(.*)\nTEXTO#\1>>>", re.S)
FORMULA = "É importante destacar que "


class Cleaner:
    """Writer stub: removes one formula from the unit it receives."""
    id = "cleaner-stub"

    def __init__(self):
        self.calls = 0

    def generate(self, prompt, n=1):
        self.calls += 1
        body = FENCE.search(prompt).group(2)
        out = re.sub(re.escape(FORMULA) + r"(\w)", lambda m: m.group(1).upper(), body)
        return [f"<final>{out}</final>"] * n


class EquivalentJudge:
    """Judge stub: always answers 'equivalent' with the claims it is shown."""
    id = "judge-stub"

    def __init__(self):
        self.calls = 0

    def generate(self, prompt, n=1):
        self.calls += 1
        claims = [{"source": "o fato da unidade", "status": "preserved", "candidate": "o fato da unidade",
                   "note": "stub"}, {"source": FORMULA.strip(), "status": "formula_removed", "candidate": None,
                                     "note": "stub"}]
        return [json.dumps({"verdict": "equivalent", "claims": claims, "added_claims": [],
                            "judge_id": self.id, "rationale": "stub"})] * n


# Three units at segment_words=12, each with one formula the planner flags.
DOC = ("É importante destacar que o inventário trimestral será entregue ao setor de compras em novembro.\n\n"
       "## Métodos\n\n"
       "É importante destacar que as contagens foram feitas nos três armazéns com duas equipes.\n\n"
       "## Resultados\n\n"
       "É importante destacar que a divergência observada foi pequena no armazém central.\n")


class LongFormBudgetCoversTheJudge(unittest.TestCase):

    def run_doc(self, budget, votes=2):
        writer, judge = Cleaner(), EquivalentJudge()
        result = engine.rewrite_document(DOC, route(DOC, genre="academic"), writer,
                                         limits=Limits(segment_words=12, max_provider_calls=budget),
                                         judge_provider=judge, judge_votes=votes, force=True)
        return result, writer, judge

    def test_control_without_a_tight_budget_the_judge_is_called(self):
        result, writer, judge = self.run_doc(budget=100)
        self.assertGreaterEqual(writer.calls, 2)
        self.assertGreater(judge.calls, 0, "control: the stub judge must be reached at all")

    def test_writer_and_judge_calls_never_exceed_the_budget(self):
        for budget in (1, 2, 3, 4, 5):
            with self.subTest(budget=budget):
                result, writer, judge = self.run_doc(budget=budget)
                self.assertLessEqual(writer.calls + judge.calls, budget,
                                     f"writer={writer.calls} judge={judge.calls}")

    def test_the_record_counts_every_call(self):
        result, writer, judge = self.run_doc(budget=100)
        self.assertEqual(result["provider_calls"], writer.calls + judge.calls)
        self.assertEqual(result.get("judge_calls"), judge.calls)

    def test_a_vote_refused_by_the_budget_is_never_an_acceptance(self):
        result, writer, judge = self.run_doc(budget=2)
        for unit in result["units"]:
            self.assertNotEqual(unit["outcome"], "accepted", unit)

    def test_same_object_as_judge_is_still_recognised_as_same_agent(self):
        class Agent(Cleaner):
            judge = EquivalentJudge()

            def generate(self, prompt, n=1):
                return super().generate(prompt, n) if "VOICE_CONTRACT" in prompt else self.judge.generate(prompt, n)
        writer = Agent()
        seen = []
        original = engine._generator_relation

        def spy(provider, judge_provider):
            seen.append(original(provider, judge_provider))
            return seen[-1]
        engine._generator_relation = spy
        try:
            engine.rewrite_document(DOC, route(DOC, genre="academic"), writer,
                                    limits=Limits(segment_words=12), judge_provider=writer, judge_votes=1,
                                    force=True)
        finally:
            engine._generator_relation = original
        self.assertTrue(seen)
        self.assertEqual(set(seen), {"same_agent"})

    def test_a_self_judged_long_document_is_never_accepted(self):
        """The consequence of DF-02: in long form the agent's own 'equivalent'
        verdict accepted every unit, while ``rewrite`` (one unit) gives
        needs_judgment for the same judgment (V08-GAP-16)."""
        class Agent(Cleaner):
            judge = EquivalentJudge()

            def generate(self, prompt, n=1):
                return super().generate(prompt, n) if "VOICE_CONTRACT" in prompt else self.judge.generate(prompt, n)
        single = Agent()
        one = DOC.split("\n\n")[0]
        control = engine.rewrite(one, route(one, genre="academic"), single, judge_provider=single, judge_votes=1,
                                 force=True)
        self.assertEqual(control["outcome"], "needs_judgment", "control: the one-unit path refuses self-approval")
        agent = Agent()
        result = engine.rewrite_document(DOC, route(DOC, genre="academic"), agent, limits=Limits(segment_words=12),
                                         judge_provider=agent, judge_votes=1, force=True)
        self.assertNotIn("accepted", [u["outcome"] for u in result["units"]])
        self.assertNotEqual(result["outcome"], "accepted")

    def test_a_different_judge_still_accepts(self):
        result, writer, judge = self.run_doc(budget=100, votes=1)
        self.assertIn("accepted", [u["outcome"] for u in result["units"]], "control: an outside judge can accept")



class Respeller(Cleaner):
    """Writer stub that respells one term in the first unit it sees only."""

    def generate(self, prompt, n=1):
        self.calls += 1
        body = FENCE.search(prompt).group(2)
        out = body.replace("email", "e-mail") if self.calls == 1 else body.replace("O ", "Esse ", 1)
        return [f"<final>{out}</final>"] * n


TERMS = ("O email de confirmação chega ao cliente logo depois do pagamento aprovado.\n\n"
         "## Métodos\n\n"
         "O email de cobrança sai do sistema financeiro no quinto dia útil de cada mês.\n\n"
         "## Resultados\n\n"
         "O email de lembrete reduziu os atrasos de pagamento no último trimestre.\n")


class LongFormKeepsOneSpellingPerTerm(unittest.TestCase):

    def run_doc(self, writer):
        return engine.rewrite_document(TERMS, route(TERMS, genre="academic"), writer, limits=Limits(segment_words=12),
                                       judge_provider=EquivalentJudge(), judge_votes=1, force=True)

    def test_a_term_spelled_two_ways_after_the_rewrite_is_flagged(self):
        result = self.run_doc(Respeller())
        self.assertIn("e-mail", result["text"])
        self.assertIn("email", result["text"].replace("e-mail", ""))
        variants = [i for i in result["guards"]["introduced"] if i["kind"] == "term_variant"]
        self.assertEqual([sorted(v["forms"]) for v in variants], [["e-mail", "email"]], result["guards"])
        self.assertEqual(result["outcome"], "needs_review")

    def test_control_a_respelling_applied_everywhere_is_not_a_split(self):
        class Everywhere(Cleaner):
            def generate(self, prompt, n=1):
                self.calls += 1
                return [f"<final>{FENCE.search(prompt).group(2).replace('email', 'e-mail')}</final>"] * n
        result = self.run_doc(Everywhere())
        self.assertNotIn("email", result["text"].replace("e-mail", ""))
        self.assertEqual([i for i in result["guards"]["introduced"] if i["kind"] == "term_variant"], [])

    def test_control_variants_already_in_the_original_are_not_introduced(self):
        mixed = TERMS.replace("O email de cobrança", "O e-mail de cobrança")
        result = engine.rewrite_document(mixed, route(mixed, genre="academic"), Respeller(),
                                         limits=Limits(segment_words=12), judge_provider=EquivalentJudge(),
                                         judge_votes=1, force=True)
        self.assertEqual([i for i in result["guards"]["introduced"] if i["kind"] == "term_variant"], [])


if __name__ == "__main__":
    unittest.main()
