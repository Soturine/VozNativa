"""v0.9 CP1: configuration files, doctor categories and rewrite --dry-run.

* precedence is flag > project file > user file > built-in default, and
  ``protect`` is the union of every source;
* a project file (it comes with a repository someone else may have written)
  cannot choose the provider command, the judge command or what environment
  reaches the model process;
* unknown keys, wrong types and invalid TOML are errors (exit 64), never
  silently ignored;
* ``doctor`` names the category of each problem and checks the configured
  provider without calling it; ``--probe-provider`` makes one real call;
* ``rewrite --dry-run`` starts no provider, even when one is configured.
"""
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import config  # noqa: E402

TEXT = ("É importante destacar que o relatório trimestral será enviado até sexta-feira, 14/11/2025. "
        "Vale ressaltar que o orçamento não pode ultrapassar R$ 12.000,00.\n")
PROVIDER = textwrap.dedent("""\
    import pathlib, sys
    sys.stdin.buffer.read()
    marker = pathlib.Path(sys.argv[1])
    marker.write_text(str(int(marker.read_text() or 0) + 1) if marker.exists() else "1")
    sys.stdout.write("ok")
""")


class Env:
    """A throwaway user config, project folder and provider script."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.user = self.tmp / "user" / "config.toml"
        self.user.parent.mkdir()
        self.project = self.tmp / "proj"
        self.project.mkdir()
        (self.project / ".git").mkdir()
        self.text = self.project / "texto.txt"
        self.text.write_text(TEXT, encoding="utf-8")
        self.provider = self.tmp / "provider.py"
        self.provider.write_text(PROVIDER, encoding="utf-8")
        self.marker = self.tmp / "calls.txt"

    @property
    def cmd(self):
        return json.dumps([sys.executable, str(self.provider), str(self.marker)])

    def env(self):
        # PYTHONPATH as in test_v08_dx: the CLI runs from a temporary folder (against the wheel,
        # ROOT holds no package and the installed one is imported).
        return dict(os.environ, VOZNATIVA_CONFIG=str(self.user), PYTHONPATH=str(ROOT))

    def cli(self, *args, cwd=None):
        done = subprocess.run([sys.executable, "-B", "-m", "voznativa", *args], capture_output=True,
                              cwd=cwd or self.project, env=self.env())
        return done.returncode, done.stdout.decode("utf-8"), done.stderr.decode("utf-8")

    def calls(self):
        return int(self.marker.read_text()) if self.marker.exists() else 0


def toml_str(value: str) -> str:
    return json.dumps(value)  # a JSON string literal is a valid TOML basic string


class Precedence(unittest.TestCase):

    def setUp(self):
        self.e = Env()

    def test_flag_beats_project_beats_user_beats_default(self):
        self.e.user.write_text("[rewrite]\nattempts = 5\nmax_calls = 50\ntimeout = 30\n", encoding="utf-8")
        (self.e.project / ".voznativa.toml").write_text("[rewrite]\nattempts = 4\n", encoding="utf-8")
        old = os.environ.get("VOZNATIVA_CONFIG")
        os.environ["VOZNATIVA_CONFIG"] = str(self.e.user)
        try:
            files = config.load(self.e.project)
            got = config.resolve({"attempts": None, "max_calls": None, "timeout": 7.0}, files)
        finally:
            os.environ.pop("VOZNATIVA_CONFIG") if old is None else os.environ.__setitem__("VOZNATIVA_CONFIG", old)
        self.assertEqual((got["attempts"]["value"], got["attempts"]["source"]), (4, "project"))
        self.assertEqual((got["max_calls"]["value"], got["max_calls"]["source"]), (50, "user"))
        self.assertEqual((got["timeout"]["value"], got["timeout"]["source"]), (7.0, "flag"))
        self.assertEqual((got["judge_votes"]["value"], got["judge_votes"]["source"]), (2, "default"))

    def test_protect_is_the_union_of_every_source(self):
        files = {"user": (Path("u"), {"protect": ["Kubernetes"]}), "project": (Path("p"), {"protect": ["ACME"]})}
        got = config.resolve({"protect": ["Ana"]}, files)["protect"]
        self.assertEqual(got["value"], ["Ana", "ACME", "Kubernetes"])
        self.assertEqual(got["source"], "flag+project+user")

    def test_project_search_stops_at_the_repository_root(self):
        outer = self.e.tmp / ".voznativa.toml"
        outer.write_text("[rewrite]\nattempts = 9\n", encoding="utf-8")
        self.assertIsNone(config.project_path(self.e.project))
        sub = self.e.project / "a" / "b"
        sub.mkdir(parents=True)
        (self.e.project / ".voznativa.toml").write_text("[rewrite]\nattempts = 2\n", encoding="utf-8")
        # resolved on both sides: the Windows CI runner's TEMP is a short 8.3 path (CI #129)
        self.assertEqual(config.project_path(sub), (self.e.project / ".voznativa.toml").resolve())


class ProjectFileTrustBoundary(unittest.TestCase):

    def setUp(self):
        self.e = Env()

    def test_a_project_file_cannot_choose_the_command(self):
        for key, value in (("cmd", toml_str(self.e.cmd)), ("judge_cmd", toml_str(self.e.cmd)),
                           ("provider_env", '"inherit"'), ("provider_env_allow", '["ANTHROPIC_API_KEY"]')):
            with self.subTest(key=key):
                (self.e.project / ".voznativa.toml").write_text(f"[rewrite]\n{key} = {value}\n", encoding="utf-8")
                code, out, err = self.e.cli("rewrite", "texto.txt", "--force")
                self.assertEqual(code, 64, out + err)
                self.assertIn("refused in a project file", err)
                self.assertEqual(self.e.calls(), 0, "the project's command ran")

    def test_the_user_file_may_choose_the_command(self):
        self.e.user.write_text(f"[rewrite]\ncmd = {toml_str(self.e.cmd)}\nattempts = 1\n", encoding="utf-8")
        code, out, err = self.e.cli("rewrite", "texto.txt", "--force")
        self.assertIn(code, (1, 2, 3), out + err)  # "ok" is not a valid rewrite: original back or review
        self.assertGreaterEqual(self.e.calls(), 1)

    def test_unknown_key_wrong_type_and_bad_toml_are_errors(self):
        for body, needle in (("[rewrite]\natempts = 3\n", "unknown key"),
                             ("[rewrite]\nattempts = \"três\"\n", "wrong type"),
                             ("[rewrite]\nlong_form = \"sempre\"\n", "must be one of"),
                             ("[rewrite\n", "invalid TOML"),
                             ("[outra]\nx = 1\n", "unknown table")):
            with self.subTest(body=body):
                self.e.user.write_text(body, encoding="utf-8")
                code, out, err = self.e.cli("rewrite", "texto.txt", "--dry-run")
                self.assertEqual(code, 64, out + err)
                self.assertIn(needle, err)


class DryRun(unittest.TestCase):

    def test_deterministic_mode_has_no_call_budget(self):
        e = Env()
        code, out, err = e.cli("rewrite", "texto.txt", "--dry-run", "--mode", "PROOFREAD", "--force")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertFalse(report["would_call_model"])
        self.assertEqual(report["budget"]["max_provider_calls"], 0)
        self.assertNotIn("note", report)

    def test_budget_accounts_for_judge_retries_on_each_attempt(self):
        e = Env()
        code, out, err = e.cli("rewrite", "texto.txt", "--dry-run", "--attempts", "2",
                               "--candidates", "2", "--judge-cmd", e.cmd, "--judge-votes", "3")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["budget"]["max_provider_calls"], 16)

    def test_dry_run_starts_no_provider_even_when_configured(self):
        e = Env()
        e.user.write_text(f"[rewrite]\ncmd = {toml_str(e.cmd)}\n", encoding="utf-8")
        code, out, err = e.cli("rewrite", "texto.txt", "--dry-run", "--force")
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertFalse(report["provider_called"])
        self.assertTrue(report["provider"]["cmd"])
        self.assertEqual(report["decision"], "edit")
        self.assertEqual(report["budget"]["max_provider_calls"], 3)
        self.assertEqual(report["config_sources"], {"cmd": "user"})
        self.assertNotIn(str(e.provider), out, "the command line is not echoed")
        self.assertEqual(e.calls(), 0)


class DoctorCategories(unittest.TestCase):

    def setUp(self):
        self.e = Env()

    def doctor(self, *extra):
        code, out, err = self.e.cli("doctor", "--json", *extra)
        return code, json.loads(out)

    def test_no_provider_is_not_a_failure(self):
        code, report = self.doctor()
        self.assertEqual(code, 0)
        self.assertEqual(report["schema_version"], 2)
        provider = next(c for c in report["checks"] if c["check"] == "provider")
        self.assertEqual(provider["status"], "OK")

    def test_missing_program_is_provider_not_found_with_an_action(self):
        self.e.user.write_text('[rewrite]\ncmd = "programa-que-nao-existe-vn09 -p"\n', encoding="utf-8")
        code, report = self.doctor()
        self.assertEqual(code, 1)
        provider = next(c for c in report["checks"] if c["check"] == "provider")
        self.assertEqual((provider["status"], provider["category"]), ("FAIL", "provider_not_found"))
        self.assertIn("PATH", provider["hint"])

    def test_invalid_config_is_a_config_failure(self):
        self.e.user.write_text("[rewrite]\natempts = 1\n", encoding="utf-8")
        code, report = self.doctor()
        self.assertEqual(code, 1)
        self.assertIn("config", {c["category"] for c in report["checks"] if c["status"] == "FAIL"})

    def test_agent_cli_with_tools_is_a_warning(self):
        claude = self.e.tmp / ("claude.exe" if os.name == "nt" else "claude")
        claude.write_bytes(b"")
        self.e.user.write_text(f"[rewrite]\ncmd = {toml_str(json.dumps([str(claude), '-p']))}\n",
                               encoding="utf-8")
        code, report = self.doctor()
        warn = [c for c in report["checks"] if c["category"] == "provider_unsafe"]
        self.assertEqual(code, 0)
        self.assertEqual(len(warn), 1)

    def test_allowed_but_missing_credential_is_named_without_a_value(self):
        self.e.user.write_text(f"[rewrite]\ncmd = {toml_str(self.e.cmd)}\nprovider_env = \"minimal\"\n"
                               "provider_env_allow = [\"VN09_CHAVE_QUE_NAO_EXISTE\"]\n", encoding="utf-8")
        code, report = self.doctor()
        cred = [c for c in report["checks"] if c["category"] == "credential"]
        self.assertEqual(len(cred), 1)
        self.assertIn("VN09_CHAVE_QUE_NAO_EXISTE", cred[0]["detail"])

    def test_doctor_calls_the_provider_only_when_asked(self):
        self.e.user.write_text(f"[rewrite]\ncmd = {toml_str(self.e.cmd)}\n", encoding="utf-8")
        code, report = self.doctor()
        self.assertEqual((code, self.e.calls()), (0, 0))
        self.assertEqual(report["network"], "not used")
        code, report = self.doctor("--probe-provider")
        self.assertEqual((code, self.e.calls()), (0, 1))
        probe = next(c for c in report["checks"] if c["check"] == "chamada de teste")
        self.assertEqual(probe["status"], "OK")

    def test_a_failing_provider_probe_is_categorised(self):
        bad = self.e.tmp / "bad.py"
        bad.write_text("import sys; sys.stdin.read(); sys.stderr.write('401 unauthorized'); sys.exit(3)\n",
                       encoding="utf-8")
        self.e.user.write_text(f"[rewrite]\ncmd = {toml_str(json.dumps([sys.executable, str(bad)]))}\n",
                               encoding="utf-8")
        code, report = self.doctor("--probe-provider")
        self.assertEqual(code, 1)
        probe = next(c for c in report["checks"] if c["check"] == "chamada de teste")
        self.assertEqual(probe["category"], "provider_call")
        self.assertIn("credencial", probe["hint"])


if __name__ == "__main__":
    unittest.main()
