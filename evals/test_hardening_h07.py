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
        # line 235: `x != hit.group(0)` -> `is not`. Both sides are regex groups: equal, never the same object.
        text = LEXICON_YAML.replace("forms: [xis]", "forms: [blz]").replace(
            "ambiguity: {ambiguous: false}", "ambiguity: {ambiguous: true, other_senses: [o], detection: form}")
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, text)
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

    @unittest.expectedFailure      # CP2
    def test_negative_count_is_refused_with_a_reason(self):
        self.assertTrue(any("count" in p and "negative" in p for p in self.problems(count=-1)))

    @unittest.expectedFailure      # CP2
    def test_boolean_float_and_string_counts_are_refused(self):
        for bad in (True, 2.0, "3"):
            self.assertTrue(any("count" in p for p in self.problems(count=bad)), bad)

    def test_zero_count_is_valid_but_attests_nothing(self):
        self.assertTrue(any("needs at least one attestation with count > 0" in p for p in self.problems(count=0)))


class PredicateLoss(unittest.TestCase):
    """H07-006/007: the README pair kept values and negation and lost the action."""

    @unittest.expectedFailure      # CP3
    def test_action_replaced_by_a_light_verb_is_flagged(self):
        r = compare("O relatório trimestral será enviado até sexta-feira, 14/11/2025.",
                    "O relatório trimestral vai até sexta-feira, 14/11/2025.")
        self.assertNotEqual(r["status"], "no_deterministic_issues")

    def test_action_kept_with_another_verb_is_not_blocked(self):
        r = compare("O relatório trimestral será enviado até sexta-feira, 14/11/2025.",
                    "O relatório trimestral será encaminhado até sexta-feira, 14/11/2025.")
        self.assertEqual(r["status"], "no_deterministic_issues")


class FutureForms(unittest.TestCase):
    """Found by the frozen predicate sample before any rule: `tense_changed`
    read "vai depositar" and "depositará" as different tenses."""

    @unittest.expectedFailure      # CP3
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
