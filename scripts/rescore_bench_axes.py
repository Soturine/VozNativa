#!/usr/bin/env python3
"""Rescore a recorded benchmark run on separate outcome axes (H2).

Reads a run written by scripts/bench_v2.py and its frozen cases, applies
voznativa.benchmark.outcome_axes to every row and writes
``<run>.axes-<date>.json`` next to it. The official run file is only read:
its sha256 is recorded so the rescore names exactly what it reinterpreted.
No model is called; no output, judgment or cost is recomputed.

    python scripts/rescore_bench_axes.py benchmarks/runs/ptbr-bench-v2-20261021T110338Z.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.benchmark import load_cases, outcome_axes, summarize_axes  # noqa: E402


def rescore(run: dict, cases: list[dict]) -> dict:
    by_id = {c["id"]: c for c in cases}
    arms: dict[str, list[dict]] = {}
    for row in run["rows"]:
        arms.setdefault(row["arm"], []).append(outcome_axes(by_id[row["id"]], row))
    return {arm: {"summary": summarize_axes(sorted(rows, key=lambda a: a["id"])),
                  "rows": sorted(rows, key=lambda a: a["id"])}
            for arm, rows in sorted(arms.items())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run")
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y%m%d"))
    args = parser.parse_args(argv)
    path = Path(args.run)
    raw = path.read_bytes()
    run = json.loads(raw.decode("utf-8"))
    cases_path = ROOT / run["manifest"]["cases_file"]
    cases_sha = hashlib.sha256(cases_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if cases_sha != run["cases_sha256"]:
        raise SystemExit("cases changed since the run; refusing to rescore")
    report = {
        "kind": "voznativa.benchmark_axes_rescore", "schema_version": 1,
        "rescored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "official_run": path.name, "official_run_sha256": hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
        "official_result_unchanged": True,
        "method": "voznativa.benchmark.outcome_axes over the recorded rows; no model call, no new output",
        "limits": ["destination and quality need people: 'met_pending_evaluation' is not 'met'",
                   "human_preference NOT_RUN: no human reviewed these outputs",
                   "n = 15 per arm, developer-written cases: intervals are wide and not general estimates"],
        "arms": rescore(run, load_cases(cases_path)),
    }
    out = path.with_name(f"{path.stem}.axes-{args.date}.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for arm, data in report["arms"].items():
        s = data["summary"]
        print(f"{arm:20s} task {s['task_met_or_pending']:6s} {s['task']}  failures {s['system_failures']}  "
              f"invariants(produced) {s['invariants_ok_where_produced']}")
    print(out.resolve().relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
