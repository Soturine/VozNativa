"""Editorial pattern detector for PT-BR (v0.3.0 M2.1).

Finds constructions the references describe as formula (ENEM-style
openings, empty metadiscourse, stacked connectors, gerundismo, support
verbs, courtesy formulas, calques, promotional adjectives, punchlines...)
and respects genre exemptions, so legal nominalizations or a courtesy line
in a WhatsApp message are left alone.

It is descriptive. It is not an authorship or "AI" score and must never be
optimized for its own sake: it tells the rewriter where to look and lets
the engine skip the model when there is nothing to change.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

from .text import sentences, words

DATA = Path(__file__).resolve().parent / "data" / "patterns_pt_br.yml"
STRONG, WEAK = "strong", "weak"


@lru_cache(maxsize=1)
def catalog() -> list[dict]:
    raw = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    out = []
    for p in raw["patterns"]:
        entry = dict(p)
        entry["compiled"] = re.compile(p["regex"], re.IGNORECASE)
        if p.get("requires"):
            entry["requires_re"] = re.compile(p["requires"], re.IGNORECASE)
        out.append(entry)
    return out


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _strength(pattern: dict, genre: str) -> str | None:
    if genre in pattern.get("exempt", []):
        return None
    if genre in pattern.get("weak_in", []):
        return WEAK
    return pattern["strength"]


def detect(text: str, genre: str = "unknown") -> dict:
    text = _nfc(text)
    prose = [s for s in sentences(text) if s.kind in {"prose", "list_item"}]
    findings = []
    for pattern in catalog():
        strength = _strength(pattern, genre)
        if strength is None:
            continue
        rx, scope = pattern["compiled"], pattern["scope"]

        def add(match_text, start, end, sentence):
            if "requires_re" in pattern and not pattern["requires_re"].search(match_text):
                return
            findings.append({"id": pattern["id"], "family": pattern["family"], "strength": strength,
                             "text": match_text, "start": start, "end": end, "sentence": sentence.index,
                             "suggestion": pattern["suggestion"]})

        if scope == "document":
            openers = [s for s in prose if rx.match(s.text.lstrip("\"'“(- "))]
            if len(prose) >= pattern.get("min_sentences", 3) and len(openers) / len(prose) >= pattern["threshold"]:
                findings.append({"id": pattern["id"], "family": pattern["family"], "strength": strength,
                                 "text": f"{len(openers)} de {len(prose)} frases abrem com conectivo",
                                 "start": openers[0].start, "end": openers[0].end, "sentence": openers[0].index,
                                 "suggestion": pattern["suggestion"]})
            continue
        for sent in prose:
            body = sent.text.lstrip("\"'“(- ")
            offset = sent.start + (len(sent.text) - len(body))
            if scope == "sentence_start":
                m = rx.match(body)
                if m:
                    add(m.group(0), offset + m.start(), offset + m.end(), sent)
            elif scope == "sentence":
                m = rx.match(body.strip())
                if m:
                    add(body.strip(), sent.start, sent.end, sent)
            else:
                for m in rx.finditer(sent.text):
                    add(m.group(0), sent.start + m.start(), sent.start + m.end(), sent)

    findings.sort(key=lambda f: f["start"])
    strong = sum(f["strength"] == STRONG for f in findings)
    weak = sum(f["strength"] == WEAK for f in findings)
    n_words = max(1, len(words(text)))
    return {
        "kind": "voznativa.pattern_report",
        "genre": genre,
        "findings": findings,
        "summary": {
            "strong": strong,
            "weak": weak,
            "per_100_words": round(100 * (strong + weak) / n_words, 2),
            "families": sorted({f["family"] for f in findings}),
        },
        # One strong finding, or weak ones in company, justify an edit; otherwise
        # the text is a NO_CHANGE candidate (see references/patterns/false-positives.md).
        "decision": "edit" if strong >= 1 or weak >= 2 else "no_change_candidate",
        "note": "editorial findings, not an authorship score; never optimize for this number",
    }
