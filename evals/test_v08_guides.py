"""v0.8 CP12: the user guides are executable.

* docs/guide/CLI.md is exactly what scripts/cli_reference.py generates from
  the parser (no drift).
* Every command in docs/guide/QUICKSTART.md annotated with `# exit N` runs
  from the repository root and exits with N."""
import os
import re
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "guide"
ENV = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8")
LINE = re.compile(r"^voznativa (.+?)\s+# exit (\d+)\s*$")


def quickstart_commands():
    text = (GUIDE / "QUICKSTART.md").read_text(encoding="utf-8")
    for block in re.findall(r"```bash\n(.*?)```", text, re.S):
        for line in block.splitlines():
            m = LINE.match(line.strip())
            if m:
                yield m.group(1).replace("$PWD", ROOT.as_posix()), int(m.group(2))


class Guides(unittest.TestCase):

    def test_cli_reference_matches_the_parser(self):
        done = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "cli_reference.py")], capture_output=True,
                              cwd=ROOT, env=ENV)
        self.assertEqual(done.returncode, 0, done.stdout.decode("utf-8", "replace"))

    def test_the_reference_does_not_depend_on_how_argparse_wraps(self):
        # CP16: the same help wrapped by Python 3.12 and by 3.13 (Linux 3.13 run of d4b0ed1).
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            from cli_reference import _version_neutral
        finally:
            sys.path.pop(0)
        py312 = ("usage: voznativa standards resolve [-h] --document-type DOCUMENT_TYPE --submission-date\n"
                 "                                   SUBMISSION_DATE [--authority AUTHORITY]\n\n"
                 "positional arguments:\n  {doctor,demo}\n                 ...\n")
        py313 = ("usage: voznativa standards resolve [-h] --document-type DOCUMENT_TYPE\n"
                 "                                   --submission-date SUBMISSION_DATE [--authority AUTHORITY]\n\n"
                 "positional arguments:\n  {doctor,demo} ...\n")
        self.assertEqual(_version_neutral(py312), _version_neutral(py313))
        self.assertIn("--submission-date SUBMISSION_DATE [--authority AUTHORITY]\n", _version_neutral(py312))

    def test_quickstart_commands_run_with_the_documented_exit_code(self):
        commands = list(quickstart_commands())
        self.assertGreaterEqual(len(commands), 12)
        for args, expected in commands:
            with self.subTest(command=args[:70]):
                done = subprocess.run([sys.executable, "-B", "-m", "voznativa", *shlex.split(args)],
                                      capture_output=True, cwd=ROOT, env=ENV, timeout=600)
                self.assertEqual(done.returncode, expected, done.stderr.decode("utf-8", "replace")[-400:])

    def test_every_guide_is_linked_from_the_docs_home(self):
        home = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        for guide in sorted(GUIDE.glob("*.md")):
            self.assertIn(f"guide/{guide.name}", home, guide.name)


if __name__ == "__main__":
    unittest.main()
