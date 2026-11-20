#!/usr/bin/env python3
"""One real host session (Claude Code, ``claude -p``) with the VozNativa Skill installed in a fresh project.

The Skill is installed the way a user installs a project Skill: ``<project>/.claude/skills/voznativa/`` with
``SKILL.md``, ``scripts/`` (CLI wrapper), the ``voznativa`` package and ``references/``. The text goes into
``texto.txt``; the request names the goal, not the tool (unless ``--explicit``). The session's event stream is
kept so that Skill discovery, every command the agent ran and the final answer are evidence, not claims.

    python scripts/v0105_host_session.py --skill-src <checkout> --text t.txt --request "..." \
        --model haiku --workdir <tmp> --out session.json [--explicit] [--no-skill]

Tools are limited to Read, Write, Skill and ``python`` commands inside the project. Nothing outside the
project is written; the original text never reaches the repository.
"""
from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import time
from pathlib import Path

from install_skill import install_skill


def run(args) -> dict:
    project = Path(args.workdir).resolve()
    project.mkdir(parents=True, exist_ok=True)
    if any(project.iterdir()):
        raise FileExistsError("o diretório da sessão precisa estar vazio")
    skill = install_skill(Path(args.skill_src), project, "claude") if not args.no_skill else None
    (project / "texto.txt").write_text(Path(args.text).read_text(encoding="utf-8"), encoding="utf-8")
    request = args.request + ("\n\nUse a skill voznativa." if args.explicit else "")
    request += "\n\nO texto está em texto.txt. Grave a versão final em final.txt (igual ao original se não houver o que mudar)."
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_CODE_", "CLAUDECODE"))}
    cmd = ["claude", "-p", request, "--model", args.model, "--output-format", "stream-json", "--verbose",
           "--allowedTools", "Read", "Write", "Edit", "Skill", "Bash(python:*)", "Bash(python3:*)", "Bash(py:*)",
           "--max-turns", str(args.max_turns)]
    if getattr(args, "max_budget_usd", None) is not None:
        cmd += ["--max-budget-usd", str(args.max_budget_usd)]
    started = time.time()
    done = subprocess.run(cmd, cwd=project, capture_output=True, env=env, timeout=args.timeout)
    seconds = round(time.time() - started, 1)
    events = []
    for line in done.stdout.decode("utf-8", "replace").splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    tools, skill_invoked, final = [], False, None
    by_id = {}
    for ev in events:
        if ev.get("type") == "user":
            # tool results: whether the host ran the call, refused it (permission) or it failed
            for block in (ev.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("tool_use_id") in by_id:
                    body = block.get("content")
                    text = body if isinstance(body, str) else " ".join(
                        c.get("text", "") for c in body or [] if isinstance(c, dict))
                    t = by_id[block["tool_use_id"]]
                    t["error"] = bool(block.get("is_error"))
                    if block.get("is_error"):
                        # head of the error only, with the session's project folder masked (local path)
                        t["error_head"] = text.replace(str(project), "<project>").replace(
                            str(project).replace("\\", "/"), "<project>")[:220]
                    t["denied"] = bool(block.get("is_error")) and bool(re.search(
                        r"permission|not allowed|requires approval|haven't granted|denied", text, re.I))
        if ev.get("type") == "assistant":
            for block in (ev.get("message") or {}).get("content") or []:
                if block.get("type") == "tool_use":
                    name, inp = block.get("name"), block.get("input") or {}
                    if name == "Skill":
                        skill_invoked = True
                    tools.append({"tool": name, "input": (inp.get("command") or inp.get("skill") or
                                                          inp.get("file_path") or "")[:300]})
                    by_id[block.get("id")] = tools[-1]
        if ev.get("type") == "result":
            final = ev
    out_file = project / "final.txt"
    # a call the host refused never ran: count only the ones that did (v0.10.5 continuation)
    cli_calls = [t["input"] for t in tools if t["tool"] == "Bash" and "voznativa_cli.py" in t["input"]
                 and "error" in t and not t.get("denied")]
    cli_denied = [t["input"] for t in tools if t["tool"] == "Bash" and "voznativa_cli.py" in t["input"] and t.get("denied")]
    return {
        "kind": "voznativa.host_session", "host": "claude-code", "host_version": subprocess.run(
            ["claude", "--version"], capture_output=True, text=True).stdout.strip(),
        "model": args.model, "explicit_request": args.explicit, "skill_installed": skill is not None,
        "skill_sha256": _tree_hash(skill) if skill else None,
        "skill_invoked": skill_invoked, "cli_calls": cli_calls, "cli_denied": cli_denied, "tools": tools,
        "exit_code": done.returncode, "seconds": seconds,
        "cost_usd": (final or {}).get("total_cost_usd"), "turns": (final or {}).get("num_turns"),
        "result_text": ((final or {}).get("result") or "")[:4000],
        "final_written": out_file.exists(),
        "final_text": out_file.read_text(encoding="utf-8") if out_file.exists() else None,
        "stderr_tail": done.stderr.decode("utf-8", "replace")[-600:],
    }


def _tree_hash(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    for p in sorted(path.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(path)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--skill-src", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--request", required=True)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--explicit", action="store_true")
    ap.add_argument("--no-skill", action="store_true")
    ap.add_argument("--max-turns", type=int, default=30)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--max-budget-usd", type=float)
    args = ap.parse_args(argv)
    record = run(args)
    Path(args.out).write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ("skill_invoked", "exit_code", "seconds", "cost_usd", "turns",
                                             "final_written")} | {"cli_calls": len(record["cli_calls"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
