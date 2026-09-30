#!/usr/bin/env python3
import json, math, re, sys
from pathlib import Path
from analyze import analyze

def windows(text: str, size: int = 4):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return ["\n\n".join(paragraphs[i:i+size]) for i in range(0, len(paragraphs), size)]

def vector(text: str):
    a = analyze(text)
    return [
        a["sentence_words_mean"],
        a["sentence_words_stdev"],
        a["em_dash_count"],
        a["ellipsis_count"],
        a["question_count"],
        a["mente_count"],
        a["gerund_count"],
    ]

def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))

def inspect(text: str, size: int = 4):
    chunks = windows(text, size)
    vecs = [vector(chunk) for chunk in chunks]
    distances = [round(distance(vecs[i-1], vecs[i]), 3) for i in range(1, len(vecs))]
    return {
        "window_count": len(chunks),
        "distances": distances,
        "max_distance": max(distances, default=0),
        "note": "baseline stylistic distance; not calibrated voice identity"
    }

if __name__ == "__main__":
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    print(json.dumps(inspect(text), ensure_ascii=False, indent=2))
