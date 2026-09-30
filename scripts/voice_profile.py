#!/usr/bin/env python3
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

STOPWORDS = {
    "a","as","o","os","de","da","das","do","dos","e","em","um","uma","uns","umas",
    "que","para","por","com","no","na","nos","nas","se","é","ser","ao","aos"
}

def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]

def profile(texts: list[str]) -> dict:
    merged = "\n\n".join(texts)
    sentences = _sentences(merged)
    sentence_lengths = [
        len(re.findall(r"\b[\wÀ-ÿ'-]+\b", sentence, re.UNICODE))
        for sentence in sentences
    ]
    paragraphs = [p for p in re.split(r"\n\s*\n", merged) if p.strip()]
    paragraph_sentence_counts = [len(_sentences(p)) for p in paragraphs]

    tokens = [t.lower() for t in re.findall(r"\b[\wÀ-ÿ'-]+\b", merged, re.UNICODE)]
    content_tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    recurring = [word for word, _ in Counter(content_tokens).most_common(20)]

    abbreviations = sorted(set(
        token for token in tokens
        if token in {"vc","vcs","tb","tbm","pq","q","nn","n","blz","vlw","msg","mds"}
    ))

    foreign_terms = sorted(set(
        token for token in tokens
        if token in {
            "deploy","sprint","feedback","bug","feature","pipeline","backend","frontend",
            "framework","stack","deadline","call","onboarding","commit","push","merge"
        }
    ))

    denom = max(1, len(sentences))
    return {
        "schema_version": 1,
        "locale": "pt-BR",
        "source": {"type": "samples", "sample_count": len(texts)},
        "sentence": {
            "mean_words": round(statistics.mean(sentence_lengths), 2) if sentence_lengths else 0,
            "stdev_words": round(statistics.pstdev(sentence_lengths), 2) if len(sentence_lengths) > 1 else 0,
        },
        "paragraph": {
            "mean_sentences": round(statistics.mean(paragraph_sentence_counts), 2)
            if paragraph_sentence_counts else 0,
        },
        "punctuation": {
            "em_dash_rate": round(merged.count("—") / denom, 3),
            "ellipsis_rate": round(merged.count("...") / denom, 3),
            "question_rate": round(merged.count("?") / denom, 3),
            "exclamation_rate": round(merged.count("!") / denom, 3),
        },
        "lexicon": {
            "recurring": recurring,
            "abbreviations": abbreviations,
            "foreign_terms": foreign_terms,
        },
        "inference_policy": {
            "observations_only": True,
            "infer_identity": False,
        },
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: voice_profile.py SAMPLE [SAMPLE ...]")
    samples = [Path(path).read_text(encoding="utf-8") for path in sys.argv[1:]]
    print(json.dumps(profile(samples), ensure_ascii=False, indent=2))
