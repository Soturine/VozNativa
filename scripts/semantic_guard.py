#!/usr/bin/env python3
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Order matters: more specific spans are reserved before generic numbers.
PATTERNS = [
    ("url", r"https?://\S+"),
    ("date", r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"),
    ("money", r"R\$\s?\d[\d.]*?(?:,\d{2})?\b"),
    ("percent", r"\b\d+(?:[.,]\d+)?%"),
    ("identifier", r"\b[A-Z]{2,}[A-Z0-9_-]*-?\d+[A-Z0-9_-]*\b"),
    ("number", r"\b\d+(?:[.,]\d+)?\b"),
]

def extract(text: str) -> list[dict]:
    occupied: list[tuple[int, int]] = []
    out: list[dict] = []

    for kind, pattern in PATTERNS:
        for match in re.finditer(pattern, text):
            start, end = match.span()
            if any(start < used_end and end > used_start for used_start, used_end in occupied):
                continue
            occupied.append((start, end))
            out.append({
                "type": kind,
                "text": match.group(0),
                "start": start,
                "end": end,
            })

    return sorted(out, key=lambda item: item["start"])

def _counts(text: str) -> Counter:
    return Counter((item["type"], item["text"]) for item in extract(text))

def guard(original: str, candidate: str) -> dict:
    original_counts = _counts(original)
    candidate_counts = _counts(candidate)
    missing = []

    for key, expected_count in original_counts.items():
        actual_count = candidate_counts.get(key, 0)
        if actual_count < expected_count:
            kind, value = key
            missing.append({
                "type": kind,
                "text": value,
                "expected_count": expected_count,
                "actual_count": actual_count,
            })

    return {
        "ok": not missing,
        "missing": missing,
        "protected_count": sum(original_counts.values()),
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
