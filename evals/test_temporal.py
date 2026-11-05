"""v0.6.0 Temporal Slang Intelligence: the lexicon validates, forms are
detected without their other senses, epochs parse strictly, and slang is
never added without evidence for the requested time and context."""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import temporal  # noqa: E402

TODAY = date(2026, 11, 5)


def context(slang=0.0, epoch=None, genre="social", register="casual"):
    return {"genre": {"value": genre}, "register": {"value": register},
            "targets": {"slang_strength": slang, "epoch": epoch}}


def att(source, start, end, count, run="evals/x.json"):
    return {"source": source, "from": start, "to": end, "count": count, "words": 1000, "run": run}


def write_lexicon(directory: Path, entries: list[dict], attestations: dict | None = None) -> Path:
    path = directory / "lexicon.yml"
    path.write_text(yaml.safe_dump({"schema_version": 2, "kind": "voznativa.slang_lexicon",
                                    "defaults": {"register": {"min": "very_casual", "max": "casual"},
                                                 "generation": {"allowed": False, "forbidden_contexts": ["technical"]}},
                                    "entries": entries}, allow_unicode=True), encoding="utf-8")
    if attestations is not None:
        (directory / temporal.ATTESTATIONS).write_text(yaml.safe_dump({"entries": attestations}), encoding="utf-8")
    return path


def entry(eid="show", **extra):
    return {"id": eid, "term": "show de bola", "forms": ["show de bola"], "type": "slang",
            "meanings": ["ótimo"], "ambiguity": {"ambiguous": False}, **extra}


class Lexicon(unittest.TestCase):
    def test_shipped_lexicon_is_valid_and_measured(self):
        lex = temporal.load_lexicon()
        self.assertEqual(lex["schema_version"], 2)
        self.assertGreaterEqual(len(lex["entries"]), 25)
        for e in lex["entries"]:
            self.assertTrue(e["period"]["attestations"], e["id"])      # every entry was measured
            self.assertFalse(e["generation"]["allowed"], e["id"])       # nothing may be generated today
            for a in e["period"]["attestations"]:
                self.assertTrue((ROOT / a["run"]).is_file(), a["run"])
        self.assertEqual({e["id"] for e in lex["entries"] if e["evidence"]["level"] == "E2"},
                         {"show-de-bola", "top", "de-boa", "kkk"})

    def test_validation_rejects_unsupported_claims(self):
        problems = temporal.validate_lexicon({"schema_version": 2, "kind": "voznativa.slang_lexicon", "entries": [
            entry("a", evidence={"level": "E2"}),                                       # E2 with no attestation
            entry("b", ambiguity={"ambiguous": True}),                                  # no other senses
            entry("c", ambiguity={"ambiguous": True, "other_senses": ["x"], "detection": "context"}),  # no detect
            entry("d", generation={"allowed": True}),                                   # generation at E0
            entry("e", deprecation={"status": "dated"}),                                # no reason
            entry("f", detect="(unclosed"),
            entry("f")]})
        text = " | ".join(problems)
        for needle in ("a: evidence E2 needs", "b: an ambiguous entry must list", "c: context detection needs",
                       "d: generation needs evidence", "e: a non-active entry needs", "f: invalid detect",
                       "duplicate id f"):
            self.assertIn(needle, text)

    def test_attestations_for_unknown_ids_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_lexicon(Path(tmp), [entry()], {"ghost": {"evidence": {"level": "E0"}}})
            with self.assertRaisesRegex(ValueError, "unknown lexicon ids"):
                temporal.load_lexicon(path)


class Detection(unittest.TestCase):
    def test_other_senses_are_not_slang(self):
        ids = lambda t: [f["id"] for f in temporal.observe(t)]  # noqa: E731
        self.assertEqual(ids("O produto é de boa qualidade e chegou no prazo."), [])
        self.assertEqual(ids("Celular top de linha, top 10 do ano."), [])
        self.assertEqual(ids("O sabor é suave e a massa de pizza ficou boa."), [])
        self.assertEqual(ids("Foi um mano-a-mano até o fim."), [])
        self.assertEqual(ids("Tinha pó no móvel."), [])                  # pó is not pô
        self.assertEqual(ids("A embalagem veio lacrada."), [])
        self.assertEqual(ids("Roda tudo de boa. O celular é muito top, show de bola kkkk"),
                         ["de-boa", "top", "show-de-bola", "kkk"])
        self.assertEqual(ids("Pô, que calor"), ["po"])

    def test_offsets_point_at_the_original_text(self):
        text = "Ficou SHOW DE BOLA, sério."
        (hit,) = temporal.observe(text)
        self.assertEqual(text[hit["start"]:hit["end"]], "SHOW DE BOLA")


class Epochs(unittest.TestCase):
    def test_parse(self):
        self.assertIsNone(temporal.parse_epoch(None))
        self.assertEqual(temporal.parse_epoch("current", TODAY), {"spec": "current", "from": 2024, "to": 2026})
        self.assertEqual(temporal.parse_epoch("1994-1996", TODAY)["to"], 1996)
        for bad in ("anos 90", "1999-1990", "2030", "19945"):
            with self.assertRaises(ValueError):
                temporal.parse_epoch(bad, TODAY)

    def test_epoch_notes_flag_forms_outside_their_attestations(self):
        found = temporal.observe("O jogo é show de bola.")
        notes = temporal.epoch_notes(found, temporal.parse_epoch("1994-1995", TODAY))
        self.assertEqual([(n["id"], n["attested"]) for n in notes], [("show-de-bola", ["2018-2018"])])
        self.assertEqual(temporal.epoch_notes(found, temporal.parse_epoch("2018", TODAY)), [])


class Activation(unittest.TestCase):
    def test_abstains_by_default_and_keeps_the_authors_forms(self):
        out = temporal.activate(context(), "O jogo é show de bola.", today=TODAY)
        self.assertEqual((out["status"], out["effective_strength"]), ("abstain", 0.0))
        self.assertEqual(out["keep"], ["show de bola"])
        self.assertIn("never adds slang on its own", " ".join(out["reasons"]))

    def test_requested_slang_still_abstains_without_evidence_for_the_epoch(self):
        out = temporal.activate(context(0.8, temporal.parse_epoch("current", TODAY)), "Texto neutro.", today=TODAY)
        self.assertEqual(out["status"], "abstain")
        self.assertEqual(out["allowed"], [])
        self.assertIn("generation not allowed", out["reasons"][-1])
        self.assertIn("no attestation in", out["reasons"][-1])

    def test_an_entry_with_evidence_for_the_request_can_be_offered(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = entry("show", generation={"allowed": True})
            path = write_lexicon(Path(tmp), [good, entry("old", term="supimpa", forms=["supimpa"])], {
                "show": {"period": {"attestations": [att("b2w", 2025, 2026, 12)], "last_verified_at": "2026-10-01"},
                         "evidence": {"level": "E2"}},
                "old": {"period": {"attestations": [att("b2w", 1990, 1991, 9)], "last_verified_at": "2026-10-01"},
                        "evidence": {"level": "E2"}}})
            epoch = temporal.parse_epoch("current", TODAY)
            out = temporal.activate(context(0.8, epoch), "Texto neutro.", today=TODAY, path=path)
            self.assertEqual((out["status"], out["allowed"]), ("active", ["show"]))
            self.assertLessEqual(out["effective_strength"], 0.3)
            # forbidden genre, a register above the entry, a stale verification: each blocks
            self.assertEqual(temporal.activate(context(0.8, epoch, genre="technical"), "x", today=TODAY,
                                               path=path)["allowed"], [])
            self.assertEqual(temporal.activate(context(0.8, epoch, register="professional-formal"), "x", today=TODAY,
                                               path=path)["allowed"], [])
            later = date(2028, 6, 1)
            self.assertEqual(temporal.activate(context(0.8, temporal.parse_epoch("2025-2026", later)), "x",
                                               today=later, path=path)["allowed"], [])
            # the guard accepts what the activation licensed and flags the rest
            self.assertEqual(temporal.introduced_terms("Ok.", "Ok, show de bola.", out, path=path), [])
            self.assertEqual([f["id"] for f in temporal.introduced_terms("Ok.", "Ok, show de bola.", None,
                                                                        path=path)], ["show"])


class Guard(unittest.TestCase):
    def test_introduced_slang_is_flagged_and_the_authors_is_not(self):
        self.assertEqual([f["id"] for f in temporal.introduced_terms("O produto é bom.",
                                                                    "O produto é top demais, mano.")],
                         ["top", "mano"])
        self.assertEqual(temporal.introduced_terms("Mano, o produto é top demais.",
                                                   "Mano, o produto é muito top."), [])


if __name__ == "__main__":
    unittest.main()
