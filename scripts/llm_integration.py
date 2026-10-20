#!/usr/bin/env python3
"""Run the Rewrite Engine against a REAL external model and record the run.

This is not part of the unit suite: it calls a model, costs money and is not
deterministic. It writes a report to evals/integration/ with everything
needed to audit the run (command, model, CLI version, raw outputs, every
attempt, deterministic status and the LLM judge's verdict).

    python scripts/llm_integration.py --cmd '["claude", "-p", "--tools", "", ...]' --model-label NAME

The judge is the same command in a separate call; its verdict is recorded
as kind=llm and never counts as human review.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.benchmark import load_cases  # noqa: E402
from voznativa.engine import rewrite  # noqa: E402
from voznativa.providers import CommandProvider  # noqa: E402
from voznativa.router import route  # noqa: E402


class RecordingProvider:
    """Wraps a provider and keeps every raw answer and its latency."""

    def __init__(self, inner, role: str):
        self.inner, self.role, self.log = inner, role, []
        self.id = f"{inner.id} ({role})"

    def generate(self, prompt: str, n: int = 1) -> list[str]:
        start = time.monotonic()
        answers = self.inner.generate(prompt, n)
        self.log.append({"role": self.role, "seconds": round(time.monotonic() - start, 1),
                         "prompt_chars": len(prompt), "answers": answers})
        return answers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cmd", required=True, help="JSON argv of the model command (prompt on stdin)")
    parser.add_argument("--model-label", required=True, help="model name as passed to the command")
    parser.add_argument("--version-cmd", help="JSON argv that prints the CLI version")
    parser.add_argument("--cases", default=str(ROOT / "benchmarks" / "cases" / "ptbr-v1.jsonl"))
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()

    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()  # noqa: E731
    code_state = {"commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain", "voznativa"))}
    version = None
    if args.version_cmd:
        version = subprocess.run(json.loads(args.version_cmd), capture_output=True, text=True).stdout.strip()
    cases_path = Path(args.cases).resolve()
    out_dir = ROOT / "evals" / "integration"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"{stamp}-{args.model_label}-{cases_path.stem}.json"
    rows = []

    def save():
        # Written after every case so a crash never loses paid model calls.
        report = {
            "kind": "voznativa.llm_integration_run",
            "kind_of_evidence": "real external model call; not deterministic; not human review",
            "run_at": stamp,
            "command": json.loads(args.cmd),
            "model_label": args.model_label,
            "cli_version": version,
            "voznativa_code": code_state,
            "cases_file": cases_path.relative_to(ROOT).as_posix() if cases_path.is_relative_to(ROOT) else str(cases_path),
            "attempts_allowed": args.attempts,
            "complete": len(rows) == total,
            "summary": {o: sum(1 for r in rows if r["outcome"] == o) for o in sorted({str(r["outcome"]) for r in rows})},
            "results": rows,
        }
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    cases = load_cases(cases_path)
    total = len(cases)
    for case in cases:
        writer = RecordingProvider(CommandProvider.from_string(args.cmd, args.timeout), "writer")
        judge = RecordingProvider(CommandProvider.from_string(args.cmd, args.timeout), "judge")
        context = route(case["text"], genre=case.get("genre"), channel=case.get("channel"))
        started = time.monotonic()
        try:
            result = rewrite(case["text"], context, writer, attempts=args.attempts, judge_provider=judge)
            error = None
        except Exception as exc:  # recorded, never hidden
            result, error = None, f"{type(exc).__name__}: {exc}"
        report = (result or {}).get("report") or {}
        rows.append({
            "id": case["id"],
            "original": case["text"],
            "outcome": (result or {}).get("outcome"),
            "final_text": (result or {}).get("text"),
            "final_status": report.get("status"),
            "attempts": (result or {}).get("attempts"),
            "judgments": [{k: j.get(k) for k in ("kind", "judge_id", "verdict", "downgraded")}
                          for j in (report.get("evidence") or {}).get("judgments", [])],
            "judge_error": report.get("judge_error"),
            "quality": (result or {}).get("quality"),
            "error": error,
            "seconds": round(time.monotonic() - started, 1),
            "calls": writer.log + judge.log,
        })
        print(f"{case['id']}: {rows[-1]['outcome']} ({rows[-1]['final_status']})", flush=True)
        save()

    save()
    print("report:", path.relative_to(ROOT).as_posix())
    return 0 if all(r["error"] is None for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
