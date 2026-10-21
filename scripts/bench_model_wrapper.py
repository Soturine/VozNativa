#!/usr/bin/env python3
"""Claude Code CLI as a plain model for benchmark runs (v0.4.0 M4).

Reads the prompt on stdin, calls the CLI with tools off, no MCP servers, no
session persistence and JSON output, in an empty temporary directory;
prints only the answer text and appends cost and latency to the JSONL file
in VN_COST_LOG. Every arm of ptbr-bench-v2, including the VozNativa engine
arms that run as subprocesses from their own checkouts, goes through this
wrapper, so all of them see the same model under the same conditions.

    VN_CLAUDE=path/to/claude VN_MODEL=claude-sonnet-5-5 VN_COST_LOG=costs.jsonl \
        python scripts/bench_model_wrapper.py < prompt.txt
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time


def main() -> int:
    prompt = sys.stdin.buffer.read().decode("utf-8")
    argv = [os.environ["VN_CLAUDE"], "-p", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
            "--model", os.environ.get("VN_MODEL", "claude-sonnet-5-5"), "--output-format", "json"]
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="vn-bench-") as workdir:
        done = subprocess.run(argv, input=prompt.encode("utf-8"), capture_output=True, cwd=workdir,
                              timeout=float(os.environ.get("VN_TIMEOUT", "400")))
    seconds = round(time.monotonic() - start, 2)
    if done.returncode != 0:
        sys.stderr.write(done.stderr.decode("utf-8", "replace")[:500])
        return done.returncode
    data = json.loads(done.stdout.decode("utf-8"))
    log = os.environ.get("VN_COST_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"tag": os.environ.get("VN_TAG"), "cost_usd": float(data.get("total_cost_usd") or 0),
                                     "seconds": seconds, "prompt_chars": len(prompt),
                                     "is_error": bool(data.get("is_error"))}) + "\n")
    if data.get("is_error"):
        sys.stderr.write(str(data.get("result"))[:500])
        return 1
    sys.stdout.buffer.write((data.get("result") or "").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
