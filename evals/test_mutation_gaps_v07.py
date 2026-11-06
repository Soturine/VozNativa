"""v0.7.0 CP14: tests for survivors of a Cosmic Ray run on voznativa/temporal.py.

875 mutants, 613 killed, 262 survived (evals/assurance/runs/2026-11-06-v07-cp14/MUTATION.md). Each test
names the executable survivor it was written for; equivalent survivors are argued in that file, not here."""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import temporal  # noqa: E402


def senses(text):
    return [(h["id"], h["sense"]) for h in temporal.observe(text)]


class HyphenBoundary(unittest.TestCase):
    """_hyphen_compound: `end + 1 < len`, `plain[end] == "-"`, `plain[end + 1].isalpha()` (line 188)."""

    def test_hyphen_at_the_very_end_is_not_a_compound(self):
        self.assertEqual(senses("tá de boa-"), [("de-boa", "slang")])     # IndexError or a wrong compound otherwise

    def test_punctuation_that_sorts_after_the_hyphen_is_not_a_hyphen(self):
        self.assertEqual(senses("tá de boa.Valeu"), [("de-boa", "slang")])

    def test_hyphen_then_letter_is_a_compound(self):
        self.assertEqual(senses("agiu de boa-fé"), [])


class NextWordAcrossALineBreak(unittest.TestCase):
    """`plain[end:m.start(1)].strip(" \\t")` (lines 176, 181): a line break ends the phrase."""

    def test_line_break_before_the_next_word(self):
        self.assertEqual(senses("tá de boa\nqualidade do produto em outro item"), [("de-boa", "slang")])

    def test_coordinated_adjective_after_a_line_break_is_not_joined(self):
        self.assertEqual(senses("foi de boa e\nmá a ideia"), [("de-boa", "slang")])


class SenseFlow(unittest.TestCase):
    def test_a_context_decided_other_sense_is_not_reopened_by_the_historic_check(self):
        # `if sense == "slang"` -> `<=` would date an other_sense hit and keep it (line 226).
        old = "Elle agiu de boa vontade naquelle anno."
        self.assertEqual(senses(old), [])

    def test_reason_is_reported_for_non_slang_senses_only(self):
        # `if reason` -> `if not reason` (line 240).
        hits = temporal.observe("O mano mais velho herdou a fazenda.")
        self.assertEqual(hits[0]["sense"], "ambiguous")
        self.assertIn("sense_reason", hits[0])
        self.assertNotIn("sense_reason", temporal.observe("o rolê foi bom")[0])


class Epochs(unittest.TestCase):
    def test_current_is_two_years_back_in_any_year(self):
        # `today.year - 2` -> `today.year ^ 2` coincides only in years like 2026 (line 263).
        self.assertEqual(temporal.parse_epoch("current", today=date(2025, 6, 1)), {"spec": "current", "from": 2023, "to": 2025})

    def test_attestation_edges_are_inclusive(self):
        entry = {"period": {"attestations": [{"from": 2010, "to": 2012, "count": 3},
                                             {"from": 2015, "to": 2015, "count": 0}]}}
        self.assertTrue(temporal.attested_in(entry, {"from": 2012, "to": 2014}))
        self.assertTrue(temporal.attested_in(entry, {"from": 2008, "to": 2010}))
        self.assertFalse(temporal.attested_in(entry, {"from": 2013, "to": 2016}), "count 0 is no attestation")

    def test_epoch_notes_report_every_form_once(self):
        # `continue` -> `break` (line 355): a repeated id must not stop the notes.
        found = temporal.observe("vlw vlw, show de bola")
        notes = temporal.epoch_notes(found, {"from": 1990, "to": 1991})
        self.assertEqual(sorted(n["id"] for n in notes), ["show-de-bola", "vlw"])
        self.assertTrue(all(isinstance(n["attested"], list) for n in notes))


class Activation(unittest.TestCase):
    def test_absent_slang_strength_means_nothing_requested(self):
        # `or 0.0` -> `or 1.0` (line 315).
        out = temporal.activate({"targets": {}, "genre": {"value": "social"}, "register": {"value": None}})
        self.assertEqual(out["requested"]["slang_strength"], 0.0)
        self.assertTrue(any("no slang requested" in r for r in out["reasons"]))


class LexiconFiles(unittest.TestCase):
    BASE = {"schema_version": 2, "kind": "voznativa.slang_lexicon",
            "defaults": {"register": {"min": "very_casual", "max": "casual"}, "generation": {"allowed": False}},
            "entries": [{"id": "x1", "term": "xis", "forms": ["xis"], "type": "slang", "meanings": ["m"],
                         "ambiguity": {"ambiguous": False}},
                        {"id": "x2", "term": "ypsilon", "forms": ["ypsilon"], "type": "slang", "meanings": ["m"],
                         "ambiguity": {"ambiguous": False}}]}

    def write(self, tmp, lexicon, attestations=None):
        path = Path(tmp) / "lexicon.yml"
        path.write_text(yaml.safe_dump(lexicon, allow_unicode=True), encoding="utf-8")
        if attestations is not None:
            (Path(tmp) / "attestations.yml").write_text(yaml.safe_dump(attestations), encoding="utf-8")
        temporal._load.cache_clear()
        return path

    def tearDown(self):
        temporal._load.cache_clear()

    def test_attestations_may_cover_only_some_ids(self):
        # set difference -> symmetric difference would refuse a lexicon id without attestations (line 132).
        with tempfile.TemporaryDirectory() as tmp:
            run = {"source": "s", "from": 2018, "to": 2018, "count": 1, "words": 10, "run": "r"}
            path = self.write(tmp, self.BASE, {"entries": {"x1": {"period": {"attestations": [run]}}}})
            self.assertEqual(len(temporal.load_lexicon(path)["entries"]), 2)
            path = self.write(tmp, self.BASE, {"entries": {"zz": {"period": {"attestations": [run]}}}})
            with self.assertRaises(ValueError):
                temporal.load_lexicon(path)

    def test_evidence_above_e0_needs_a_counted_attestation_with_every_field(self):
        # `count > 0` (line 99) and the per-attestation field check loop (line 100).
        entry = dict(self.BASE["entries"][0], evidence={"level": "E2", "sources": [], "notes": []},
                     period={"attestations": [{"source": "s", "from": 2018, "to": 2018, "count": 0, "words": 1,
                                               "run": "r"}]})
        problems = temporal.validate_lexicon(dict(self.BASE, entries=[entry]))
        self.assertTrue(any("needs at least one attestation" in p for p in problems))
        entry["period"] = {"attestations": [{"source": "s", "count": 2}]}
        problems = temporal.validate_lexicon(dict(self.BASE, entries=[entry]))
        self.assertTrue(any("source, from, to, count, words and run" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
