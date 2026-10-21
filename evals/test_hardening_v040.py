"""v0.4.0 M0: regression tests for defects confirmed in the v0.3.0 audit.

Each class names the defect it pins down. Frozen suites are read, never edited.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.evals import check, run

SEMANTIC = ROOT / "evals" / "semantic"


class Ho007IsAClassificationDivergence(unittest.TestCase):
    """ho-007 asks for span_added; the engine catches the inserted clause as
    possible_addition. It was detected, so it must not be reported as a
    missed detection, and the strict count must not hide it either."""

    def test_detected_but_classified_under_another_code(self):
        case = next(c for c in map(json.loads, (SEMANTIC / "holdout.jsonl").read_text(encoding="utf-8").splitlines())
                    if c["id"] == "ho-007")
        result = check(case)
        self.assertIn(result["status"], {"fail", "review_required"})
        self.assertIn("possible_addition", result["codes"])
        self.assertFalse(result["passed"])
        self.assertEqual(result["failure_kind"], "classification_divergence")

    def test_suite_reports_strict_and_status_counts_apart(self):
        report = run(SEMANTIC / "holdout.jsonl", require_frozen=True)
        self.assertEqual(report["passed"], 23)          # the frozen expectation still fails
        self.assertEqual(report["status_passed"], 24)   # but nothing was missed
        self.assertEqual(report["failure_kinds"], {"classification_divergence": 1})

    def test_missed_detection_is_a_false_green(self):
        case = {"id": "x", "category": "value", "original": "O prazo é sexta.", "candidate": "O prazo é sexta.",
                "expect": {"status": ["fail"]}}
        self.assertEqual(check(case)["failure_kind"], "false_green")
        case = dict(case, candidate="O prazo não é sexta.", expect={"status": ["no_deterministic_issues"]})
        self.assertEqual(check(case)["failure_kind"], "false_red")


from voznativa.engine import rewrite  # noqa: E402
from voznativa.judge import sources_hash  # noqa: E402
from voznativa.providers import StaticProvider  # noqa: E402
from voznativa.review import content_hash  # noqa: E402
from voznativa.router import route  # noqa: E402

FACTS = ["Lançamento: 3 de novembro. Preço: R$ 49,90 por mês. Disponível para Android."]
REQUEST = "Escreva um anúncio curto para o app."


def grounding_answer(sources, candidate, verdict, claims):
    return "<final>" + candidate + "</final>", json.dumps({
        "kind": "llm", "judge_id": "fake", "verdict": verdict, "claims": claims,
        "sources_sha256": sources_hash(sources), "candidate_sha256": content_hash(candidate), "rationale": "x"})


class CreateModeJudgeChecksTheSources(unittest.TestCase):
    """v0.3.0 judged a created text against the request only (judge.prompt(request,
    candidate)); claims without a protected value passed every check."""

    def setUp(self):
        from voznativa.engine import authorized_sources
        self.ctx = route(REQUEST, task="create", genre="social")
        self.sources = authorized_sources(REQUEST, FACTS)

    def run_create(self, candidate, verdict, claims, votes=1):
        writer, judge_json = grounding_answer(self.sources, candidate, verdict, claims)
        judge = StaticProvider([judge_json] * 4)
        result = rewrite(REQUEST, self.ctx, StaticProvider([writer]), facts=FACTS, judge_provider=judge,
                         judge_votes=votes, attempts=1)
        return result, judge

    def test_judge_prompt_carries_the_fact_sources(self):
        candidate = "Chega em 3 de novembro, por R$ 49,90 por mês."
        _, judge = self.run_create(candidate, "supported", [
            {"claim": "chega em 3 de novembro", "status": "supported", "evidence": "Lançamento: 3 de novembro"}])
        self.assertIn("FONTES AUTORIZADAS", judge.calls[0])
        self.assertIn("Disponível para Android", judge.calls[0])
        self.assertIn("<<<PEDIDO", judge.calls[0])
        self.assertNotIn("<<<ORIGINAL", judge.calls[0])

    def test_unsupported_claim_without_a_value_is_rejected(self):
        # "milhares de clientes" has no number span: only the judge can see it.
        candidate = "Chega em 3 de novembro e já conquistou milhares de clientes."
        result, _ = self.run_create(candidate, "unsupported", [
            {"claim": "já conquistou milhares de clientes", "status": "unsupported", "evidence": None}])
        self.assertEqual(result["outcome"], "returned_original")

    def test_supported_verdict_needs_evidence_found_in_the_sources(self):
        candidate = "Chega em 3 de novembro, o app mais rápido do mercado."
        result, _ = self.run_create(candidate, "supported", [
            {"claim": "o app mais rápido do mercado", "status": "supported", "evidence": "o mais rápido do mercado"}])
        self.assertEqual(result["outcome"], "needs_review")
        judgment = result["report"]["evidence"]["judgments"][-1]
        self.assertEqual(judgment["downgraded"], "supported claims quote evidence that is not in the sources")

    def test_backed_verdict_is_accepted_as_grounded(self):
        candidate = "Chega em 3 de novembro para Android, por R$ 49,90 por mês."
        result, _ = self.run_create(candidate, "supported", [
            {"claim": "chega em 3 de novembro", "status": "supported", "evidence": "Lançamento: 3 de novembro."},
            {"claim": "para Android", "status": "supported", "evidence": "disponível para android"},
            {"claim": "R$ 49,90 por mês", "status": "supported", "evidence": "Preço: R$ 49,90 por mês"}], votes=2)
        self.assertEqual(result["outcome"], "accepted")
        self.assertEqual(result["report"]["semantic_equivalence"], "judged_grounded_by_llm")

    def test_values_stated_in_the_request_are_a_source(self):
        ctx = route("Convite curto para a reunião de sexta às 15h.", task="create", genre="email")
        result = rewrite("Convite curto para a reunião de sexta às 15h.", ctx,
                         StaticProvider(["<final>Reunião na sexta, às 15h.</final>"]), attempts=1)
        self.assertNotEqual(result["outcome"], "returned_original", result["attempts"])

    def test_placeholder_needs_a_person(self):
        result = rewrite(REQUEST, self.ctx, StaticProvider(
            ["<final>Chega em 3 de novembro. Suporte: [DADO NECESSÁRIO: e-mail de suporte].</final>"]),
            facts=FACTS, attempts=1)
        self.assertEqual(result["outcome"], "needs_review")
        self.assertIn("missing_data_placeholder", result["attempts"][0]["codes"])

    def test_cli_ground_applies_a_grounding_judgment(self):
        import io
        import tempfile
        from contextlib import redirect_stdout
        from voznativa import cli
        candidate = "Chega em 3 de novembro, por R$ 49,90 por mês."
        with tempfile.TemporaryDirectory() as tmp:
            files = {name: Path(tmp, name) for name in ("req.txt", "fact.txt", "cand.txt", "j.json")}
            files["req.txt"].write_text(REQUEST, encoding="utf-8")
            files["fact.txt"].write_text(FACTS[0], encoding="utf-8")
            files["cand.txt"].write_text(candidate, encoding="utf-8")
            _, judge_json = grounding_answer(self.sources, candidate, "unsupported", [
                {"claim": "por R$ 49,90", "status": "contradicted", "evidence": None}])
            files["j.json"].write_text(judge_json, encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli.main(["ground", str(files["cand.txt"]), "--request", str(files["req.txt"]),
                                 "--fact", str(files["fact.txt"]), "--judgment", str(files["j.json"])])
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(out.getvalue())["status"], "fail")
            out = io.StringIO()
            with redirect_stdout(out):
                cli.main(["judge-prompt", str(files["req.txt"]), str(files["cand.txt"]),
                          "--fact", str(files["fact.txt"])])
            self.assertIn(sources_hash(self.sources), out.getvalue())


if __name__ == "__main__":
    unittest.main()
