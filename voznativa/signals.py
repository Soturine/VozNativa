"""Closed-class semantic markers: negation, modality, quantifiers, conditions,
causality, commitments and attribution.

The marker lexicon lives in ``data/markers_pt_br.json`` with its evidence level
and known gaps. Matching is accent-folded and longest-phrase-first, so "a não
ser que" counts as a condition and does not also count as a negation.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .text import fold

DATA = Path(__file__).resolve().parent / "data" / "markers_pt_br.json"
_TOKEN_RE = re.compile(r"\w+(?:-\w+)*|[,;:()]", re.UNICODE)
_CLAUSE_OPENERS = frozenset({"e", "mas", "ou", "so", "somente", "apenas", "porem", ",", ";", ":", "("})


@dataclass(frozen=True)
class Marker:
    category: str
    cls: str
    phrase: str
    start: int
    end: int

    @property
    def label(self) -> str:
        return f"{self.category}.{self.cls}"


@lru_cache(maxsize=1)
def lexicon() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _phrases() -> list[tuple[tuple[str, ...], str, str]]:
    items = []
    for category, classes in lexicon()["categories"].items():
        for cls, phrases in classes.items():
            for phrase in phrases:
                items.append((tuple(fold(phrase).split()), category, cls))
    # Longest phrases first so multiword expressions win over their parts;
    # among equal lengths, exact entries win over prefix (*) entries.
    items.sort(key=lambda item: (len(item[0]), not item[0][-1].endswith("*")), reverse=True)
    return items


@lru_cache(maxsize=1)
def _compounds() -> dict[str, list[tuple[str, str]]]:
    raw = lexicon().get("compounds", {})
    return {fold(word): [tuple(label.split(".", 1)) for label in labels]
            for word, labels in raw.items() if not word.startswith("_")}


@lru_cache(maxsize=1)
def _patterns() -> list[tuple[re.Pattern, str, str]]:
    return [(re.compile(p["regex"], re.I), *p["label"].split(".", 1)) for p in lexicon().get("patterns", [])]


@lru_cache(maxsize=1)
def _backward_causal() -> list[tuple[str, ...]]:
    return [tuple(fold(p).split()) for p in lexicon().get("causal_orientation", {}).get("backward", [])]


def causal_orientation(phrase: str) -> str:
    """'backward' when the cause follows the marker (X porque Y), else 'forward'."""
    tokens = [fold(t) for t in _TOKEN_RE.findall(phrase)]
    for candidate in _backward_causal():
        if len(candidate) == len(tokens) and _phrase_matches(candidate, tokens):
            return "backward"
    return "forward"


@lru_cache(maxsize=1)
def polarity_antonyms() -> list[tuple[str, str]]:
    return [tuple(pair) for pair in lexicon().get("polarity_antonyms", [])]


@lru_cache(maxsize=1)
def severity_rules() -> dict[str, frozenset[str]]:
    raw = lexicon().get("comparison", {}).get("severity", {})
    return {key: frozenset(raw.get(key, [])) for key in
            ("critical_when_localized", "review_only_on_addition", "informational")}


@lru_cache(maxsize=1)
def category_level() -> frozenset[str]:
    return frozenset(lexicon().get("comparison", {}).get("category_level", []))


def markers(text: str) -> list[Marker]:
    tokens = [(fold(m.group(0)), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]
    folded = [t[0] for t in tokens]
    used = [False] * len(tokens)
    found: list[Marker] = []

    # 1. Constructions (regex) consume their tokens first.
    for pattern, category, cls in _patterns():
        for m in pattern.finditer(text):
            idx = [i for i, t in enumerate(tokens) if t[1] >= m.start() and t[2] <= m.end()]
            if not idx or any(used[i] for i in idx):
                continue
            for i in idx:
                used[i] = True
            found.append(Marker(category, cls, m.group(0), m.start(), m.end()))

    # 2. Compound words that carry two meanings (im+possível).
    compounds = _compounds()
    for i, token in enumerate(folded):
        if not used[i] and token in compounds:
            used[i] = True
            for category, cls in compounds[token]:
                found.append(Marker(category, cls, text[tokens[i][1]:tokens[i][2]], tokens[i][1], tokens[i][2]))

    # 3. Closed-class phrases, longest first. Prepositions inside a phrase
    #    also match their article contractions ("leva a" ~ "leva à/ao").
    for phrase, category, cls in _phrases():
        n = len(phrase)
        for i in range(len(tokens) - n + 1):
            if any(used[i:i + n]) or not _phrase_matches(phrase, folded[i:i + n]):
                continue
            if phrase == ("se",) and not _clause_initial(folded, i):
                continue
            for j in range(i, i + n):
                used[j] = True
            found.append(Marker(category, cls, text[tokens[i][1]:tokens[i + n - 1][2]],
                                tokens[i][1], tokens[i + n - 1][2]))
    return _negative_concord(sorted(found, key=lambda m: m.start))


_CONTRACTIONS = {
    "a": frozenset({"a", "ao", "aos", "as"}),
    "de": frozenset({"de", "do", "da", "dos", "das"}),
    "em": frozenset({"em", "no", "na", "nos", "nas", "num", "numa"}),
    "por": frozenset({"por", "pelo", "pela", "pelos", "pelas"}),
}


def _token_matches(pattern: str, token: str) -> bool:
    if pattern.endswith("*"):  # prefix entry ("aument*" ~ aumentou, aumento)
        return token.startswith(pattern[:-1]) and len(token) > len(pattern) - 1
    return pattern == token


def _phrase_matches(phrase: tuple[str, ...], window: list[str]) -> bool:
    if len(phrase) == 1:
        return _token_matches(phrase[0], window[0])
    return all(p == w or (p in _CONTRACTIONS and w in _CONTRACTIONS[p]) for p, w in zip(phrase, window))


_HEAD_NEGATORS = frozenset({"nao", "nn"})


def _negative_concord(found: list[Marker]) -> list[Marker]:
    """PT-BR negative concord: in "não afetou nenhum cliente" the n-word after
    "não" repeats the same negation. Relabel it so negation is counted once."""
    out, seen_head = [], False
    for m in found:
        if m.category == "negation" and m.cls == "explicit":
            if fold(m.phrase) in _HEAD_NEGATORS:
                seen_head = True
            elif seen_head:
                m = Marker("negation_concord", "n_word", m.phrase, m.start, m.end)
        out.append(m)
    return out


def _clause_initial(folded: list[str], i: int) -> bool:
    return i == 0 or folded[i - 1] in _CLAUSE_OPENERS


def profile(text: str) -> Counter:
    """Counter of ``category.class`` labels."""
    return Counter(m.label for m in markers(text))
