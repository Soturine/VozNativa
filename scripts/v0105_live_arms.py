#!/usr/bin/env python3
"""Live arms of the v0.10.5 fire trial: the same task, model and text through four arms, repeated.

Tasks: ``evals/v0105/live_tasks.json`` (frozen before any product change); texts from ``items.jsonl`` outside
the repository (only public-domain and CC BY items are sent to the model). Arms, in a shuffled order per
(task, repetition) with a fixed seed:

* ``A1_direct``  — one ``claude -p`` call: the request and the text, nothing else;
* ``A2_skill``   — a real Claude Code session with the VozNativa Skill of the version under test installed in a
  fresh project; the request does not name the Skill (``scripts/v0105_host_session.py``);
* ``A3_engine``  — ``voznativa rewrite`` of that version, the request passed as the open attribute ``pedido``
  plus the task's attributes and editorial mode;
* ``A3_bare``    — the same engine without attributes and with the knowledge block removed (ablation).

Every arm uses the same model (default Haiku). Outputs and costs are written per run under ``--out-dir`` (outside
the repository). Nothing here judges quality: that is ``scripts/v0105_judge.py``.

    python scripts/v0105_live_arms.py --version-root <checkout> --label v0100 --items <items.jsonl> \
        --out-dir <dir> [--split development] [--reps 3] [--only T01]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVIDER = ROOT / "scripts" / "experiments" / "claude_cost_provider.py"
DIRECT = ("{request}\n\nResponda só com o texto final, sem comentários. Se o texto já estiver adequado ao pedido, "
          "devolva-o igual.\n\nTEXTO:\n{text}")
BARE = ("import sys; from voznativa import knowledge as k; "
        "k.for_text = lambda *a, **kw: {'selected': [], 'skipped': [], 'used_chars': 0, 'budget_chars': 0, "
        "'registry_errors': []}; from voznativa.cli import main; sys.exit(main(sys.argv[1:]))")
ARMS = ("A1_direct", "A2_skill", "A3_engine", "A3_bare")
# v0.10.5 continuation: a valid factorial ablation. Every variant gets the SAME request (the user's words as the
# open attribute ``pedido``) and the same mode; only the other attributes and the knowledge block change.
# (A3_bare, kept for the frozen development data, removed the request too, so it measured the request.)
ABLATION = {"A3_noattrs": (False, True), "A3_noknow": (True, False), "A3_neither": (False, False)}
ALL_ARMS = ARMS + tuple(ABLATION)
NO_KNOWLEDGE = ("import sys; from voznativa import knowledge as k; "
                "k.for_text = lambda *a, **kw: {'selected': [], 'skipped': [], 'used_chars': 0, 'budget_chars': 0, "
                "'registry_errors': []}; from voznativa.cli import main; sys.exit(main(sys.argv[1:]))")
MAX_PROVIDER_FAILURES = 3


def provider_failed(rec: dict) -> bool:
    """True when the run never reached the model (quota, auth, network): not a result of the arm.

    Such a run is kept under ``failed/`` for the record and is retried on resume; it never becomes an output.
    """
    if rec.get("outcome") == "provider_error":
        return True
    if rec["arm"] == "A1_direct":
        return rec.get("exit_code") != 0 or not rec.get("output")
    if rec["arm"] == "A2_skill":
        return not rec.get("final_written") and not rec.get("tools") and not rec.get("cost_usd")
    return False


def _env(cost_log: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_CODE_", "CLAUDECODE"))}
    env["VN_COST_LOG"] = str(cost_log)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _costs(path: Path) -> tuple[float, int]:
    if not path.exists():
        return 0.0, 0
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return round(sum(r.get("cost_usd") or 0 for r in rows), 6), len(rows)


def direct(task, text, model, work: Path) -> dict:
    log = work / "cost.jsonl"
    started = time.time()
    done = subprocess.run([sys.executable, str(PROVIDER), model], input=DIRECT.format(request=task["request"],
                          text=text).encode("utf-8"), capture_output=True, env=_env(log), timeout=900)
    cost, calls = _costs(log)
    return {"output": done.stdout.decode("utf-8", "replace").strip() or None, "exit_code": done.returncode,
            "cost_usd": cost, "calls": calls, "seconds": round(time.time() - started, 1)}


def engine(task, text_file: Path, model, root: Path, work: Path, bare: bool, attrs_on: bool = True,
           knowledge_on: bool = True) -> dict:
    log = work / "cost.jsonl"
    cmd = json.dumps([sys.executable, str(PROVIDER), model])
    args = ["rewrite", str(text_file), "--cmd", cmd, "--provider-env", "minimal", "--provider-env-allow",
            "VN_COST_LOG", "--provider-env-allow", "PYTHONIOENCODING", "--attempts", "2"]
    if task.get("engine_mode"):
        args += ["--mode", task["engine_mode"]]
    if not bare:
        attrs = dict(task["attrs"] if attrs_on else {}, pedido=task["request"])
        for key, value in attrs.items():
            args += ["--attr", f"{key}={value}"]
    head = ([sys.executable, "-c", BARE] if bare else [sys.executable, "-c", NO_KNOWLEDGE] if not knowledge_on
            else [sys.executable, "-m", "voznativa"])
    started = time.time()
    done = subprocess.run(head + args, cwd=root, capture_output=True, env=_env(log), timeout=1800)
    cost, calls = _costs(log)
    try:
        result = json.loads(done.stdout.decode("utf-8"))
    except ValueError:
        return {"output": None, "exit_code": done.returncode, "cost_usd": cost, "calls": calls,
                "seconds": round(time.time() - started, 1),
                "error": done.stderr.decode("utf-8", "replace")[-600:]}
    return {"output": result.get("text"), "outcome": result.get("outcome"), "exit_code": done.returncode,
            "status": (result.get("report") or {}).get("status"), "cost_usd": cost, "calls": calls,
            "knowledge": [k["id"] for k in (result.get("knowledge") or {}).get("selected", [])],
            "seconds": round(time.time() - started, 1)}


def skill(task, text_file: Path, model, root: Path, work: Path) -> dict:
    session_out = work / "session.json"
    done = subprocess.run([sys.executable, str(ROOT / "scripts" / "v0105_host_session.py"), "--skill-src", str(root),
                           "--text", str(text_file), "--request", task["request"], "--model", model,
                           "--workdir", str(work / "project"), "--out", str(session_out)],
                          capture_output=True, env=_env(work / "unused.jsonl"), timeout=1800)
    if not session_out.exists():
        return {"output": None, "exit_code": done.returncode, "error": done.stderr.decode("utf-8", "replace")[-600:]}
    s = json.loads(session_out.read_text(encoding="utf-8"))
    return {"output": (s.get("final_text") or "").strip() or None, "exit_code": s["exit_code"],
            "skill_invoked": s["skill_invoked"], "cli_calls": s["cli_calls"], "tools": [t["tool"] for t in s["tools"]],
            "cost_usd": s.get("cost_usd"), "turns": s.get("turns"), "seconds": s["seconds"],
            "final_written": s["final_written"], "answer": (s.get("result_text") or "")[:1500]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version-root", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--items", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--split", default="development")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--only", action="append")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--tasks-file", default=str(ROOT / "evals/v0105/live_tasks.json"))
    args = ap.parse_args(argv)
    root = Path(args.version_root).resolve()
    items = {json.loads(x)["id"]: json.loads(x) for x in Path(args.items).expanduser().read_text(
        encoding="utf-8").splitlines() if x.strip()}
    tasks = [t for t in json.loads(Path(args.tasks_file).read_text(encoding="utf-8"))["tasks"]
             if t["split"] == args.split and (not args.only or t["task"] in args.only)]
    out_dir = Path(args.out_dir).expanduser() / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    arms = [a for a in ALL_ARMS if a in args.arms.split(",")]
    failures = 0
    for task in tasks:
        item = items[task["item"]]
        assert item["rights"] in ("public_domain", "cc_by", "model_api_ok"), "only API-eligible texts go to a provider"
        for rep in range(1, args.reps + 1):
            order = arms[:]
            random.Random(f"{task['task']}-{rep}").shuffle(order)
            for arm in order:
                target = out_dir / f"{task['task']}-r{rep}-{arm}.json"
                if target.exists():
                    continue          # resumable
                with tempfile.TemporaryDirectory(prefix="vn-fire-") as tmp:
                    work = Path(tmp)
                    text_file = work / "texto.txt"
                    text_file.write_text(item["text"], encoding="utf-8")
                    if arm == "A1_direct":
                        rec = direct(task, item["text"], args.model, work)
                    elif arm == "A2_skill":
                        rec = skill(task, text_file, args.model, root, work)
                    elif arm in ABLATION:
                        rec = engine(task, text_file, args.model, root, work, bare=False,
                                     attrs_on=ABLATION[arm][0], knowledge_on=ABLATION[arm][1])
                    else:
                        rec = engine(task, text_file, args.model, root, work, bare=arm == "A3_bare")
                rec.update({"task": task["task"], "rep": rep, "arm": arm, "label": args.label, "model": args.model,
                            "item": task["item"], "order": order.index(arm)})
                if provider_failed(rec):
                    failures += 1
                    (out_dir / "failed").mkdir(exist_ok=True)
                    (out_dir / "failed" / f"{target.stem}-{int(time.time())}.json").write_text(
                        json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
                    print(task["task"], rep, arm, "PROVIDER_FAILED (not a result; retried on resume)", flush=True)
                    if failures >= MAX_PROVIDER_FAILURES:
                        print("stopping: provider unavailable", flush=True)
                        return 75
                    continue
                failures = 0
                target.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
                print(task["task"], rep, arm, {k: rec.get(k) for k in ("exit_code", "outcome", "cost_usd", "calls",
                                                                          "skill_invoked", "seconds")}, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
