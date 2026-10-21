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

UNSAFE = {"fail", "review_required"}
CLEARED = {"no_deterministic_issues", "identical"}


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def failure_kind(status: str, expected: list[str]) -> str:
    """Why the status was wrong, so a missed detection is never mixed up with
    a problem caught under another issue code (``classification_divergence``,
    set in ``check``).

    * ``false_green``: the case expected a block and the gate cleared it.
    * ``false_red``: the case expected a cleared result and the gate blocked it.
    * ``severity_divergence``: blocked, but with another severity
      (``review_required`` where ``fail`` was expected, or the reverse)."""
    if status in CLEARED and set(expected) <= UNSAFE:
        return "false_green"
    if status in UNSAFE and not set(expected) & UNSAFE:
        return "false_red"
    return "severity_divergence" if status in UNSAFE else "status_mismatch"


def check(case: dict) -> dict:
    report = compare(case["original"], case["candidate"])
    expect = case["expect"]
    codes = {i["code"] for i in report["issues"]}
    problems, code_problems = [], []
    status_ok = report["status"] in expect["status"]
    if not status_ok:
        problems.append(f"status {report['status']} not in {expect['status']}")
    for code in expect.get("codes", []):
        if code not in codes:
            code_problems.append(f"missing issue {code}")
    for code in expect.get("absent_codes", []):
        if code in codes:
            code_problems.append(f"unexpected issue {code}")
    if "safe" in expect and report["safe_to_auto_accept"] != expect["safe"]:
        problems.append(f"safe_to_auto_accept={report['safe_to_auto_accept']}")
    # Global invariant: nothing but identity is auto-accepted without a judgment.
    if report["safe_to_auto_accept"] and report["status"] != "identical":
        problems.append("auto-accepted without identity or judgment")
    if not status_ok:
        kind = failure_kind(report["status"], expect["status"])
    elif problems:
        kind = "acceptance_mismatch"
    else:
        kind = "classification_divergence" if code_problems else None
    problems += code_problems
    return {"id": case["id"], "category": case["category"], "status": report["status"],
            "codes": sorted(codes), "passed": not problems, "problems": problems,
            **({"failure_kind": kind} if kind else {})}


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
    failures = [r for r in results if not r["passed"]]
    kinds = Counter(r["failure_kind"] for r in failures)
    return {
        "kind": "voznativa.semantic_eval_report",
        "suite": path.name,
        "provenance": origin,
        "independent_validation": bool(origin.get("independent")),
        "cases": len(results),
        # Strict: status AND issue codes as written in the case. The headline number.
        "passed": sum(r["passed"] for r in results),
        # Status only: the gate decided as expected, whatever code it used.
        "status_passed": len(results) - sum(n for k, n in kinds.items() if k != "classification_divergence"),
        "failure_kinds": dict(sorted(kinds.items())),
        "by_category": {c: f"{passed[c]}/{n}" for c, n in sorted(by_category.items())},
        "failures": failures,
    }


# --- Engine decision suite (v0.4.0 M4) ----------------------------------------------

def check_decision(case: dict) -> dict:
    """Does the planner call the model (edit/transform) when it should, stay
    out (no_change) when it should, and leave the listed sentences alone?"""
    from .planner import plan
    from .router import route
    hints = case.get("hints") or {}
    context = route(case["text"], genre=case.get("genre"), **hints)
    p = plan(case["text"], context)
    expect = case["expect"]
    problems = []
    if p["decision"] != expect["decision"]:
        problems.append(f"decision {p['decision']} != {expect['decision']}")
    ops = {r["index"]: r["op"] for r in p["sentences"]}
    for index in expect.get("keep", []):
        if ops.get(index) != "keep":
            problems.append(f"sentence {index} planned as {ops.get(index)}, should be kept")
    called, should_call = p["decision"] != "no_change", expect["decision"] != "no_change"
    kind = None
    if problems:
        kind = ("unnecessary_change" if called and not should_call else
                "missed_change" if should_call and not called else
                "wrong_scope" if p["decision"] != expect["decision"] else "unplanned_sentence")
    return {"id": case["id"], "decision": p["decision"], "scope": p["scope"], "passed": not problems,
            "problems": problems, **({"failure_kind": kind} if kind else {})}


def run_decisions(path: Path) -> dict:
    results = [check_decision(c) for c in load(path)]
    kinds = Counter(r["failure_kind"] for r in results if not r["passed"])
    return {"kind": "voznativa.decision_eval_report", "suite": str(path.name), "cases": len(results),
            "passed": sum(r["passed"] for r in results), "failure_kinds": dict(sorted(kinds.items())),
            "failures": [r for r in results if not r["passed"]]}
