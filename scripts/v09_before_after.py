#!/usr/bin/env python3
"""Before x after for v0.9 CP7: the same instruments on two checkouts.

    python scripts/v09_before_after.py --before /path/to/v0.8.1/checkout [--after .] --out report.json

Instruments (each run with the engine of the checkout it measures, on the
data of the *after* checkout, which keeps frozen files byte-identical):

* ``evaluate``: the v0.8 Evaluation Core datasets (gate-and-planner,
  events): sensitivity and false alarm per split, decision accuracy;
* ``prospective``: the v0.9 frozen sets (``evals/v09``), development and
  holdout, semantic and diagnose;
* ``unnecessary_edit``: how many texts the frozen suites say need no change
  still get an ``edit``/``transform`` plan.

Axes are reported separately and never summed. None of these numbers is
human judgment or independent evaluation: same author, development data.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

AFTER = Path(__file__).resolve().parent.parent

CHILD = r'''
import json, sys, glob
from pathlib import Path
engine, data = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(engine))
from voznativa import __version__, evaluation
from voznativa.planner import plan
from voznativa.router import route
from voznativa.patterns import detect
out = {"engine_version": __version__}
ev = {}
for spec_path in sorted((data / "evals" / "v08" / "datasets").glob("*.json")):
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    rec = evaluation.run(spec, data, recorded_at="before-after")
    ev[spec_path.stem] = {split: {k: v for k, v in m.items() if k in ("semantic_risk", "decision")}
                          for split, m in rec["metrics"].items()}
out["evaluate"] = ev
# unnecessary edits: texts the frozen suites say need no change
cases = []
for f in sorted((data / "evals").rglob("*.jsonl")):
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            c = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(c, dict):
            continue
        exp = c.get("expect") if isinstance(c.get("expect"), dict) else {}
        text = c.get("text") or c.get("input")
        if isinstance(text, str) and (exp.get("decision") in ("no_change", "no_change_candidate")
                                      or c.get("expected_decision") == "no_change"):
            cases.append((str(f.relative_to(data)), c.get("id"), text, c.get("genre")))
edits = []
for path, cid, text, genre in cases:
    try:
        decision = plan(text, route(text, genre=genre) if genre else route(text))["decision"]
    except Exception as error:      # a case the older engine cannot read is reported, not hidden
        decision = f"error:{type(error).__name__}"
    if decision != "no_change":
        edits.append({"file": path, "id": cid, "decision": decision})
out["unnecessary_edit"] = {"cases": len(cases), "edit_decisions": len(edits), "examples": edits[:15]}
print(json.dumps(out, ensure_ascii=False))
'''


def run_child(engine: Path, data: Path) -> dict:
    done = subprocess.run([sys.executable, "-c", CHILD, str(engine), str(data)], capture_output=True)
    if done.returncode != 0:
        raise SystemExit(done.stderr.decode("utf-8", "replace")[-2000:])
    return json.loads(done.stdout.decode("utf-8"))


def prospective(engine: Path) -> dict:
    out = {}
    for split in ("development", "holdout"):
        done = subprocess.run([sys.executable, str(AFTER / "scripts" / "v09_prospective_eval.py"), "--split", split,
                               "--root", str(engine)], capture_output=True)
        line = done.stdout.decode("utf-8").strip().splitlines()[-1]
        out[split] = line
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", default=str(AFTER))
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    before, after = Path(args.before).resolve(), Path(args.after).resolve()
    report = {"kind": "voznativa.v09_before_after", "data_root": str(after.name),
              "before": run_child(before, after), "after": run_child(after, after),
              "prospective": {"before": prospective(before), "after": prospective(after)},
              "independent": False}
    text = json.dumps(report, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
