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
from voznativa.redact import new_key, redact_argv, scrub_message, scrub_secrets  # noqa: E402
from voznativa.redact import shield as keyed_shield  # noqa: E402
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
    parser.add_argument("--redact", action="store_true",
                        help="store only keyed hashes, lengths and metrics, never texts or raw model answers")
    parser.add_argument("--redact-key", help="file with the hex key for --redact hashes (created if missing); "
                                             "keep it to compare runs. Without it the key is random and not stored")
    args = parser.parse_args()

    def git(*a):
        """Empty when git is missing or this is not a checkout (e.g. a container)."""
        try:
            return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        except OSError:
            return ""

    commit = git("rev-parse", "HEAD")
    code_state = {"commit": commit or None, "dirty": bool(git("status", "--porcelain", "voznativa")) if commit else None}
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
            # Credentials in the command are masked with or without --redact.
            "command": redact_argv(json.loads(args.cmd)),
            "model_label": args.model_label,
            "cli_version": version,
            "voznativa_code": code_state,
            "cases_file": cases_file,
            "attempts_allowed": args.attempts,
            "complete": len(rows) == total,
            "redacted": args.redact,
            **({"redaction": {"texts": "HMAC-SHA256 and length; the key is not in this report",
                              "key": "--redact-key file" if args.redact_key else "random, discarded after the run",
                              "free_text": "errors scrubbed of secrets, quotes and sentences of the texts",
                              "command": "credential values masked"}} if args.redact else {}),
            "summary": {o: sum(1 for r in rows if r["outcome"] == o) for o in sorted({str(r["outcome"]) for r in rows})},
            "results": rows,
        }
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    key = new_key()
    if args.redact and args.redact_key:
        key_file = Path(args.redact_key)
        if not key_file.exists():
            key_file.write_text(key.hex(), encoding="ascii")
        key = bytes.fromhex(key_file.read_text(encoding="ascii").strip())

    def shield(text):
        """With --redact, replace a text by a keyed hash and its length.
        Without it the text is kept, but credentials in it are still masked."""
        if args.redact:
            return keyed_shield(text, key)
        return scrub_secrets(text) if text else text

    def free_text(message, texts):
        """Errors can echo the texts or a credential: scrub them."""
        return scrub_message(message, texts) if args.redact else scrub_secrets(message) if message else message

    in_root = cases_path.is_relative_to(ROOT)
    cases_file = (cases_path.name if args.redact else
                  cases_path.relative_to(ROOT).as_posix() if in_root else str(cases_path))

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
        seen = [case["text"], (result or {}).get("text") or ""] + [a for c in writer.log + judge.log
                                                                     for a in c["answers"]]
        rows.append({
            "id": case["id"],
            "original": shield(case["text"]),
            "outcome": (result or {}).get("outcome"),
            "final_text": shield((result or {}).get("text")),
            "final_status": report.get("status"),
            "attempts": [{k: scrub_secrets(v) if k == "preview" else v for k, v in a.items()
                          if not (args.redact and k == "preview")}
                         for a in (result or {}).get("attempts") or []],
            "judgments": [{k: scrub_secrets(str(j.get(k))) if k == "judge_id" else j.get(k)
                           for k in ("kind", "judge_id", "verdict", "downgraded")}
                          for j in (report.get("evidence") or {}).get("judgments", [])],
            "judge_error": free_text(report.get("judge_error"), seen),
            "quality": (result or {}).get("quality"),
            "reason": free_text((result or {}).get("reason"), seen),
            "error": free_text(error, seen),
            "seconds": round(time.monotonic() - started, 1),
            "calls": [{**c, "answers": [shield(a) for a in c["answers"]]} for c in writer.log + judge.log],
        })
        print(f"{case['id']}: {rows[-1]['outcome']} ({rows[-1]['final_status']})", flush=True)
        save()

    save()
    print("report:", path.relative_to(ROOT).as_posix())
    return 0 if all(r["error"] is None for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
