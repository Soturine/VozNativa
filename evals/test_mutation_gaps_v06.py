"""v0.6.0 CP12: tests written for mutants that survived Cosmic Ray on
voznativa/stuffing.py (32/72) and voznativa/temporal.py (264/701) at f5f2d30.
Each test pins a boundary or a branch the earlier tests did not; equivalent
mutants (annotations under `from __future__ import annotations`, `is` vs
`==` on small ints/interned strings) are documented in
evals/assurance/runs/2026-11-05-v06-cp12/MUTATION.md, not tested."""
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import stuffing, temporal  # noqa: E402


class StuffingBoundaries(unittest.TestCase):
    def test_density_and_repeat_thresholds_are_exact(self):
        self.assertEqual(stuffing.level(0.04, 0), "medium")       # > 0.04 is high, 0.04 is not
        self.assertEqual(stuffing.level(0.0401, 0), "high")
        self.assertEqual(stuffing.level(0.02, 0), "low")          # > 0.02 is medium, 0.02 is not
        self.assertEqual(stuffing.level(0.0201, 0), "medium")
        self.assertEqual(stuffing.level(0.0, 3), "medium")
        self.assertEqual(stuffing.level(0.0, 2), "low")
        self.assertEqual(stuffing.level(0.0, 4), "high")
        self.assertEqual(stuffing.level(0.0, 5), "high")
        self.assertEqual((stuffing.HIGH_DENSITY, stuffing.MEDIUM_DENSITY, stuffing.HIGH_REPEAT,
                          stuffing.MEDIUM_REPEAT), (0.04, 0.02, 4, 3))

    def test_measure_values(self):
        m = stuffing.measure(["Top", "top", "kkk"], 9)
        self.assertEqual(m["density"], 0.3333)                    # 3/9 rounded to 4 places
        self.assertEqual((m["count"], m["max_repeat"], m["forms"]), (3, 2, {"top": 2, "kkk": 1}))
        empty = stuffing.measure([], 0)
        self.assertEqual((empty["density"], empty["max_repeat"], empty["level"]), (0.0, 0, "low"))
        self.assertEqual(stuffing.measure(["x"], 0)["density"], 1.0)   # no division by zero

    def test_compare_flags_only_a_rise(self):
        self.assertFalse(stuffing.compare("s", ["a"] * 4, ["a"] * 3, 500, 500)["stuffed"])   # high -> medium
        self.assertFalse(stuffing.compare("s", ["a"] * 3, ["a"] * 3, 500, 500)["stuffed"])   # medium -> medium
        self.assertTrue(stuffing.compare("s", ["a"] * 3, ["a"] * 4, 500, 500)["stuffed"])    # medium -> high
        self.assertFalse(stuffing.compare("s", [], [], 50, 50)["stuffed"])


TODAY = date(2026, 11, 5)


def lexicon(tmp: Path, last_verified, count=5, extra=None) -> Path:
    entry = {"id": "x", "term": "xis", "forms": ["xis"], "type": "slang", "meanings": ["m"],
             "ambiguity": {"ambiguous": False}, "generation": {"allowed": True}, **(extra or {})}
    (tmp / "lexicon.yml").write_text(yaml.safe_dump({
        "schema_version": 2, "kind": "voznativa.slang_lexicon",
        "defaults": {"register": {"min": "very_casual", "max": "casual"}, "generation": {"forbidden_contexts": []}},
        "entries": [entry]}), encoding="utf-8")
    (tmp / temporal.ATTESTATIONS).write_text(yaml.safe_dump({"entries": {"x": {
        "period": {"attestations": [{"source": "s", "from": 2025, "to": 2026, "count": count, "words": 9,
                                     "run": "r"}], "last_verified_at": last_verified},
        "evidence": {"level": "E2" if count else "E0"}}}}), encoding="utf-8")
    temporal._load.cache_clear()
    return tmp / "lexicon.yml"


def ctx(strength, epoch="current", genre="social"):
    return {"genre": {"value": genre}, "register": {"value": "casual"},
            "targets": {"slang_strength": strength, "epoch": temporal.parse_epoch(epoch, TODAY) if epoch else None}}


class TemporalBranches(unittest.TestCase):
    def tearDown(self):
        temporal._load.cache_clear()

    def test_parse_epoch_edges(self):
        self.assertEqual(temporal.parse_epoch("2026", TODAY), {"spec": "2026", "from": 2026, "to": 2026})
        self.assertEqual(temporal.parse_epoch("current", date(2031, 1, 1))["from"], 2029)
        self.assertEqual(temporal.parse_epoch("2020 - 2022", TODAY)["to"], 2022)
        for nothing in (None, "", "none"):
            self.assertIsNone(temporal.parse_epoch(nothing, TODAY))
        with self.assertRaises(ValueError):
            temporal.parse_epoch("currently", TODAY)
        with self.assertRaises(ValueError):
            temporal.parse_epoch("2027", TODAY)

    def test_staleness_boundary_and_missing_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            on_edge = (TODAY - timedelta(days=temporal.STALE_AFTER_DAYS)).isoformat()
            path = lexicon(Path(tmp), on_edge)
            self.assertEqual(temporal.activate(ctx(0.5), "x", today=TODAY, path=path)["allowed"], ["x"])
            path = lexicon(Path(tmp), (TODAY - timedelta(days=temporal.STALE_AFTER_DAYS + 1)).isoformat())
            self.assertEqual(temporal.activate(ctx(0.5), "x", today=TODAY, path=path)["allowed"], [])
            path = lexicon(Path(tmp), None)
            out = temporal.activate(ctx(0.5), "x", today=TODAY, path=path)
            self.assertEqual(out["allowed"], [])
            self.assertIn("verification missing", out["reasons"][-1])

    def test_strength_rounding_negative_request_and_reasons(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = lexicon(Path(tmp), "2026-10-01")
            self.assertEqual(temporal.activate(ctx(0.12345), "nada", today=TODAY, path=path)["effective_strength"],
                             0.123)
            self.assertEqual(temporal.activate(ctx(0.9), "nada", today=TODAY, path=path)["effective_strength"], 0.3)
            negative = temporal.activate(ctx(-0.5), "nada", today=TODAY, path=path)
            self.assertEqual((negative["status"], negative["allowed"]), ("abstain", []))
            plain = temporal.activate(ctx(0.0), "nada aqui", today=TODAY, path=path)
            self.assertEqual(len(plain["reasons"]), 1)                       # no "author's forms" reason
            with_form = temporal.activate(ctx(0.0), "o xis", today=TODAY, path=path)
            self.assertIn("author's forms are kept", with_form["reasons"][0])

    def test_abstain_reason_counts_each_cause(self):
        out = temporal.activate(ctx(0.8, "1994-1995", genre="technical"), "Texto.", today=TODAY)
        reason = out["reasons"][-1]
        n = len(temporal.load_lexicon()["entries"])
        self.assertIn(f"({n} entries)", reason)
        self.assertIn(f"generation not allowed by the entry ({n})", reason)
        self.assertIn(f"is a forbidden context ({n})", reason)
        first = reason.split(": ", 1)[1].split("; ")[0]
        self.assertTrue(first.endswith(f"({n})"))                        # most frequent cause first

    def test_unattested_counts_and_repeated_forms(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = lexicon(Path(tmp), "2026-10-01", count=0, extra={"generation": {"allowed": False}})
            found = temporal.observe("xis, xis e xis", path)
            self.assertEqual(len(found), 3)
            notes = temporal.epoch_notes(found, temporal.parse_epoch("2025", TODAY), path)
            self.assertEqual([(n["id"], n["attested"]) for n in notes], [("x", [])])   # one note, no span
            self.assertEqual(temporal.attested_in(temporal.load_lexicon(path)["entries"][0],
                                                  temporal.parse_epoch("2025", TODAY)), [])
        # several forms in the candidate: every new id is reported, not only the first
        added = temporal.introduced_terms("Ok.", "Ok, show de bola, show de bola, top demais, kkk.")
        self.assertEqual([a["id"] for a in added], ["show-de-bola", "show-de-bola", "top", "kkk"])
        self.assertEqual(temporal.introduced_terms("show de bola", "show de bola kkk"),
                         [{"id": "kkk", "form": "kkk", "type": "chat_form"}])


def _entry(**extra):
    return {"id": "x", "term": "xis", "forms": ["xis"], "type": "slang", "meanings": ["m"],
            "ambiguity": {"ambiguous": False}, **extra}


def _att(count):
    return {"period": {"attestations": [{"source": "s", "from": 2025, "to": 2026, "count": count, "words": 9,
                                         "run": "r"}], "last_verified_at": "2026-10-01"}}


class LexiconValidationSecondRound(unittest.TestCase):
    """Second round, after the after-run still showed survivors in validate_lexicon, _load and entry_status."""

    def problems(self, entries, **top):
        doc = {"schema_version": 2, "kind": "voznativa.slang_lexicon", "entries": entries,
               "defaults": {"register": {"min": "very_casual", "max": "casual"}}, **top}
        return " | ".join(temporal.validate_lexicon(doc))

    def test_header_and_required_fields(self):
        for version in (1, 3):
            self.assertIn("schema_version must be 2", self.problems([], schema_version=version))
        for kind in ("voznativa.other", "zzz"):
            self.assertIn("kind must be", self.problems([], kind=kind))
        self.assertEqual(self.problems([]), "")
        no_term = _entry()
        no_term.pop("term")
        self.assertIn("x: missing term", self.problems([no_term]))
        self.assertNotIn("missing meanings", self.problems([_entry(meanings=[])]))   # an empty list is present
        self.assertIn("register min/max", self.problems([_entry(register={"min": "nope", "max": "casual"})]))

    def test_evidence_needs_a_positive_count_and_reasons(self):
        self.assertEqual(self.problems([dict(_entry(evidence={"level": "E2"}), **_att(1))]), "")
        self.assertIn("needs at least one attestation", self.problems([dict(_entry(evidence={"level": "E2"}),
                                                                             **_att(0))]))
        no_count = dict(_entry(evidence={"level": "E2"}), **_att(1))
        no_count["period"]["attestations"][0].pop("count")
        self.assertIn("needs at least one attestation", self.problems([no_count]))
        self.assertEqual(self.problems([dict(_entry(evidence={"level": "E3"}, generation={"allowed": True}),
                                             **_att(4))]), "")
        self.assertIn("context detection needs", self.problems([_entry(ambiguity={
            "ambiguous": True, "other_senses": ["y"], "detection": "context"})]))
        self.assertEqual(self.problems([_entry(ambiguity={"ambiguous": True, "other_senses": ["y"],
                                                          "detection": "form"})]), "")

    def test_load_errors_and_kept_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "lexicon.yml"
            bad.write_text(yaml.safe_dump({"schema_version": 1, "kind": "voznativa.slang_lexicon", "entries": []}),
                           encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"invalid slang lexicon .*schema_version must be 2"):
                temporal.load_lexicon(bad)
        temporal._load.cache_clear()
        lex = temporal.load_lexicon()
        for key in ("kind", "defaults", "version", "status", "locale"):
            self.assertIn(key, lex)

    def test_entry_status_edges(self):
        epoch = temporal.parse_epoch("current", TODAY)
        base = temporal._merge({"register": {"min": "very_casual", "max": "neutral"}, "generation": {}},
                               dict(_entry(evidence={"level": "E3"}, generation={"allowed": True}),
                                    **_att(5)))
        self.assertEqual(temporal.entry_status(base, epoch, "social", "casual", TODAY)["reasons"], [])
        self.assertEqual(temporal.entry_status(base, epoch, "social", "professional-natural", TODAY)["reasons"], [])
        self.assertTrue(temporal.entry_status(base, epoch, "social", "academic", TODAY)["reasons"])
        dated = dict(base, deprecation={"status": "dated", "reason": "r"})
        self.assertIn("deprecation status dated", temporal.entry_status(dated, epoch, "social", None, TODAY)["reasons"])


if __name__ == "__main__":
    unittest.main()
