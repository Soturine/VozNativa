"""Deterministic benchmark scoring over frozen cases and per-system outputs.

Layout: ``outputs/<system>/<case_id>.txt``. Missing outputs count as failures
so a system cannot raise its pass rate by skipping hard cases. The runner never
calls detectors and never calls a model.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .compare import compare
from .text import fold

NEGATORS = {"nao", "nunca", "jamais", "nem", "nn"}


def load_cases(path: Path) -> list[dict]:
    cases = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        case = json.loads(line)
        for required in ("id", "text"):
            if required not in case:
                raise ValueError(f"{path}:{number}: case missing '{required}'")
        cases.append(case)
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate case ids")
    return cases


def _occurrences(phrase: str, text: str) -> list[int]:
    pattern = re.compile(r"(?<!\w)" + re.escape(fold(phrase)) + r"(?!\w)")
    return [m.start() for m in pattern.finditer(fold(text))]


def _negated(text: str, position: int) -> bool:
    window = re.findall(r"\w+", fold(text)[max(0, position - 30):position])[-3:]
    return any(w in NEGATORS for w in window)


def invariant_preserved(phrase: str, original: str, candidate: str) -> bool:
    """True when ``phrase`` survives as a whole word/phrase with the same
    polarity it had in the original (``pode`` is lost in ``não pode``)."""
    found = _occurrences(phrase, candidate)
    if not found:
        return False
    source_negated = any(_negated(original, p) for p in _occurrences(phrase, original))
    return any(_negated(candidate, p) == source_negated for p in found)


def score_case(case: dict, candidate: str) -> dict:
    original = case["text"]
    report = compare(original, candidate)
    span_codes = {"span_missing", "span_added", "binding_changed"}
    protected_issues = [i for i in report["issues"] if i["code"] in span_codes and i["severity"] == "critical"]
    explicit_missing = [v for v in case.get("must_preserve", [])
                        if not invariant_preserved(v, original, candidate)]
    expected = case.get("expected_status")
    return {
        "id": case["id"],
        "status": report["status"],
        "semantic_equivalence": report["semantic_equivalence"],
        "protected_ok": not protected_issues,
        "protected_missing": [{"type": i.get("type"), "text": i.get("text")} for i in protected_issues
                              if i["code"] == "span_missing"],
        "explicit_invariants_ok": not explicit_missing,
        "explicit_missing": explicit_missing,
        "issue_codes": sorted({i["code"] for i in report["issues"]}),
        "length_ratio": round(len(candidate.split()) / max(1, len(original.split())), 3),
        **({"expected_status": expected} if expected else {}),
    }


def summarize(rows: list[dict]) -> dict:
    total = len(rows)
    completed = [r for r in rows if not r.get("missing_output")]
    hard_pass = sum(1 for r in completed if r["protected_ok"] and r["explicit_invariants_ok"])
    statuses: dict[str, int] = {}
    for r in completed:
        if "status" in r:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    return {
        "cases": total,
        "completed": len(completed),
        "missing_outputs": total - len(completed),
        "hard_pass": hard_pass,
        # Denominator is every case: a skipped case is a failed case.
        "hard_pass_rate": round(hard_pass / total, 3) if total else None,
        "status_counts": statuses,
        "auto_acceptable": sum(1 for r in completed if r.get("status") == "identical"),
    }


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cases_path: Path, outputs_root: Path) -> dict:
    cases = load_cases(cases_path)
    systems = sorted(p.name for p in outputs_root.iterdir() if p.is_dir()) if outputs_root.exists() else []
    report = {
        "kind": "voznativa.benchmark_report",
        "cases_file": str(cases_path),
        "cases_sha256": file_sha256(cases_path),
        "cases": len(cases),
        "scoring": "deterministic tier 0 only; semantic equivalence is never asserted",
        "systems": {},
    }
    for system in systems:
        rows = []
        for case in cases:
            candidate_path = outputs_root / system / f'{case["id"]}.txt'
            if not candidate_path.exists():
                rows.append({"id": case["id"], "missing_output": True})
                continue
            rows.append(score_case(case, candidate_path.read_text(encoding="utf-8")))
        report["systems"][system] = {**summarize(rows), "results": rows}
    return report
