"""Behavioral eval runner for the deterministic semantic layer.

Each case states which statuses are acceptable, which issue codes must and
must not appear, and (optionally) whether the result may be auto-accepted.
Cases marked ``known_limitation`` document gaps: they pass only if the system
refuses to call the candidate safe, not if it detects the problem.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .compare import compare


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check(case: dict) -> dict:
    report = compare(case["original"], case["candidate"])
    expect = case["expect"]
    codes = {i["code"] for i in report["issues"]}
    problems = []
    if report["status"] not in expect["status"]:
        problems.append(f"status {report['status']} not in {expect['status']}")
    for code in expect.get("codes", []):
        if code not in codes:
            problems.append(f"missing issue {code}")
    for code in expect.get("absent_codes", []):
        if code in codes:
            problems.append(f"unexpected issue {code}")
    if "safe" in expect and report["safe_to_auto_accept"] != expect["safe"]:
        problems.append(f"safe_to_auto_accept={report['safe_to_auto_accept']}")
    # Global invariant: nothing but identity is auto-accepted without a judgment.
    if report["safe_to_auto_accept"] and report["status"] != "identical":
        problems.append("auto-accepted without identity or judgment")
    return {"id": case["id"], "category": case["category"], "status": report["status"],
            "codes": sorted(codes), "passed": not problems, "problems": problems}


def run(path: Path) -> dict:
    results = [check(case) for case in load(path)]
    by_category = Counter()
    passed = Counter()
    for r in results:
        by_category[r["category"]] += 1
        passed[r["category"]] += r["passed"]
    return {
        "kind": "voznativa.semantic_eval_report",
        "cases": len(results),
        "passed": sum(r["passed"] for r in results),
        "by_category": {c: f"{passed[c]}/{n}" for c, n in sorted(by_category.items())},
        "failures": [r for r in results if not r["passed"]],
    }
