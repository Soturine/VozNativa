#!/usr/bin/env python3
"""Prospective benchmark ptbr-bench-v3 (v0.5.0 CP7).

Arms, cases and instruments come from the frozen manifest
(benchmarks/manifests/ptbr-bench-v3.json); the runner refuses to start if the
cases changed. Prompt and skill arms send the same model the same text through
scripts/bench_model_wrapper.py; engine arms run rewrite() from a worktree at
their commit (or from this checkout) with the case's hints, including the
requested region. Every output is scored with the same v0.5.0 instruments and
classified on separate outcome axes (voznativa.benchmark.outcome_axes):
delivery, semantic safety, task, destination, regional behaviour, pending
evaluation, human preference (NOT_RUN), cost and latency.

    python scripts/bench_v3.py --manifest benchmarks/manifests/ptbr-bench-v3.json \
        --claude PATH_TO_CLAUDE --model claude-sonnet-5-5 --budget-usd 15

The first complete run is the official result. ``--out-dir`` writes elsewhere
(the harness test uses it with a fake model; such runs are never official).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import bench_v2 as v2  # noqa: E402
from scripts.bench_skill_only import FINAL, ONE_LINE, SKILL_TASK, fetch_skill  # noqa: E402
from voznativa.benchmark import load_cases, outcome_axes, summarize_axes  # noqa: E402
from voznativa.compare import compare  # noqa: E402
from voznativa.engine import parse_candidate  # noqa: E402
from voznativa.region import inspect as region_inspect  # noqa: E402
from voznativa.regional import activate, forms_in, introduced_forms, load_packs, referent_swaps  # noqa: E402
from voznativa.router import route  # noqa: E402

ENGINE_HINTS = frozenset({"channel", "register", "audience", "region", "region_strength"})


def regional_fields(case: dict, output: str) -> dict:
    """What the output did regionally, judged by the v0.5.0 instruments for
    every arm: forms or E0 markers it added without a licensing activation,
    referent-changing swaps, and whether a pack suggestion appears."""
    hints = case.get("hints") or {}
    original = case["text"]
    context = route(original, genre=case["genre"], region=hints.get("region"),
                    region_strength=float(hints.get("region_strength") or 0.0))
    activation = activate(context, original)
    added = [a["form"] for a in introduced_forms(original, output, activation)]
    before, after = region_inspect(original)["markers"], region_inspect(output)["markers"]
    added += sorted(m for m in after if m not in before)
    suggested = {f["suggest"] for f in activation["features"] if f.get("suggest")}
    used = any(form in forms_in(output, feature) for pack in load_packs() for feature in pack["features"]
               for form in suggested)
    return {"regional_introduced": added, "regional_swaps": referent_swaps(original, output),
            "regional_suggestion_used": used, "regional_activation": activation["status"]}


def run_arm(arm: str, spec, case: dict, skills: dict, checkouts: dict, env: dict, spend: v2.Spend) -> dict:
    text, request = case["text"], case.get("request", "")
    tag = f"{arm}:{case['id']}"
    raw = None
    started = datetime.now(timezone.utc)
    if spec == "original":
        output = text
    elif spec == "one_line":
        output = parse_candidate(v2.ask(f"{ONE_LINE} {request} {FINAL}\n\n{text}".replace("  ", " "), tag, env, spend),
                                 text)[0]
    elif arm in skills:
        output = parse_candidate(v2.ask(f"<skill>\n{skills[arm][0]}\n</skill>\n\n{SKILL_TASK} {request} {FINAL}\n\n{text}",
                                        tag, env, spend), text)[0]
    elif arm in checkouts:
        output, raw = v2.engine(checkouts[arm], case, tag, env, spend, hint_keys=ENGINE_HINTS)
    else:
        raise ValueError(f"unknown arm {arm}")
    seconds = (datetime.now(timezone.utc) - started).total_seconds()
    return {"arm": arm, "id": case["id"], "kind": case["kind"], "output": output, "raw": raw,
            "cost_usd": round(spend.total(tag), 4), "seconds": round(seconds, 1)}


def score(case: dict, output: str, arm: str, env: dict, spend: v2.Spend) -> dict:
    row = v2.score(case, output, arm, env, spend)
    row.update(regional_fields(case, output))
    return row


def summarize(rows: list[dict], cases: dict) -> dict:
    out = {}
    for arm in sorted({r["arm"] for r in rows}):
        arm_rows = [r for r in rows if r["arm"] == arm]
        out[arm] = summarize_axes([outcome_axes(cases[r["id"]], r) for r in arm_rows])
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--claude", required=True, help="model CLI path, or a JSON argv list")
    parser.add_argument("--model", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--budget-usd", type=float, default=15.0)
    parser.add_argument("--arms")
    parser.add_argument("--cases", help="comma-separated case ids (only for harness checks; never official)")
    parser.add_argument("--out-dir", help="write the run here instead of benchmarks/runs (not official)")
    args = parser.parse_args(argv)

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cases_path = ROOT / manifest["cases_file"]
    sha = hashlib.sha256(cases_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if sha != manifest["cases_sha256"]:
        raise SystemExit("cases changed after freezing; refusing to run")
    official = not (args.out_dir or args.cases or args.arms)
    if official and subprocess.run(["git", "status", "--porcelain", "voznativa", "scripts"], cwd=ROOT,
                                   capture_output=True, text=True).stdout.strip():
        raise SystemExit("the current-checkout arm runs this code: commit first so the run names it")
    cases = load_cases(cases_path)
    if args.cases:
        wanted = set(args.cases.split(","))
        cases = [c for c in cases if c["id"] in wanted]
    by_id = {c["id"]: c for c in cases}
    arms = manifest["arms"] if not args.arms else {a: manifest["arms"][a] for a in args.arms.split(",")}
    skills = {name: fetch_skill(spec, ROOT / "benchmarks" / ".cache")
              for name, spec in arms.items() if isinstance(spec, dict) and spec.get("repo")}

    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "benchmarks" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"{manifest['benchmark']}-{stamp}.json"
    log = out_path.with_suffix(".costs.jsonl")
    spend = v2.Spend(log, args.budget_usd)
    env = dict(os.environ, VN_CLAUDE=args.claude, VN_MODEL=args.model, VN_COST_LOG=str(log))
    worktrees, checkouts = [], {}
    for name, spec in arms.items():
        if isinstance(spec, dict) and spec.get("engine_commit"):
            tree = Path(tempfile.mkdtemp(prefix="vn-arm-")) / "wt"
            subprocess.run(["git", "worktree", "add", "-q", "--detach", str(tree), spec["engine_commit"]], cwd=ROOT,
                           check=True)
            worktrees.append(tree)
            checkouts[name] = tree
        elif isinstance(spec, dict) and spec.get("engine") == "checkout":
            checkouts[name] = ROOT
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rows, lock = [], threading.Lock()

    def save(final=False):
        report = {"kind": "voznativa.benchmark_v3", "manifest": manifest, "cases_sha256": sha, "run_at": stamp,
                  "official": official, "model": args.model, "voznativa_commit": head,
                  "skills_fetched_sha256": {k: v[1] for k, v in skills.items()}, "budget_usd": args.budget_usd,
                  "spent_usd": round(spend.total(), 3), "complete": final,
                  "summary": summarize(rows, by_id), "rows": rows}
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    def task(arm, case):
        spec = arms[arm] if not isinstance(arms[arm], dict) else arms[arm].get("kind", "skill")
        try:
            row = run_arm(arm, spec, case, skills, checkouts, env, spend)
            row["score"] = score(case, row["output"], arm, env, spend)
        except Exception as error:  # recorded, never hidden: counts as a system failure
            row = {"arm": arm, "id": case["id"], "kind": case["kind"], "error": f"{type(error).__name__}: {error}"[:400]}
        with lock:
            rows.append(row)
            save()

    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for arm in arms:
                for case in cases:
                    pool.submit(task, arm, case)
        save(final=not any("error" in r for r in rows))
    finally:
        for tree in worktrees:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT)
    print(json.dumps(summarize(rows, by_id), ensure_ascii=False, indent=2))
    print("report:", out_path.as_posix(), "| spent USD:", round(spend.total(), 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
