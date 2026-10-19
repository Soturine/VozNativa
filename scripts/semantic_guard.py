#!/usr/bin/env python3
"""Legacy entry point for protected-span checks.

Kept for compatibility with v0.1.0 callers. New code should use
``voznativa compare`` (full ledger report) instead of this summary.
"""
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from voznativa import spans as _spans
from voznativa.compare import compare

_SPAN_CODES = {"span_missing", "span_added", "binding_changed"}


def extract(text: str) -> list[dict]:
    return [span.as_dict() for span in _spans.extract(text)]


def guard(original: str, candidate: str) -> dict:
    """Protected-content summary. ``ok`` means no deterministic span violation;
    it never means the candidate is semantically equivalent (see ``status``)."""
    report = compare(original, candidate)
    span_issues = [i for i in report["issues"] if i["code"] in _SPAN_CODES and i["severity"] == "critical"]
    missing = [{"type": i["type"], "text": i["text"], "expected_count": i["expected_count"],
                "actual_count": i["actual_count"]} for i in span_issues if i["code"] == "span_missing"]
    added = [{"type": i["type"], "text": i["text"]} for i in span_issues if i["code"] == "span_added"]
    swapped = [{"text": i["text"]} for i in span_issues if i["code"] == "binding_changed"]
    return {
        "ok": not span_issues,
        "missing": missing,
        "added": added,
        "swapped": swapped,
        "protected_count": len(_spans.extract(original)),
        "status": report["status"],
        "semantic_equivalence": report["semantic_equivalence"],
    }


if __name__ == "__main__":
    if len(sys.argv) == 2:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
        print(json.dumps(extract(text), ensure_ascii=False, indent=2))
    elif len(sys.argv) == 3:
        original = Path(sys.argv[1]).read_text(encoding="utf-8")
        candidate = Path(sys.argv[2]).read_text(encoding="utf-8")
        print(json.dumps(guard(original, candidate), ensure_ascii=False, indent=2))
    else:
        raise SystemExit("usage: semantic_guard.py ORIGINAL [CANDIDATE]")
