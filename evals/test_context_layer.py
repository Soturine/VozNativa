"""Context Router, Reference Selector and Project Context behavior."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.project import ground, scan
from voznativa.references import select
from voznativa.router import infer_genre, route

ROUTER_CASES = [json.loads(line) for line in
                (ROOT / "evals" / "router" / "cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


class Router(unittest.TestCase):
    def test_router_never_picks_a_wrong_specific_genre(self):
        # "unknown" is a safe fallback (generic references only); a wrong genre
        # loads the wrong rules. Only the latter is a failure.
        for case in ROUTER_CASES:
            got = infer_genre(case["text"])["value"]
            self.assertIn(got, set(case["expect"]) | {"unknown"}, case["id"])

    def test_router_accuracy_floor(self):
        hits = sum(infer_genre(c["text"])["value"] in c["expect"] for c in ROUTER_CASES)
        self.assertGreaterEqual(hits / len(ROUTER_CASES), 0.85)

    def test_explicit_hints_win(self):
        contract = route("vc viu?? kkk", genre="academic", register="academic")
        self.assertEqual(contract["genre"]["source"], "explicit")
        self.assertEqual(contract["genre"]["value"], "academic")
        self.assertFalse(contract["flags"]["register_conflict"])

    def test_register_conflict_is_flagged(self):
        contract = route("vc viu o deploy de hj?? nn subiu kkk", register="professional-formal")
        self.assertEqual(contract["genre"]["value"], "whatsapp")
        self.assertTrue(contract["flags"]["register_conflict"])

    def test_sources_are_kept_apart(self):
        with tempfile.TemporaryDirectory() as tmp:
            fact, sample = Path(tmp, "notas.txt"), Path(tmp, "amostra.txt")
            fact.write_text("O prazo é 30/09.", encoding="utf-8")
            sample.write_text("blz, mando amanhã", encoding="utf-8")
            contract = route("Texto.", fact_sources=[str(fact)], voice_samples=[str(sample)])
        self.assertEqual([s["kind"] for s in contract["sources"]["fact_sources"]], ["user_fact"])
        self.assertEqual([s["kind"] for s in contract["sources"]["voice_samples"]], ["voice_sample"])
        self.assertFalse(contract["policy"]["infer_identity"])

    def test_invalid_task_is_rejected(self):
        with self.assertRaises(ValueError):
            route("x", task="humanize-everything")


class ReferenceSelector(unittest.TestCase):
    def paths(self, contract, budget=8000):
        return [s["path"] for s in select(contract, budget_words=budget)["selected"]]

    def test_genre_specific_references(self):
        chat = self.paths(route("vc viu o deploy de hj?? nn subiu ainda kkk"))
        self.assertIn("references/genres/whatsapp.md", chat)
        self.assertNotIn("references/genres/technical.md", chat)
        self.assertNotIn("references/genres/academic.md", chat)

    def test_unknown_genre_loads_no_genre_file(self):
        selected = self.paths(route("Obrigado."))
        self.assertFalse(any(p.startswith("references/genres/") for p in selected))
        self.assertIn("references/patterns/false-positives.md", selected)

    def test_voice_and_region_references_need_their_flags(self):
        base = self.paths(route("O prazo é sexta.", genre="corporate"))
        self.assertNotIn("references/voice/idiolect.md", base)
        self.assertNotIn("references/regions/README.md", base)
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp, "a.txt")
            sample.write_text("oi", encoding="utf-8")
            voiced = self.paths(route("O prazo é sexta.", genre="corporate", voice_samples=[str(sample)]))
        self.assertIn("references/voice/idiolect.md", voiced)
        regional = self.paths(route("O prazo é sexta.", genre="corporate", region="MG", region_strength=0.2))
        self.assertIn("references/regions/README.md", regional)

    def test_budget_is_respected_and_reported(self):
        result = select(route("O prazo é sexta.", genre="corporate"), budget_words=900)
        self.assertLessEqual(result["used_words"], 900)
        self.assertTrue(any("over budget" in s["reason"] for s in result["skipped"]))


class Home(unittest.TestCase):
    def test_voznativa_home_takes_precedence(self):
        import os
        from voznativa.paths import home
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "references").mkdir()
            (Path(tmp) / "references" / "index.yml").write_text("schema_version: 1\nentries: []\n",
                                                                encoding="utf-8")
            previous = os.environ.get("VOZNATIVA_HOME")
            os.environ["VOZNATIVA_HOME"] = tmp
            try:
                self.assertEqual(home(), Path(tmp))
            finally:
                if previous is None:
                    os.environ.pop("VOZNATIVA_HOME")
                else:
                    os.environ["VOZNATIVA_HOME"] = previous


class ProjectContext(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "src").mkdir()
        (root / "pyproject.toml").write_text(
            '[project]\nname = "demo"\nversion = "1.4.0"\n[project.scripts]\ndemo = "src.cli:main"\n', encoding="utf-8")
        (root / "src" / "cli.py").write_text(
            "def main():\n    p.add_parser('sync')\n    p.add_argument('--dry-run')\n\nMAX_RETRIES = 3\n",
            encoding="utf-8")
        (root / "README.md").write_text("# Demo\n\n```bash\ndemo sync --dry-run\n```\n", encoding="utf-8")
        self.root = root
        self.project = scan(root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_indexes_files_cli_and_versions(self):
        self.assertIn("src/cli.py", self.project.files)
        self.assertIn("sync", self.project.cli_names)
        self.assertEqual(self.project.versions["demo"], "1.4.0")
        self.assertIn("demo sync --dry-run", self.project.commands)

    def test_grounding_accepts_real_and_rejects_invented_references(self):
        ok = ground("Rode `demo sync --dry-run` e veja src/cli.py; o limite é `MAX_RETRIES`.", project=self.project)
        self.assertEqual(ok["status"], "no_deterministic_issues", ok["issues"])
        bad = ground("Rode `demo deploy --force` e edite src/config.py.", project=self.project)
        self.assertEqual(bad["status"], "fail")
        self.assertEqual({i["text"] for i in bad["issues"]}, {"`demo deploy --force`", "src/config.py"})

    def test_repository_never_supports_values(self):
        # The README contains "3" (MAX_RETRIES = 3 is in code), but a number in a
        # new sentence needs an explicit source.
        report = ground("O cliente tenta 3 vezes.", project=self.project)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(ground("O cliente tenta 3 vezes.", facts=["Tentativas: 3 vezes."],
                                project=self.project)["status"], "no_deterministic_issues")

    def test_repository_doc_used_as_voice_sample_warns(self):
        contract = route("Texto.", repo=str(self.root), voice_samples=[str(self.root / "README.md")])
        self.assertTrue(contract["warnings"])


if __name__ == "__main__":
    unittest.main()
