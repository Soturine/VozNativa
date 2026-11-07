"""ptbr-bench-v3 harness check with a fake model (no cost, never official).

Runs scripts/bench_v3.py end to end (prompt arm, engine arm, original) on two
frozen cases into a temporary directory, with a fake model CLI that fails on
purpose for one arm and case: the failure must come out as a system failure,
not as preserved invariants, and nothing may be written to benchmarks/runs.
"""
import io
import json
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FAKE_MODEL = textwrap.dedent('''
    import json, os, sys
    prompt = sys.stdin.buffer.read().decode("utf-8")
    if "B1-one-line:bv3-em-02" in os.environ.get("VN_TAG", ""):
        sys.stderr.write("simulated provider outage")
        sys.exit(1)
    if "LEDGER" in prompt:
        answer = "NO_CHANGE"
    else:
        answer = "<final>" + prompt.strip().split("\\n\\n")[-1] + "</final>"
    sys.stdout.write(json.dumps({"result": answer, "total_cost_usd": 0.0, "is_error": False}))
''')


class HarnessCheck(unittest.TestCase):
    def test_runner_end_to_end_with_a_fake_model(self):
        import voznativa
        if Path(voznativa.__file__).resolve().parents[1] != ROOT:
            # v0.8 (GAP-06): the harness refuses an engine that is not this checkout's (its own
            # guard against benchmarking the wrong code); against an installed wheel that is the point.
            self.skipTest("bench_v3 pins the engine to this checkout; voznativa comes from elsewhere")
        from scripts import bench_v3
        runs = ROOT / "benchmarks" / "runs"
        before = set(runs.iterdir())
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "fake_model.py"
            fake.write_text(FAKE_MODEL, encoding="utf-8")
            out_dir = Path(tmp) / "out"
            with redirect_stdout(io.StringIO()):
                code = bench_v3.main(["--manifest", str(ROOT / "benchmarks" / "manifests" / "ptbr-bench-v3.json"),
                                      "--claude", json.dumps([sys.executable, str(fake)]), "--model", "fake",
                                      "--arms", "B0-original,B1-one-line,B6-voznativa-v050",
                                      "--cases", "bv3-em-02,bv3-reg-03", "--out-dir", str(out_dir), "--workers", "1"])
            self.assertEqual(code, 0)
            report = json.loads(next(out_dir.glob("ptbr-bench-v3-*.json")).read_text(encoding="utf-8"))
        self.assertEqual(set(runs.iterdir()), before, "a harness check must not write to benchmarks/runs")
        self.assertFalse(report["official"])
        self.assertEqual(len(report["rows"]), 6)
        summary = report["summary"]
        self.assertEqual(summary["B1-one-line"]["system_failures"], 1)
        self.assertEqual(summary["B1-one-line"]["invariants_ok_where_produced"], "1/1")
        self.assertEqual(summary["B0-original"]["system_failures"], 0)
        self.assertEqual(summary["B0-original"]["task"], {"met": 2})
        # the engine arm ran from this checkout with the regional hints and abstained
        engine_rows = [r for r in report["rows"] if r["arm"] == "B6-voznativa-v050"]
        self.assertTrue(all("error" not in r for r in engine_rows), engine_rows)
        reg = next(r for r in engine_rows if r["id"] == "bv3-reg-03")
        self.assertEqual(reg["score"]["regional_activation"], "abstain")
        self.assertEqual(reg["score"]["regional_introduced"], [])


if __name__ == "__main__":
    unittest.main()
