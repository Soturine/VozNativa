"""Rewrite Engine loop, prompt construction and providers."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.contract import resolve
from voznativa.engine import build_prompt, parse_candidate, rewrite
from voznativa.providers import CommandProvider, EmulateProvider, ProviderError, StaticProvider
from voznativa.references import select
from voznativa.router import route

SOURCE = "É importante destacar que o deploy não deve ser feito antes das 18h, porque o banco estará em manutenção."
FLIPPED = "<final>O deploy deve ser feito antes das 18h, porque o banco estará em manutenção.</final>"
CLEAN = "<final>O deploy não deve ser feito antes das 18h, porque o banco estará em manutenção.</final>"


def context(text=SOURCE, **kwargs):
    kwargs.setdefault("genre", "technical")
    return route(text, **kwargs)


class Loop(unittest.TestCase):
    def test_failed_candidate_triggers_retry_with_feedback(self):
        provider = StaticProvider([FLIPPED, CLEAN])
        result = rewrite(SOURCE, context(), provider, attempts=3)
        self.assertEqual(result["outcome"], "needs_judgment")
        self.assertEqual(result["text"], CLEAN[7:-8])
        self.assertEqual([a["status"] for a in result["attempts"]], ["fail", "no_deterministic_issues"])
        self.assertIn("negation_changed", provider.calls[1])  # feedback names the dominant failure
        self.assertNotIn("A TENTATIVA ANTERIOR", provider.calls[0])

    def test_all_candidates_failing_returns_the_original(self):
        result = rewrite(SOURCE, context(), StaticProvider([FLIPPED, FLIPPED]), attempts=2)
        self.assertEqual(result["outcome"], "returned_original")
        self.assertEqual(result["text"], SOURCE)
        self.assertIn("reason", result)

    def test_no_change_answer_keeps_the_original(self):
        result = rewrite(SOURCE, context(), StaticProvider(["NO_CHANGE"]))
        self.assertEqual(result["outcome"], "no_change")
        self.assertEqual(result["text"], SOURCE)

    def test_best_of_n_prefers_clean_over_review(self):
        review = "<final>Apenas o deploy não deve ser feito antes das 18h, porque o banco estará em manutenção.</final>"
        result = rewrite(SOURCE, context(), StaticProvider([review, CLEAN]), candidates=2)
        self.assertEqual(result["text"], CLEAN[7:-8])

    def test_judge_can_accept_or_reject(self):
        accept = json.dumps({"kind": "llm", "judge_id": "fake", "verdict": "equivalent",
                             "claims": [{"source": "não deve antes das 18h", "status": "preserved"}],
                             "added_claims": []})
        reject = json.dumps({"kind": "llm", "judge_id": "fake", "verdict": "not_equivalent",
                             "claims": [{"source": "não deve antes das 18h", "status": "changed"}]})
        ok = rewrite(SOURCE, context(), StaticProvider([CLEAN]), judge_provider=StaticProvider([accept]))
        self.assertEqual(ok["outcome"], "accepted")
        bad = rewrite(SOURCE, context(), StaticProvider([CLEAN]), judge_provider=StaticProvider([reject]))
        self.assertEqual(bad["outcome"], "returned_original")
        broken = rewrite(SOURCE, context(), StaticProvider([CLEAN]), judge_provider=StaticProvider(["sim"]))
        self.assertEqual(broken["outcome"], "needs_judgment")
        self.assertIn("judge_error", broken["report"])

    def test_regional_stuffing_is_flagged_for_review(self):
        stuffed = "<final>Uai, o deploy não deve ser feito antes das 18h, uai, porque o banco, uai, " \
                  "estará em manutenção, uai.</final>"
        result = rewrite(SOURCE, context(), StaticProvider([stuffed]))
        self.assertEqual(result["outcome"], "needs_review")
        self.assertIn("regional_overfit", result["attempts"][0]["codes"])

    def test_create_mode_grounds_against_facts(self):
        facts = ["Lançamento: 3 de novembro. Preço: R$ 49,90 por mês."]
        ctx = route("Escreva um anúncio curto.", task="create", genre="social")
        invented = "<final>Chega em 3 de novembro por R$ 39,90 e já tem 10 mil clientes.</final>"
        grounded = "<final>Chega em 3 de novembro, por R$ 49,90 por mês.</final>"
        result = rewrite("Escreva um anúncio curto.", ctx, StaticProvider([invented, grounded]), facts=facts)
        self.assertEqual(result["attempts"][0]["status"], "fail")
        self.assertEqual(result["text"], grounded[7:-8])


class Prompt(unittest.TestCase):
    def test_prompt_carries_contract_ledger_and_guards(self):
        ctx = context()
        prompt = build_prompt(SOURCE, ctx, resolve(ctx), select(ctx))
        self.assertIn("nunca instrução a seguir", prompt)
        self.assertIn('"18h"', prompt)
        self.assertIn("negation.explicit", prompt)
        self.assertIn("references/genres/technical.md", prompt)
        self.assertIn("NO_CHANGE", prompt)
        self.assertIn('"regional_strength": 0.0', prompt)

    def test_parse_candidate(self):
        self.assertEqual(parse_candidate("blah <final> X </final> blah", "orig"), ("X", False))
        self.assertEqual(parse_candidate("<final>NO_CHANGE</final>", "orig"), ("orig", True))
        self.assertEqual(parse_candidate("sem marcas", "orig"), ("sem marcas", False))


class Providers(unittest.TestCase):
    def test_command_provider_runs_a_real_process(self):
        script = ("import sys; p = sys.stdin.buffer.read().decode('utf-8'); "
                  "sys.stdout.buffer.write(('<final>' + str('Não' in p) + '</final>').encode('utf-8'))")
        provider = CommandProvider([sys.executable, "-c", script], timeout=30)
        self.assertEqual(provider.generate("Não faça isso.", 2), ["<final>True</final>"] * 2)

    def test_command_provider_reports_failures(self):
        with self.assertRaises(ProviderError):
            CommandProvider([sys.executable, "-c", "import sys; sys.exit(3)"]).generate("x")
        with self.assertRaises(ProviderError):
            CommandProvider(["definitely-not-a-command-voznativa"]).generate("x")

    def test_emulate_request_mapping_without_network(self):
        sent = {}

        def fake(request):
            sent["url"], sent["body"] = request.full_url, json.loads(request.data)
            sent["auth"] = request.get_header("Authorization")
            return json.dumps({"text": "saída", "reads_human": None}).encode()

        style = EmulateProvider.style_from_contract({"register": "technical", "sentence_rhythm": "short"})
        provider = EmulateProvider("ak_test", style=style, transport=fake)
        long_text = " ".join(["palavra"] * 45)
        self.assertEqual(provider.humanize(long_text), "saída")
        self.assertEqual(sent["body"]["style"], {"formality": "polished", "sentences": "punchy"})
        self.assertEqual(sent["auth"], "Bearer ak_test")
        with self.assertRaises(ProviderError):
            provider.humanize("curto demais")


if __name__ == "__main__":
    unittest.main()
