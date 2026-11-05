"""Semantic Ledger: the factual inventory a rewrite must preserve.

The ledger is built deterministically from the source text. It records, per
sentence, the protected spans and the semantic markers (negation, modality,
quantifiers, conditions, causality, commitments, attribution). It does not
claim to understand propositions; claim-level checks belong to the judge
layer (see ``voznativa.judge``), which is recorded separately.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from . import signals, spans
from .text import Sentence, canonical, content_stems, fold, sentences, words

SCHEMA_VERSION = 1

# Spans whose inner words belong to the span, not to the sentence's markers.
OPAQUE_TYPES = frozenset({"inline_code", "url", "path", "quote", "code_block", "command", "email",
                          "protected_term"})


@dataclass
class SentenceEntry:
    sentence: Sentence
    spans: list[spans.Span]
    markers: list[signals.Marker]
    stems: list[str]
    tokens: list[str] = field(default_factory=list)  # all non-marker words, for short sentences
    content: str = ""  # sentence text with protected values and markers blanked (punctuation kept)

    def signal_counts(self) -> Counter:
        return Counter(m.label for m in self.markers)

    def as_dict(self) -> dict:
        return {
            "index": self.sentence.index,
            "kind": self.sentence.kind,
            "paragraph": self.sentence.paragraph,
            "text": self.sentence.text,
            "spans": [s.as_dict() for s in self.spans],
            "markers": [{"label": m.label, "text": m.phrase} for m in self.markers],
        }


@dataclass
class Ledger:
    text: str
    entries: list[SentenceEntry]
    spans: list[spans.Span]
    extras: dict = field(default_factory=dict)

    def signal_counts(self) -> Counter:
        total = Counter()
        for entry in self.entries:
            total.update(entry.signal_counts())
        return total

    def stems(self) -> set[str]:
        return {st for entry in self.entries for st in entry.stems}

    def as_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "voznativa.semantic_ledger",
            "method": "deterministic: protected spans + closed-class markers; no claim understanding",
            "sentence_count": len(self.entries),
            "protected": [s.as_dict() for s in self.spans],
            "signals": dict(sorted(self.signal_counts().items())),
            "sentences": [e.as_dict() for e in self.entries],
            **self.extras,
        }


def build(text: str, protect: list[str] | tuple = ()) -> Ledger:
    text = canonical(text)
    all_spans = spans.extract(text, protect=protect)
    entries = []
    for sent in sentences(text):
        inside = [s for s in all_spans if s.start >= sent.start and s.end <= sent.end]
        if sent.kind == "code":
            marks, stems, tokens, content = [], [], [], ""
        else:
            rel = [(s.start - sent.start, s.end - sent.start, s.type) for s in inside]
            masked = _mask(sent.text, [(a, b) for a, b, t in rel if t in OPAQUE_TYPES])
            marks = signals.markers(masked)
            # Alignment and coverage look at propositional content only: protected
            # values are compared by key and markers are compared by label, so both
            # are removed here; otherwise deleting "pode" would also hide the change
            # by lowering sentence similarity.
            content = _mask(masked, [(a, b) for a, b, t in rel if t in spans.HARD_TYPES]
                            + [(m.start, m.end) for m in marks])
            stems = content_stems(content)
            tokens = [fold(w) for w in words(content)]
        entries.append(SentenceEntry(sent, inside, marks, stems, tokens, content))
    return Ledger(text, entries, all_spans)


def _mask(text: str, ranges: list[tuple[int, int]]) -> str:
    """Blank out code/URL/quote spans so their words do not count as markers
    (a quoted "não" belongs to the quote, which is protected as a whole)."""
    chars = list(text)
    for start, end in ranges:
        for i in range(max(0, start), min(len(chars), end)):
            chars[i] = " "
    return "".join(chars)
