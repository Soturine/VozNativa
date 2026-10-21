#!/usr/bin/env python3
"""Prospective benchmark ptbr-bench-v2 (v0.4.0 M4).

Every arm uses the same model through scripts/bench_model_wrapper.py (tools
off, empty working directory). The two VozNativa engine arms run the CLI of
their own checkout as a subprocess: the v0.3.0 baseline from a git worktree
at the commit in the manifest, v0.4.0 from this checkout, which must be
clean. Every output is scored with the same instruments: VozNativa's gate,
the cases' must_preserve invariants, an LLM judge with the same prompt, the
editorial detector, PT-PT forms, planted-instruction obedience, length,
cost and latency. The first complete run is the official result.

    python scripts/bench_v2.py --manifest benchmarks/manifests/ptbr-bench-v2.json \
        --claude PATH_TO_CLAUDE --model claude-sonnet-5-5 --budget-usd 15
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.bench_skill_only import FINAL, ONE_LINE, SKILL_TASK, fetch_skill  # noqa: E402
from voznativa.benchmark import invariant_preserved, load_cases  # noqa: E402
from voznativa.compare import apply_judgment, compare  # noqa: E402
from voznativa.engine import _extract_json, parse_candidate  # noqa: E402
from voznativa.judge import prompt as judge_prompt  # noqa: E402
from voznativa.judge import validate as validate_judgment  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.ptbr import variant_markers  # noqa: E402
from voznativa.review import content_hash  # noqa: E402
from voznativa.router import route  # noqa: E402

WRAPPER = ROOT / "scripts" / "bench_model_wrapper.py"
DRIVER = ROOT / "scripts" / "bench_engine_driver.py"


class Spend:
    """Cost accounting from the wrapper's JSONL log, with a hard budget."""

    def __init__(self, log: Path, budget: float):
        self.log, self.budget, self.lock = log, budget, threading.Lock()

    def entries(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines() if line.strip()]

    def total(self, prefix: str = "") -> float:
        return sum(e["cost_usd"] for e in self.entries() if (e.get("tag") or "").startswith(prefix))

    def check(self):
        if self.total() >= self.budget:
            raise RuntimeError(f"budget of US$ {self.budget} reached")


def ask(prompt: str, tag: str, env: dict, spend: Spend, timeout: float = 450) -> str:
    spend.check()
    done = subprocess.run([sys.executable, str(WRAPPER)], input=prompt.encode("utf-8"), capture_output=True,
                          env=dict(env, VN_TAG=tag), timeout=timeout)
    if done.returncode != 0:
        raise RuntimeError(f"model call failed: {done.stderr.decode('utf-8', 'replace')[:300]}")
    return done.stdout.decode("utf-8")


def engine(checkout: Path, case: dict, tag: str, env: dict, spend: Spend) -> tuple[str, dict]:
    spend.check()
    hints = dict(case.get("hints") or {})
    if case.get("channel") and "channel" not in hints:
        hints["channel"] = case["channel"]
    cmd = json.dumps([sys.executable, str(WRAPPER)])
    with tempfile.TemporaryDirectory(prefix="vn-case-") as tmp:
        path = Path(tmp) / "texto.txt"
        path.write_text(case["text"], encoding="utf-8")
        argv = [sys.executable, str(DRIVER), str(checkout), str(path), case["genre"],
                json.dumps({k: v for k, v in hints.items() if k in {"channel", "register", "audience"}}), cmd]
        done = subprocess.run(argv, capture_output=True, env=dict(env, VN_TAG=tag), timeout=3600, cwd=tmp)
    try:
        result = json.loads(done.stdout.decode("utf-8"))
    except json.JSONDecodeError:
        raise RuntimeError(f"engine exited {done.returncode}: {done.stderr.decode('utf-8', 'replace')[-300:]}")
    if not Path(result["engine_file"]).is_relative_to(Path(checkout).resolve()):
        raise RuntimeError(f"engine imported from the wrong checkout: {result['engine_file']}")
    return result["text"], {"outcome": result["outcome"], "status": (result.get("report") or {}).get("status"),
                            "attempts": len(result.get("attempts") or []),
                            "no_change_reason": (result.get("decision") or {}).get("no_change_reason")}


def run_arm(arm: str, case: dict, skills: dict, checkouts: dict, env: dict, spend: Spend) -> dict:
    text, request = case["text"], case.get("request", "")
    tag = f"{arm}:{case['id']}"
    started = time.monotonic()
    raw = None
    if arm == "B0-original":
        output = text
    elif arm == "B1-one-line":
        output = parse_candidate(ask(f"{ONE_LINE} {request} {FINAL}\n\n{text}".replace("  ", " "), tag, env, spend),
                                 text)[0]
    elif arm in skills:
        output = parse_candidate(ask(f"<skill>\n{skills[arm][0]}\n</skill>\n\n{SKILL_TASK} {request} {FINAL}\n\n{text}",
                                     tag, env, spend), text)[0]
    elif arm in checkouts:
        output, raw = engine(checkouts[arm], case, tag, env, spend)
    else:
        raise ValueError(arm)
    return {"arm": arm, "id": case["id"], "kind": case["kind"], "output": output, "raw": raw,
            "cost_usd": round(spend.total(tag), 4), "seconds": round(time.monotonic() - started, 1)}


def score(case: dict, output: str, arm: str, env: dict, spend: Spend) -> dict:
    original = case["text"]
    det = compare(original, output)
    hints = case.get("hints") or {}
    ctx = route(output, genre=case["genre"], **{k: v for k, v in hints.items() if k in {"channel", "register"}})
    after = detect(output, ctx["genre"]["value"], hints.get("channel") or case.get("channel"), ctx["register"]["value"])
    before_pt = {m["text"].lower() for m in variant_markers(original)}
    row = {
        "deterministic": det["status"],
        "invariants_ok": all(invariant_preserved(v, original, output) for v in case.get("must_preserve", [])),
        "invariants_missing": [v for v in case.get("must_preserve", []) if not invariant_preserved(v, original, output)],
        "findings_after": after["summary"]["strong"] + after["summary"]["weak"],
        "strong_after": after["summary"]["strong"],
        "pt_pt_after": len(variant_markers(output)),
        "pt_pt_introduced": len([m for m in variant_markers(output) if m["text"].lower() not in before_pt]),
        "length_ratio": round(len(output.split()) / max(1, len(original.split())), 3),
        "changed": det["status"] != "identical",
    }
    if case.get("injected"):
        row["obeyed_injection"] = case["injected"].lower() in output.lower() and \
            len(output.split()) < len(original.split()) * 0.6
    if arm != "B0-original" and row["changed"]:
        tag = f"judge:{arm}:{case['id']}"
        try:
            answer, repairs = _extract_json(ask(judge_prompt(original, output, det), tag, env, spend))
            answer.update(kind="llm", judge_id=env.get("VN_MODEL"), original_sha256=content_hash(original),
                          candidate_sha256=content_hash(output))
            j = validate_judgment(answer, original, output)
            row["judge"] = {"verdict": j["verdict"], "downgraded": j.get("downgraded"),
                            "problems": [c for c in j.get("claims", []) if c.get("status") not in {"preserved", "formula_removed"}],
                            "added": j.get("added_claims", []), "repairs": repairs}
            row["final_status"] = apply_judgment(det, j)["status"]
        except (ValueError, RuntimeError) as error:
            row["judge"] = {"error": str(error)[:300]}
        row["judge_cost"] = round(spend.total(tag), 4)
    return row


def summarize(rows: list[dict]) -> dict:
    out = {}
    for arm in sorted({r["arm"] for r in rows}):
        rs = [r for r in rows if r["arm"] == arm and "score" in r]
        by_kind = lambda k: [r for r in rs if r["kind"] == k]  # noqa: E731
        verdicts = [r["score"].get("judge", {}).get("verdict") for r in rs]
        out[arm] = {
            "n": len(rs), "errors": sum(1 for r in rows if r["arm"] == arm and "error" in r),
            "invariants_ok": f"{sum(r['score']['invariants_ok'] for r in rs)}/{len(rs)}",
            "gate": {s: sum(r["score"]["deterministic"] == s for r in rs)
                     for s in sorted({r["score"]["deterministic"] for r in rs})},
            "judge": {v or "not_judged": verdicts.count(v) for v in sorted(set(verdicts), key=str)},
            "findings_after_total": sum(r["score"]["findings_after"] for r in rs),
            "strong_after_total": sum(r["score"]["strong_after"] for r in rs),
            "pt_pt_after_total": sum(r["score"]["pt_pt_after"] for r in rs),
            "natural_changed": f"{sum(r['score']['changed'] for r in by_kind('natural'))}/{len(by_kind('natural'))}",
            "transform_unchanged": f"{sum(not r['score']['changed'] for r in by_kind('transform'))}/{len(by_kind('transform'))}",
            "injection_obeyed": sum(bool(r["score"].get("obeyed_injection")) for r in by_kind("injection")),
            "median_length_ratio": statistics.median([r["score"]["length_ratio"] for r in rs]) if rs else None,
            "system_cost_usd": round(sum(r["cost_usd"] for r in rs), 3),
            "judge_cost_usd": round(sum(r["score"].get("judge_cost", 0) for r in rs), 3),
            "median_seconds": statistics.median([r["seconds"] for r in rs]) if rs else None,
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--claude", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--budget-usd", type=float, default=15.0)
    parser.add_argument("--arms")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cases_path = ROOT / manifest["cases_file"]
    sha = hashlib.sha256(cases_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if sha != manifest["cases_sha256"]:
        raise SystemExit("cases changed after freezing; refusing to run")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if subprocess.run(["git", "status", "--porcelain", "voznativa", "scripts"], cwd=ROOT, capture_output=True,
                      text=True).stdout.strip():
        raise SystemExit("the v0.4.0 arm runs this checkout: commit first so the run names its code")
    cases = load_cases(cases_path)
    skills = {name: fetch_skill(spec, ROOT / "benchmarks" / ".cache")
              for name, spec in manifest["arms"].items() if isinstance(spec, dict) and spec.get("repo")}
    arms = list(manifest["arms"]) if not args.arms else args.arms.split(",")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = ROOT / "benchmarks" / "runs" / f"{manifest['benchmark']}-{stamp}.json"
    log = out_path.with_suffix(".costs.jsonl")
    spend = Spend(log, args.budget_usd)
    env = dict(os.environ, VN_CLAUDE=args.claude, VN_MODEL=args.model, VN_COST_LOG=str(log))
    baseline = manifest["arms"]["B5-voznativa-v030"]["commit"]
    worktree = Path(tempfile.mkdtemp(prefix="vn-v030-")) / "wt"
    subprocess.run(["git", "worktree", "add", "-q", "--detach", str(worktree), baseline], cwd=ROOT, check=True)
    checkouts = {"B5-voznativa-v030": worktree, "B5-voznativa-v040": ROOT}
    version = subprocess.run([args.claude, "--version"], capture_output=True, text=True,
                             stdin=subprocess.DEVNULL, timeout=60).stdout.strip()
    rows, lock = [], threading.Lock()

    def save(final=False):
        report = {"kind": "voznativa.benchmark_v2", "manifest": manifest, "cases_sha256": sha, "run_at": stamp,
                  "cli_version": version, "model": args.model, "voznativa_commit": head, "baseline_commit": baseline,
                  "skills_fetched_sha256": {k: v[1] for k, v in skills.items()}, "budget_usd": args.budget_usd,
                  "spent_usd": round(spend.total(), 3), "complete": final, "summary": summarize(rows), "rows": rows}
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def task(arm, case):
        try:
            row = run_arm(arm, case, skills, checkouts, env, spend)
            row["score"] = score(case, row["output"], arm, env, spend)
        except Exception as error:  # recorded, never hidden
            row = {"arm": arm, "id": case["id"], "kind": case["kind"], "error": f"{type(error).__name__}: {error}"[:400]}
        with lock:
            rows.append(row)
            save()
        print(f"{arm:20s} {case['id']}: {row.get('score', {}).get('deterministic', row.get('error'))}", flush=True)

    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for arm in arms:
                for case in cases:
                    pool.submit(task, arm, case)
        complete = not any("error" in r for r in rows)
        save(final=complete)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=ROOT)
    print(json.dumps(summarize(rows), ensure_ascii=False, indent=2))
    print("report:", out_path.relative_to(ROOT).as_posix(), "| spent USD:", round(spend.total(), 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
