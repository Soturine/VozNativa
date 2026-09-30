#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

PATTERNS = {
    "url": r"https?://\S+",
    "date": r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b",
    "percent": r"\b\d+(?:[.,]\d+)?%",
    "money": r"R\$\s?\d[\d.]*?(?:,\d{2})?\b",
    "identifier": r"\b[A-Z]{2,}[A-Z0-9_-]*-?\d+[A-Z0-9_-]*\b",
    "number": r"\b\d+(?:[.,]\d+)?\b",
}

def extract(text: str) -> list[dict]:
    out = []
    for kind, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text):
            out.append({
                "type": kind,
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            })
    return sorted(out, key=lambda x: (x["start"], -(x["end"] - x["start"])))

def guard(original: str, candidate: str) -> dict:
    missing = []
    seen = set()
    for item in extract(original):
        key = (item["type"], item["text"])
        if key in seen:
            continue
        seen.add(key)
        if item["text"] not in candidate:
            missing.append({"type": item["type"], "text": item["text"]})
    return {"ok": not missing, "missing": missing}

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
