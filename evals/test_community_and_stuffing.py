"""v0.6.0 community packs, the shared stuffing guard and their integration
(router, contract, planner, engine review, profile, CLI): community terms
are kept and never added, anglicism findings on preserved terms are
withdrawn only when the community is requested, and slang or jargon a
candidate adds is reported."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import community, region, stuffing  # noqa: E402
from voznativa.cli import main as cli_main  # noqa: E402
from voznativa.contract import compact, resolve  # noqa: E402
from voznativa.engine import validate_candidate  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.planner import plan, prompt_block  # noqa: E402
from voznativa.profile import build as build_profile  # noqa: E402
from voznativa.router import route, transformation_targets  # noqa: E402

TECH_MAIL = ("Oi, equipe. Amanhã faço o deploy do backend depois da revisão dos pull requests. "
             "Se aparecer algum bug, eu aviso no canal.")


class Packs(unittest.TestCase):
    def test_shipped_packs_are_valid_drafts_that_never_add(self):
        packs = community.load_packs()
        self.assertEqual({p["id"] for p in packs}, {"tech", "corporate", "academia", "gaming"})
        for p in packs:
            self.assertEqual((p["status"], p["evidence"]["level"]), ("draft", "E0"))
            self.assertFalse(p["generation"]["allowed"])
            for item in p["items"]:
                self.assertIn(item["category"], community.CATEGORIES)

    def test_validation(self):
        base = {"schema_version": 2, "kind": "voznativa.community_pack", "id": "x", "name": "x",
                "context_of_practice": "x", "period": {}, "items": []}
        bad = dict(base, status="calibrated", evidence={"level": "E0", "sources": []}, generation={"allowed": True})
        text = " | ".join(community.validate_pack(bad))
        for needle in ("needs evidence E2", "needs evidence.sources", "generation needs a non-draft"):
            self.assertIn(needle, text)
        item = {"term": "sextou", "forms": ["sextou"], "category": "meme", "behaviour": "preserve",
                "legitimate_in": [], "false_positive": "-", "evidence": "E0"}
        draft = dict(base, status="draft", evidence={"level": "E0"}, generation={"allowed": False},
                     items=[item, dict(item, term="dup", category="jargon")])
        text = " | ".join(community.validate_pack(draft))
        self.assertIn("temporal", text)
        self.assertIn("listed twice", text)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "other.yml").write_text(yaml.safe_dump(dict(draft, items=[])), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "id must match the file name"):
                community.load_packs(Path(tmp))


class Activation(unittest.TestCase):
    def test_abstains_without_a_request_and_explains_unknown_packs(self):
        self.assertEqual(community.activate({"targets": {}}, TECH_MAIL)["status"], "abstain")
        out = community.activate({"targets": {"community": "astrologia"}}, TECH_MAIL)
        self.assertIsNone(out["pack"])
        self.assertIn("unknown community pack", out["reasons"][0])

    def test_keeps_the_texts_terms_and_withdraws_anglicism_findings_only_when_requested(self):
        # A thesis about software engineering: the academic genre flags tech borrowings.
        thesis = ("Este trabalho mede o tempo de deploy em equipes que usam backend monolítico. "
                  "Os resultados indicam redução de falhas após a adoção de revisão por pares.")
        context = route(thesis, genre="academic")
        report = detect(thesis, "academic")
        flagged = {f["text"].lower() for f in report["findings"] if f["id"] == "anglicism_out_of_domain"}
        self.assertEqual(flagged & {"deploy", "backend"}, {"deploy", "backend"})
        self.assertIs(community.apply_to_report(report, context, thesis), report)   # no community: unchanged
        tech = route(thesis, genre="academic", community="tech")
        applied = community.apply_to_report(report, tech, thesis)
        self.assertFalse({f["text"].lower() for f in applied["findings"]
                          if f["id"] == "anglicism_out_of_domain"} & {"deploy", "backend"})
        # CP14 (UNCHECKED_ALL, confirmed): a report that dropped the withdrawn list passed vacuously.
        self.assertEqual({w["text"].lower() for w in applied["withdrawn"]} & {"deploy", "backend"},
                         {"deploy", "backend"}, "every withdrawn finding is listed")
        self.assertTrue(all(w["withdrawn_by"] == "community:tech" for w in applied["withdrawn"]))
        self.assertLessEqual(applied["summary"]["weak"] + applied["summary"]["strong"],
                             report["summary"]["weak"] + report["summary"]["strong"])


class Stuffing(unittest.TestCase):
    def test_levels_and_rise(self):
        self.assertEqual(stuffing.level(0.0, 0), "low")
        self.assertEqual(stuffing.level(0.03, 1), "medium")
        self.assertEqual(stuffing.level(0.0, 4), "high")
        rise = stuffing.compare("slang", [], ["top", "top", "top"], 50, 50)
        self.assertTrue(rise["stuffed"])
        dense_source = stuffing.compare("slang", ["top"] * 3, ["top"] * 3, 50, 50)
        self.assertFalse(dense_source["stuffed"])            # the author's own density is not stuffing

    def test_region_guard_uses_the_shared_thresholds(self):
        report = region.inspect("uai uai uai uai sô")
        self.assertEqual(report["regional_overfit"], "high")
        self.assertEqual(region.inspect("Bom dia a todos.")["regional_overfit"], "low")


class Integration(unittest.TestCase):
    def test_router_epoch(self):
        context = route("Texto.", epoch="1994-1996")
        self.assertEqual(context["targets"]["epoch"], {"spec": "1994-1996", "from": 1994, "to": 1996})
        self.assertTrue(context["flags"]["epoch_target"])
        self.assertEqual(transformation_targets("Texto.", context), [])      # an epoch alone asks for no rewrite
        with self.assertRaises(ValueError):
            route("Texto.", epoch="anos 90")

    def test_contract_reports_temporal_and_community_decisions(self):
        text = "O jogo é show de bola, roda tudo de boa."
        contract = resolve(route(text, genre="social", slang_strength=0.6, epoch="1994-1995"), None, None, text)
        self.assertEqual(contract["slang_strength"], {"requested": 0.6, "effective": 0.0})
        self.assertEqual(contract["temporal"]["keep"], ["de boa", "show de bola"])
        self.assertEqual({n["id"] for n in contract["temporal"]["epoch_notes"]}, {"show-de-bola", "de-boa"})
        self.assertTrue(any("slang strength stays 0.0" in w for w in contract["warnings"]))
        self.assertEqual(compact(contract)["keep_author_slang"], ["de boa", "show de bola"])
        tech = resolve(route(TECH_MAIL, genre="email", community="tech"), None, None, TECH_MAIL)
        self.assertEqual(tech["community_terms_preserve"], ["backend", "bug", "deploy", "pull request"])
        self.assertTrue(any("is a draft" in w for w in tech["warnings"]))
        unknown = resolve(route(TECH_MAIL, community="astrologia"), None, None, TECH_MAIL)
        self.assertTrue(any("unknown community pack" in w for w in unknown["warnings"]))

    def test_planner_tells_the_writer_to_keep_the_authors_slang_and_terms(self):
        text = ("Comprei o celular e achei muito top, show de bola mesmo. Mas a entrega foi realizada com "
                "atraso e a efetivação da troca foi feita de forma lenta, o que gerou insatisfação.")
        context = route(text, genre="social", community="tech")
        p = plan(text, context)
        self.assertEqual(p["decision"], "transform")    # a requested community is a destination target
        self.assertEqual(p["temporal"]["keep"], ["muito top", "show de bola"])
        self.assertEqual(p["community"]["pack"], "tech")
        self.assertIn("gíria do autor: mantenha 'muito top', 'show de bola'", prompt_block(p))

    def test_engine_review_flags_added_slang_and_jargon(self):
        original = "O produto chegou no prazo e funciona bem."
        context = route(original, genre="social")
        review = validate_candidate(original, "O produto chegou no prazo e é top demais, show de bola, mano.",
                                    context, None)
        codes = {i["code"]: i["severity"] for i in review["issues"]}
        self.assertEqual(codes.get("slang_introduced"), "major")
        mail = "Amanhã publico a nova versão do sistema."
        review = validate_candidate(mail, "Amanhã faço o deploy da nova versão, alinhado com a call de ontem.",
                                    route(mail, genre="email"), None)
        severities = [i["severity"] for i in review["issues"] if i["code"] == "community_term_introduced"]
        self.assertIn("info", severities)          # terminology (deploy)
        self.assertIn("major", severities)         # jargon / discourse habit (call, alinhar)

    def test_engine_review_keeps_quiet_on_the_authors_own_slang(self):
        original = "Chegou rápido, show de bola. Recomendo."
        review = validate_candidate(original, "Chegou rápido, show de bola! Recomendo.", route(original), None)
        self.assertFalse({"slang_introduced", "slang_stuffing", "author_slang_removed"}
                         & {i["code"] for i in review["issues"]})
        dropped = validate_candidate(original, "Chegou rápido. Recomendo.", route(original), None)
        self.assertIn(("author_slang_removed", "info"),
                      {(i["code"], i["severity"]) for i in dropped["issues"]})

    def test_profile_records_the_authors_slang_as_a_habit_to_keep(self):
        samples = ["Chegou rápido, show de bola, recomendo pra todo mundo que precisa de um fone bom e barato.",
                   "Show de bola esse carregador, funciona certinho e não esquenta nada, comprei dois de uma vez.",
                   "Mais um pedido que chegou antes do prazo, show de bola, a loja está de parabéns pelo cuidado."]
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, s in enumerate(samples):
                p = Path(tmp) / f"s{i}.txt"
                p.write_text(s, encoding="utf-8")
                paths.append(str(p))
            profile = build_profile([{"text": Path(p).read_text(encoding="utf-8"), "path": p} for p in paths])
        habits = {h["id"]: h for h in profile.get("habits", [])}
        self.assertIn("slang.show-de-bola", habits)
        self.assertEqual(habits["slang.show-de-bola"]["value"], "keep")

    def test_cli_rejects_a_malformed_epoch_as_a_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = Path(tmp) / "t.txt"
            text.write_text("Texto.", encoding="utf-8")
            err, out = io.StringIO(), io.StringIO()
            with redirect_stderr(err), redirect_stdout(out):
                code = cli_main(["route", str(text), "--epoch", "anos 90"])
            self.assertEqual(code, 64)
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                self.assertEqual(cli_main(["route", str(text), "--epoch", "current"]), 0)


if __name__ == "__main__":
    unittest.main()
