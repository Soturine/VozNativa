"""v0.6.0 `voznativa corpus` commands: each answers from the registry and the
data policy, refuses with exit 77 when the policy or the personal-data guard
says no, treats an unknown source as a usage error (64), never writes the
registry, and keeps an unreadable input file a usage error (not 77)."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.cli import EXIT_NOPERM, EXIT_USAGE, main  # noqa: E402
from voznativa.corpus.registry import REGISTRY_DIR  # noqa: E402


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


def registry_bytes():
    return {p.name: p.read_bytes() for p in REGISTRY_DIR.glob("*.yml")}


class CorpusCommands(unittest.TestCase):
    def setUp(self):
        self.before = registry_bytes()

    def tearDown(self):
        self.assertEqual(registry_bytes(), self.before, "a corpus command changed the registry")

    def test_list_info_permissions_report_validate(self):
        code, out, _ = run("corpus", "list", "--status", "EVALUATION_INTEGRATED")
        self.assertEqual(code, 0)
        self.assertIn("ud-portuguese-bosque", {r["id"] for r in json.loads(out)["sources"]})
        code, out, _ = run("corpus", "info", "b2w-reviews01")
        self.assertEqual(json.loads(out)["license"]["code"], "CC-BY-NC-SA-4.0")
        code, out, _ = run("corpus", "permissions", "b2w-reviews01")
        decisions = json.loads(out)["decisions"]
        self.assertEqual(decisions["EXPORT_SAMPLES"]["state"], "DENIED")
        self.assertEqual(decisions["EXPORT_STATISTICS"]["state"], "ALLOWED")
        code, out, _ = run("corpus", "permissions", "b2w-reviews01", "--purpose", "commercial")
        self.assertEqual(json.loads(out)["decisions"]["PROCESS_LOCAL"]["state"], "DENIED")
        code, out, _ = run("corpus", "report")
        self.assertIn("machado-de-assis-corpus", json.loads(out)["evidence"])
        self.assertEqual(run("corpus", "validate")[0], 0)

    def test_validate_reports_each_bad_file_with_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.yml").write_text("schema_version: 1\nid: y\nstatus: SOURCE_VERIFIED\n", encoding="utf-8")
            code, out, _ = run("corpus", "validate", "--directory", tmp)
        self.assertEqual(code, 1)
        self.assertIn("x.yml", json.loads(out)["problems"])

    def test_refusals_and_usage_errors(self):
        code, _, err = run("corpus", "info", "nope")
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("unknown corpus source", err)
        code, _, err = run("corpus", "sample", "obras")            # CATALOGUED: no verified access
        self.assertEqual(code, EXIT_NOPERM)
        self.assertIn("PROCESS_LOCAL", err)
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("VOZNATIVA_CORPUS_CACHE")
            os.environ["VOZNATIVA_CORPUS_CACHE"] = tmp
            try:
                code, _, err = run("corpus", "sample", "b2w-reviews01")   # personal data, no flag
                self.assertEqual(code, EXIT_NOPERM)
                self.assertIn("--allow-personal-data", err)
                code, _, err = run("corpus", "sample", "ud-portuguese-bosque")   # no local copy
                self.assertEqual(code, EXIT_USAGE)
                self.assertIn("no local copy", err)
            finally:
                if old is None:
                    os.environ.pop("VOZNATIVA_CORPUS_CACHE", None)
                else:
                    os.environ["VOZNATIVA_CORPUS_CACHE"] = old

    def test_an_unreadable_input_is_still_a_usage_error(self):
        code, _, _ = run("patterns", str(ROOT / "does-not-exist.txt"))
        self.assertEqual(code, EXIT_USAGE)


class RunFilesKeepEvidence(unittest.TestCase):
    """CP10 regression: `corpus_verify --only` overwrote the full CP2 run of the same day."""

    def test_a_run_over_other_sources_never_replaces_an_existing_file(self):
        from voznativa.corpus.runs import RUNS, run_file
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / RUNS).mkdir(parents=True)
            full = root / RUNS / "verify-2026-11-05.json"
            self.assertEqual(run_file(root, "verify", "2026-11-05", {"a", "b"}), full)   # nothing there yet
            full.write_text(json.dumps({"results": [{"id": "a"}, {"id": "b"}]}), encoding="utf-8")
            partial = run_file(root, "verify", "2026-11-05", {"c"})
            self.assertNotEqual(partial, full)
            self.assertEqual(partial.name, "verify-2026-11-05-c.json")
            self.assertEqual(run_file(root, "verify", "2026-11-05", {"b", "a"}), full)   # same scope refreshes
            for shape in ({"sources": {"a": {}}}, {"reports": [{"source": "a"}]}):
                full.write_text(json.dumps(shape), encoding="utf-8")
                self.assertEqual(run_file(root, "verify", "2026-11-05", {"a"}), full)
            full.write_text("not json", encoding="utf-8")                      # unreadable: never overwritten
            self.assertNotEqual(run_file(root, "verify", "2026-11-05", {"a"}), full)


if __name__ == "__main__":
    unittest.main()
