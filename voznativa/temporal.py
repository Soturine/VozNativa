"""Temporal slang intelligence (v0.6.0): slang only where time evidence exists.

The lexicon (``data/slang/lexicon.yml``, contract in references/slang/schema.yml)
lists informal forms with their meanings, ambiguity, register range and the
periods in which VozNativa's own corpora attest them.

Questions this module answers, always with reasons:

* ``observe``: which lexicon forms a text uses (the author's words; the
  rewrite keeps them unless the request changes the register).
* ``parse_epoch``: what period a request names (``current``, a year or a
  range); ``None`` means no temporal target.
* ``activate``: whether slang may be added for this request. Abstention is
  the default and the reasons say why: no slang requested, a context the
  entry forbids, no attestation inside the requested epoch, a stale
  verification, evidence below E2, or generation not allowed by the entry.
* ``epoch_notes``: forms in the text with no attestation in the requested
  epoch (information for the author, never an automatic removal).
* ``introduced_terms``: lexicon forms a candidate added that the source did
  not have and the activation did not license (the stuffing guard).

Nothing here infers a writer's age or generation from the forms they use.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

SCHEMA_VERSION = 2
LEXICON = Path(__file__).resolve().parent / "data" / "slang" / "lexicon.yml"
ATTESTATIONS = "attestations.yml"   # next to the lexicon; written by scripts/slang_attest.py
EVIDENCE = ("E0", "E1", "E2", "E3", "E4")
TYPES = ("slang", "meme", "interjection", "address_term", "intensifier", "discourse_marker", "borrowing",
         "chat_form")
REGISTERS = ("very_casual", "casual", "neutral", "formal")
# Router registers on the lexicon's formality scale ("personalized" says nothing about formality).
FORMALITY = {"colloquial": "very_casual", "casual": "casual", "spoken": "casual", "professional-natural": "neutral",
             "marketing": "neutral", "journalistic": "neutral", "professional-formal": "formal",
             "technical": "formal", "academic": "formal", **{r: r for r in REGISTERS}}
DETECTION = ("form", "context")
DEPRECATION = ("active", "fading", "dated", "obsolete")
ENTRY_REQUIRED = ("id", "term", "forms", "type", "meanings", "ambiguity")
STALE_AFTER_DAYS = 548           # 18 months: slang verified longer ago is not offered
GENERATION_MIN_EVIDENCE = "E2"


def _norm(text: str) -> str:
    """Lower-case and NFC, keeping accents ("pô" is not "pó", "mó" is not "mo")."""
    return unicodedata.normalize("NFC", text.lower())


def _merge(defaults: dict, entry: dict) -> dict:
    out = dict(entry)
    for key in ("register", "generation"):
        out[key] = {**(defaults.get(key) or {}), **(entry.get(key) or {})}
    out.setdefault("period", {})
    out["period"] = {"attestations": [], "observed_from": None, "observed_until": None, "last_verified_at": None,
                     **out["period"]}
    out.setdefault("evidence", {"level": "E0", "sources": [], "notes": []})
    out.setdefault("deprecation", {"status": "active", "reason": None})
    return out


def validate_lexicon(lexicon: dict) -> list[str]:
    problems = []
    if lexicon.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version must be {SCHEMA_VERSION}")
    if lexicon.get("kind") != "voznativa.slang_lexicon":
        problems.append("kind must be voznativa.slang_lexicon")
    seen = set()
    for raw in lexicon.get("entries") or []:
        entry = _merge(lexicon.get("defaults") or {}, raw)
        eid = entry.get("id")
        problems += [f"{eid}: missing {k}" for k in ENTRY_REQUIRED if not entry.get(k) and entry.get(k) != []]
        if eid in seen:
            problems.append(f"duplicate id {eid}")
        seen.add(eid)
        if entry.get("type") not in TYPES:
            problems.append(f"{eid}: type must be one of {TYPES}")
        amb = entry.get("ambiguity") or {}
        if amb.get("ambiguous"):
            if not amb.get("other_senses"):
                problems.append(f"{eid}: an ambiguous entry must list other_senses")
            if amb.get("detection") not in DETECTION:
                problems.append(f"{eid}: an ambiguous entry needs detection form|context")
            if amb.get("detection") == "context" and not entry.get("detect"):
                problems.append(f"{eid}: context detection needs a detect pattern")
        reg = entry["register"]
        if reg.get("min") not in REGISTERS or reg.get("max") not in REGISTERS:
            problems.append(f"{eid}: register min/max must be in {REGISTERS}")
        level = entry["evidence"].get("level")
        if level not in EVIDENCE:
            problems.append(f"{eid}: evidence.level must be one of {EVIDENCE}")
        attested = [a for a in entry["period"]["attestations"] if a.get("count", 0) > 0]
        for a in entry["period"]["attestations"]:
            if not all(a.get(k) is not None for k in ("source", "from", "to", "count", "words", "run")):
                problems.append(f"{eid}: an attestation needs source, from, to, count, words and run")
        if level != "E0" and not attested:
            problems.append(f"{eid}: evidence {level} needs at least one attestation with count > 0")
        if entry["generation"].get("allowed") and EVIDENCE.index(level) < EVIDENCE.index(GENERATION_MIN_EVIDENCE):
            problems.append(f"{eid}: generation needs evidence {GENERATION_MIN_EVIDENCE} or higher")
        if entry["deprecation"].get("status") not in DEPRECATION:
            problems.append(f"{eid}: deprecation.status must be one of {DEPRECATION}")
        if entry["deprecation"].get("status") != "active" and not entry["deprecation"].get("reason"):
            problems.append(f"{eid}: a non-active entry needs deprecation.reason")
        try:
            _pattern(entry)
        except re.error as exc:
            problems.append(f"{eid}: invalid detect pattern ({exc})")
    return problems


def _pattern(entry: dict) -> re.Pattern:
    if entry.get("detect"):
        return re.compile(entry["detect"], re.I)
    forms = sorted({_norm(f) for f in entry["forms"]}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(f) for f in forms) + r")(?!\w)", re.I)


def _with_attestations(raw: dict, path: Path) -> dict:
    """Merge the machine-written attestation file (period and evidence per id)."""
    att_path = path.parent / ATTESTATIONS
    if not att_path.is_file():
        return raw
    att = yaml.safe_load(att_path.read_text(encoding="utf-8")) or {}
    by_id = att.get("entries") or {}
    unknown = sorted(set(by_id) - {e.get("id") for e in raw.get("entries") or []})
    if unknown:
        raise ValueError(f"attestations for unknown lexicon ids: {unknown}")
    merged = []
    for e in raw.get("entries") or []:
        extra = by_id.get(e.get("id")) or {}
        merged.append({**e, **{k: extra[k] for k in ("period", "evidence") if k in extra}})
    return {**raw, "entries": merged}


@lru_cache(maxsize=4)
def _load(path: str) -> dict:
    raw = _with_attestations(yaml.safe_load(Path(path).read_text(encoding="utf-8")), Path(path))
    problems = validate_lexicon(raw)
    if problems:
        raise ValueError(f"invalid slang lexicon {path}: " + "; ".join(problems))
    entries = tuple(_merge(raw.get("defaults") or {}, e) for e in raw["entries"])
    return {**{k: v for k, v in raw.items() if k != "entries"}, "entries": entries,
            "_rx": tuple((e, _pattern(e)) for e in entries)}


def load_lexicon(path: Path | None = None) -> dict:
    return _load(str(path or LEXICON))


def observe(text: str, path: Path | None = None) -> list[dict]:
    """Lexicon forms in the text, with offsets (accent-sensitive)."""
    plain = _norm(text or "")
    found = []
    for entry, rx in load_lexicon(path)["_rx"]:
        for hit in rx.finditer(plain):
            found.append({"id": entry["id"], "term": entry["term"], "text": text[hit.start():hit.end()],
                          "start": hit.start(), "end": hit.end(), "type": entry["type"],
                          "ambiguous": bool(entry["ambiguity"].get("ambiguous"))})
    return sorted(found, key=lambda f: (f["start"], f["id"]))


# --- epochs --------------------------------------------------------------------------------

_EPOCH = re.compile(r"^(\d{4})(?:\s*[-–]\s*(\d{4}))?$")


def parse_epoch(spec: str | None, today: date | None = None) -> dict | None:
    """``current`` (the last 2 years up to today), ``1995`` or ``1994-1996``."""
    if spec in (None, "", "none"):
        return None
    today = today or date.today()
    if spec == "current":
        return {"spec": spec, "from": today.year - 2, "to": today.year}
    m = _EPOCH.match(str(spec).strip())
    if not m:
        raise ValueError(f"epoch must be 'current', a year or a range like 1994-1996, not {spec!r}")
    start, end = int(m.group(1)), int(m.group(2) or m.group(1))
    if start > end or end > today.year:
        raise ValueError(f"epoch {spec!r} must be an ordered range that does not end after {today.year}")
    return {"spec": str(spec), "from": start, "to": end}


def attested_in(entry: dict, epoch: dict) -> list[dict]:
    return [a for a in entry["period"]["attestations"]
            if a.get("count", 0) > 0 and a["from"] <= epoch["to"] and a["to"] >= epoch["from"]]


def _stale(entry: dict, today: date) -> bool:
    verified = entry["period"].get("last_verified_at")
    if not verified:
        return True
    return (today - date.fromisoformat(str(verified))).days > STALE_AFTER_DAYS


def entry_status(entry: dict, epoch: dict | None, genre: str, register: str | None, today: date) -> dict:
    """Whether this entry may be offered for generation, and why not."""
    reasons = []
    gen = entry["generation"]
    if not gen.get("allowed"):
        reasons.append("generation not allowed by the entry")
    level = entry["evidence"]["level"]
    if EVIDENCE.index(level) < EVIDENCE.index(GENERATION_MIN_EVIDENCE):
        reasons.append(f"evidence {level} < {GENERATION_MIN_EVIDENCE}")
    if genre in gen.get("forbidden_contexts", []):
        reasons.append(f"genre {genre!r} is a forbidden context")
    formality = FORMALITY.get(register or "")
    if formality and REGISTERS.index(formality) > REGISTERS.index(entry["register"]["max"]):
        reasons.append(f"register {register!r} is above the entry's maximum {entry['register']['max']!r}")
    if epoch and not attested_in(entry, epoch):
        reasons.append(f"no attestation in {epoch['from']}-{epoch['to']}")
    if _stale(entry, today):
        reasons.append("verification missing or older than 18 months")
    if entry["deprecation"]["status"] != "active":
        reasons.append(f"deprecation status {entry['deprecation']['status']}")
    return {"id": entry["id"], "allowed": not reasons, "reasons": reasons}


def activate(context: dict, text: str | None = None, profile: dict | None = None, today: date | None = None,
             path: Path | None = None) -> dict:
    """Which slang may inform this rewrite: the author's own forms are always
    kept; new forms only for a request that asks for slang and an entry whose
    evidence covers the requested epoch, genre and register."""
    today = today or date.today()
    targets = context.get("targets") or {}
    requested = float(targets.get("slang_strength") or 0.0)
    epoch = targets.get("epoch")
    genre = (context.get("genre") or {}).get("value", "unknown")
    register = (context.get("register") or {}).get("value")
    in_text = observe(text, path) if text is not None else []
    out = {"kind": "voznativa.temporal_activation", "schema_version": SCHEMA_VERSION,
           "requested": {"slang_strength": requested, "epoch": epoch}, "status": "abstain", "reasons": [],
           "keep": sorted({f["text"].lower() for f in in_text}), "allowed": [], "effective_strength": 0.0,
           "epoch_notes": epoch_notes(in_text, epoch, path) if epoch else []}
    if in_text:
        out["reasons"].append("the text already uses " + ", ".join(repr(t) for t in out["keep"])
                              + ": the author's forms are kept")
    if requested <= 0:
        out["reasons"].append("no slang requested: VozNativa never adds slang on its own")
        return out
    statuses = [entry_status(e, epoch, genre, register, today) for e in load_lexicon(path)["entries"]]
    out["allowed"] = [s["id"] for s in statuses if s["allowed"]]
    if not out["allowed"]:
        tally: dict[str, int] = {}
        for s in statuses:
            for reason in s["reasons"]:
                key = re.sub(r"'[^']*'|\d{4}-\d{4}|E\d", "…", reason)
                tally[key] = tally.get(key, 0) + 1
        out["reasons"].append(f"no lexicon entry may be added ({len(statuses)} entries): "
                              + "; ".join(f"{k} ({v})" for k, v in sorted(tally.items(), key=lambda x: -x[1])))
        return out
    out["status"] = "active"
    out["effective_strength"] = round(min(requested, 0.3), 3)
    return out


def epoch_notes(found: list[dict], epoch: dict | None, path: Path | None = None) -> list[dict]:
    """Forms in the text with no attestation in the requested epoch. A note,
    not a correction: absence from two corpora is not absence from the language."""
    if not epoch:
        return []
    entries = {e["id"]: e for e in load_lexicon(path)["entries"]}
    notes, seen = [], set()
    for f in found:
        if f["id"] in seen:
            continue
        seen.add(f["id"])
        entry = entries[f["id"]]
        if not attested_in(entry, epoch):
            spans = sorted({(a["from"], a["to"]) for a in entry["period"]["attestations"] if a.get("count", 0) > 0})
            notes.append({"id": f["id"], "text": f["text"], "attested": [f"{a}-{b}" for a, b in spans],
                          "note": "no attestation in the requested epoch in VozNativa's corpora"})
    return notes


def introduced_terms(original: str, candidate: str, activation: dict | None = None,
                     path: Path | None = None) -> list[dict]:
    """Lexicon forms the candidate added that the source lacked and the
    activation did not license."""
    licensed = set((activation or {}).get("allowed") or [])
    before = {(f["id"], f["text"].lower()) for f in observe(original, path)}
    seen_ids = {i for i, _ in before}
    out = []
    for f in observe(candidate, path):
        if f["id"] in licensed or f["id"] in seen_ids or (f["id"], f["text"].lower()) in before:
            continue
        out.append({"id": f["id"], "form": f["text"], "type": f["type"]})
    return out
