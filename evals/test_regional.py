"""v0.5.0 Regional Evidence Packs: regionality only from evidence, abstention
by default, the author's observed form over a regional default, and guards
for referent swaps and unlicensed regional forms."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import regional  # noqa: E402
from voznativa.compare import compare  # noqa: E402
from voznativa.contract import resolve  # noqa: E402
from voznativa.engine import rewrite  # noqa: E402
from voznativa.planner import plan  # noqa: E402
from voznativa.profile import build  # noqa: E402
from voznativa.providers import StaticProvider  # noqa: E402
from voznativa.router import route  # noqa: E402

AIPIM = "Amanhã tem aipim frito no almoço, bora?"
PACK = yaml.safe_load((ROOT / "voznativa" / "data" / "regional_packs" / "br-norte-lex-mandioca.yml")
                      .read_text(encoding="utf-8"))


def ctx(text, region=None, strength=0.2, genre="whatsapp"):
    return route(text, genre=genre, region=region, region_strength=strength if region else 0.0)


class PackContract(unittest.TestCase):
    def test_shipped_pack_is_valid_and_counts_add_up(self):
        self.assertEqual(regional.validate_pack(PACK), [])
        feature = PACK["features"][0]
        self.assertEqual(sum(f["count"] for f in feature["forms"]), feature["total_answers"])

    def test_invalid_packs_are_refused(self):
        cases = {
            "no source url": lambda p: p["sources"][0].pop("url"),
            "region inferred": lambda p: p["activation"].update(requires_explicit_region=False),
            "author does not win": lambda p: p["activation"].update(author_form_wins=False),
            "strength above 0.25 uncalibrated": lambda p: p["activation"].update(max_strength=0.6),
            "unknown state": lambda p: p["scope"]["states"].append("XX"),
            "counts do not add up": lambda p: p["features"][0]["forms"][0].update(count=91),
            "confusion names an unlisted form": lambda p: p["features"][0]["confusions"].append(
                {"forms": ["macaxeira", "batata"], "risk": "x"}),
        }
        for name, mutate in cases.items():
            pack = copy.deepcopy(PACK)
            mutate(pack)
            self.assertNotEqual(regional.validate_pack(pack), [], name)

    def test_an_invalid_pack_file_fails_loading_instead_of_being_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = copy.deepcopy(PACK)
            bad["activation"]["requires_explicit_region"] = False
            (Path(tmp) / "bad.yml").write_text(yaml.safe_dump(bad, allow_unicode=True), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid regional evidence pack"):
                regional.load_packs(Path(tmp))


class Activation(unittest.TestCase):
    def test_abstains_without_a_requested_region_even_with_regional_words(self):
        a = regional.activate(ctx(AIPIM), AIPIM)
        self.assertEqual((a["status"], a["effective_strength"], a["features"]), ("abstain", 0.0, []))
        self.assertIn("never infers a region", a["reasons"][0])

    def test_abstains_for_a_region_no_pack_covers(self):
        for code in ("sp", "nordeste", "mineiro"):
            a = regional.activate(ctx(AIPIM, code), AIPIM)
            self.assertEqual(a["status"], "abstain", code)
            self.assertEqual(a["effective_strength"], 0.0)

    def test_abstains_outside_the_contexts_of_the_evidence_and_without_the_referent(self):
        technical = "O cultivo de aipim exige solo drenado."
        self.assertEqual(regional.activate(ctx(technical, "norte", genre="technical"), technical)["status"], "abstain")
        other = "O relatório sai amanhã."
        self.assertEqual(regional.activate(ctx(other, "norte"), other)["status"], "abstain")

    def test_a_recorded_exception_blocks_the_state(self):
        a = regional.activate(ctx(AIPIM, "to"), AIPIM)
        self.assertEqual(a["status"], "abstain")
        self.assertIn("exception", a["reasons"][0])

    def test_suggests_the_region_form_as_an_option_with_capped_strength(self):
        a = regional.activate(ctx(AIPIM, "am", strength=0.9), AIPIM)
        self.assertEqual(a["status"], "active")
        self.assertEqual(a["effective_strength"], 0.25)
        f = a["features"][0]
        self.assertEqual((f["suggest"], f["replaces"]), ("macaxeira", ["aipim"]))

    def test_a_form_that_can_change_the_referent_is_kept(self):
        text = "Amanhã tem mandioca frita no almoço, bora?"
        f = regional.activate(ctx(text, "norte"), text)["features"][0]
        self.assertIsNone(f["suggest"])
        self.assertEqual(f["keep"], ["mandioca"])

    def test_the_authors_observed_form_wins(self):
        profile = build([{"text": "Fiz aipim cozido hoje."}, {"text": "O aipim da feira tava bom."},
                         {"text": "Sem novidade, só trabalho."}])
        self.assertIn("regional_form.aipim", {h["id"] for h in profile["habits"]})
        for text in (AIPIM, "Vou levar macaxeira pra festa."):
            f = regional.activate(ctx(text, "norte"), text, profile)["features"][0]
            self.assertIsNone(f["suggest"], text)
            self.assertIn("aipim", f["keep"])

    def test_profile_keeps_counts_not_text(self):
        profile = build([{"text": "Comprei aipim na feira da Rua das Flores."}] * 3)
        habit = next(h for h in profile["habits"] if h["id"] == "regional_form.aipim")
        self.assertEqual((habit["value"], habit["evidence_count"], habit["sample_support"]), ("keep", 3, 3))
        self.assertNotIn("Flores", str(profile))


class Integration(unittest.TestCase):
    def test_voice_contract_strength_follows_the_activation(self):
        self.assertEqual(resolve(ctx(AIPIM, "norte"), text=AIPIM)["regional_strength"]["effective"], 0.2)
        c = resolve(ctx(AIPIM, "sp"), text=AIPIM)
        self.assertEqual(c["regional_strength"]["effective"], 0.0)
        self.assertTrue(any("regional strength stays 0.0" in w for w in c["warnings"]))

    def test_plan_carries_the_decision(self):
        self.assertEqual(plan(AIPIM, ctx(AIPIM, "norte"))["regional"]["features"][0]["suggest"], "macaxeira")
        self.assertEqual(plan(AIPIM, ctx(AIPIM))["regional"]["status"], "abstain")

    def test_ledger_flags_a_referent_changing_swap_and_not_a_same_referent_one(self):
        r = compare("Comprei macaxeira na feira.", "Comprei mandioca na feira.")
        self.assertEqual(r["status"], "review_required")
        self.assertIn("regional_referent_changed", {i["code"] for i in r["issues"]})
        self.assertNotIn("regional_referent_changed",
                         {i["code"] for i in compare("Comprei aipim na feira.", "Comprei macaxeira na feira.")["issues"]})

    def test_engine_blocks_regional_decoration_nobody_asked_for(self):
        candidate = "<final>Amanhã tem macaxeira frita no almoço, bora?</final>"
        result = rewrite(AIPIM, ctx(AIPIM), StaticProvider([candidate] * 3), force=True, attempts=1)
        codes = {i["code"] for i in result["report"]["issues"]}
        self.assertIn("regional_form_introduced", codes)
        self.assertNotEqual(result["outcome"], "accepted")
        licensed = rewrite(AIPIM, ctx(AIPIM, "norte"), StaticProvider([candidate] * 3), force=True, attempts=1)
        self.assertNotIn("regional_form_introduced", {i["code"] for i in licensed["report"]["issues"]})


if __name__ == "__main__":
    unittest.main()
