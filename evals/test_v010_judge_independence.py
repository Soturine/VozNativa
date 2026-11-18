"""v0.10 CP6 (D-02): independence is shown, not assumed; partial independence is stated."""
import unittest

from voznativa import judge
from voznativa.compare import apply_judgment, compare
from voznativa.providers import vendor_of
from voznativa.review import content_hash

ORIGINAL = "É importante destacar que o relatório será enviado na segunda-feira."
CANDIDATE = "O relatório será enviado na segunda-feira."


def answer(relation, **extra):
    return {"kind": "llm", "judge_id": "unit", "verdict": "equivalent", "generator_relation": relation,
            "original_sha256": content_hash(ORIGINAL), "candidate_sha256": content_hash(CANDIDATE),
            "claims": [{"source": "o relatório será enviado na segunda-feira", "status": "preserved"}],
            "added_claims": [], **extra}


class Independence(unittest.TestCase):
    def test_verified_independence_needs_evidence(self):
        with self.assertRaises(ValueError):
            judge.validate(answer("independence_verified"), ORIGINAL, CANDIDATE)
        ok = judge.validate(answer("independence_verified", independence_evidence="revisora externa, modelo X"),
                            ORIGINAL, CANDIDATE)
        report = apply_judgment(compare(ORIGINAL, CANDIDATE), ok)
        self.assertEqual(report["status"], "accepted_by_llm")
        self.assertEqual(report["judge_independence"]["level"], "declared")

    def test_same_vendor_accepts_with_partial_independence_stated(self):
        report = apply_judgment(compare(ORIGINAL, CANDIDATE),
                                judge.validate(answer("same_vendor"), ORIGINAL, CANDIDATE))
        self.assertEqual(report["status"], "accepted_by_llm")
        self.assertEqual(report["judge_independence"]["level"], "partial")
        provider = apply_judgment(compare(ORIGINAL, CANDIDATE),
                                  judge.validate(answer("different_provider"), ORIGINAL, CANDIDATE))
        self.assertEqual(provider["judge_independence"]["level"], "provider")

    def test_vendor_comes_only_from_declared_configuration(self):
        self.assertEqual(vendor_of({"program": "x", "model": "claude-haiku-5-5"}), "anthropic")
        self.assertEqual(vendor_of({"program": "x", "model": "openrouter/gpt-5"}), "openai")
        self.assertEqual(vendor_of({"program": "gemini", "model": None}), "google")
        self.assertIsNone(vendor_of({"program": "python", "model": "modelo-local-7b"}))


if __name__ == "__main__":
    unittest.main()
