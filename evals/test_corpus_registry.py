"""v0.6.0 Corpus Registry: statuses are proven claims, invalid files never
load partially, overlapping sources are not independent, and a new corpus is
added with a YAML file alone. No network: host checks run before any I/O."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.corpus import registry  # noqa: E402
from voznativa.corpus.connectors import AccessError, allowed_hosts, fetch, host_allowed, page_identifies  # noqa: E402

BASE = {"schema_version": 1, "kind": "voznativa.corpus_source", "id": "toy-corpus", "name": "Toy Corpus",
        "maintainer": "test", "urls": {"official": "https://example.org/toy", "official_kind": "project_site"},
        "identity_terms": ["Toy Corpus"], "modality": "written", "genres": ["teste"], "regions": ["BR"],
        "period": {"from": 2020, "to": 2021}, "license": {"code": "CC-BY-4.0", "per_document": False,
                                                          "evidence": "test"},
        "access": {"type": "open_download", "note": ""}, "relations": [], "status": "CATALOGUED",
        "evidence_role": "test", "notes": []}
VERIFIED = {"source": {"date": "2026-11-05", "url": "https://example.org/toy", "method": "GET", "result": "verified"}}


def write(tmp: Path, *entries):
    for e in entries:
        (tmp / f"{e['id']}.yml").write_text(yaml.safe_dump(e, allow_unicode=True), encoding="utf-8")
    registry._load.cache_clear()
    return tmp


class ShippedRegistry(unittest.TestCase):
    def test_loads_and_every_status_is_backed_by_evidence(self):
        entries = registry.load_registry()
        self.assertGreaterEqual(len(entries), 25)
        for e in entries:
            self.assertEqual(registry.validate_source(e), [], e["id"])

    def test_citation_only_sources_never_claim_verification(self):
        for e in registry.load_registry():
            if e["urls"]["official_kind"] in {"citation", "containing_corpus"}:
                self.assertEqual(e["status"], "CATALOGUED", e["id"])

    def test_coraa_and_the_projects_it_contains_are_one_dependency_group(self):
        groups = registry.independent_groups()
        coraa = next(g for g in groups if "coraa-asr" in g)
        self.assertTrue({"sp2010", "alip", "c-oral-brasil-i", "nurc-recife"} <= coraa)
        folha = next(g for g in groups if "cetenfolha" in g)
        self.assertTrue({"mac-morpho", "ud-portuguese-bosque", "chave"} <= folha)


class StatusEvidence(unittest.TestCase):
    def check(self, **over):
        entry = copy.deepcopy(BASE)
        entry.update(over)
        return registry.validate_source(entry, frozenset({"local-files"}), root=ROOT)

    def test_catalogued_needs_no_verification(self):
        self.assertEqual(self.check(), [])

    def test_each_rung_needs_its_evidence(self):
        self.assertTrue(any("verification.source" in p for p in self.check(status="SOURCE_VERIFIED")))
        self.assertEqual(self.check(status="SOURCE_VERIFIED", verification=VERIFIED), [])
        self.assertTrue(any("verification.access" in p for p in self.check(status="ACCESS_VERIFIED",
                                                                            verification=VERIFIED)))
        access = dict(VERIFIED, access={"date": "2026-11-05", "method": "read", "result": "data_read"})
        self.assertTrue(any("connector.id" in p for p in self.check(status="CONNECTOR_READY", verification=access)))
        self.assertTrue(any("not registered" in p for p in self.check(status="CONNECTOR_READY", verification=access,
                                                                       connector={"id": "nope"})))
        self.assertTrue(any("verification.connector" in p for p in self.check(
            status="CONNECTOR_READY", verification=access, connector={"id": "local-files"})))
        ready = dict(status="LOCALLY_VALIDATED", verification=access, connector={"id": "local-files"},
                     processing_runs=["evals/corpus/runs/does-not-exist.json"])
        self.assertTrue(any("not found" in p for p in self.check(**ready)))

    def test_evidence_files_are_checked_in_the_checkout_but_not_required_in_a_wheel(self):
        access = dict(VERIFIED, access={"date": "2026-11-05", "method": "read", "result": "data_read"},
                      connector={"date": "2026-11-05", "records_read": 3, "result": "read"})
        entry = dict(copy.deepcopy(BASE), status="EVALUATION_INTEGRATED", verification=access,
                     connector={"id": "local-files"}, processing_runs=["evals/corpus/runs/gone.json"],
                     evaluations=["evals/corpus/runs/gone-too.json"])
        in_checkout = registry.validate_source(entry, frozenset({"local-files"}), root=ROOT)
        self.assertEqual(sum("not found" in p for p in in_checkout), 2)
        with tempfile.TemporaryDirectory() as installed:            # site-packages: no evals/ or scripts/
            self.assertEqual(registry.validate_source(entry, frozenset({"local-files"}), root=Path(installed)), [])
        self.assertTrue(any("needs evaluations" in p for p in registry.validate_source(
            dict(entry, evaluations=[]), frozenset({"local-files"}), root=ROOT)))   # the claim still needs a list

    def test_citation_cannot_be_source_verified(self):
        urls = {"official": "https://doi.org/x", "official_kind": "citation"}
        self.assertTrue(any("not a citation" in p for p in self.check(status="SOURCE_VERIFIED", urls=urls,
                                                                       verification=VERIFIED)))

    def test_restriction_states_need_a_reason(self):
        self.assertTrue(any("status_reason" in p for p in self.check(status="RESTRICTED")))
        self.assertEqual(self.check(status="RESTRICTED", status_reason="ELRA licence"), [])


class Loading(unittest.TestCase):
    def tearDown(self):
        registry._load.cache_clear()

    def test_one_invalid_file_refuses_the_whole_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = dict(copy.deepcopy(BASE), id="bad-corpus", status="ACCESS_VERIFIED")
            write(Path(tmp), BASE, bad)
            with self.assertRaisesRegex(ValueError, "bad-corpus.yml"):
                registry.load_registry(Path(tmp))

    def test_relation_to_an_unregistered_source_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp), dict(copy.deepcopy(BASE), relations=[{"type": "contains", "target": "ghost"}]))
            with self.assertRaisesRegex(ValueError, "ghost"):
                registry.load_registry(Path(tmp))

    def test_file_name_must_match_the_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "other.yml").write_text(yaml.safe_dump(BASE), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "file name"):
                registry.load_registry(Path(tmp))

    def test_a_new_corpus_is_added_with_a_yaml_file_alone(self):
        # Extension contract: no code change, the registry and its summary see it.
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp), BASE, dict(copy.deepcopy(BASE), id="toy-two", status="SOURCE_VERIFIED",
                                        verification=VERIFIED))
            summary = registry.summary(registry.load_registry(Path(tmp)))
            self.assertEqual(summary["sources"], 2)
            self.assertEqual(summary["at_least"]["SOURCE_VERIFIED"], 1)


class HostBoundary(unittest.TestCase):
    def test_hosts_come_from_the_entry_and_www_is_equivalent(self):
        hosts = allowed_hosts(BASE)
        self.assertEqual(hosts, {"example.org"})
        self.assertTrue(host_allowed("www.example.org", hosts))
        self.assertFalse(host_allowed("example.org.evil.com", hosts))
        self.assertFalse(host_allowed("evil.com", hosts))
        self.assertTrue(host_allowed("us.aws.cdn.hf.co", {"*.hf.co"}))
        self.assertFalse(host_allowed("hf.co.evil.com", {"*.hf.co"}))

    def test_fetch_refuses_another_host_and_other_schemes_before_any_io(self):
        for url in ("https://evil.com/x", "file:///etc/passwd", "ftp://example.org/x"):
            with self.assertRaises(AccessError) as caught:
                fetch(url, {"example.org"})
            self.assertEqual(caught.exception.kind, "host_not_allowed", url)

    def test_identity_terms_are_accent_and_case_insensitive(self):
        self.assertEqual(page_identifies("<h1>Atlas LINGUISTICO do Brasil</h1>", ["Atlas Linguístico", "Outro"]),
                         ["Atlas Linguístico"])


if __name__ == "__main__":
    unittest.main()
