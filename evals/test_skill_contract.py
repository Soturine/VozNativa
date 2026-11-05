"""SKILL.md must not drift from the CLI it tells agents to run."""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import cli

SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")


def subparsers():
    parser = cli.build_parser()
    action = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
    return action.choices


class SkillMatchesCli(unittest.TestCase):
    def test_every_documented_command_and_flag_exists(self):
        commands = subparsers()
        for line in re.findall(r"\$VN ([^`|\n]+)", SKILL):
            name = line.split()[0]
            self.assertIn(name, commands, f"SKILL.md documents unknown command: {name}")
            known = {opt for a in commands[name]._actions for opt in a.option_strings}
            for flag in re.findall(r"(?<![\w-])(--[a-z][\w-]*)", line):
                self.assertIn(flag, known, f"SKILL.md documents unknown flag {flag} for {name}")

    def test_every_flag_mentioned_anywhere_exists(self):
        known = {opt for p in subparsers().values() for a in p._actions for opt in a.option_strings}
        mentioned = set(re.findall(r"`(--[a-z][\w-]*)", SKILL)) | set(re.findall(r"\s(--[a-z][\w-]*)", SKILL))
        self.assertGreater(len(mentioned), 8)
        self.assertEqual(mentioned - known, set())

    def test_readme_commands_exist(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        commands = subparsers()
        lines = re.findall(r"^voznativa ([^#\n]+)", readme, re.M)
        self.assertGreater(len(lines), 8)
        for line in lines:
            name = line.split()[0]
            self.assertIn(name, commands, f"README documents unknown command: {name}")
            known = {opt for a in commands[name]._actions for opt in a.option_strings}
            # Flags inside a quoted value ('["claude", "-p", "--tools", ""]') belong to the model CLI.
            for flag in re.findall(r"(?<![\w-])(--[a-z][\w-]*)", re.sub(r"'[^']*'", "", line)):
                self.assertIn(flag, known, f"README documents unknown flag {flag} for {name}")

    def test_exit_code_table_matches_cli(self):
        for code, status in re.findall(r"^\| (\d) \| `([a-z_]+)`", SKILL, re.M):
            self.assertEqual(cli.EXIT_BY_STATUS[status], int(code), status)

    def test_no_script_shadows_the_package(self):
        # scripts/voznativa.py shadowed the package for code run from scripts/ (found on Linux).
        names = {p.stem for p in (ROOT / "scripts").glob("*.py")}
        self.assertNotIn("voznativa", names)

    def test_entry_script_runs_outside_the_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp, "a.txt")
            a.write_text("O prazo não é sexta.", encoding="utf-8")
            b = Path(tmp, "b.txt")
            b.write_text("O prazo é sexta.", encoding="utf-8")
            done = subprocess.run([sys.executable, str(ROOT / "scripts" / "voznativa_cli.py"), "compare", str(a), str(b)],
                                  cwd=tmp, capture_output=True)
        self.assertEqual(done.returncode, 1, done.stderr.decode("utf-8", "replace"))


if __name__ == "__main__":
    unittest.main()


class DemoV05(unittest.TestCase):
    """CP9: the v0.5.0 demonstration is derived, not written by hand: it
    regenerates identically from the code and carries no machine path."""

    def test_demo_regenerates_identically_and_shows_every_outcome(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("demo_v05", ROOT / "scripts" / "demo_v05.py")
        demo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(demo)
        page = demo.render()
        self.assertEqual(page, (ROOT / "examples" / "v0.5.0-demo.md").read_text(encoding="utf-8").replace("\r\n", "\n"))
        for outcome in ("needs_judgment", "returned_original", "needs_review", "provider_error"):
            self.assertIn(f"desfecho `{outcome}`", page)
        self.assertIn("embedded_instruction", page)
        self.assertIn("regionalidade: `abstain`", page)
        for leak in ("\\Users\\\\", "/Users/", "/home/", "AppData"):
            self.assertNotIn(leak, page)
