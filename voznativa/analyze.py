"""Deterministic, descriptive text measurements.

Nothing here is a quality score, an authorship score or an optimization
target. Counts describe the text so other components (Voice Profile, drift,
audit) can compare texts with each other.
"""
from __future__ import annotations

import json
import re
import statistics
from functools import lru_cache
from pathlib import Path

from . import signals
from .text import fold, sentences, words

DATA = Path(__file__).resolve().parent / "data" / "analyzer_pt_br.json"
# "estaremos realizando": future + estar + gerund (corporate gerundismo), folded.
GERUNDISM_RE = re.compile(r"\b(?:estaremos|estarei|vamos estar|iremos estar|vou estar|vai estar)\s+\w+ndo\b")


@lru_cache(maxsize=1)
def data() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _sets():
    d = data()
    return (frozenset(fold(w) for w in d["non_gerunds"]),
            frozenset(fold(w) for w in d["non_adverbs_mente"]),
            [fold(c) for c in d["connector_openers"]])


def gerunds(tokens: list[str]) -> list[str]:
    non, _, _ = _sets()
    return [t for t in tokens if re.fullmatch(r"\w{3,}(?:ando|endo|indo)", fold(t)) and fold(t) not in non]


def mente_adverbs(tokens: list[str]) -> list[str]:
    _, non, _ = _sets()
    return [t for t in tokens if len(t) >= 7 and fold(t).endswith("mente") and fold(t) not in non]


def per_100(count: int, total: int) -> float:
    return round(100 * count / total, 2) if total else 0.0


def analyze(text: str) -> dict:
    sents = [s for s in sentences(text) if s.kind != "code"]
    tokens = words(text)
    lengths = [len(words(s.text)) for s in sents]
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    low = fold(text)
    _, _, connectors = _sets()
    connector_counts = {c: len(re.findall(r"(?<!\w)" + re.escape(c) + r"(?!\w)", low)) for c in connectors}
    openers = [fold(" ".join(words(s.text)[:2])) for s in sents if words(s.text)]
    marker_counts = signals.profile(text)
    return {
        "chars": len(text),
        "words": len(tokens),
        "sentences": len(sents),
        "paragraphs": len(paragraphs),
        "sentence_words_mean": round(statistics.mean(lengths), 2) if lengths else 0,
        "sentence_words_median": statistics.median(lengths) if lengths else 0,
        "sentence_words_stdev": round(statistics.pstdev(lengths), 2) if len(lengths) > 1 else 0,
        "em_dash_count": text.count("—"),
        "en_dash_spaced_count": len(re.findall(r"\s–\s", text)),
        "ellipsis_count": text.count("...") + text.count("…"),
        "question_count": text.count("?"),
        "exclamation_count": text.count("!"),
        "semicolon_count": text.count(";"),
        "colon_count": text.count(":"),
        "parenthesis_count": text.count("("),
        "comma_count": text.count(","),
        "mente_count": len(mente_adverbs(tokens)),
        "gerund_count": len(gerunds(tokens)),
        "gerundism_count": len(GERUNDISM_RE.findall(low)),
        "metadiscourse_count": marker_counts.get("metadiscourse.framing", 0),
        "connector_counts": {c: n for c, n in connector_counts.items() if n},
        "repeated_openers": {o: n for o, n in _counts(openers).items() if n > 1},
        "emoji_count": len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", text)),
        "uppercase_sentence_starts": sum(1 for s in sents if s.text[:1].isupper()),
    }


def _counts(items):
    out = {}
    for item in items:
        out[item] = out.get(item, 0) + 1
    return out
