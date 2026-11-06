#!/usr/bin/env python3
"""Checkpoint harness: run commands without hiding exit codes, and push
only when the remote really has the commit.

Why: ``python -m unittest ... | tail`` and ``git push ... | tail`` report the
exit code of ``tail``. A failed suite or a rejected push then looks green.
This runner executes argv lists (no shell), records each step and stops at
the first failure; ``push`` succeeds only when ``git ls-remote`` shows the
local SHA on the remote branch.

    python scripts/checkpoint.py run --out rec.json -- python -m unittest discover -s evals
    python scripts/checkpoint.py steps plan.json --out rec.json   # [["argv", ...], ...]
    python scripts/checkpoint.py push dev/v0.7.0 --out push.json

Exit: the failing step's exit code (or 1 for a timeout / missing program);
``push``: 0 verified, 1 push failed, 4 pushed but the remote does not match.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXIT_REMOTE_MISMATCH = 4


def _tail(text: str, lines: int = 15) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def git(argv: list[str], cwd: Path = ROOT) -> tuple[int, str]:
    done = subprocess.run(["git", *argv], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", stdin=subprocess.DEVNULL)
    return done.returncode, (done.stdout or "").strip()


def revision(cwd: Path = ROOT) -> dict:
    code, sha = git(["rev-parse", "HEAD"], cwd)
    _, dirty = git(["status", "--porcelain"], cwd)
    return {"sha": sha if code == 0 else None, "dirty": bool(dirty)}


def run_step(argv: list[str], cwd: Path = ROOT, timeout: float = 3600.0) -> dict:
    """One argv, captured. Never raises for the command's own failure."""
    started = time.monotonic()
    record = {"argv": argv, "cwd": str(cwd), "timeout_s": timeout}
    try:
        done = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL,
                              env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"))
        out, err, code = done.stdout, done.stderr, done.returncode
    except FileNotFoundError as error:
        out, err, code = b"", str(error).encode(), None
        record["error"] = "program not found"
    except subprocess.TimeoutExpired as error:
        out, err, code = error.stdout or b"", error.stderr or b"", None
        record["error"] = "timeout"
    stdout, stderr = out.decode("utf-8", "replace"), err.decode("utf-8", "replace")
    record.update(exit_code=code, seconds=round(time.monotonic() - started, 2),
                  stdout_sha256=hashlib.sha256(out).hexdigest(), stderr_sha256=hashlib.sha256(err).hexdigest(),
                  stdout_tail=_tail(stdout), stderr_tail=_tail(stderr))
    return record


def step_failed(step: dict) -> bool:
    return step.get("exit_code") != 0


def run_steps(steps: list[list[str]], cwd: Path = ROOT, timeout: float = 3600.0) -> dict:
    """Run in order; stop at the first failure. The overall exit code is the
    failing step's (1 when it has none: timeout, program missing)."""
    records, code = [], 0
    for argv in steps:
        rec = run_step(argv, cwd, timeout)
        records.append(rec)
        if step_failed(rec):
            code = rec["exit_code"] if isinstance(rec["exit_code"], int) and rec["exit_code"] != 0 else 1
            break
    return {"kind": "voznativa.checkpoint_run", "schema_version": 1,
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "revision": revision(cwd), "environment": {"python": platform.python_version(),
                                                       "platform": platform.platform(terse=True)},
            "steps": records, "not_run": [s for s in steps[len(records):]], "exit_code": code,
            "status": "PASS" if code == 0 else "FAIL"}


def verify_push(branch: str, remote: str = "origin", cwd: Path = ROOT) -> dict:
    """Push ``branch`` and compare the remote ref with the local SHA."""
    code_local, local = git(["rev-parse", f"refs/heads/{branch}"], cwd)
    if code_local != 0:
        return {"status": "FAIL", "exit_code": 1, "reason": f"no local branch {branch}"}
    push = run_step(["git", "push", remote, branch], cwd, timeout=600)
    result = {"branch": branch, "remote": remote, "local_sha": local, "push": push}
    if step_failed(push):
        return dict(result, status="FAIL", exit_code=1, reason="git push exited non-zero")
    code_ls, listing = git(["ls-remote", remote, f"refs/heads/{branch}"], cwd)
    remote_sha = listing.split()[0] if code_ls == 0 and listing else None
    result["remote_sha"] = remote_sha
    if remote_sha != local:
        return dict(result, status="FAIL", exit_code=EXIT_REMOTE_MISMATCH,
                    reason="push exited 0 but the remote branch does not point at the local commit")
    return dict(result, status="PASS", exit_code=0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out")
    r.add_argument("--timeout", type=float, default=3600.0)
    r.add_argument("command", nargs=argparse.REMAINDER)
    s = sub.add_parser("steps")
    s.add_argument("plan")
    s.add_argument("--out")
    s.add_argument("--timeout", type=float, default=3600.0)
    p = sub.add_parser("push")
    p.add_argument("branch")
    p.add_argument("--remote", default="origin")
    p.add_argument("--out")
    args = parser.parse_args(argv)
    if args.cmd == "run":
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        if not command:
            parser.error("run needs a command after --")
        report = run_steps([command], timeout=args.timeout)
    elif args.cmd == "steps":
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        if not isinstance(plan, list) or not all(isinstance(x, list) and x for x in plan):
            parser.error("plan must be a JSON list of non-empty argv lists")
        report = run_steps(plan, timeout=args.timeout)
    else:
        report = verify_push(args.branch, args.remote)
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {k: report.get(k) for k in ("status", "exit_code", "reason", "local_sha", "remote_sha") if k in report}
    print(json.dumps(summary, ensure_ascii=False))
    return int(report["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
