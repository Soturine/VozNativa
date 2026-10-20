"""Behavioral eval runner for the deterministic semantic layer.

Each case states which statuses are acceptable, which issue codes must and
must not appear, and (optionally) whether the result may be auto-accepted.
Cases marked ``known_limitation`` document gaps: they pass only if the system
refuses to call the candidate safe, not if it detects the problem.
"""
from __future__ import annotations

import hashlib
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


def sha256_lf(path: Path) -> str:
    """Hash with LF line endings so checkouts on Windows and Linux agree."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def provenance(path: Path) -> dict:
    """Entry for ``path`` in the MANIFEST.json next to it; unknown suites are
    reported as unverified, never as independent."""
    manifest_path = path.parent / "MANIFEST.json"
    entry = {}
    if manifest_path.exists():
        entry = json.loads(manifest_path.read_text(encoding="utf-8")).get("suites", {}).get(path.name, {})
    if not entry:
        return {"role": "unknown", "independent": False, "note": "suite not listed in MANIFEST.json"}
    entry = dict(entry)
    if entry.get("frozen"):
        entry["sha256_matches"] = sha256_lf(path) == entry.get("sha256")
    return entry


def run(path: Path, require_frozen: bool = False) -> dict:
    origin = provenance(path)
    if require_frozen and not (origin.get("frozen") and origin.get("sha256_matches")):
        raise ValueError(f"{path.name}: not a frozen suite with a matching sha256 in MANIFEST.json")
    cases = load(path)
    for case in cases:
        missing = {"id", "category", "original", "candidate", "expect"} - case.keys()
        if missing:
            raise ValueError(f"{path.name}: case {case.get('id', '?')} lacks {sorted(missing)}; "
                             "not a semantic eval suite (router cases run in the test suite)")
    results = [check(case) for case in cases]
    by_category = Counter()
    passed = Counter()
    for r in results:
        by_category[r["category"]] += 1
        passed[r["category"]] += r["passed"]
    return {
        "kind": "voznativa.semantic_eval_report",
        "suite": path.name,
        "provenance": origin,
        "independent_validation": bool(origin.get("independent")),
        "cases": len(results),
        "passed": sum(r["passed"] for r in results),
        "by_category": {c: f"{passed[c]}/{n}" for c, n in sorted(by_category.items())},
        "failures": [r for r in results if not r["passed"]],
    }
