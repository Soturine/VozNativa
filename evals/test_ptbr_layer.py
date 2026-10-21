"""v0.4.0 M2: PT-BR contextual layer in the engine (variant, domain terms,
forms of address). Detector-level cases live in evals/patterns/cases.jsonl."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.contract import resolve
from voznativa.engine import build_prompt, rewrite
from voznativa.providers import StaticProvider
from voznativa.ptbr import candidate_issues, foreign_terms, variant_markers
from voznativa.router import route

TECH = "É importante destacar que o deploy da release 2.4 corrigiu o bug do cache. Você pode conferir no log."


class EngineChecks(unittest.TestCase):
    def test_rewrite_that_introduces_european_portuguese_needs_review(self):
        bad = "<final>O deploy da release 2.4 corrigiu o bug do cache, de facto. Você pode conferir no log.</final>"
        result = rewrite(TECH, route(TECH, genre="technical"), StaticProvider([bad]), attempts=1)
        self.assertEqual(result["outcome"], "needs_review")
        self.assertIn("variant_drift", result["attempts"][0]["codes"])

    def test_translating_domain_terms_is_reported_not_blocked(self):
        issues = candidate_issues(TECH, "A implantação da versão 2.4 corrigiu o erro do cache. Você pode conferir no log.",
                                  "technical")
        codes = {i["code"]: i["severity"] for i in issues}
        self.assertEqual(codes.get("domain_term_translated"), "info")

    def test_form_of_address_change_needs_a_request(self):
        changed = "O deploy da release 2.4 corrigiu o bug do cache. O senhor pode conferir no log."
        self.assertIn("treatment_changed", {i["code"] for i in candidate_issues(TECH, changed, "technical")})
        self.assertNotIn("treatment_changed",
                         {i["code"] for i in candidate_issues(TECH, changed, "technical", register_explicit=True)})

    def test_prompt_tells_the_writer_what_to_keep(self):
        ctx = route(TECH, genre="technical")
        prompt = build_prompt(TECH, ctx, resolve(ctx))
        self.assertIn("termos do domínio, mantenha como estão: bug, cache, deploy, log, release", prompt)
        self.assertIn("forma de tratamento do original: você", prompt)
        pt = "A propina da universidade subiu e a equipa vai reunir-se amanhã."
        ctx = route(pt, genre="corporate")
        prompt = build_prompt(pt, ctx, resolve(ctx))
        self.assertIn("equipa -> equipe / time", prompt)
        self.assertIn("falsos amigos: confira o sentido antes de trocar: propina", prompt)


class Lexicon(unittest.TestCase):
    def test_quotes_keep_their_variant(self):
        self.assertEqual(variant_markers('Ele disse: "a equipa está a jogar bem".'), [])

    def test_bare_word_is_not_estar_a_infinitive(self):
        self.assertEqual(variant_markers("O documento está a seguir. Estou a fim de sair."), [])

    def test_domain_depends_on_genre(self):
        text = "Recebi o feedback sobre o deploy."
        self.assertEqual({t["text"] for t in foreign_terms(text, "technical")["out_of_domain"]}, {"feedback"})
        self.assertEqual(foreign_terms(text, "corporate")["out_of_domain"], [])


if __name__ == "__main__":
    unittest.main()
