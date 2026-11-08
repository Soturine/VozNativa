"""v0.8 (V08-GAP-17): the Skill's default flow must not answer NO_CHANGE over a
formal error that only `diagnose` sees.

Found in the agent-led pilot (evals/v08/agent-pilot/PILOT.md, P3): following
"Rewrite (padrão)" as written at 103414d, `patterns` and `plan` say
no_change for a text with a repeated word and a weekday/date contradiction,
so the agent answered NO_CHANGE; `diagnose` was only in another section."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
ERROS = ROOT / "examples" / "quickstart" / "erros.txt"


def vn(*args):
    done = subprocess.run([sys.executable, "-B", "-m", "voznativa", *args], capture_output=True, cwd=ROOT)
    return json.loads(done.stdout.decode("utf-8"))


class DefaultFlow(unittest.TestCase):

    def step_one(self):
        section = SKILL.split("## Rewrite (padrão)", 1)[1].split("\n2. ", 1)[0]
        return section

    def test_the_no_change_step_runs_diagnose_too(self):
        step = self.step_one()
        self.assertIn("$VN patterns", step)
        self.assertIn("$VN diagnose", step)
        self.assertLess(step.index("$VN diagnose"), step.index("NO_CHANGE"))
        self.assertRegex(step, r"nenhum erro formal")
        self.assertIn("PROOFREAD", step)

    def test_contradictions_are_suggestions_not_edits(self):
        self.assertRegex(self.step_one(), r"contradição[^.]*sugestão")

    def test_the_commands_still_disagree_on_the_pilot_text(self):
        # Why the rule matters: patterns alone says no change, diagnose sees an auto_fix error.
        self.assertEqual(vn("patterns", str(ERROS))["decision"], "no_change_candidate")
        actions = {d["type"]: d.get("action") for d in vn("diagnose", str(ERROS))["diagnostics"]}
        self.assertEqual(actions.get("repeated_word"), "auto_fix")
        self.assertEqual(actions.get("weekday_date_mismatch"), "suggest")


if __name__ == "__main__":
    unittest.main()
