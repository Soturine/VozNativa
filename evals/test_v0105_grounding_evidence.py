"""v0.10.5 continuation: a grounding claim marked "supported" must quote evidence found verbatim in a source, but
any substring counted, so a one-character quote ("2") or a single word ("sim") backed any claim. Found by a real
Claude Code session guided by the Derivanta Framework Skill (installed with its new installer), auditing judge.py;
confirmed by reading `_in_sources`. Fixtures invented."""
import unittest

from voznativa import judge
from voznativa.review import content_hash

SOURCES = [("notas.md", "O clube abre às 7h. A anuidade de 2026 é de 120 reais e vence em março.")]
CANDIDATE = "A anuidade de 2026 custa 150 reais."


def grounding(evidence):
    return {"kind": "llm", "judge_id": "unit", "verdict": "supported", "generator_relation": "same_agent",
            "sources_sha256": judge.sources_hash(SOURCES), "candidate_sha256": content_hash(CANDIDATE),
            "claims": [{"claim": "A anuidade de 2026 custa 150 reais.", "status": "supported", "evidence": evidence}]}


class GroundingEvidence(unittest.TestCase):
    def test_defect_trivial_quotes_do_not_back_a_claim(self):
        for evidence in ("2", "sim", "a", "2026", "reais"):
            result = judge.validate_grounding(grounding(evidence), SOURCES, CANDIDATE)
            self.assertEqual(result["verdict"], "uncertain", evidence)
            self.assertIn("unbacked_claims", result, evidence)

    def test_control_a_real_quote_still_backs_the_claim(self):
        result = judge.validate_grounding(grounding("A anuidade de 2026 é de 120 reais"), SOURCES, CANDIDATE)
        self.assertEqual(result["verdict"], "equivalent")
        self.assertNotIn("unbacked_claims", result)

    def test_control_a_short_but_specific_quote_passes(self):
        result = judge.validate_grounding(grounding("abre às 7h"), SOURCES, CANDIDATE)
        self.assertNotIn("unbacked_claims", result)


if __name__ == "__main__":
    unittest.main()
