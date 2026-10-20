#!/usr/bin/env python3
"""Experiment (v0.3.0 M3.1): does the Voice Contract move rewrites toward the
author's style?

Rewrites the same drafts twice with a real model, without and with a Voice
Profile, and measures the scaled style distance of each final text to the
profile (voznativa.drift.voice_distance) and its semantic status. The
author is synthetic (evals/voice/synthetic-author-a), so this shows the
mechanism works, not that it calibrates a real person.

    python scripts/experiments/voice_match.py --claude PATH --model claude-sonnet-5-5
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from voznativa.benchmark import load_cases  # noqa: E402
from voznativa.drift import voice_distance  # noqa: E402
from voznativa.engine import rewrite  # noqa: E402
from voznativa.profile import build  # noqa: E402
from voznativa.providers import CommandProvider  # noqa: E402
from voznativa.router import route  # noqa: E402

CASES = ["ai-corp-001", "ai-status-001", "ai-support-001", "ai-tech-001"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    samples = sorted((ROOT / "evals/voice/synthetic-author-a").glob("s*.txt"))
    profile = build([{"text": p.read_text(encoding="utf-8"), "channel": "slack"} for p in samples])
    argv = [args.claude, "-p", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
            "--model", args.model, "--output-format", "text"]
    cases = {c["id"]: c for c in load_cases(ROOT / "benchmarks/cases/ptbr-ai-drafts-v1.jsonl")}
    rows = []
    for case_id in CASES:
        text = cases[case_id]["text"]
        ctx = route(text, genre="corporate", channel="slack")
        row = {"id": case_id, "original_distance": voice_distance(text, profile)["mean"]}
        for label, prof in (("without_profile", None), ("with_profile", profile)):
            result = rewrite(text, ctx, CommandProvider(argv, timeout=400), profile=prof, attempts=3, force=True)
            row[label] = {"outcome": result["outcome"],
                          "status": (result.get("report") or {}).get("status"),
                          "distance": voice_distance(result["text"], profile)["mean"],
                          "text": result["text"]}
        rows.append(row)
        print(case_id, row["original_distance"], row["without_profile"]["distance"], row["with_profile"]["distance"],
              flush=True)
    changed = [r for r in rows if r["with_profile"]["text"] != cases[r["id"]]["text"]
               and r["without_profile"]["text"] != cases[r["id"]]["text"]]
    summary = {
        "author": "synthetic-author-a (written by the developer)",
        "profile_maturity": profile["maturity"],
        "cases": len(rows),
        "pairs_where_both_rewrote": len(changed),
        "median_distance": {
            "original": statistics.median(r["original_distance"] for r in rows),
            "without_profile": statistics.median(r["without_profile"]["distance"] for r in rows),
            "with_profile": statistics.median(r["with_profile"]["distance"] for r in rows),
        },
        "with_profile_closer": sum(r["with_profile"]["distance"] < r["without_profile"]["distance"] for r in changed),
    }
    out = ROOT / "evals/experiments/voice_match_synthetic_a.json"
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or None
    except OSError:  # git missing
        commit = None
    out.write_text(json.dumps({"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model": args.model,
                               "voznativa_commit": commit, "summary": summary, "rows": rows},
                              ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
