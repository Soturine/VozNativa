"""Length-normalized style features shared by Voice Profile and Voice Drift.

Every feature is a rate (per 100 words or per sentence) or a ratio, so a
long window and a short window are comparable. Topic words are deliberately
excluded: what someone writes about is not how they write.
"""
from __future__ import annotations

import re
import statistics

from .analyze import analyze, per_100
from .text import fold, sentences, words

CHAT_ABBREVIATIONS = frozenset({
    "vc", "vcs", "tb", "tbm", "pq", "q", "nn", "n", "blz", "vlw", "msg", "mds", "obg", "pfv", "pf",
    "tmj", "sdds", "fds", "hj", "amn", "td", "tds", "cmg", "ctz", "kkk", "kkkk", "rs", "rsrs",
})
CONTRACTIONS = frozenset({"pra", "pro", "pros", "pras", "tá", "tô", "tamo", "né", "cê", "num", "numa", "dum", "duma"})
FIRST_PERSON = frozenset({"eu", "meu", "minha", "meus", "minhas", "comigo", "nós", "nosso", "nossa", "a gente"})

FEATURES = [
    "sentence_words_mean", "sentence_words_stdev", "comma_per_100w", "semicolon_per_100w",
    "colon_per_100w", "em_dash_per_100w", "ellipsis_per_100w", "question_per_sentence",
    "exclamation_per_sentence", "parenthesis_per_100w", "emoji_per_100w", "gerund_per_100w",
    "mente_per_100w", "metadiscourse_per_100w", "connector_per_100w", "abbreviation_per_100w",
    "contraction_per_100w", "first_person_per_100w", "lowercase_start_ratio", "list_line_ratio",
]


def vector(text: str) -> dict[str, float]:
    a = analyze(text)
    n_words = max(1, a["words"])
    n_sent = max(1, a["sentences"])
    tokens = [fold(t) for t in words(text)]
    low = fold(text)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    sents = [s for s in sentences(text) if s.kind == "prose"]
    folded_contractions = {fold(c) for c in CONTRACTIONS}
    return {
        "sentence_words_mean": a["sentence_words_mean"],
        "sentence_words_stdev": a["sentence_words_stdev"],
        "comma_per_100w": per_100(a["comma_count"], n_words),
        "semicolon_per_100w": per_100(a["semicolon_count"], n_words),
        "colon_per_100w": per_100(a["colon_count"], n_words),
        "em_dash_per_100w": per_100(a["em_dash_count"] + a["en_dash_spaced_count"], n_words),
        "ellipsis_per_100w": per_100(a["ellipsis_count"], n_words),
        "question_per_sentence": round(a["question_count"] / n_sent, 3),
        "exclamation_per_sentence": round(a["exclamation_count"] / n_sent, 3),
        "parenthesis_per_100w": per_100(a["parenthesis_count"], n_words),
        "emoji_per_100w": per_100(a["emoji_count"], n_words),
        "gerund_per_100w": per_100(a["gerund_count"], n_words),
        "mente_per_100w": per_100(a["mente_count"], n_words),
        "metadiscourse_per_100w": per_100(a["metadiscourse_count"], n_words),
        "connector_per_100w": per_100(sum(a["connector_counts"].values()), n_words),
        "abbreviation_per_100w": per_100(sum(t in CHAT_ABBREVIATIONS for t in tokens), n_words),
        "contraction_per_100w": per_100(sum(t in folded_contractions for t in tokens), n_words),
        "first_person_per_100w": per_100(sum(t in {fold(w) for w in FIRST_PERSON} for t in tokens)
                                         + len(re.findall(r"\ba gente\b", low)), n_words),
        "lowercase_start_ratio": round(sum(1 for s in sents if s.text[:1].islower()) / max(1, len(sents)), 3),
        "list_line_ratio": round(sum(1 for ln in lines if re.match(r"\s*(?:[-*+•]|\d+[.)])\s", ln))
                                 / max(1, len(lines)), 3),
    }


def windows(text: str, target_words: int = 120) -> list[str]:
    """Group paragraphs into windows of roughly ``target_words`` words."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out, current, count = [], [], 0
    for p in paragraphs:
        current.append(p)
        count += len(p.split())
        if count >= target_words:
            out.append("\n\n".join(current))
            current, count = [], 0
    if current:
        if out and count < target_words / 2:
            out[-1] += "\n\n" + "\n\n".join(current)
        else:
            out.append("\n\n".join(current))
    return out


def summarize(vectors: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    out = {}
    for name in FEATURES:
        values = [v[name] for v in vectors]
        out[name] = {
            "mean": round(statistics.mean(values), 3) if values else 0.0,
            "stdev": round(statistics.pstdev(values), 3) if len(values) > 1 else None,
            "n": len(values),
        }
    return out
