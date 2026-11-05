"""Editorial pattern detector for PT-BR (v0.3.0 M2.1; Pattern Library v2 in v0.4.0 M1).

Finds constructions the references describe as formula (ENEM-style
openings, empty metadiscourse, stacked connectives, gerundismo, support
verbs, courtesy formulas, calques, promotional and corporate vagueness,
punchlines, pleonasms, formulaic triads...) and decides by context, not by
the word alone:

* genre and channel: a pattern can be exempt (legal nominalizations,
  courtesy in WhatsApp) or weak in a genre (connectives in academic prose);
* position: an opening formula counts only when it opens, a closing formula
  only at the end;
* function: guards skip uses with a real job (a durative gerund anchored to
  a time, "em suma" closing a long document, a triad after a colon that
  announces a list);
* frequency: a weak pattern becomes strong only when it repeats, and a
  single weak finding never justifies an edit.

It is descriptive. It is not an authorship or "AI" score and must never be
optimized for its own sake: it tells the rewriter where to look and lets
the engine skip the model when there is nothing to change.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import yaml

from .text import canonical, fold, sentences, words

DATA = Path(__file__).resolve().parent / "data" / "patterns_pt_br.yml"
STRONG, WEAK = "strong", "weak"
_LEAD = "\"'“(- "


def _compile(value: str | None):
    return re.compile(value, re.IGNORECASE) if value else None


@lru_cache(maxsize=1)
def catalog() -> list[dict]:
    raw = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    out = []
    for p in raw["patterns"]:
        entry = dict(p)
        entry["compiled"] = _compile(p.get("regex"))
        for key in ("requires", "skip_if_sentence", "skip_if_match", "strong_if_match"):
            entry[key + "_re"] = _compile(p.get(key))
        if p.get("skip_if_both"):
            entry["skip_if_both_re"] = [_compile(r) for r in p["skip_if_both"]]
        out.append(entry)
    return out


@lru_cache(maxsize=1)
def sources() -> dict:
    return yaml.safe_load(DATA.read_text(encoding="utf-8")).get("sources", {})


def _strength(pattern: dict, contexts: set[str]) -> str | None:
    if contexts & set(pattern.get("exempt", [])):
        return None
    if contexts & set(pattern.get("weak_in", [])):
        return WEAK
    return pattern["strength"]


def _position_ok(pattern: dict, sent, prose: list) -> bool:
    where = pattern.get("position")
    if not where:
        return True
    first_in_paragraph = all(s.paragraph != sent.paragraph for s in prose if s.index < sent.index)
    return {"first": sent is prose[0], "last": sent is prose[-1],
            "paragraph_first": first_in_paragraph}.get(where, True)


def _guarded(pattern: dict, match_text: str, sentence_text: str) -> bool:
    """True when a guard says this occurrence has a legitimate function."""
    if pattern.get("requires_re") and not pattern["requires_re"].search(match_text):
        return True
    if pattern.get("skip_if_match_re") and pattern["skip_if_match_re"].search(match_text):
        return True
    if pattern.get("skip_if_sentence_re") and pattern["skip_if_sentence_re"].search(sentence_text):
        return True
    both = pattern.get("skip_if_both_re")
    return bool(both and both[0].search(match_text) and both[1].search(sentence_text))


# --- Structural detectors (not expressible as one regex) ---------------------------

ABSTRACT = re.compile(r"\w+(?:ção|ções|dade|dades|ência|ências|ância|âncias|mento|mentos|ismo|ismos|ura|uras)$", re.I)


def _triads(pattern: dict, prose: list) -> list[tuple]:
    """"X, Y e Z" where at least two items are abstract nouns or evaluative
    adjectives from the catalog list. A colon right before announces a real
    list, which is not a formula."""
    evaluative = {fold(str(w)) for w in pattern.get("evaluative", [])}
    item = r"[A-Za-zÀ-ÿ-]+(?: [A-Za-zÀ-ÿ-]+)?"
    rx = re.compile(rf"(?<![:\w])\s*({item}), ({item}) e ({item})\b", re.I)
    hits = []
    for sent in prose:
        for m in rx.finditer(sent.text):
            prefix = sent.text[:m.start()].rstrip()
            if prefix.endswith(":"):
                continue
            heads = [g.split()[-1] for g in m.groups()]
            vague = sum(bool(ABSTRACT.match(h)) or fold(h) in evaluative for h in heads)
            if vague >= 2:
                hits.append((m.group(0).strip(), sent.start + m.start(), sent.start + m.end(), sent))
    return hits


def _anaphora(pattern: dict, prose: list) -> list[tuple]:
    """Three or more consecutive sentences opening with the same word
    ("É sobre... É sobre... É sobre..."), function words excluded."""
    skip = {fold(str(w)) for w in pattern.get("ignore_openers", [])}
    hits, run = [], []
    for sent in prose + [None]:
        first = fold(words(sent.text)[0]) if sent is not None and words(sent.text) else None
        if run and first == run[-1][0] and first not in skip:
            run.append((first, sent))
            continue
        if len(run) >= pattern.get("min_run", 3):
            s0, sn = run[0][1], run[-1][1]
            hits.append((f"{len(run)} frases seguidas abrem com '{run[0][0]}'", s0.start, sn.end, s0))
        run = [(first, sent)] if first else []
    return hits


def _repeated_evaluation(pattern: dict, prose: list) -> list[tuple]:
    """The same evaluative word used again and again ("fundamental" three
    times in a short text) carries no information after the first."""
    vocabulary = {fold(str(w)) for w in pattern.get("evaluative", [])}
    counts = Counter()
    first_seen = {}
    for sent in prose:
        for token in words(sent.text):
            key = fold(token)
            if key in vocabulary:
                counts[key] += 1
                first_seen.setdefault(key, sent)
    hits = []
    for key, n in counts.items():
        if n >= pattern.get("min_count", 3):
            sent = first_seen[key]
            hits.append((f"'{key}' aparece {n} vezes", sent.start, sent.end, sent))
    return hits


DETECTORS = {"triad": _triads, "anaphora": _anaphora, "repeated_evaluation": _repeated_evaluation}


def detect(text: str, genre: str = "unknown", channel: str | None = None, register: str | None = None) -> dict:
    text = canonical(text)
    contexts = {genre} | ({channel} if channel else set())
    prose = [s for s in sentences(text) if s.kind in {"prose", "list_item"}]
    findings = []
    for pattern in catalog():
        strength = _strength(pattern, contexts)
        if strength is None or not prose:
            continue
        if pattern.get("max_sentences") and len(prose) > pattern["max_sentences"]:
            continue
        rx, scope = pattern["compiled"], pattern["scope"]
        found = []

        def add(match_text, start, end, sentence):
            if _guarded(pattern, match_text, sentence.text) or not _position_ok(pattern, sentence, prose):
                return
            found.append((match_text, start, end, sentence))

        if scope == "detector":
            for hit in DETECTORS[pattern["detector"]](pattern, prose):
                add(*hit)
        elif scope == "document":
            openers = [s for s in prose if rx.match(s.text.lstrip(_LEAD))]
            if len(prose) >= pattern.get("min_sentences", 3) and len(openers) / len(prose) >= pattern["threshold"]:
                found.append((f"{len(openers)} de {len(prose)} frases abrem com conectivo",
                              openers[0].start, openers[0].end, openers[0]))
        else:
            for sent in prose:
                body = sent.text.lstrip(_LEAD)
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

        # A genre that makes the pattern weak (weak_in) caps repetition there; a
        # form listed in strong_if_match is strong in any genre that is not exempt
        # ("a nível de" is wrong in an e-mail as much as in a chat).
        capped = bool(contexts & set(pattern.get("weak_in", [])))
        escalate = pattern.get("escalate")
        for match_text, start, end, sent in found:
            level = strength
            if pattern.get("strong_if_match_re") and pattern["strong_if_match_re"].search(match_text):
                level = STRONG
            if not capped and escalate and len(found) >= escalate:
                level = STRONG  # the pattern repeats: the repetition is the formula
            findings.append({"id": pattern["id"], "family": pattern["family"], "strength": level,
                             "text": match_text, "start": start, "end": end, "sentence": sent.index,
                             "suggestion": pattern["suggestion"],
                             **({"legitimate_when": pattern["legitimate"]} if pattern.get("legitimate") else {})})

    # PT-BR contextual layer: PT-PT forms, foreign terms out of their domain,
    # mixed forms of address, chat/speech forms in a formal register.
    from . import ptbr
    findings += ptbr.findings(text, genre, channel, register)
    findings.sort(key=lambda f: (f["start"], f["id"]))
    strong = sum(f["strength"] == STRONG for f in findings)
    weak = sum(f["strength"] == WEAK for f in findings)
    n_words = max(1, len(words(text)))
    # Weak findings justify an edit only in company, and the company must grow
    # with the text: two weak findings in 600 words are not a pattern.
    weak_needed = max(2, math.ceil(n_words / 150))
    return {
        "kind": "voznativa.pattern_report",
        "schema_version": 2,
        "genre": genre,
        "channel": channel,
        "register": register,
        "findings": findings,
        "summary": {
            "strong": strong,
            "weak": weak,
            "per_100_words": round(100 * (strong + weak) / n_words, 2),
            "families": sorted({f["family"] for f in findings}),
            "weak_needed_for_edit": weak_needed,
        },
        "decision": "edit" if strong >= 1 or weak >= weak_needed else "no_change_candidate",
        "note": "editorial findings, not an authorship score; never optimize for this number",
    }
