"""v0.10.5 V105-GAP-11 (found by the Derivanta Framework audit session, confirmed by reading compare.py):
a judgment file may *declare* any generator_relation, including one that accepts. The report must say the
relation was declared, not observed, and a file cannot pass itself off as engine-observed."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from voznativa import cli, judge
from voznativa.compare import apply_judgment, compare
from voznativa.review import content_hash

ORIGINAL = "É importante destacar que o relatório será enviado na segunda-feira."
CANDIDATE = "O relatório será enviado na segunda-feira."


def answer(relation, **extra):
    return {"kind": "llm", "judge_id": "unit", "verdict": "equivalent", "generator_relation": relation,
            "original_sha256": content_hash(ORIGINAL), "candidate_sha256": content_hash(CANDIDATE),
            "claims": [{"source": "o relatório será enviado na segunda-feira", "status": "preserved"}],
            "added_claims": [], **extra}


class RelationEvidence(unittest.TestCase):
    def _cli(self, judgment):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for name, body in (("o.txt", ORIGINAL), ("c.txt", CANDIDATE), ("j.json", json.dumps(judgment))):
                (Path(d) / name).write_text(body, encoding="utf-8")
                paths.append(str(Path(d) / name))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["compare", paths[0], paths[1], "--judgment", paths[2]])
        return code, json.loads(out.getvalue())

    def test_a_declared_relation_accepts_nothing(self):
        # defect (continuation of V105-GAP-11): the agent that wrote the candidate could write a judgment file
        # declaring different_model and get accepted_by_llm, exit 0, safe_to_auto_accept
        for relation, extra in (("different_model", {}), ("different_provider", {}), ("same_vendor", {}),
                                ("independence_verified", {"independence_evidence": "outro modelo, confie"}),
                                ("different_model", {"relation_evidence": "ENGINE_OBSERVED"})):
            code, report = self._cli(answer(relation, **extra))
            self.assertEqual(report["status"], "no_deterministic_issues", relation)
            self.assertFalse(report["safe_to_auto_accept"], relation)
            self.assertIn("independent_judgment", report["requires"], relation)
            self.assertEqual(report["declared_assessment"]["relation_evidence"], "DECLARED", relation)
            self.assertNotIn("judge_independence", report, relation)
            self.assertNotEqual(code, 0, relation)

    def test_declared_judgment_through_the_api_is_conservative_too(self):
        # a dict without relation_evidence (library users, benchmark files) is declared, not observed
        report = apply_judgment(compare(ORIGINAL, CANDIDATE),
                                judge.validate(answer("different_provider"), ORIGINAL, CANDIDATE))
        self.assertEqual(report["status"], "no_deterministic_issues")
        self.assertFalse(report["safe_to_auto_accept"])

    def test_control_a_declared_rejection_still_counts(self):
        # rejections only make the result safer, whoever declares them
        bad = dict(answer("different_model"), verdict="not_equivalent")
        code, report = self._cli(bad)
        self.assertEqual(report["status"], "fail")

    def test_engine_observed_relation_is_kept(self):
        observed = judge.validate(answer("different_provider", relation_evidence="ENGINE_OBSERVED"),
                                  ORIGINAL, CANDIDATE)
        report = apply_judgment(compare(ORIGINAL, CANDIDATE), observed)
        self.assertEqual(report["judge_independence"]["relation_evidence"], "ENGINE_OBSERVED")
        self.assertEqual(report["judge_independence"]["level"], "provider")      # level semantics unchanged

    def test_the_engine_marks_the_relation_it_ran_as_observed(self):
        from evals.test_v08_judge_relation import ORIGINAL as O8, OneProvider
        from voznativa import engine
        from voznativa.router import route
        writer, judge_p = OneProvider(), OneProvider()
        writer.model, judge_p.model = "writer-model", "judge-model"
        result = engine.rewrite(O8, route(O8), writer, judge_provider=judge_p)
        self.assertEqual(result["outcome"], "accepted")
        self.assertEqual(result["report"]["judge_independence"]["relation_evidence"], "ENGINE_OBSERVED")

    def test_self_assessment_still_accepts_nothing(self):
        code, report = self._cli(answer("same_agent"))
        self.assertEqual(report["status"], "no_deterministic_issues")
        self.assertIn("independent_judgment", report["requires"])


if __name__ == "__main__":
    unittest.main()
