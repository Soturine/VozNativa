"""v0.10.5 R18: the Observatory page only draws; every number comes from scripts/v0105_observatory.py. These tests
pin the derived metrics (interval, edit decision, sanitised agent steps, headline) and the escaping of the payload.
Fixtures are invented; no corpus text."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("v0105_observatory", ROOT / "scripts" / "v0105_observatory.py")
obs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(obs)


class DerivedMetrics(unittest.TestCase):
    def test_wilson_interval(self):
        self.assertIsNone(obs.wilson(0, 0))
        lo, hi = obs.wilson(236, 239)
        self.assertTrue(lo < 236 / 239 < hi <= 1.0)
        self.assertEqual(obs.wilson(10, 10)[1], 1.0)
        self.assertEqual(obs.wilson(0, 10)[0], 0.0)
        a, b = obs.wilson(5, 10), obs.wilson(50, 100)
        self.assertLess(b[1] - b[0], a[1] - a[0])          # more cases, narrower interval

    def test_edit_decision_against_frozen_expectation(self):
        self.assertEqual(obs.decision("no_change_expected", True), "unnecessary_edit")
        self.assertEqual(obs.decision("no_change_expected", False), "ok")
        self.assertEqual(obs.decision("edit_required", False), "missed_edit")
        self.assertEqual(obs.decision("edit_required", True), "ok")
        self.assertEqual(obs.decision("edit_allowed", True), "open")
        self.assertEqual(obs.decision("constrained_edit", False), "open")
        self.assertEqual(obs.decision("edit_required", None), "failed")   # no output is never a correct decision

    def test_agent_steps_keep_only_subcommand_names(self):
        calls = ['cd "D:\\scratch\\run-17\\project" && VN="python .claude/skills/voznativa/'
                 'scripts/voznativa_cli.py"; $VN route texto.txt --genre literary; $VN diagnose texto.txt',
                 'python .claude/skills/voznativa/scripts/voznativa_cli.py compare a.txt b.txt --protect "Fulano"',
                 'python .claude/skills/voznativa/scripts/voznativa_cli.py compare a.txt c.txt',
                 'ls -la']
        steps = obs.cli_steps(calls)
        self.assertEqual(steps, ["route", "diagnose", "compare"])
        self.assertNotIn("scratch", json.dumps(steps))
        self.assertEqual(obs.cli_steps(None), [])

    def test_run_record_changed_and_failed(self):
        base = {"label": "v0105", "task": "T01", "rep": 1, "cost_usd": 0.01, "seconds": 3.0}
        same = obs._run_record(dict(base, arm="A1_direct", output="Texto.\n"), "Texto.", "no_change_expected")
        self.assertIs(same["changed"], False)
        self.assertEqual(same["decision"], "ok")
        moved = obs._run_record(dict(base, arm="A1_direct", output="Outro texto."), "Texto.", "no_change_expected")
        self.assertEqual(moved["decision"], "unnecessary_edit")
        empty = obs._run_record(dict(base, arm="A1_direct", output=None), "Texto.", "edit_required")
        self.assertIsNone(empty["changed"])
        self.assertEqual(empty["decision"], "failed")
        kept = obs._run_record(dict(base, arm="A3_engine", output="Texto.", outcome="no_change"), "Texto.", "edit_required")
        self.assertEqual(kept["decision"], "missed_edit")
        self.assertNotIn("output", kept)                     # the text itself never enters a run record

    def test_headline_counts_misses_and_alarms_separately(self):
        off = lambda flag_ok, clean_ok: {"kinds": {"neg": {"correct": flag_ok, "total": 10, "expected": "flag"},
                                                   "wrap": {"correct": clean_ok, "total": 5, "expected": "clean"}},
                                         "confirmed_items": 1, "plans": {"edit": 2}}
        data = {"offline": {"v0.10.0": off(6, 3), "v0.10.5": off(9, 2)}, "live": {"arms": {}},
                "perf_17600_cpu_min_s": {"base": [10.0, 11.0], "cand": [10.5, 12.0]}}
        h = obs._headline(data)
        self.assertEqual(h["offline_missed"], [4, 1])
        self.assertEqual(h["offline_false_alarms"], [2, 3])
        self.assertEqual([k["kind"] for k in h["kinds_improved"]], ["neg"])
        self.assertEqual([k["kind"] for k in h["kinds_worse"]], ["wrap"])   # a worse measure is reported, not hidden
        self.assertEqual(h["perf_ratio_17600"], 1.05)


class PayloadEscaping(unittest.TestCase):
    def test_payload_cannot_close_its_script_tag(self):
        template = obs.TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertIn("__PAYLOAD__", template)
        page = obs.render()
        start = page.index('<script type="application/json" id="payload">')
        end = page.index("</script>", start)
        body = page[start:end]
        self.assertNotIn("</", body[50:])
        self.assertNotIn("<", body[len('<script type="application/json" id="payload">'):])
        json.loads(body[len('<script type="application/json" id="payload">'):])

    def test_page_is_self_contained(self):
        import re
        page = obs.render()
        # anything that would load a resource over the network (an SVG namespace or a DOI in the data is not a load)
        loads = re.findall(r"<script[^>]+src=|<link[^>]+rel=.stylesheet|@import|url\(\s*['\"]?https?:|"
                           r"(?:src|srcset)=[\"']https?:|fetch\(|XMLHttpRequest|navigator\.sendBeacon|document\.cookie", page)
        self.assertEqual(loads, [])


if __name__ == "__main__":
    unittest.main()
