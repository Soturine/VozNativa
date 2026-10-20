"""Eval suites must state who wrote them and must not be read as independent validation."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.evals import provenance, run, sha256_lf

SEMANTIC = ROOT / "evals" / "semantic"
MANIFEST = json.loads((SEMANTIC / "MANIFEST.json").read_text(encoding="utf-8"))
INDEPENDENT_FIELDS = ("author", "sha256", "written_without_reading_engine", "first_run")


class Provenance(unittest.TestCase):
    def test_every_suite_is_listed(self):
        listed = set(MANIFEST["suites"])
        present = {p.name for p in SEMANTIC.glob("*.jsonl")}
        self.assertEqual(present - listed, set())
        self.assertEqual(listed - present, set())

    def test_frozen_suites_were_not_edited(self):
        for name, entry in MANIFEST["suites"].items():
            if entry.get("frozen"):
                self.assertEqual(sha256_lf(SEMANTIC / name), entry["sha256"], f"{name} changed after freezing")

    def test_independent_claims_need_the_protocol_fields(self):
        for name, entry in MANIFEST["suites"].items():
            if entry.get("independent"):
                missing = [f for f in INDEPENDENT_FIELDS if not entry.get(f)]
                self.assertEqual(missing, [], f"{name} claims independence without {missing}")
                self.assertTrue(entry.get("frozen"), name)

    def test_current_suites_are_not_reported_as_independent(self):
        for name in MANIFEST["suites"]:
            self.assertFalse(run(SEMANTIC / name)["independent_validation"], name)

    def test_unlisted_suite_is_unknown_not_independent(self):
        origin = provenance(ROOT / "benchmarks" / "cases" / "smoke.jsonl")
        self.assertEqual(origin["role"], "unknown")
        self.assertFalse(origin["independent"])

    def test_require_frozen_refuses_dev_suites(self):
        with self.assertRaises(ValueError):
            run(SEMANTIC / "cases.jsonl", require_frozen=True)
        self.assertTrue(run(SEMANTIC / "holdout2.jsonl", require_frozen=True)["provenance"]["sha256_matches"])

    def test_non_semantic_file_is_refused_with_a_clear_error(self):
        with self.assertRaisesRegex(ValueError, "not a semantic eval suite"):
            run(ROOT / "evals" / "router" / "cases.jsonl")


if __name__ == "__main__":
    unittest.main()
