"""v0.8 (V08-GAP-16): an agent judging its own candidate is not an independent judge.

Before: the judge contract recorded only ``kind`` and ``judge_id``; in Skill
mode the host agent writes the candidate and then judges it, and its
"equivalent" became ``accepted_by_llm`` like an independent model's. Now a
judgment carries ``generator_relation``; ``same_agent`` + equivalent is
recorded as ``agent_assessment`` (AGENT_OBSERVED) and accepts nothing."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import engine, judge  # noqa: E402
from voznativa.compare import apply_judgment, compare  # noqa: E402
from voznativa.review import content_hash  # noqa: E402
from voznativa.router import route  # noqa: E402

ORIGINAL = "É importante destacar que o relatório será enviado na segunda-feira."
CANDIDATE = "O relatório será enviado na segunda-feira."


def judgment(verdict="equivalent", relation=None):
    j = {"kind": "llm", "judge_id": "host-agent", "verdict": verdict,
         "original_sha256": content_hash(ORIGINAL), "candidate_sha256": content_hash(CANDIDATE),
         "claims": [{"source": "o relatório será enviado na segunda-feira", "status": "preserved",
                     "candidate": "O relatório será enviado na segunda-feira."},
                    {"source": "É importante destacar que", "status": "formula_removed", "candidate": None}]}
    if relation:
        j["generator_relation"] = relation
    return judge.validate(j, ORIGINAL, CANDIDATE)


class Contract(unittest.TestCase):

    def setUp(self):
        self.report = compare(ORIGINAL, CANDIDATE)
        self.assertEqual(self.report["status"], "no_deterministic_issues")

    def test_self_assessment_accepts_nothing(self):
        merged = apply_judgment(self.report, judgment(relation="same_agent"))
        self.assertEqual(merged["status"], "no_deterministic_issues")
        self.assertFalse(merged["safe_to_auto_accept"])
        self.assertIn("independent_judgment", merged["requires"])
        self.assertEqual(merged["agent_assessment"]["evidence"], "AGENT_OBSERVED")
        self.assertIn("not an independent", merged["agent_assessment"]["note"])

    def test_a_self_rejection_still_makes_the_result_safer(self):
        merged = apply_judgment(self.report, judgment("not_equivalent", "same_agent"))
        self.assertEqual(merged["status"], "fail")

    def test_unknown_or_different_model_keeps_the_previous_contract(self):
        for relation in (None, "unknown", "different_model"):
            with self.subTest(relation=relation):
                self.assertEqual(apply_judgment(self.report, judgment(relation=relation))["status"], "accepted_by_llm")

    def test_invalid_relation_is_refused(self):
        with self.assertRaises(ValueError):
            judgment(relation="independent")

    def test_the_prompt_asks_for_the_relation(self):
        self.assertIn("generator_relation", judge.prompt(ORIGINAL, CANDIDATE, self.report))


JUDGE_OK = ('{"kind": "llm", "judge_id": "stub", "generator_relation": "different_model", "verdict": "equivalent", '
            '"claims": [{"source": "o relatório será enviado na segunda-feira", "status": "preserved", '
            '"candidate": "O relatório será enviado na segunda-feira."}, {"source": "É importante destacar que", '
            '"status": "formula_removed", "candidate": null}], "added_claims": [], "rationale": "ok"}')


class OneProvider:
    """Generates the candidate and, when asked to judge, answers like a judge."""
    id = "one"

    def generate(self, prompt, n=1):
        if "BINDING" in prompt and "RESPONSE_SCHEMA" in prompt:
            return [JUDGE_OK] * n
        return [f"<final>{CANDIDATE}</final>"] * n


class Engine(unittest.TestCase):

    def run_with(self, judge_provider, generator):
        return engine.rewrite(ORIGINAL, route(ORIGINAL), generator, judge_provider=judge_provider)

    def test_the_generator_judging_itself_is_not_accepted(self):
        same = OneProvider()
        result = self.run_with(same, same)
        self.assertEqual(result["outcome"], "needs_judgment", "a self-assessment must not accept")

    def test_a_separate_judge_still_accepts_and_its_own_claim_is_ignored(self):
        result = self.run_with(OneProvider(), OneProvider())
        self.assertEqual(result["outcome"], "accepted")

    def test_same_command_line_is_the_same_agent(self):
        class Cmd:
            def __init__(self, argv):
                self.argv, self.id = argv, "cmd"
        self.assertEqual(engine._generator_relation(Cmd(["claude", "-p"]), Cmd(["claude", "-p"])), "same_agent")
        self.assertEqual(engine._generator_relation(Cmd(["claude", "-p"]), Cmd(["codex", "exec"])), "unknown")
        p = OneProvider()
        self.assertEqual(engine._generator_relation(p, p), "same_agent")


if __name__ == "__main__":
    unittest.main()
