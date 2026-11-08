"""v0.8 (V08-GAP-11 and the CP12 docs move): what counts as post-CI evidence.

The v0.8 state and qualification records are evidence; the moved v0.7 records
keep being evidence at their new paths; code, guides and other docs are not."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("ci_evidence_v08", ROOT / "scripts" / "ci_evidence.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ci_evidence_v08"] = module
    spec.loader.exec_module(module)
    return module


ci = _load()


class EvidencePaths(unittest.TestCase):

    def test_round_records_are_evidence(self):
        for path in ("docs/releases/v0.8/EXECUTION_STATE.md", "docs/releases/v0.8/RELEASE_QUALIFICATION.md",
                     "docs/releases/v0.7/V07_EXECUTION_STATE.md", "docs/releases/v0.7/V07_RELEASE_QUALIFICATION.md"):
            self.assertTrue(ci.is_evidence_path(path), path)

    def test_everything_else_is_not(self):
        for path in ("docs/releases/v0.8/PLAN.md", "docs/guide/QUICKSTART.md", "README.md", "voznativa/compare.py",
                     "docs/V07_EXECUTION_STATE.md", "docs/v08/EXECUTION_STATE.md",
                     "evals/assurance/runs/x/harness.py"):
            self.assertFalse(ci.is_evidence_path(path), path)

    def test_listed_files_exist_or_are_the_pending_qualification_record(self):
        for path in ci.EVIDENCE_PATHS:
            if path.endswith("/") or path.endswith("external.json"):
                continue
            if path == "docs/releases/v0.8/RELEASE_QUALIFICATION.md":
                continue        # written in CP16, before the final CI
            self.assertTrue((ROOT / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
