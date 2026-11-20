#!/usr/bin/env python3
"""Command provider for experiments: ``claude -p`` that prints the answer and logs the cost.

Reads the prompt on stdin (as ``voznativa rewrite --cmd`` sends it), runs ``claude -p --output-format json``
with the model given and no tools, prints the answer text, and appends ``{"cost_usd", "model", "seconds"}``
to the JSONL file named by ``VN_COST_LOG`` (when set). The cost is the ``total_cost_usd`` the CLI reports
(API-equivalent price), not an invoice.

    voznativa rewrite t.txt --cmd '["python", "scripts/experiments/claude_cost_provider.py", "haiku"]'
"""
import json
import os
import subprocess
import sys
import time


def main() -> int:
    model = sys.argv[1] if len(sys.argv) > 1 else "haiku"
    prompt = sys.stdin.buffer.read().decode("utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_CODE_", "CLAUDECODE"))}
    started = time.time()
    done = subprocess.run(["claude", "-p", "--model", model, "--output-format", "json", "--tools", ""],
                          input=prompt.encode("utf-8"), capture_output=True, env=env, timeout=600)
    try:
        data = json.loads(done.stdout.decode("utf-8"))
    except ValueError:
        sys.stderr.write(done.stderr.decode("utf-8", "replace")[-500:])
        return 1
    log = os.environ.get("VN_COST_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"cost_usd": data.get("total_cost_usd"), "model": model,
                                 "seconds": round(time.time() - started, 1), "is_error": data.get("is_error")}) + "\n")
    if data.get("is_error"):
        sys.stderr.write(str(data.get("result"))[:500])
        return 1
    sys.stdout.buffer.write((data.get("result") or "").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
