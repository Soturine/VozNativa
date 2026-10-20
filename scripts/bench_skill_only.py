#!/usr/bin/env python3
"""Skill-only benchmark runner (v0.3.0 M4.2).

Runs the arms fixed in benchmarks/manifests/<name>.json over the frozen
cases with the same model and wrapper, then scores every output with the
same instruments: VozNativa's deterministic gate, the must_preserve
invariants, editorial findings, length, latency, cost and an LLM judge
(same prompt for every arm). Detectors are not used.

    python scripts/bench_skill_only.py --manifest benchmarks/manifests/ptbr-bench-v1.json \
        --claude PATH_TO_CLAUDE --model claude-sonnet-5-5

The report is written after every result to benchmarks/runs/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.benchmark import invariant_preserved, load_cases  # noqa: E402
from voznativa.compare import apply_judgment, compare  # noqa: E402
from voznativa.contract import resolve  # noqa: E402
from voznativa.engine import _extract_json, build_prompt, parse_candidate, rewrite  # noqa: E402
from voznativa.judge import prompt as judge_prompt  # noqa: E402
from voznativa.judge import validate as validate_judgment  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.references import select  # noqa: E402
from voznativa.review import content_hash  # noqa: E402
from voznativa.router import route  # noqa: E402

FINAL = "Responda apenas com o texto final entre <final> e </final>."
ONE_LINE = "Reescreva para soar mais natural, sem alterar o significado."
SKILL_TASK = "Humanize este texto em português brasileiro, seguindo a skill acima."


class Model:
    """Claude Code CLI as a plain model: no tools, empty working directory,
    JSON output so cost and latency are recorded."""

    def __init__(self, claude: str, model: str, timeout: float = 400):
        self.argv = [claude, "-p", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
                     "--model", model, "--output-format", "json"]
        self.timeout, self.id = timeout, f"claude-cli:{model}"
        self.lock, self.cost, self.calls = threading.Lock(), 0.0, 0

    def ask(self, prompt: str) -> tuple[str, float, float]:
        start = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="vn-bench-") as workdir:
            done = subprocess.run(self.argv, input=prompt.encode("utf-8"), capture_output=True,
                                  timeout=self.timeout, cwd=workdir)
        seconds = time.monotonic() - start
        if done.returncode != 0:
            raise RuntimeError(done.stderr.decode("utf-8", "replace")[:300])
        data = json.loads(done.stdout.decode("utf-8"))
        cost = float(data.get("total_cost_usd") or 0)
        with self.lock:
            self.cost += cost
            self.calls += 1
        return data.get("result", ""), cost, seconds

    # Provider protocol for the VozNativa engine arm
    def generate(self, prompt: str, n: int = 1) -> list[str]:
        return [self.ask(prompt)[0] for _ in range(n)]


def fetch_skill(arm: dict, cache: Path) -> tuple[str, str]:
    repo = arm["repo"].removeprefix("https://github.com/")
    url = f"https://raw.githubusercontent.com/{repo}/{arm['commit']}/{arm['file']}"
    target = cache / repo.replace("/", "__") / arm["commit"] / arm["file"]
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(urllib.request.urlopen(url, timeout=60).read())
    data = target.read_bytes()
    return data.decode("utf-8"), hashlib.sha256(data).hexdigest()


def score(case: dict, output: str, model: Model | None, judge: bool) -> dict:
    original = case["text"]
    det = compare(original, output)
    after = detect(output, case["genre"])["summary"]
    row = {
        "deterministic": det["status"],
        "invariants_ok": all(invariant_preserved(v, original, output) for v in case.get("must_preserve", [])),
        "invariants_missing": [v for v in case.get("must_preserve", []) if not invariant_preserved(v, original, output)],
        "findings_after": after["strong"] + after["weak"],
        "length_ratio": round(len(output.split()) / max(1, len(original.split())), 3),
        "changed": det["status"] != "identical",
    }
    if judge and model and row["changed"]:
        raw, cost, _ = model.ask(judge_prompt(original, output, det))
        try:
            answer, repairs = _extract_json(raw)
            answer.update(kind="llm", judge_id=model.id, original_sha256=content_hash(original),
                          candidate_sha256=content_hash(output))
            j = validate_judgment(answer, original, output)
            row["judge"] = {"verdict": j["verdict"], "downgraded": j.get("downgraded"),
                            "problems": [c for c in j.get("claims", []) if c.get("status") not in {"preserved", "formula_removed"}],
                            "added": j.get("added_claims", []), "repairs": repairs}
            row["final_status"] = apply_judgment(det, j)["status"]
        except ValueError as error:
            row["judge"] = {"error": str(error)}
        row["judge_cost"] = cost
    return row


def run_arm(arm: str, spec, case: dict, model: Model, skills: dict) -> dict:
    text = case["text"]
    started = time.monotonic()
    cost, raw = 0.0, None
    if arm == "B0-original":
        output = text
    elif arm == "B1-one-line":
        raw, cost, _ = model.ask(f"{ONE_LINE} {FINAL}\n\n{text}")
        output = parse_candidate(raw, text)[0]
    elif arm in skills:
        raw, cost, _ = model.ask(f"<skill>\n{skills[arm][0]}\n</skill>\n\n{SKILL_TASK} {FINAL}\n\n{text}")
        output = parse_candidate(raw, text)[0]
    elif arm == "B5a-voznativa-prompt":
        ctx = route(text, genre=case["genre"], channel=case.get("channel"))
        p = build_prompt(text, ctx, resolve(ctx), select(ctx), inline_references=True,
                         findings=detect(text, case["genre"]))
        raw, cost, _ = model.ask(p)
        output = parse_candidate(raw, text)[0]
    elif arm == "B5b-voznativa-engine":
        before = model.cost
        ctx = route(text, genre=case["genre"], channel=case.get("channel"))
        result = rewrite(text, ctx, model, attempts=3, judge_provider=model)
        output, cost = result["text"], model.cost - before  # approximate under concurrency
        raw = {"outcome": result["outcome"], "attempts": result["attempts"],
               "status": (result.get("report") or {}).get("status")}
    else:
        raise ValueError(arm)
    seconds = round(time.monotonic() - started, 1)
    return {"arm": arm, "id": case["id"], "kind": case.get("kind"), "output": output, "raw": raw,
            "cost_usd": round(cost, 4), "seconds": seconds}


def summarize(rows: list[dict], cases: list[dict]) -> dict:
    out = {}
    kinds = {c["id"]: c.get("kind") for c in cases}
    for arm in sorted({r["arm"] for r in rows}):
        rs = [r for r in rows if r["arm"] == arm and "score" in r]
        def count(key, value, subset=rs):
            return sum(1 for r in subset if r["score"].get(key) == value)
        natural = [r for r in rs if kinds[r["id"]] == "natural"]
        out[arm] = {
            "n": len(rs),
            "invariants_ok": f"{sum(r['score']['invariants_ok'] for r in rs)}/{len(rs)}",
            "deterministic": {s: count("deterministic", s) for s in sorted({r['score']['deterministic'] for r in rs})},
            "judge_not_equivalent": sum(1 for r in rs if r["score"].get("judge", {}).get("verdict") == "not_equivalent"),
            "findings_after_total": sum(r["score"]["findings_after"] for r in rs),
            "natural_texts_changed": f"{sum(r['score']['changed'] for r in natural)}/{len(natural)}",
            "cost_usd": round(sum(r["cost_usd"] + r["score"].get("judge_cost", 0) for r in rs), 3),
            "median_seconds": statistics.median([r["seconds"] for r in rs]) if rs else None,
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--claude", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--arms", help="comma-separated subset (default: all)")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    cases_path = ROOT / manifest["cases_file"]
    sha = hashlib.sha256(cases_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if sha != manifest["cases_sha256"]:
        raise SystemExit("cases changed after freezing; refusing to run")
    cases = load_cases(cases_path)
    model = Model(args.claude, args.model)
    cache = ROOT / "benchmarks" / ".cache"
    skills = {name: fetch_skill(spec, cache) for name, spec in manifest["arms"].items() if isinstance(spec, dict)}
    arms = list(manifest["arms"]) if not args.arms else args.arms.split(",")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = ROOT / "benchmarks" / "runs" / f"{manifest['benchmark']}-{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([args.claude, "--version"], capture_output=True, text=True).stdout.strip()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rows, lock = [], threading.Lock()

    def save(final=False):
        report = {"kind": "voznativa.skill_only_benchmark", "manifest": manifest, "cases_sha256": sha,
                  "run_at": stamp, "cli_version": version, "model": args.model, "voznativa_commit": commit,
                  "skills_fetched_sha256": {k: v[1] for k, v in skills.items()}, "complete": final,
                  "summary": summarize(rows, cases), "rows": rows}
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def task(arm, case):
        try:
            row = run_arm(arm, manifest["arms"][arm], case, model, skills)
            row["score"] = score(case, row["output"], model, judge=arm != "B0-original")
        except Exception as error:  # recorded, never hidden
            row = {"arm": arm, "id": case["id"], "error": f"{type(error).__name__}: {error}"}
        with lock:
            rows.append(row)
            save()
        print(f"{arm:22s} {case['id']}: {row.get('score', {}).get('deterministic', row.get('error'))}", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for arm in arms:
            for case in cases:
                pool.submit(task, arm, case)
    save(final=True)
    print(json.dumps(summarize(rows, cases), ensure_ascii=False, indent=2))
    print("report:", out_path.relative_to(ROOT).as_posix(), "| model calls:", model.calls,
          "| cost USD:", round(model.cost, 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
