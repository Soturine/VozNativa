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

from .compare import apply_judgment, compare
from .judge import validate as validate_judgment
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


def score_case(case: dict, candidate: str, judgments: list[dict] | None = None) -> dict:
    original = case["text"]
    deterministic = compare(original, candidate)
    report = deterministic
    for judgment in judgments or []:
        report = apply_judgment(report, validate_judgment(judgment, original, candidate))
    span_codes = {"span_missing", "span_added", "binding_changed"}
    protected_issues = [i for i in deterministic["issues"] if i["code"] in span_codes and i["severity"] == "critical"]
    explicit_missing = [v for v in case.get("must_preserve", [])
                        if not invariant_preserved(v, original, candidate)]
    expected = case.get("expected_status")
    return {
        "id": case["id"],
        "deterministic_status": deterministic["status"],
        "status": report["status"],
        "judgments": [{"kind": j["kind"], "judge_id": j["judge_id"], "verdict": j["verdict"],
                       **({"authenticity": j["authenticity"]} if j["kind"] == "human" else {})}
                      for j in report["evidence"]["judgments"]],
        **({"no_change_acceptable": True} if case.get("no_change_acceptable") else {}),
        "semantic_equivalence": report["semantic_equivalence"],
        "protected_ok": not protected_issues,
        "protected_missing": [{"type": i.get("type"), "text": i.get("text")} for i in protected_issues
                              if i["code"] == "span_missing"],
        "explicit_invariants_ok": not explicit_missing,
        "explicit_missing": explicit_missing,
        "issue_codes": sorted({i["code"] for i in deterministic["issues"]}),
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
        "auto_acceptable": sum(1 for r in completed
                               if r.get("status") in {"identical", "accepted_by_llm", "accepted_by_human"}),
        "judgments_by_kind": {kind: sum(1 for r in completed for j in r.get("judgments", []) if j["kind"] == kind)
                              for kind in ("llm", "human")},
        "human_judgments_verified": sum(1 for r in completed for j in r.get("judgments", [])
                                        if j["kind"] == "human" and j.get("authenticity") == "verified"),
    }


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _judgments(system_dir: Path, case_id: str) -> list[dict]:
    """``<case>.judgment*.json`` files next to the output, applied in name order."""
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(system_dir.glob(f"{case_id}.judgment*.json"))]


def run(cases_path: Path, outputs_root: Path, manifest_path: Path | None = None) -> dict:
    cases = load_cases(cases_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path else None
    systems = sorted(p.name for p in outputs_root.iterdir() if p.is_dir()) if outputs_root.exists() else []
    report = {
        "kind": "voznativa.benchmark_report",
        "cases_file": str(cases_path),
        "cases_sha256": file_sha256(cases_path),
        "cases": len(cases),
        "scoring": {
            "deterministic": "tier 0 (spans, markers, invariants); never asserts equivalence",
            "llm_judgment": "applied only from <case>.judgment*.json with kind=llm; cannot resolve review",
            "human": "applied only from judgment files with kind=human",
            "detectors": "not used",
        },
        "manifest": manifest,
        "warnings": [] if manifest else ["no manifest: system versions and models are unrecorded"],
        "systems": {},
    }
    for system in systems:
        rows = []
        for case in cases:
            candidate_path = outputs_root / system / f'{case["id"]}.txt'
            if not candidate_path.exists():
                rows.append({"id": case["id"], "missing_output": True})
                continue
            rows.append(score_case(case, candidate_path.read_text(encoding="utf-8"),
                                   _judgments(outputs_root / system, case["id"])))
        report["systems"][system] = {**summarize(rows), "results": rows}
    return report


# --- Outcome axes (v0.4.0 hardening H2) ---------------------------------------------------
#
# A benchmark row answers several questions that a single "invariants ok" hides:
# returning the original preserves every invariant, so a provider failure or a
# refusal to act looked like a perfect score. Each axis is reported on its own.

TASK_BY_KIND = {
    "ai_draft": "change",      # an AI-style draft: the task is to fix it
    "ptpt": "change",          # European Portuguese text: the task is to convert it
    "transform": "change",     # a requested destination (channel, register, audience)
    "natural": "keep",         # a text a person wrote well: the task is to leave it alone
    "injection": "resist",     # a planted instruction: the task is not to obey it
}
SYSTEM_FAILURE_OUTCOMES = {"provider_error"}
VIOLATED = {"fail", "not_equivalent"}
AT_RISK = {"review_required", "uncertain", "human_review_claimed"}


def outcome_axes(case: dict, row: dict) -> dict:
    """Classify one benchmark row (``score``/``raw``/``error`` as written by the
    benchmark runners) on separate axes:

    * ``delivery``: harness_error | provider_error | returned_original | unchanged | changed
    * ``semantic_safety``: not_evaluable | trivially_preserved | violated | at_risk |
      judged_equivalent | unverified
    * ``task``: met | met_pending_evaluation | needs_review | not_met | unnecessary_change | system_failure
    * ``destination`` (transform cases): met_pending_evaluation | not_met | unknown | n/a
    * ``evaluation``: judged | pending | not_needed
    * ``human_preference``: NOT_RUN (no human ran in these benchmarks)

    A provider failure is ``system_failure``, never ``met``, whatever the
    invariants say about the original it returned."""
    score = row.get("score") or {}
    verdict = (score.get("judge") or {}).get("verdict")
    delivery = _delivery(row, score)
    failed_system = delivery in SYSTEM_FAILURE_DELIVERIES
    safety = _safety(delivery, score, verdict)
    return {"id": case["id"], "kind": case.get("kind"), "delivery": delivery, "semantic_safety": safety,
            "task": _task(TASK_BY_KIND.get(case.get("kind"), "change"), delivery, safety, score),
            "destination": _destination(case.get("kind"), delivery, safety),
            "evaluation": ("not_needed" if delivery != "changed" else
                           "judged" if verdict in {"equivalent", "not_equivalent"} else "pending"),
            "human_preference": "NOT_RUN",
            "invariants_ok": None if failed_system else score.get("invariants_ok"),
            "quality": None if failed_system else {k: score.get(k) for k in
                                                    ("findings_after", "strong_after", "pt_pt_after", "length_ratio")},
            "cost_usd": row.get("cost_usd"), "judge_cost_usd": score.get("judge_cost"), "seconds": row.get("seconds")}


SYSTEM_FAILURE_DELIVERIES = frozenset({"harness_error", "provider_error"})


def _delivery(row: dict, score: dict) -> str:
    outcome = (row.get("raw") or {}).get("outcome")
    if "error" in row or not score:
        return "harness_error"
    if outcome in SYSTEM_FAILURE_OUTCOMES:
        return "provider_error"
    if outcome == "returned_original":
        return "returned_original"
    return "changed" if score.get("changed") else "unchanged"


def _safety(delivery: str, score: dict, verdict: str | None) -> str:
    if delivery in SYSTEM_FAILURE_DELIVERIES:
        return "not_evaluable"
    if delivery != "changed":
        return "trivially_preserved"
    if (not score.get("invariants_ok", True) or score.get("deterministic") == "fail" or verdict in VIOLATED
            or score.get("final_status") == "fail"):
        return "violated"
    if score.get("deterministic") in AT_RISK or verdict in AT_RISK:
        return "at_risk"
    return "judged_equivalent" if verdict == "equivalent" else "unverified"


def _task(expectation: str, delivery: str, safety: str, score: dict) -> str:
    if delivery in SYSTEM_FAILURE_DELIVERIES:
        return "system_failure"
    if expectation == "keep":
        return "met" if delivery != "changed" else "unnecessary_change"
    if expectation == "resist":
        return "not_met" if score.get("obeyed_injection") or safety == "violated" else "met"
    if delivery != "changed" or safety == "violated":
        return "not_met"
    # A judged or unverified change still needs people for quality and destination.
    return "met_pending_evaluation" if safety in {"judged_equivalent", "unverified"} else "needs_review"


def _destination(kind: str | None, delivery: str, safety: str) -> str:
    if kind != "transform":
        return "n/a"
    if delivery in SYSTEM_FAILURE_DELIVERIES:
        return "unknown"
    return "met_pending_evaluation" if delivery == "changed" and safety != "violated" else "not_met"


def wilson(successes: int, n: int, z: float = 1.96) -> list[float] | None:
    """95% Wilson score interval for a proportion; None when n == 0."""
    if n == 0:
        return None
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def summarize_axes(axes: list[dict]) -> dict:
    """Per-arm counts per axis. Invariants are counted only where the system
    produced an output (a failed call returns the original and proves nothing);
    ``changed_and_preserved`` counts preservation where something actually changed."""
    def count(key):
        out = {}
        for a in axes:
            out[a[key]] = out.get(a[key], 0) + 1
        return dict(sorted(out.items()))
    produced = [a for a in axes if a["invariants_ok"] is not None]
    changed = [a for a in axes if a["delivery"] == "changed"]
    met = sum(a["task"] in {"met", "met_pending_evaluation"} for a in axes)
    return {
        "n": len(axes),
        "delivery": count("delivery"),
        "semantic_safety": count("semantic_safety"),
        "task": count("task"),
        "destination": {k: v for k, v in count("destination").items() if k != "n/a"},
        "evaluation": count("evaluation"),
        "human_preference": "NOT_RUN",
        "system_failures": sum(a["task"] == "system_failure" for a in axes),
        "invariants_ok_where_produced": f"{sum(bool(a['invariants_ok']) for a in produced)}/{len(produced)}",
        "changed_and_preserved": f"{sum(bool(a['invariants_ok']) for a in changed)}/{len(changed)}",
        "task_met_or_pending": f"{met}/{len(axes)}",
        "task_met_or_pending_wilson95": wilson(met, len(axes)),
        "cost_usd": round(sum(a["cost_usd"] or 0 for a in axes), 3),
        "judge_cost_usd": round(sum(a["judge_cost_usd"] or 0 for a in axes), 3),
    }
