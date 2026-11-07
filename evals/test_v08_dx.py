"""v0.8 CP3: first use without a model or key (doctor, demo, error messages)
and the suite against the installed wheel (V08-GAP-06)."""
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import onboarding  # noqa: E402

QUICKSTART = ROOT / "examples" / "quickstart"


def cli(*args, cwd=None, env=None):
    done = subprocess.run([sys.executable, "-B", "-m", "voznativa", *args], capture_output=True, cwd=cwd,
                          env=env)
    return done.returncode, done.stdout.decode("utf-8"), done.stderr.decode("utf-8")


def _read(name):
    return (QUICKSTART / name).read_text(encoding="utf-8").replace("\r\n", "\n").strip()


class DemoMatchesTheQuickstart(unittest.TestCase):

    def test_bundled_texts_are_the_quickstart_files(self):
        self.assertEqual(onboarding.DEMO_ORIGINAL, _read("original.txt"))
        self.assertEqual(onboarding.DEMO_ERRORS, _read("erros.txt"))
        for name, text in onboarding.DEMO_CANDIDATES:
            with self.subTest(name=name):
                self.assertEqual(text, _read(f"{name}.txt"))

    def test_demo_reports_the_three_outcomes_without_a_model(self):
        result = onboarding.demo()
        status = {c["candidate"]: c["status"] for c in result["comparisons"]}
        self.assertEqual(status, {"candidata-boa": "no_deterministic_issues", "candidata-ruim": "fail",
                                  "candidata-perde-acao": "review_required"})
        self.assertTrue(all(c["semantic_equivalence"] != "verified" for c in result["comparisons"]))
        self.assertFalse(result["model_called"])
        self.assertEqual(result["plan"]["decision"], "edit")
        classes = {d["class"] for d in result["diagnosis"]["diagnostics"]}
        self.assertIn("formal_error", classes)
        self.assertIn("internal_contradiction", classes)

    def test_demo_cli_writes_no_file_and_needs_no_checkout(self):
        # From an empty directory: the package comes from ROOT here and from the wheel in the wheel suite.
        env = dict(os.environ, PYTHONPATH=str(ROOT))
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = cli("demo", cwd=tmp, env=env)
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(os.listdir(tmp), [])
        self.assertIn("candidata-ruim: reprovada", out)
        self.assertIn("negation_changed", out)
        self.assertIn("unverified", out)
        code, out, _ = cli("demo", "--json")
        self.assertEqual(json.loads(out)["kind"], "voznativa.demo")


class Doctor(unittest.TestCase):

    def test_ok_here_and_never_touches_the_network(self):
        def refuse(*a, **k):
            raise AssertionError("doctor opened a socket")
        with mock.patch.object(socket, "socket", refuse), mock.patch.object(socket, "create_connection", refuse):
            report = onboarding.doctor()
        self.assertEqual(report["status"], "OK", report)
        self.assertEqual(report["network"], "not used")
        names = {c["check"] for c in report["checks"]}
        self.assertTrue({"python", "voznativa", "pyyaml", "references", "dados do pacote", "provider"} <= names)

    def test_never_prints_a_secret(self):
        env = dict(os.environ, ANTHROPIC_API_KEY="sk-ant-NAO-DEVE-APARECER-123")
        for args in (("doctor",), ("doctor", "--json")):
            with self.subTest(args=args):
                code, out, err = cli(*args, env=env)
                self.assertEqual(code, 0, err)
                self.assertNotIn("NAO-DEVE-APARECER", out + err)
                self.assertIn("ANTHROPIC_API_KEY", out)

    def test_a_missing_dependency_is_a_fail_with_a_hint(self):
        real = importlib.util.find_spec
        with mock.patch.object(importlib.util, "find_spec", lambda n, *a: None if n == "yaml" else real(n, *a)):
            report = onboarding.doctor()
        self.assertEqual(report["status"], "FAIL")
        yaml_check = next(c for c in report["checks"] if c["check"] == "pyyaml")
        self.assertIn("pip install", yaml_check["hint"])


class ErrorsSayWhatToDo(unittest.TestCase):

    def test_missing_file(self):
        code, _, err = cli("compare", "nao-existe.txt", "nem-este.txt")
        self.assertEqual(code, 64)
        self.assertIn("arquivo não encontrado: nao-existe.txt", err)
        self.assertNotIn("Traceback", err)

    def test_not_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "latin1.txt"
            bad.write_bytes("ação".encode("latin-1"))
            code, _, err = cli("diagnose", str(bad))
        self.assertEqual(code, 64)
        self.assertIn("não está em UTF-8", err)

    def test_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = cli("diagnose", tmp)
        self.assertEqual(code, 64)
        self.assertIn("é uma pasta", err)

    def test_path_with_spaces_and_accents(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "pasta com espaço"
            folder.mkdir()
            (folder / "ação.txt").write_text("O prazo é 14/11/2025.", encoding="utf-8")
            (folder / "candidata.txt").write_text("O prazo é 15/11/2025.", encoding="utf-8")
            code, out, err = cli("compare", str(folder / "ação.txt"), str(folder / "candidata.txt"))
        self.assertEqual(code, 1, err)
        self.assertEqual(json.loads(out)["status"], "fail")

    def test_rewrite_without_provider_points_to_the_demo(self):
        code, _, err = cli("rewrite", str(QUICKSTART / "original.txt"))
        self.assertEqual(code, 64)
        self.assertIn("voznativa demo", err)


def _load_qualify():
    spec = importlib.util.spec_from_file_location("qualify_v08", ROOT / "scripts" / "qualify.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["qualify_v08"] = module      # dataclasses look the module up while it executes
    spec.loader.exec_module(module)
    return module


class SuiteAgainstTheWheel(unittest.TestCase):

    def test_refuses_a_voznativa_that_is_not_the_venv_one(self):
        """Negative control of the origin guard: an interpreter whose voznativa (if any) is not
        inside the given venv must give FAIL before any test runs."""
        qualify = _load_qualify()
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            (src / "evals").mkdir(parents=True)
            (src / "voznativa").mkdir()
            (src / "voznativa" / "__init__.py").write_text("__version__ = 'checkout'\n", encoding="utf-8")
            result = qualify._suite_against_wheel(src, Path(tmp) / "suite", Path(sys.executable),
                                                  Path(tmp) / "not-a-venv")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("not imported from the wheel", result["reason"])

    def test_the_copy_leaves_the_package_out(self):
        qualify = _load_qualify()
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            (src / "evals").mkdir(parents=True)
            (src / "voznativa").mkdir()
            (src / "voznativa" / "__init__.py").write_text("", encoding="utf-8")
            (src / "pyproject.toml").write_text("", encoding="utf-8")
            (src / "evals" / "fixture.jsonl").write_text("{}\n", encoding="utf-8")
            qualify._suite_against_wheel(src, Path(tmp) / "suite", Path(sys.executable), Path(tmp) / "nv")
            suite = Path(tmp) / "suite"
            self.assertFalse((suite / "voznativa").exists())
            self.assertFalse((suite / "pyproject.toml").exists())
            self.assertTrue((suite / "evals" / "fixture.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
