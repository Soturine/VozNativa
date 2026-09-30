#!/usr/bin/env python3
import json, re, statistics, sys
from pathlib import Path

CONNECTORS = ["além disso","nesse contexto","nesse sentido","dessa forma","por fim","ademais","outrossim"]

def analyze(text: str) -> dict:
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    words = re.findall(r"\b[\wÀ-ÿ'-]+\b", text, re.UNICODE)
    lengths = [len(re.findall(r"\b[\wÀ-ÿ'-]+\b", s, re.UNICODE)) for s in sentences]
    low = text.lower()
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return {
        "chars": len(text),
        "words": len(words),
        "sentences": len(sentences),
        "paragraphs": len(paragraphs),
        "sentence_words_mean": round(statistics.mean(lengths), 2) if lengths else 0,
        "sentence_words_stdev": round(statistics.pstdev(lengths), 2) if len(lengths) > 1 else 0,
        "em_dash_count": text.count("—"),
        "ellipsis_count": text.count("..."),
        "question_count": text.count("?"),
        "mente_count": len(re.findall(r"\b\w+mente\b", low)),
        "gerund_count": len(re.findall(r"\b\w+(?:ando|endo|indo)\b", low)),
        "connector_counts": {c: low.count(c) for c in CONNECTORS if low.count(c)},
    }

if __name__ == "__main__":
    data = Path(sys.argv[1]).read_text(encoding="utf-8")
    print(json.dumps(analyze(data), ensure_ascii=False, indent=2))
