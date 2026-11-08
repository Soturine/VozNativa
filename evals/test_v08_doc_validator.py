"""v0.8 CP12: the documentation validator detects what it claims to detect.

Each defect is planted in an isolated temporary tree and must be reported;
each control must not be. Then the real repository must be clean."""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load():
    spec = importlib.util.spec_from_file_location("validate_package_v08", ROOT / "scripts" / "validate_package.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_package_v08"] = module
    spec.loader.exec_module(module)
    return module


vp = _load()
SUBCOMMANDS = {"compare", "doctor", "demo"}


class PlantedDefects(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "guide").mkdir(parents=True)
        (self.root / "docs" / "alvo.md").write_text("# Título Alvo\n\n## Seção `Dois`\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def problems(self, body, name="docs/guide/pagina.md"):
        path = self.root / name
        path.write_text(body, encoding="utf-8")
        return vp.markdown_problems(self.root, [path], SUBCOMMANDS)

    def test_controls_are_clean(self):
        body = ("Veja [alvo](../alvo.md), [seção](../alvo.md#seção-dois), [site](https://example.invalid), "
                "rode `voznativa compare a b` e `voznativa doctor`.\n\n```bash\n[falso](nao-existe.md)\n```\n")
        self.assertEqual(self.problems(body), [])

    def test_a_personal_path_leaks_from_code_blocks_too(self):
        body = "```powershell\ncd C:\\Users\\alguem\\projeto\n```\n"
        self.assertTrue(any("personal absolute path" in p for p in self.problems(body)))

    def test_broken_link(self):
        self.assertTrue(any("broken link" in p for p in self.problems("[x](../sumiu.md)\n")))

    def test_missing_anchor(self):
        self.assertTrue(any("anchor" in p for p in self.problems("[x](../alvo.md#nao-ha)\n")))

    def test_personal_paths(self):
        for body in ("Em C:\\Users\\rafael\\docs\n", "Em /home/rafael/projeto/\n", "Em C:/Users/maria/x\n"):
            with self.subTest(body=body):
                self.assertTrue(any("personal absolute path" in p for p in self.problems(body)))
        self.assertEqual(self.problems("Use C:\\Users\\<voce>\\pasta\n"), [], "a placeholder is fine")

    def test_secrets(self):
        for token in ("sk-ant-api03-ABCDEFGHIJKLMNOP", "ghp_" + "a" * 30, "AKIA" + "B" * 16,
                      "-----BEGIN RSA PRIVATE KEY-----"):
            with self.subTest(token=token[:8]):
                self.assertTrue(any("secret" in p for p in self.problems(f"chave: {token}\n")))

    def test_unknown_subcommand_only_in_current_docs(self):
        self.assertTrue(any("not a subcommand" in p for p in self.problems("rode `voznativa inventado x`\n")))
        historical = self.problems("rode `voznativa inventado x`\n", name="docs/PLAN_v0.3.0.md")
        self.assertEqual(historical, [], "history may name commands of its own time")


class RealRepository(unittest.TestCase):

    def test_documentation_is_clean(self):
        from voznativa.cli import build_parser
        action = next(a for a in build_parser()._actions if a.__class__.__name__ == "_SubParsersAction")
        problems = vp.markdown_problems(ROOT, vp.documentation_files(ROOT), set(action.choices))
        self.assertEqual(problems, [])
        self.assertGreater(len(vp.documentation_files(ROOT)), 50)

    def test_a_renamed_document_is_caught_in_a_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            for rel in ("README.md", "docs/README.md", "docs/v08/EVAL_PROTOCOL.md"):
                (copy / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, copy / rel)
            problems = vp.markdown_problems(copy, [copy / "README.md"], None)
        self.assertTrue(any("EVAL_PROTOCOL" not in p and "broken link" in p for p in problems),
                        "README links many files absent from the copy")


if __name__ == "__main__":
    unittest.main()
