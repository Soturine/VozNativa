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

    def test_a_file_relation_is_declared_even_when_the_file_claims_otherwise(self):
        # defect: before v0.10.5 the report showed level "provider" with nothing saying nobody observed it
        code, report = self._cli(answer("different_model", relation_evidence="ENGINE_OBSERVED"))
        self.assertEqual(report["status"], "accepted_by_llm")
        self.assertEqual(report["judge_independence"]["relation_evidence"], "DECLARED")
        self.assertEqual(code, 0)

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
