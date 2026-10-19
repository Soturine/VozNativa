"""Regressions for false reds found in the real-model integration runs of 2026-10-19
(evals/integration/*ptbr-ai-drafts-v1.json and *ptbr-v1.json, claude-sonnet-5-5)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare
from voznativa.judge import validate
from voznativa.region import inspect as region
from voznativa.review import content_hash


class RegionalMarkersKeepAccents(unittest.TestCase):
    def test_so_is_not_the_mineiro_marker_so(self):
        # ai-corp-001 / ai-support-001: "só" folded to "so" matched "sô".
        self.assertEqual(region("Os pedidos só serão processados depois.")["marker_count"], 0)
        self.assertEqual(region("uai, sô, que trem bão")["marker_count"], 2)


class FixedExpressions(unittest.TestCase):
    def test_politeness_formula_is_not_negation(self):
        # ai-support-001 attempt 1: "não hesite em" -> "é só" failed as a negation flip.
        report = compare("Caso tenha dúvida, não hesite em entrar em contato.",
                         "Se tiver dúvida, é só entrar em contato.")
        self.assertNotEqual(report["status"], "fail", report["issues"])

    def test_conforme_alinhado_is_not_attribution(self):
        # bm-corporate-001: "conforme alinhado" -> "como alinhamos" needed review.
        report = compare("Pessoal, conforme alinhado ontem, a entrega foi adiada.",
                         "Pessoal, como alinhamos ontem, a entrega foi adiada.")
        self.assertNotIn("attribution_changed", {i["code"] for i in report["issues"]})

    def test_real_attribution_is_still_protected(self):
        self.assertEqual(compare("Segundo a Anvisa, o lote foi liberado.", "O lote foi liberado.")["status"], "fail")
        self.assertIn("attribution_changed", {i["code"] for i in compare(
            "Conforme o IBGE, o desemprego caiu.", "O desemprego caiu.")["issues"]})


class JudgeFormulaRemoval(unittest.TestCase):
    TEXTS = ("Liderança é sobre pessoas. E isso muda tudo.", "Liderança é sobre pessoas.")

    def judgment(self, statuses):
        return {"kind": "llm", "judge_id": "t", "verdict": "equivalent",
                "original_sha256": content_hash(self.TEXTS[0]), "candidate_sha256": content_hash(self.TEXTS[1]),
                "claims": [{"source": f"c{i}", "status": s} for i, s in enumerate(statuses)]}

    def test_removed_emphasis_formula_is_compatible_with_equivalence(self):
        # ai-social-001: the judge rejected the removal of "E isso muda tudo.".
        result = validate(self.judgment(["preserved", "formula_removed"]), *self.TEXTS)
        self.assertEqual(result["verdict"], "equivalent")
        self.assertEqual(result["formulas_removed"], 1)

    def test_all_formula_removed_is_not_equivalence(self):
        self.assertEqual(validate(self.judgment(["formula_removed"]), *self.TEXTS)["verdict"], "uncertain")

    def test_omitted_claim_still_blocks_equivalence(self):
        self.assertEqual(validate(self.judgment(["preserved", "omitted"]), *self.TEXTS)["verdict"], "uncertain")


if __name__ == "__main__":
    unittest.main()
