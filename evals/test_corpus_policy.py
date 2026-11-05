"""v0.6.0 Data Policy: licences are not interchangeable, unknown terms are
never presumed allowed, personal data gates samples and model calls, and a
permission covers only what it names."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.corpus.policy import OPERATIONS, PolicyDenied, decide, matrix, require  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402

ACCESS = {"source": {"date": "d", "url": "u", "method": "m", "result": "verified"},
          "access": {"date": "d", "method": "m", "result": "data_read"}}


def source(code, personal=False, status="ACCESS_VERIFIED", access="open_download", per_document=False, **extra):
    return {"id": "t", "status": status, "license": {"code": code, "per_document": per_document, "evidence": "test"},
            "access": {"type": access}, "privacy": {"personal_data": personal}, "verification": ACCESS, **extra}


def state(entry, op, **kw):
    return decide(entry, op, **kw).state


class LicenceFamilies(unittest.TestCase):
    def test_the_families_differ_where_they_should(self):
        rows = {code: {op: state(source(code), op) for op in ("PROCESS_LOCAL", "EXPORT_SAMPLES",
                                                                "PUBLISH_DERIVATIVES", "SEND_TO_EXTERNAL_MODEL",
                                                                "TRAIN_MODEL")}
                for code in ("CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "CC-BY-NC-4.0", "CC-BY-ND-4.0", "none_stated",
                             "unknown", "research_only")}
        self.assertEqual(rows["CC0-1.0"], dict.fromkeys(rows["CC0-1.0"], "ALLOWED"))
        self.assertEqual(rows["CC-BY-4.0"]["EXPORT_SAMPLES"], "ALLOWED")
        self.assertEqual(rows["CC-BY-SA-4.0"]["EXPORT_SAMPLES"], "DENIED")     # into the MIT repository
        self.assertEqual(rows["CC-BY-ND-4.0"]["PUBLISH_DERIVATIVES"], "DENIED")
        self.assertEqual(rows["CC-BY-NC-4.0"]["SEND_TO_EXTERNAL_MODEL"], "REQUIRES_PERMISSION")
        self.assertEqual(rows["CC-BY-4.0"]["TRAIN_MODEL"], "REQUIRES_PERMISSION")
        for code in ("none_stated", "unknown"):
            self.assertEqual(set(rows[code].values()), {"UNKNOWN"}, code)  # never presumed allowed
        self.assertEqual(rows["research_only"]["PROCESS_LOCAL"], "REQUIRES_PERMISSION")
        identified = [r for code, r in rows.items() if code not in {"none_stated", "unknown"}]
        self.assertEqual(len({tuple(sorted(r.items())) for r in identified}), len(identified))
        # the two undecidable codes share the state but say different things
        self.assertNotEqual(decide(source("none_stated"), "PROCESS_LOCAL").reasons,
                            decide(source("unknown"), "PROCESS_LOCAL").reasons)

    def test_non_commercial_terms_deny_a_commercial_purpose(self):
        self.assertEqual(state(source("CC-BY-NC-4.0"), "PROCESS_LOCAL", purpose="commercial"), "DENIED")
        self.assertEqual(state(source("CC-BY-NC-4.0"), "PROCESS_LOCAL"), "ALLOWED")

    def test_share_alike_can_be_published_apart_under_the_same_licence(self):
        entry = source("CC-BY-SA-4.0")
        self.assertEqual(state(entry, "EXPORT_SAMPLES", destination="CC-BY-SA-4.0"), "ALLOWED")
        self.assertEqual(state(entry, "EXPORT_SAMPLES", destination="CC-BY-4.0"), "DENIED")

    def test_query_only_sources_allow_querying_and_nothing_else(self):
        entry = source("query_only", access="open_query")
        self.assertEqual(state(entry, "QUERY"), "ALLOWED")
        self.assertEqual(state(entry, "DOWNLOAD"), "DENIED")


class DataAccessAndStatus(unittest.TestCase):
    def test_catalogue_operations_are_always_allowed(self):
        for status in ("CATALOGUED", "RESTRICTED"):
            self.assertEqual(state(source("unknown", status=status, status_reason="r"), "READ_METADATA"), "ALLOWED")

    def test_data_operations_need_verified_access(self):
        self.assertEqual(state(source("CC0-1.0", status="SOURCE_VERIFIED"), "DOWNLOAD"), "UNKNOWN")
        self.assertEqual(state(source("CC0-1.0", status="AWAITING_PERMISSION", status_reason="gated"), "DOWNLOAD"),
                         "REQUIRES_PERMISSION")
        self.assertEqual(state(source("CC0-1.0", access="registration"), "DOWNLOAD"), "REQUIRES_PERMISSION")

    def test_a_corpus_licence_never_stands_in_for_its_documents(self):
        entry = source("per_document", per_document=True)
        self.assertEqual(state(entry, "PROCESS_LOCAL"), "ALLOWED")
        self.assertEqual(state(entry, "EXPORT_SAMPLES"), "UNKNOWN")
        self.assertEqual(state(entry, "EXPORT_SAMPLES", document_license="CC-BY-4.0"), "ALLOWED")
        self.assertEqual(state(entry, "EXPORT_SAMPLES", document_license="CC-BY-NC-SA-4.0"), "DENIED")


class PersonalDataAndPermissions(unittest.TestCase):
    def test_personal_data_needs_permission_for_samples_and_model_calls(self):
        for personal in (True, "possible", "unknown"):
            entry = source("CC0-1.0", personal=personal)
            self.assertEqual(state(entry, "SEND_TO_EXTERNAL_MODEL"), "REQUIRES_PERMISSION", personal)
            self.assertEqual(state(entry, "EXPORT_SAMPLES"), "REQUIRES_PERMISSION", personal)
            self.assertEqual(state(entry, "EXPORT_STATISTICS"), "ALLOWED", personal)
        self.assertEqual(state(source("CC0-1.0", personal=False), "SEND_TO_EXTERNAL_MODEL"), "ALLOWED")

    def test_a_permission_covers_only_what_it_names(self):
        grant = {"operations": ["PROCESS_LOCAL"], "purposes": ["noncommercial_research"], "granted_by": "rights holder",
                 "date": "2026-11-05", "evidence": "e-mail archived by the maintainer"}
        entry = source("none_stated", permissions=[grant])
        self.assertEqual(state(entry, "PROCESS_LOCAL"), "ALLOWED")
        self.assertEqual(state(entry, "EXPORT_SAMPLES"), "UNKNOWN")
        self.assertEqual(state(entry, "PROCESS_LOCAL", purpose="commercial"), "UNKNOWN")
        undocumented = source("none_stated", permissions=[dict(grant, evidence="")])
        self.assertEqual(state(undocumented, "PROCESS_LOCAL"), "UNKNOWN")

    def test_require_fails_closed(self):
        with self.assertRaises(PolicyDenied):
            require(source("unknown"), "PROCESS_LOCAL")
        self.assertTrue(require(source("CC0-1.0"), "PROCESS_LOCAL").allowed)

    def test_decisions_carry_reasons_and_evidence(self):
        for op, d in matrix(source("CC-BY-SA-4.0")).items():
            self.assertTrue(d["reasons"], op)
            self.assertTrue(d["evidence"], op)

    def test_unknown_operation_or_purpose_is_refused(self):
        with self.assertRaises(ValueError):
            decide(source("CC0-1.0"), "SELL")
        with self.assertRaises(ValueError):
            decide(source("CC0-1.0"), "PROCESS_LOCAL", purpose="whatever")


class ShippedSources(unittest.TestCase):
    def test_policy_over_the_processable_sources(self):
        bosque, b2w, coraa = (get_source(s) for s in ("ud-portuguese-bosque", "b2w-reviews01", "coraa-asr"))
        self.assertEqual(state(bosque, "PROCESS_LOCAL"), "ALLOWED")
        self.assertEqual(state(bosque, "EXPORT_SAMPLES"), "DENIED")
        self.assertEqual(state(b2w, "SEND_TO_EXTERNAL_MODEL"), "REQUIRES_PERMISSION")
        self.assertEqual(state(b2w, "EXPORT_STATISTICS"), "ALLOWED")
        self.assertEqual({decide(coraa, op).state for op in OPERATIONS[2:]}, {"UNKNOWN"})


if __name__ == "__main__":
    unittest.main()
