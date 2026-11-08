"""Rubric Engine (v0.8 CP11, ST-05): objective criteria with evidence, nothing graded.

Given a text and a ``document_profile``, the engine asks the Standards
Registry which source applies (``standards.resolve``) and goes through that
source's criteria:

* an **objective** criterion with a ``check`` is checked only when the
  source decision is ``APPLICABLE`` or ``APPLICABLE_UNVERIFIED`` **and** the
  criterion itself is at least ``SOURCE_CITED``; the result is ``MET`` or
  ``NOT_MET`` with evidence and offsets;
* anything else is ``NOT_ENFORCED`` with the reason (criterion only
  catalogued, source unknown or conflicted, no check defined);
* a **subjective** criterion is ``NEEDS_JUDGMENT``: listed for a person or a
  judge, never turned into a boolean or a score.

No total, no weight and no grade are computed: an official score belongs to
the official evaluators. Each result names its source, edition and validity.

Checks: ``word_range`` {min, max}, ``line_range`` {min, max} (non-empty
lines), ``required_sections`` [heading texts, case-insensitive].
"""
from __future__ import annotations

import re

from . import standards

ENFORCEABLE_SOURCE = ("APPLICABLE", "APPLICABLE_UNVERIFIED")
ENFORCEABLE_CRITERION = ("SOURCE_CITED", "VERIFIED")
_HEADING = re.compile(r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")


def _check(check: dict, text: str) -> tuple[bool, dict]:
    kind = check.get("type")
    if kind == "word_range":
        n = len(text.split())
        ok = (check.get("min") is None or n >= check["min"]) and (check.get("max") is None or n <= check["max"])
        return ok, {"words": n, "min": check.get("min"), "max": check.get("max")}
    if kind == "line_range":
        n = sum(1 for line in text.splitlines() if line.strip())
        ok = (check.get("min") is None or n >= check["min"]) and (check.get("max") is None or n <= check["max"])
        return ok, {"lines": n, "min": check.get("min"), "max": check.get("max")}
    if kind == "required_sections":
        found = {m.group(1).strip().casefold(): m.start() for m in _HEADING.finditer(text)}
        missing = [s for s in check.get("sections", []) if s.casefold() not in found]
        present = {s: found[s.casefold()] for s in check.get("sections", []) if s.casefold() in found}
        return not missing, {"missing": missing, "present_at": present}
    raise ValueError(f"unknown check type {kind!r}")


def evaluate(text: str, profile: dict, entries: tuple[dict, ...] | None = None) -> dict:
    entries = standards.load() if entries is None else entries
    resolution = standards.resolve(profile, entries)
    by_id = {e["id"]: e for e in entries}
    sources = [by_id[i] for i in resolution.get("edition_found", resolution.get("selected", []))]
    results = []
    for source in sources:
        cite = {"source": source["id"], "edition": source["edition"], "validity": source["validity"],
                "source_verification": source["verification"]["status"]}
        for c in source["criteria"]:
            base = dict(cite, criterion=c["id"], kind=c["kind"], statement=c.get("statement"),
                        criterion_verification=c["verification"])
            # Evidence first, for every kind: an unverified criterion is not presented as applicable.
            if resolution["decision"] not in ENFORCEABLE_SOURCE:
                results.append(dict(base, status="NOT_ENFORCED",
                                    reason=f"source decision {resolution['decision']}: {resolution['reason']}"))
            elif c["verification"] not in ENFORCEABLE_CRITERION:
                results.append(dict(base, status="NOT_ENFORCED",
                                    reason=f"criterion only {c['verification']}: not verified in an official source"))
            elif c["kind"] == "subjective":
                results.append(dict(base, status="NEEDS_JUDGMENT",
                                    reason="subjective criterion: a person or a judge decides; no score is produced"))
            elif not c.get("check"):
                results.append(dict(base, status="NOT_ENFORCED", reason="no deterministic check defined"))
            else:
                ok, evidence = _check(c["check"], text)
                results.append(dict(base, status="MET" if ok else "NOT_MET", evidence=evidence))
    counts = {s: sum(r["status"] == s for r in results) for s in ("MET", "NOT_MET", "NOT_ENFORCED", "NEEDS_JUDGMENT")}
    return {"kind": "voznativa.rubric_report", "schema_version": 1, "profile": profile, "resolution": resolution,
            "criteria": results, "counts": counts,
            "note": "objective checks only where source and criterion are verified enough; subjective criteria are "
                    "listed, never scored; no total or official grade is produced"}
