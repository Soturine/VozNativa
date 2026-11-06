"""v0.7.0.dev1 hardening (docs/PLAN_v0.7.0.dev1.md): reproductions written
before the fixes.

* H07-001/002: ``==`` against values that are equal but not the same object.
  The v0.7 mutation triage called 12 ``==``/``!=`` -> ``is``/``is not``
  survivors equivalent because "literals are interned"; values that come from
  YAML, regex groups or ``join`` are not. Each test reaches the mutated line
  through a public entry point with such a value.
* H07-003..005: the attestation ``count`` contract (expected failures until CP2).
* H07-006/007: an action or commitment that disappears behind a light verb
  (expected failure until CP3).
"""
import operator
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import temporal  # noqa: E402
from voznativa.compare import compare  # noqa: E402

TODAY = date(2026, 11, 6)

LEXICON_YAML = """\
schema_version: 2
kind: voznativa.slang_lexicon
defaults:
  register: {min: very_casual, max: casual}
  generation: {allowed: false}
entries:
- id: x1
  term: xis
  forms: [xis]
  type: slang
  meanings: [m]
  ambiguity: {ambiguous: false}
  generation: {allowed: true}
  evidence: {level: E2, sources: [s], notes: []}
  deprecation: {status: active, reason: null}
  period:
    last_verified_at: '%s'
    attestations:
    - {source: s, from: 2025, to: 2026, count: 3, words: 1000, run: r}
""" % (TODAY - timedelta(days=10)).isoformat()


def not_the_literal(value, literal):
    """Precondition of a contrast test: the value equals the literal but is
    another object. If a runtime ever interns it, the contrast cannot be made."""
    return value == literal and not operator.is_(value, literal)


class LexiconFile(unittest.TestCase):
    def write(self, tmp, text):
        path = Path(tmp) / "lexicon.yml"
        path.write_text(text, encoding="utf-8")
        temporal._load.cache_clear()
        return path

    def tearDown(self):
        temporal._load.cache_clear()


class DynamicStringsReachTheComparisons(LexiconFile):
    """H07-001/002. Each test names the temporal.py line (revision e7506f5) whose
    `==`/`!=` -> `is`/`is not` mutant survived the v0.7 run."""

    def test_status_active_from_yaml_is_active(self):
        # line 109 (validate_lexicon) and line 303 (entry_status): `!= "active"` -> `is not`.
        raw = yaml.safe_load(LEXICON_YAML)
        status = raw["entries"][0]["deprecation"]["status"]
        if not not_the_literal(status, "active"):
            self.skipTest("this runtime returned the interned literal; no contrast possible")
        self.assertEqual(temporal.validate_lexicon(raw), [])
        with tempfile.TemporaryDirectory() as tmp:
            entry = temporal.load_lexicon(self.write(tmp, LEXICON_YAML))["entries"][0]
            status = temporal.entry_status(entry, {"from": 2025, "to": 2026}, "whatsapp", "casual", TODAY)
        self.assertEqual(status, {"id": "x1", "allowed": True, "reasons": []})

    def test_context_detection_from_yaml_needs_a_detect_pattern(self):
        # line 91: `== "context"` -> `is`: an ambiguous entry decided by context but with no pattern.
        text = LEXICON_YAML.replace("ambiguity: {ambiguous: false}",
                                    "ambiguity: {ambiguous: true, other_senses: [o], detection: context}")
        raw = yaml.safe_load(text)
        self.assertTrue(not_the_literal(raw["entries"][0]["ambiguity"]["detection"], "context")
                        or self.skipTest("interned"))
        self.assertIn("x1: context detection needs a detect pattern", temporal.validate_lexicon(raw))

    def test_epoch_current_from_outside_the_module(self):
        # line 262: `spec == "current"` -> `is`. CLI arguments and YAML contexts are not the literal.
        for spec in (yaml.safe_load("epoch: current")["epoch"], "".join(["cur", "rent"])):
            if not not_the_literal(spec, "current"):
                self.skipTest("interned")
            self.assertEqual(temporal.parse_epoch(spec, TODAY), {"spec": "current", "from": 2024, "to": 2026})

    def test_an_ambiguous_form_that_is_also_a_chat_cue_does_not_corroborate_itself(self):
        # line 235: `x != hit.group(0)` -> `is not`. Both sides are regex groups. When a pattern
        # matches the WHOLE string, CPython returns the input object itself from group(0), so
        # "blz" alone cannot tell `is` from `==` (the first version of this test used it and the
        # mutant survived: dev1 CP1). A match inside a longer text is a new object on each side.
        text = LEXICON_YAML.replace("forms: [xis]", "forms: [blz]").replace(
            "ambiguity: {ambiguous: false}", "ambiguity: {ambiguous: true, other_senses: [o], detection: form}")
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, text)
            self.assertEqual([h["sense"] for h in temporal.observe("ok, blz.", path)], ["ambiguous"])
            self.assertEqual([h["sense"] for h in temporal.observe("blz", path)], ["ambiguous"])
            self.assertEqual([h["sense"] for h in temporal.observe("blz vc", path)], ["slang"])


class CountContract(LexiconFile):
    """H07-003..005: `count` is a non-negative integer (the producer writes
    len(findall)); the validator, not each consumer, enforces it."""

    def problems(self, **attestation):
        base = {"source": "s", "from": 2025, "to": 2026, "count": 3, "words": 1000, "run": "r"}
        raw = yaml.safe_load(LEXICON_YAML)
        raw["entries"][0]["period"]["attestations"] = [dict(base, **attestation)]
        return temporal.validate_lexicon(raw)

    def test_negative_count_is_refused_with_a_reason(self):
        self.assertIn("x1: attestation count must not be negative (-1)", self.problems(count=-1))

    def test_boolean_float_and_string_counts_are_refused(self):
        # A string "3" used to raise TypeError at `count > 0` before any message.
        for bad in (True, False, 2.0, "3"):
            problems = self.problems(count=bad)
            self.assertTrue(any(p.startswith("x1: attestation count must be an integer") for p in problems),
                            (bad, problems))

    def test_missing_count_is_reported_once_by_the_presence_check(self):
        problems = self.problems(count=None)
        self.assertIn("x1: an attestation needs source, from, to, count, words and run", problems)
        self.assertFalse(any("must be an integer" in p for p in problems), problems)

    def test_words_years_and_verification_date(self):
        self.assertIn("x1: attestation words must not be negative (-5)", self.problems(words=-5))
        self.assertIn("x1: attestation from 2026 is after to 2025", self.problems(**{"from": 2026, "to": 2025}))
        self.assertTrue(any("from must be an integer year" in p for p in self.problems(**{"from": "2025"})))
        raw = yaml.safe_load(LEXICON_YAML)
        raw["entries"][0]["period"]["last_verified_at"] = "ontem"
        self.assertIn("x1: period.last_verified_at must be an ISO date, not 'ontem'",
                      temporal.validate_lexicon(raw))
        raw["entries"][0]["period"]["last_verified_at"] = date(2026, 10, 1)    # unquoted YAML date
        self.assertEqual(temporal.validate_lexicon(raw), [])

    def test_valid_boundaries_are_accepted(self):
        self.assertEqual(self.problems(count=1, words=0, **{"from": 2025, "to": 2025}), [])

    def test_schema_version_must_be_an_integer(self):
        for bad in (2.0, "2", True):
            raw = dict(yaml.safe_load(LEXICON_YAML), schema_version=bad)
            self.assertIn("schema_version must be 2", temporal.validate_lexicon(raw), bad)

    def test_zero_count_is_valid_but_attests_nothing(self):
        self.assertTrue(any("needs at least one attestation with count > 0" in p for p in self.problems(count=0)))
        self.assertFalse(any("count" in p and "integer" in p for p in self.problems(count=0)))

    def test_zero_count_is_not_an_attestation_for_consumers(self):
        # H07-004: "searched and found nothing" must not open an epoch or license generation.
        text = LEXICON_YAML.replace("evidence: {level: E2, sources: [s], notes: []}",
                                    "evidence: {level: E0, sources: [], notes: []}").replace(
            "generation: {allowed: true}", "generation: {allowed: false}").replace("count: 3", "count: 0")
        epoch = {"from": 2025, "to": 2026}
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, text)
            entry = temporal.load_lexicon(path)["entries"][0]
            self.assertEqual(temporal.attested_in(entry, epoch), [])
            status = temporal.entry_status(entry, epoch, "whatsapp", "casual", TODAY)
            self.assertIn("no attestation in 2025-2026", status["reasons"])
            notes = temporal.epoch_notes([{"id": "x1", "text": "xis"}], dict(epoch, spec="2025-2026"), path)
            self.assertEqual(notes[0]["attested"], [])

    def test_the_shipped_lexicon_and_its_attestations_satisfy_the_contract(self):
        temporal._load.cache_clear()
        self.assertGreater(len(temporal.load_lexicon()["entries"]), 0)


class PredicateLoss(unittest.TestCase):
    """H07-006/007: the README pair kept values and negation and lost the action."""

    def test_action_replaced_by_a_light_verb_is_flagged(self):
        r = compare("O relatório trimestral será enviado até sexta-feira, 14/11/2025.",
                    "O relatório trimestral vai até sexta-feira, 14/11/2025.")
        self.assertNotEqual(r["status"], "no_deterministic_issues")

    def test_action_kept_with_another_verb_is_not_blocked(self):
        r = compare("O relatório trimestral será enviado até sexta-feira, 14/11/2025.",
                    "O relatório trimestral será encaminhado até sexta-feira, 14/11/2025.")
        self.assertEqual(r["status"], "no_deterministic_issues")


class PredicateGuardBoundaries(unittest.TestCase):
    """H07-007..010: what the predicate check must not do, and where it must reach."""

    def codes(self, original, candidate):
        return {i["code"]: i["severity"] for i in compare(original, candidate)["issues"]}

    def test_agent_patient_inversion_still_fails(self):            # H07-008
        r = compare("A Ana demitiu o Bruno.", "O Bruno demitiu a Ana.")
        self.assertEqual(r["status"], "fail")
        self.assertIn("role_reversed", [i["code"] for i in r["issues"]])

    def test_passive_with_agent_and_nominalization_keep_the_action(self):   # H07-007
        for original, candidate in (
                ("A Ana enviou o relatório ontem.", "O relatório foi enviado pela Ana ontem."),
                ("A empresa pagará a multa em março.", "O pagamento da multa será feito pela empresa em março."),
                ("O auditor revisará as contas em maio.", "Em maio, o auditor fará a revisão das contas.")):
            codes = self.codes(original, candidate)
            self.assertNotIn("predicate_missing", codes, (original, candidate))
            self.assertNotIn("predicate_replaced", codes, (original, candidate))

    def test_another_content_verb_is_information_not_a_block(self):       # H07-007
        codes = self.codes("O cliente assinou o contrato em 3 de março.", "O cliente recebeu o contrato em 3 de março.")
        self.assertEqual(codes.get("predicate_replaced"), "info")

    def test_literary_ellipsis_is_never_a_confirmed_error(self):          # H07-009
        self.assertEqual(self.codes("Ela comprou pão e ele comprou leite.", "Ela comprou pão; ele, leite."), {})
        self.assertEqual(self.codes("A noite chegou, e com ela chegou o cansaço.", "A noite chegou e, com ela, o cansaço."),
                         {})
        # A verbless poetic line loses the verb: at most a review, never a fail from this rule.
        r = compare("O vento soprava forte sobre a noite escura.", "Vento forte sobre a noite escura.")
        self.assertNotEqual(r["status"], "fail")
        self.assertTrue(all(i["severity"] != "critical" for i in r["issues"] if i["code"].startswith("predicate")))

    def test_light_verbs_and_prepositions_are_not_anchors(self):
        from voznativa.compare import _event_anchors
        self.assertEqual(_event_anchors("A Ana tem prazo para o contrato durante a semana."), {})
        self.assertEqual(_event_anchors("Vou para casa depois do trabalho."), {})

    def test_a_long_document_does_not_hide_a_lost_action_in_a_later_segment(self):   # H07-010
        from voznativa import engine
        from voznativa.document import Limits
        from voznativa.router import route
        intro = ("É importante destacar que o lote {i} saiu do armazém na segunda-feira e chegou ao cliente "
                 "sem atraso. A equipe conferiu as {n} caixas e não encontrou avarias.")
        action = "A equipe enviará o relatório final ao cliente até sexta-feira, 14/11/2025."
        doc = "\n\n".join([intro.format(i=1, n=4), intro.format(i=2, n=5), action]) + "\n"

        class Provider:
            id = "fn-stub"

            def generate(self, prompt, n=1):
                import re
                body = re.search(r"<<<TEXTO#(\w+)\n(.*)\nTEXTO#\1>>>", prompt, re.S).group(2)
                body = body.replace("É importante destacar que o", "O").replace(
                    action, "O relatório final fica para sexta-feira, 14/11/2025.")
                return [f"<final>{body}</final>"] * n
        result = engine.rewrite_document(doc, route(doc, genre="corporate"), Provider(),
                                         limits=Limits(segment_words=40), force=True)
        if action not in result["text"]:     # the unit was kept: then someone must be told
            self.assertEqual(result["outcome"], "needs_review", result["outcome"])
            self.assertIn("predicate_missing", str(result["global_report"]) + str(result["units"]))
        self.assertNotIn(result["outcome"], {"accepted", "needs_judgment"})


class FutureForms(unittest.TestCase):
    """Found by the frozen predicate sample before any rule: `tense_changed`
    read "vai depositar" and "depositará" as different tenses."""

    def test_periphrastic_and_synthetic_future_are_the_same_time(self):
        r = compare("O banco vai depositar o valor na conta até o dia 10.",
                    "O banco depositará o valor na conta até o dia 10.")
        self.assertNotIn("tense_changed", [i["code"] for i in r["issues"]])

    def test_past_and_future_still_differ(self):
        r = compare("O banco depositou o valor na conta até o dia 10.",
                    "O banco vai depositar o valor na conta até o dia 10.")
        self.assertIn("tense_changed", [i["code"] for i in r["issues"]])


class SplitTableRow(unittest.TestCase):
    """H07-016: VN07-DISC-016 was split in two by a heredoc that expanded "\\n"."""

    def test_validator_reports_a_table_row_split_across_lines(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate_package_h07", ROOT / "scripts" / "validate_package.py")
        vp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vp)
        with tempfile.TemporaryDirectory() as tmp:
            vp.ROOT = Path(tmp)
            (Path(tmp) / "r.md").write_text("| a | b |\n|---|---|\n| x | `\n` |\n| ok | ok |\n", encoding="utf-8")
            errors = []
            vp.check_text_files(errors)
        self.assertEqual(errors, ["r.md:3: Markdown table row does not end with '|' (a row split across lines?)"])


if __name__ == "__main__":
    unittest.main()
