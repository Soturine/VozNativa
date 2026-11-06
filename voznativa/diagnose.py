"""Original-error awareness and editorial modes (v0.7.0 CP9D).

The original is evidence of what the author meant, not proof that it is
correct. ``diagnose`` reports what may be wrong *in the source*, typed, with
offsets, severity, confidence and the action the editorial mode allows. It
never edits by itself; ``proofread`` applies only high-confidence formal
fixes, and only in a mode that authorises them.

Classes (the addendum's seven):

* ``formal_error``           clearly identifiable form error ("o o")
* ``possible_contextual_error`` may be an error; a person decides
* ``internal_contradiction`` the document disagrees with itself
* ``source_mismatch``        a value disagrees with an authorised source
* ``legitimate_choice``      looks unusual, is legitimate (pre-reform spelling)
* ``literary_license``       repetition or form that is the author's art
* ``unresolved_ambiguity``   cannot be decided; no correction

Absence of evidence is never falsity: a value not found in the sources is
``no_evidence`` (information), not a mismatch. Fiction and poetry are not
checked against external facts.

Editorial modes extend the existing tasks instead of a parallel API:
PRESERVE and REVIEW never change the text; PROOFREAD applies formal fixes;
POLISH edits form without content; ADAPT changes a requested destination
(genre, channel, register, audience: ``router.transformation_targets``);
CREATE is the ``create`` task.
"""
from __future__ import annotations

import re

SCHEMA_VERSION = 1
CLASSES = ("formal_error", "possible_contextual_error", "internal_contradiction", "source_mismatch",
           "legitimate_choice", "literary_license", "unresolved_ambiguity", "no_evidence")
MODES = {
    "PRESERVE": {"task": "audit", "rewrite": False, "authorized": []},
    "REVIEW": {"task": "audit", "rewrite": False, "authorized": []},
    "PROOFREAD": {"task": "rewrite", "rewrite": False, "authorized": ["formal_error"]},
    "POLISH": {"task": "rewrite", "rewrite": True, "authorized": ["formal_error", "style", "formula"]},
    "ADAPT": {"task": "rewrite", "rewrite": True,
              "authorized": ["formal_error", "style", "formula", "destination"]},
    "CREATE": {"task": "create", "rewrite": True, "authorized": ["new_text_from_sources"]},
}
NEVER_AUTO = ("facts", "plot", "causality", "intent", "commitments")
# Spaces only between the two words: a heading followed by a paragraph that starts with
# the same word ("Registro\n\nRegistro é...") is not a typo (v0.7.0 CP9D, human-text check).
_REPEATED_WORD = re.compile(r"(?<![\w-])([^\W\d_]{1,12})[ \t]+\1\b", re.I | re.U)
_ACRONYM_DEF = re.compile(r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w ÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç-]{3,80}?)\s*\(([A-Z]{2,8})\)")
# Reduplication that is Portuguese, not a typo.
LEGIT_REPEATS = {"bem", "muito", "pouco", "corre", "pisca", "quase", "agora", "não", "nao", "sim", "já", "ja",
                 "logo", "devagar", "bate", "pega", "lambe", "puxa", "mata", "quebra", "tão", "tao", "mais",
                 "se", "que",   # "se se deixar" (conjunction + reflexive), "o que que é" (colloquial)
                 "bla", "blá", "ai", "ok", "ha", "há", "he", "hum", "oi", "ei", "tchau", "bora", "pois", "tá", "ta"}


def mode_policy(mode: str | None) -> dict:
    """What a mode authorises (None: the tool's default rewrite behaviour)."""
    if mode is None:
        return {"mode": None, "rewrite": True, "authorized": ["formal_error", "style", "formula", "destination"],
                "never_automatic": list(NEVER_AUTO)}
    key = mode.upper()
    if key not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    return {"mode": key, **MODES[key], "never_automatic": list(NEVER_AUTO)}


def _d(cls, kind, severity, confidence, start, end, text, message, impact, action, **extra) -> dict:
    return {"class": cls, "type": kind, "severity": severity, "confidence": confidence, "start": start, "end": end,
            "text": text, "message": message, "impact": impact, "action": action, **extra}


def _artistic(context: dict | None, text: str) -> bool:
    from .longform import literary_policy
    genre = ((context or {}).get("genre") or {}).get("value", "unknown")
    conservative = bool(((context or {}).get("protections") or {}).get("conservative"))
    return literary_policy(text, genre, conservative=conservative)["policy"] != "default"


def diagnose(text: str, context: dict | None = None, facts: list[str] | None = None) -> dict:
    """Typed diagnostics of the source. Each says what action is allowed:
    ``auto_fix`` (formal, high confidence; applied only by PROOFREAD and up),
    ``suggest`` (a person decides) or ``preserve``."""
    from . import ledger as ledger_mod
    from .planner import _weekday_conflicts
    from .router import infer_time_of_text
    out = []
    artistic = _artistic(context, text)
    genre = ((context or {}).get("genre") or {}).get("value")
    register = ((context or {}).get("register") or {}).get("value")
    informal = genre in ("whatsapp", "social") or register in ("colloquial", "casual") or bool(
        re.search(r"\b(?:vc|pq|tbm|kkk+|rs|blz|vlw)\b", text, re.I))

    for m in _REPEATED_WORD.finditer(text):
        word = m.group(1).lower()
        second = m.group(0).split()[-1]
        symbol = len(word) == 1 and word not in "oaeéà"
        if word in LEGIT_REPEATS or symbol or (m.group(1)[:1].isupper() and second[:1].isupper()):
            # reduplicated names ("Dee Dee", "Boutros Boutros-Ghali"), grammatical pairs, symbols ("x x")
            continue
        if artistic:
            out.append(_d("literary_license", "repetition", "info", "medium", m.start(), m.end(), m.group(0),
                          "repeated word in literary or verse text: may be the author's choice", "none", "preserve"))
        elif informal:
            # "ruim ruim" in a review is emphasis as often as a slip: a person decides.
            out.append(_d("possible_contextual_error", "repeated_word", "info", "low", m.start(), m.end(), m.group(0),
                          f"'{m.group(1)}' repeated in informal text: emphasis or slip", "form only", "suggest"))
        else:
            out.append(_d("formal_error", "repeated_word", "minor", "high", m.start(), m.end(), m.group(0),
                          f"'{m.group(1)}' repeated", "form only", "auto_fix", fix=m.group(1)))

    led = ledger_mod.build(text)
    for w in _weekday_conflicts(led):
        sentence = led.entries[w["sentence"]].sentence
        out.append(_d("internal_contradiction", "weekday_date_mismatch", "major", "high", sentence.start,
                      sentence.end, sentence.text, w.get("message", "weekday does not match the date"),
                      "facts", "suggest"))

    defs: dict[str, set] = {}
    positions: dict[str, tuple] = {}
    for m in _ACRONYM_DEF.finditer(text):
        expansion = " ".join(m.group(1).split()[-6:]).lower()
        defs.setdefault(m.group(2), set()).add(expansion)
        positions.setdefault(m.group(2), (m.start(), m.end()))
    for acronym, expansions in defs.items():
        if len(expansions) > 1:
            start, end = positions[acronym]
            out.append(_d("internal_contradiction", "acronym_redefined", "major", "medium", start, end, acronym,
                          f"{acronym} is introduced with different expansions: {sorted(expansions)}",
                          "terminology", "suggest"))

    seen: dict[str, tuple] = {}
    for entry in led.entries:
        key = " ".join(entry.sentence.text.lower().split())
        if len(key.split()) >= 6 and key in seen:
            cls = "literary_license" if artistic else "possible_contextual_error"
            out.append(_d(cls, "repeated_sentence", "info" if artistic else "minor", "high", entry.sentence.start,
                          entry.sentence.end, entry.sentence.text, "the same sentence appears twice",
                          "none" if artistic else "redundancy", "preserve" if artistic else "suggest"))
        seen.setdefault(key, (entry.sentence.start, entry.sentence.end))

    time_info = infer_time_of_text(text)
    if time_info["value"] == "pre_reform_orthography":
        out.append(_d("legitimate_choice", "historical_spelling", "info", "medium", 0, 0, ", ".join(time_info["evidence"]),
                      "pre-reform spelling: the text's time, not an error to modernise without a request",
                      "none", "preserve"))

    out += _tense_mix(text, artistic)
    grounding = _grounding(text, facts, context)
    out += grounding["diagnostics"]
    out.sort(key=lambda d: (d["start"], d["class"]))
    counts = {c: sum(d["class"] == c for d in out) for c in CLASSES}
    return {"kind": "voznativa.diagnosis", "schema_version": SCHEMA_VERSION, "diagnostics": out,
            "counts": {k: v for k, v in counts.items() if v}, "grounding": grounding["status"],
            "note": "diagnostics of the source; none is applied automatically except formal fixes in an "
                    "authorising mode"}


def _tense_mix(text: str, artistic: bool) -> list[dict]:
    """Adjacent narrative sentences switching between preterite and present
    may be a slip or a historical present: always an unresolved ambiguity."""
    from .morph import tense_profile
    from .text import sentences
    out = []
    labels = []
    for s in sentences(text):
        tenses = {next(iter(v)) for v in tense_profile(s.text, prefer_indicative=True).values() if len(v) == 1}
        labels.append((s, tenses))
    for (a, ta), (b, tb) in zip(labels, labels[1:]):
        if ta == {"pret_perf"} and tb == {"pres_ind"} and not artistic:
            out.append(_d("unresolved_ambiguity", "tense_switch", "info", "low", b.start, b.end, b.text,
                          "narration switches from preterite to present: a slip or a historical present",
                          "time of events", "suggest"))
    return out


def _grounding(text: str, facts: list[str] | None, context: dict | None) -> dict:
    """Values of the text against authorised sources. A value whose context
    words match a source value of the same type with another key is a
    mismatch; a value absent from every source is no_evidence (never false)."""
    if not facts:
        return {"status": "not_requested", "diagnostics": []}
    genre = ((context or {}).get("genre") or {}).get("value")
    if genre == "literary":
        return {"status": "skipped_fiction", "diagnostics": []}
    from .spans import HARD_TYPES, extract
    source_spans = [s for f in facts for s in extract(f) if s.type in HARD_TYPES]
    keys = {s.key for s in source_spans}
    out = []
    for span in extract(text):
        if span.type not in HARD_TYPES or span.key in keys:
            continue
        rivals = [s for s in source_spans if s.type == span.type and set(s.anchors) & set(span.anchors)]
        if rivals:
            out.append(_d("source_mismatch", f"{span.type}_differs", "major", "medium", span.start, span.end,
                          span.text, f"the source gives {rivals[0].text} in the same context", "facts", "suggest",
                          source_value=rivals[0].text))
        else:
            out.append(_d("no_evidence", f"{span.type}_not_in_sources", "info", "high", span.start, span.end,
                          span.text, "not found in the authorised sources (absence is not falsity)", "none",
                          "suggest"))
    return {"status": "checked", "diagnostics": out}


def proofread(text: str, diagnosis: dict, mode: str | None) -> dict:
    """Apply the fixes the mode authorises (formal, high confidence, auto_fix).
    Everything else stays as a suggestion. Returns the text and what changed."""
    policy = mode_policy(mode)
    if "formal_error" not in policy["authorized"]:
        return {"text": text, "applied": [], "mode": policy["mode"], "reason": "mode does not authorise edits"}
    fixes = [d for d in diagnosis["diagnostics"] if d["class"] == "formal_error" and d["action"] == "auto_fix"
             and d["confidence"] == "high" and "fix" in d]
    out, last, applied = [], 0, []
    for d in sorted(fixes, key=lambda d: d["start"]):
        if d["start"] < last:
            continue
        out.append(text[last:d["start"]] + d["fix"])
        last = d["end"]
        applied.append({"type": d["type"], "before": d["text"], "after": d["fix"], "start": d["start"]})
    out.append(text[last:])
    return {"text": "".join(out), "applied": applied, "mode": policy["mode"]}
