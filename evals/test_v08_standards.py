"""v0.8 CP10 (ST-01..ST-04): Standards Registry, Applicability Resolver, document_profile.

The historical replay uses SYNTHETIC registry entries (an invented
"universidade-exemplo" manual in three editions and an invented event
edital), written to temporary directories: no institutional manual was
verified in this round. The real registry entries (Inep's Enem essay guides)
are checked separately, with the verification each one actually has."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import standards  # noqa: E402
from voznativa.router import route  # noqa: E402

SHA = "a" * 64


def entry(id_, edition, start, until, status="VERIFIED", series="manual-tcc", event_year=None,
          document_types=("tcc",), criteria=()):
    return {"schema_version": 1, "kind": standards.KIND, "id": id_, "authority": "universidade-exemplo",
            "series": series, "category": "manual", "title": f"Manual (SYNTHETIC) {edition}",
            "urls": {"official": "https://example.invalid/manual"}, "edition": edition, "published": start,
            "validity": {"from": start, "until": until},
            "applies_to": {"document_types": list(document_types), "event_year": event_year},
            "rights": {"text": "metadata_only"},
            "verification": {"status": status, "checked_at": "2026-11-07" if status != "CATALOGUED" else None,
                             "evidence": "SYNTHETIC test fixture" if status != "CATALOGUED" else None,
                             "sha256": SHA if status == "VERIFIED" else None},
            "criteria": list(criteria)}


MANUALS = (entry("manual-2019", "2019", "2019-02-01", "2023-01-31"),
           entry("manual-2023", "2023", "2023-02-01", "2025-01-31"),
           entry("manual-2025", "2025", "2025-02-01", None))


def profile(day, **extra):
    return {"document_type": "tcc", "authority": "universidade-exemplo", "submission_date": day, **extra}


class HistoricalReplay(unittest.TestCase):
    """The edition is chosen by the document's date, never by recency."""

    def test_each_date_gets_its_own_edition(self):
        for day, expected in (("2022-06-30", "manual-2019"), ("2023-11-20", "manual-2023"),
                              ("2025-03-01", "manual-2025"), ("2026-11-07", "manual-2025")):
            with self.subTest(day=day):
                result = standards.resolve(profile(day), MANUALS)
                self.assertEqual((result["decision"], result["selected"]), ("APPLICABLE", [expected]))

    def test_a_2023_submission_ignores_the_2025_manual(self):
        result = standards.resolve(profile("2023-11-20"), MANUALS)
        self.assertNotIn("manual-2025", result["selected"])

    def test_before_any_edition_is_unknown_not_the_latest(self):
        result = standards.resolve(profile("2018-05-01"), MANUALS)
        self.assertEqual((result["decision"], result["selected"]), ("UNKNOWN", []))
        self.assertIn("not assumed", result["reason"])

    def test_two_valid_editions_are_a_conflict_for_a_person(self):
        overlap = MANUALS + (entry("manual-2025b", "2025b", "2025-06-01", None),)
        result = standards.resolve(profile("2025-08-01"), overlap)
        self.assertEqual((result["decision"], result["selected"]), ("CONFLICTED", []))

    def test_an_event_edital_is_not_used_for_another_year(self):
        editais = (entry("edital-inic-2026", "2026", "2026-03-01", None, series="edital-inic", event_year=2026,
                         document_types=("artigo-inic",)),)
        ok = standards.resolve({"document_type": "artigo-inic", "submission_date": "2026-08-01", "event_year": 2026},
                               editais)
        self.assertEqual(ok["selected"], ["edital-inic-2026"])
        other_year = standards.resolve({"document_type": "artigo-inic", "submission_date": "2026-08-01",
                                        "event_year": 2024}, editais)
        self.assertEqual(other_year["decision"], "NOT_APPLICABLE")

    def test_evidence_level_limits_the_decision(self):
        for status, decision in (("SOURCE_CITED", "APPLICABLE_UNVERIFIED"), ("CATALOGUED", "UNKNOWN"),
                                 ("STALE", "STALE"), ("BLOCKED", "BLOCKED"), ("CONFLICTED", "CONFLICTED")):
            with self.subTest(status=status):
                result = standards.resolve(profile("2026-01-01"), (entry("m", "x", "2025-02-01", None, status),))
                self.assertEqual(result["decision"], decision)
                if decision not in ("APPLICABLE", "APPLICABLE_UNVERIFIED"):
                    self.assertEqual(result["selected"], [])

    def test_a_date_is_required(self):
        self.assertEqual(standards.resolve({"document_type": "tcc"}, MANUALS)["decision"], "UNKNOWN")


class Validation(unittest.TestCase):

    def problems(self, mutate):
        e = copy.deepcopy(MANUALS[1])
        mutate(e)
        return " | ".join(standards.validate_entry(e))

    def test_valid_entry(self):
        self.assertEqual(standards.validate_entry(MANUALS[1]), [])

    def test_refusals(self):
        cases = {
            "sha256": lambda e: e["verification"].update(sha256=None),
            "checked_at": lambda e: e["verification"].update(checked_at=None),
            "https": lambda e: e["urls"].update(official="http://example.invalid"),
            "before validity.from": lambda e: e["validity"].update(until="2020-01-01"),
            "not redistributable": lambda e: e.update(text="o texto integral do manual"),
            "weight": lambda e: e.update(criteria=[{"id": "c1", "kind": "objective", "verification": "VERIFIED",
                                                    "weight": 2}]),
            "category": lambda e: e.update(category="blog"),
            "duplicate id": lambda e: e.update(criteria=[{"id": "c", "kind": "objective", "verification": "VERIFIED"},
                                                         {"id": "c", "kind": "objective", "verification": "VERIFIED"}]),
        }
        for fragment, mutate in cases.items():
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.problems(mutate))

    def test_registry_refuses_an_invalid_file_and_a_misnamed_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = dict(MANUALS[0], id="outro-nome")
            Path(tmp, "manual-2019.yml").write_text(yaml.safe_dump(bad), encoding="utf-8")
            with self.assertRaises(ValueError):
                standards.load(Path(tmp))


class RealRegistry(unittest.TestCase):

    def test_enem_entries_carry_their_real_evidence(self):
        by_id = {e["id"]: e for e in standards.load()}
        e2026 = by_id["inep-enem-redacao-cartilha-2026"]
        self.assertEqual(e2026["verification"]["status"], "SOURCE_CITED")
        self.assertIsNone(e2026["verification"]["sha256"], "the file was not downloaded: no hash may be claimed")
        self.assertEqual(by_id["inep-enem-redacao-cartilha-2025"]["verification"]["status"], "CATALOGUED")
        unverified = [c["id"] for c in e2026["criteria"] if c["verification"] == "CATALOGUED"]
        self.assertIn("limite-de-linhas", unverified)

    def test_enem_resolution(self):
        enem = {"document_type": "redacao-enem", "series": "enem-redacao-cartilha"}
        r2026 = standards.resolve(dict(enem, event_year=2026, submission_date="2026-11-08"))
        self.assertEqual((r2026["decision"], r2026["selected"]), ("APPLICABLE_UNVERIFIED",
                                                                   ["inep-enem-redacao-cartilha-2026"]))
        r2025 = standards.resolve(dict(enem, event_year=2025, submission_date="2025-11-09"))
        self.assertEqual((r2025["decision"], r2025["selected"]), ("UNKNOWN", []))


class DocumentProfileInTheContract(unittest.TestCase):

    def test_absent_profile_changes_nothing(self):
        text = (ROOT / "examples" / "quickstart" / "original.txt").read_text(encoding="utf-8")
        self.assertEqual(route(text), route(text, document_profile=None))
        self.assertNotIn("document_profile", route(text))

    def test_profile_is_validated_and_resolved(self):
        contract = route("Texto.", document_profile={"document_type": "redacao-enem", "series": "enem-redacao-cartilha",
                                                     "event_year": 2026, "submission_date": "2026-11-08"})
        self.assertEqual(contract["document_profile"]["standards"]["decision"], "APPLICABLE_UNVERIFIED")
        with self.assertRaises(ValueError):
            route("Texto.", document_profile={"document_type": "tcc", "nota": 1000})
        with self.assertRaises(ValueError):
            route("Texto.", document_profile={"series": "x"})


if __name__ == "__main__":
    unittest.main()
