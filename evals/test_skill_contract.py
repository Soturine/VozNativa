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

    def test_exit_code_table_matches_cli(self):
        for code, status in re.findall(r"^\| (\d) \| `([a-z_]+)`", SKILL, re.M):
            self.assertEqual(cli.EXIT_BY_STATUS[status], int(code), status)

    def test_entry_script_runs_outside_the_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp, "a.txt")
            a.write_text("O prazo não é sexta.", encoding="utf-8")
            b = Path(tmp, "b.txt")
            b.write_text("O prazo é sexta.", encoding="utf-8")
            done = subprocess.run([sys.executable, str(ROOT / "scripts" / "voznativa.py"), "compare", str(a), str(b)],
                                  cwd=tmp, capture_output=True)
        self.assertEqual(done.returncode, 1, done.stderr.decode("utf-8", "replace"))


if __name__ == "__main__":
    unittest.main()
