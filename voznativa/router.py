"""Context Router: build the Context Contract for a task.

Explicit hints always win over inference. Inference uses weighted surface
cues from ``data/router_pt_br.json`` and returns ``unknown`` when the
evidence is weak or ambiguous, so the Reference Selector loads only the
generic references instead of the wrong genre's rules.

The contract keeps two source lists apart:
* ``fact_sources``: where facts may come from (the original, user notes,
  repository docs/code). Never used for voice.
* ``voice_samples``: texts the author wrote, given explicitly. Never used
  as a source of facts.
"""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "router_pt_br.json"
TASKS = ("rewrite", "audit", "create", "profile", "compare")
REGISTERS = ("colloquial", "casual", "professional-natural", "professional-formal", "technical",
             "academic", "journalistic", "marketing", "spoken", "personalized")


@lru_cache(maxsize=1)
def data() -> dict:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    raw["_compiled"] = {g: [re.compile(p) for p in spec["regex"]] for g, spec in raw["genres"].items()}
    return raw


_NOT_PROSE_LINE = re.compile(r"^\s*(?:[-*•]\s|\d{1,3}[.)]\s|>|```|#{1,6}\s|\|)")
WRAP_MIN_MEDIAN = 45          # characters; chat turns and verse lines are shorter


def unwrap_for_inference(text: str) -> tuple[str, dict]:
    """Join hard-wrapped prose lines (fixed-width editions, e-mail wrapping)
    for *inference only*; the original text is never changed.

    A paragraph is unwrapped when its non-final lines are long (median >= 45
    characters) and most line breaks fall mid-sentence (the line does not end
    a sentence and the next one continues in lower case). Verse (short
    lines), chat turns (short lines), lists, quotes, tables and code keep
    their breaks: those breaks carry structure (v0.7.0 CP5, G1)."""
    out, joined = [], 0
    text = text.replace("\r\n", "\n").replace("\r", "\n")   # CRLF text routed as unknown (metamorphic test)
    for par in re.split(r"(\n[ \t]*\n)", text):
        lines = par.split("\n")
        body = [ln.rstrip() for ln in lines if ln.strip()]
        if len(body) < 2 or par.strip().startswith("```") or any(_NOT_PROSE_LINE.match(ln) for ln in body):
            out.append(par)
            continue
        lengths = sorted(len(ln) for ln in body[:-1])
        median = lengths[len(lengths) // 2]
        breaks = list(zip(body, body[1:]))
        mid = sum(1 for a, b in breaks if not a.endswith((".", "!", "?", ":", ";")) and b.lstrip()[:1].islower())
        if median >= WRAP_MIN_MEDIAN and mid / len(breaks) >= 0.5:
            out.append(" ".join(ln.strip() for ln in body))
            joined += len(breaks)
        else:
            out.append(par)
    return "".join(out), {"joined_line_breaks": joined}


# Spellings that only exist before the Portuguese/Brazilian orthographic reforms
# (1911 PT, 1943/1945 BR): evidence of the time of the text, never of PT-PT.
# Forms shared with current PT-PT ("facto", "acção") are deliberately absent.
_HISTORIC = re.compile(
    r"\b(?:elle|ella|elles|ellas|aquelle|aquella|aquelles|aquellas|d'?elle|n'?elle|ahi|anno|annos|sabbado|"
    r"cousa|cousas|hontem|emfim|comtudo|quasi|pae|mãi|paes|egreja|theatro|thesouro|"
    r"pharmacia|photographia|orthographia|commercio|commodo|effeito|apparecer|apparece|"
    r"succedeu|succede|occasião|occasiao|difficil|differente|annunciar|annuncio|direcção|direccao|"
    r"assumpto|prompto|escripto|escriptor)\b", re.I)


def infer_time_of_text(text: str) -> dict:
    """When the text was written, from spelling only: pre-reform orthography
    (at least two distinct forms) or unknown. Absence of old spelling says
    nothing (modern editions of old texts exist), so it is never 'current'."""
    found = sorted({m.group(0).lower() for m in _HISTORIC.finditer(text)})
    if len(found) >= 2:
        return {"value": "pre_reform_orthography", "source": "inferred", "confidence": "medium",
                "evidence": found[:10], "note": "spelling predates the 1911 (PT) / 1943 (BR) reforms; "
                                                "current PT-PT markers in such text are not evidence of PT-PT"}
    return {"value": "unknown", "source": "inferred", "confidence": "low",
            **({"evidence": found} if found else {})}


def infer_genre(text: str) -> dict:
    d = data()
    text, unwrap = unwrap_for_inference(text)
    scores, evidence = {}, {}
    for genre, patterns in d["_compiled"].items():
        weight = d["genres"][genre]["weight"]
        hits = []
        for pattern in patterns:
            found = pattern.findall(text)
            if found:
                hits.append(f"{pattern.pattern[:40]} x{len(found)}")
                scores[genre] = scores.get(genre, 0.0) + weight * min(3, len(found))
        if hits:
            evidence[genre] = hits
    uncorroborated = {}
    for genre, needed in (d.get("min_distinct_cues") or {}).items():
        if genre in scores and len(evidence.get(genre, [])) < needed:
            uncorroborated[genre] = scores.pop(genre)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    if not ranked or ranked[0][1] < d["min_score"]:
        return {"value": "unknown", "source": "inferred", "confidence": "low",
                "scores": dict(ranked), "reason": "no genre reached the minimum score"}
    top, top_score = ranked[0]
    runner = ranked[1][1] if len(ranked) > 1 else 0.0
    if top_score - runner < d["min_margin"]:
        return {"value": "unknown", "source": "inferred", "confidence": "low", "scores": dict(ranked),
                "reason": f"ambiguous between {top} and {ranked[1][0]}", "candidates": [top, ranked[1][0]],
                "normalization": unwrap}
    confidence = "high" if top_score - runner >= 3 else "medium"
    return {"value": top, "source": "inferred", "confidence": confidence, "scores": dict(ranked),
            "evidence": evidence.get(top, []), "normalization": unwrap}


def _source(path: str, kind: str, channel: str | None = None) -> dict:
    p = Path(path)
    entry = {"path": str(p), "kind": kind}
    if p.is_file():
        entry["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        entry["words"] = len(p.read_text(encoding="utf-8", errors="replace").split())
    else:
        entry["missing"] = True
    if channel:
        entry["channel"] = channel
    return entry


def route(text: str, task: str = "rewrite", genre: str | None = None, channel: str | None = None,
          register: str | None = None, audience: str | None = None, region: str | None = None,
          region_strength: float = 0.0, community: str | None = None, slang_strength: float = 0.0,
          epoch: str | None = None, spoken: bool | None = None, fact_sources: list[str] | None = None,
          voice_samples: list[str] | None = None, voice_channel: str | None = None,
          repo: str | None = None) -> dict:
    from .text import canonical
    text = canonical(text)
    if task not in TASKS:
        raise ValueError(f"task must be one of {TASKS}")
    if register and register not in REGISTERS:
        raise ValueError(f"register must be one of {REGISTERS}")
    from .temporal import parse_epoch
    epoch_info = parse_epoch(epoch)        # ValueError on a malformed epoch, like an unknown register
    d = data()
    genre_info = ({"value": genre, "source": "explicit", "confidence": "explicit"} if genre
                  else infer_genre(text) if text.strip() else
                  {"value": "unknown", "source": "inferred", "confidence": "low", "reason": "empty text"})
    default_register = d["default_register"].get(genre_info["value"])
    register_info = ({"value": register, "source": "explicit"} if register
                     else {"value": default_register, "source": "genre_default" if default_register else "unknown"})
    if spoken is None:
        spoken = any(re.search(cue, text, re.I) for cue in d["spoken_cues"]) and genre_info["value"] in {
            "unknown", "literary", "social"}

    facts = [_source(p, "user_fact") for p in (fact_sources or [])]
    warnings = []
    if repo:
        from .project import scan
        project = scan(repo)
        facts.append({"path": str(Path(repo)), "kind": "repository", "files": project.summary()["files"],
                      "doc_sources": project.summary()["doc_sources"]})
        doc_paths = {str((Path(repo) / d_).resolve()) for d_ in project.doc_sources}
        for sample in voice_samples or []:
            if str(Path(sample).resolve()) in doc_paths:
                warnings.append(f"voice sample {sample} is also a repository doc; repository docs may have "
                                "several authors. Confirm the author wrote it before using it for voice.")
    samples = [_source(p, "voice_sample", voice_channel) for p in (voice_samples or [])]

    flags = {
        "has_voice_samples": bool(samples),
        "regional_target": bool(region) and region_strength > 0,
        "community_target": bool(community),
        "slang_target": slang_strength > 0,
        "epoch_target": epoch_info is not None,
        "spoken": bool(spoken),
        "register_explicit": bool(register),
        "register_conflict": bool(register and default_register and register != default_register),
        "has_code": bool(re.search(r"```|`[^`\n]+`", text)),
        "has_markdown": bool(re.search(r"(?m)^#{1,6} |^\s*[-*] |\*\*[^*]+\*\*", text)),
    }
    time_info = infer_time_of_text(text)
    structure_info = infer_structure(text)
    protections = conservative_protections(genre_info, time_info, structure_info)
    dims = dimensions(task=task, genre_info=genre_info, channel=channel, register_info=register_info,
                      time_info=time_info, epoch_info=epoch_info, text=text, region=region,
                      region_strength=region_strength, community=community, structure_info=structure_info,
                      audience=audience, samples=samples, flags=flags)
    return {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "kind": "voznativa.context_contract",
        "dimensions": dims,
        "protections": protections,
        "task": task,
        "genre": genre_info,
        "channel": {"value": channel or genre_info["value"], "source": "explicit" if channel else "genre"},
        "audience": audience,
        "register": register_info,
        "targets": {"region": {"code": region.lower() if region else None, "strength": region_strength},
                    "community": community, "slang_strength": slang_strength, "epoch": epoch_info},
        "flags": flags,
        "constraints": {
            "preserve_markdown_structure": flags["has_markdown"],
            "preserve_code_verbatim": flags["has_code"],
            # Even in create mode facts come only from fact_sources; fiction is out of scope.
            "invent_facts": False,
        },
        "sources": {"fact_sources": facts, "voice_samples": samples},
        "policy": {
            "facts_from": "original text and fact_sources only",
            "voice_from": "voice_samples only; never repository docs unless the user confirms authorship",
            "infer_identity": False,
        },
        "warnings": warnings,
        "words": len(text.split()),
    }


CONTRACT_SCHEMA_VERSION = 3
# v1 fields (task, genre, channel, register, targets, flags, constraints, sources,
# policy) keep their meaning; v3 adds ``dimensions`` and ``protections``.
DIMENSIONS = ("genre", "channel", "register", "time_of_text", "time_of_target", "language_variant",
              "region_of_text", "target_region", "community", "structure", "audience", "task", "restrictions",
              "author_voice")


def _dim(value, source: str, confidence: str, evidence=None, **extra) -> dict:
    out = {"value": value, "source": source, "confidence": confidence}
    if evidence:
        out["evidence"] = evidence
    out.update(extra)
    return out


def infer_structure(text: str) -> dict:
    """Dominant structure from the long-form block kinds (paragraph-level)."""
    from .longform import blocks
    kinds: dict[str, int] = {}
    for b in blocks(text):
        if b.kind not in ("separator",):
            kinds[b.kind] = kinds.get(b.kind, 0) + b.words
    total = sum(kinds.values())
    if not total:
        return _dim("unknown", "inferred", "low")
    top, words = max(kinds.items(), key=lambda kv: kv[1])
    value = top if words / total >= 0.6 else "mixed"
    return _dim(value, "inferred", "medium" if value != "mixed" else "low",
                {k: round(v / total, 3) for k, v in sorted(kinds.items())})


def infer_language_variant(text: str, time_info: dict) -> dict:
    """PT-PT only on exclusive current markers and no pre-reform spelling;
    PT-BR is never inferred from absence (abstention)."""
    from .ptbr import variant_markers
    markers = variant_markers(text)
    exclusive = sorted({m["text"].lower() for m in markers if m.get("confidence") == "exclusive"})
    if time_info["value"] == "pre_reform_orthography":
        return _dim("unknown", "inferred", "low", exclusive[:5] or None,
                    reason="pre-reform spelling overlaps current PT-PT forms")
    if len(exclusive) >= 2:
        return _dim("pt-PT", "inferred", "medium", exclusive[:5])
    return _dim("unknown", "inferred", "low", exclusive[:5] or None,
                reason="no exclusive marker set; PT-BR is not inferred from absence")


def conservative_protections(genre_info: dict, time_info: dict, structure_info: dict) -> dict:
    """Abstention keeps protections (RN-05): an unknown genre with literary or
    historical evidence gets the literary limits without claiming the genre;
    verse and dialogue structure keep their line breaks whatever the genre."""
    reasons = []
    if genre_info["value"] == "unknown":
        scores = genre_info.get("scores") or {}
        if scores.get("literary", 0) > 0 or "literary" in (genre_info.get("candidates") or []):
            reasons.append("literary cues present although the genre is undecided")
        if time_info["value"] == "pre_reform_orthography":
            reasons.append("pre-reform spelling: a historical text")
    structure = structure_info["value"]
    return {"conservative": bool(reasons), "reasons": reasons,
            "preserve_line_breaks": structure in ("verse", "dialogue", "list", "code"),
            "historical_spelling_is_not_an_error": time_info["value"] == "pre_reform_orthography"}


def dimensions(*, task, genre_info, channel, register_info, time_info, epoch_info, text, region, region_strength,
               community, structure_info, audience, samples, flags) -> dict:
    explicit = "explicit"
    return {
        "genre": genre_info if genre_info.get("source") == explicit else
        _dim(genre_info["value"], "inferred", genre_info.get("confidence", "low"), genre_info.get("evidence"),
             **({"candidates": genre_info["candidates"]} if genre_info.get("candidates") else {})),
        "channel": _dim(channel, explicit, explicit) if channel else _dim("unknown", "unknown", "low"),
        "register": _dim(register_info["value"] or "unknown", register_info["source"],
                         explicit if register_info["source"] == explicit else "low"),
        "time_of_text": time_info,
        "time_of_target": _dim(epoch_info, explicit, explicit) if epoch_info else _dim("unknown", "unknown", "low"),
        "language_variant": infer_language_variant(text, time_info),
        "region_of_text": _dim("unknown", "not_inferred", "low",
                               reason="region is never inferred from the text (policy infer_identity: false)"),
        "target_region": _dim({"code": region.lower(), "strength": region_strength}, explicit, explicit)
        if region else _dim("unknown", "unknown", "low"),
        "community": _dim(community, explicit, explicit) if community else _dim("unknown", "unknown", "low"),
        "structure": structure_info,
        "audience": _dim(audience, explicit, explicit) if audience else _dim("unknown", "unknown", "low"),
        "task": _dim(task, explicit, explicit),
        "restrictions": _dim(sorted(k for k in ("has_code", "has_markdown") if flags.get(k)), "inferred", "high"),
        "author_voice": _dim("voice_samples", explicit, explicit, [s["path"] for s in samples]) if samples
        else _dim("unknown", "unknown", "low"),
    }


def transformation_targets(text: str, context: dict, profile: dict | None = None,
                           explicit: dict | None = None) -> list[dict]:
    """Destination properties the request sets and the source may not meet.

    A text with no editorial finding can still need a rewrite: an e-mail asked
    for WhatsApp, a casual note asked for the formal register, a profile to
    match. Each target says whether the source already differs from it
    (``differs``: True) or whether that cannot be told (None: an explicit
    register on a text of unknown genre, an audience, a voice profile).
    Targets the source already meets are left out, so labeling a text with
    its own genre asks for nothing."""
    d = data()
    explicit_genre = context["genre"]["source"] == "explicit"
    source_genre = infer_genre(text)["value"] if explicit_genre else context["genre"]["value"]
    known = source_genre != "unknown"
    targets = []

    def add(target: str, value, differs):
        if differs is not False:
            targets.append({"target": target, "value": value, "source": source_genre if known else None,
                            "differs": differs})

    # Genre and channel labels are routine context (benchmarks pass them for
    # every case): they ask for a change only when the source is confidently
    # something else, never when its genre is unknown or the channel unmapped.
    groups = [set(g) for g in d.get("compatible_genres", {}).get("groups", [])]

    def different(a: str, b: str) -> bool:
        return a != b and not any(a in g and b in g for g in groups)

    if explicit_genre and known and different(context["genre"]["value"], source_genre):
        add("genre", context["genre"]["value"], True)
    if context["channel"]["source"] == "explicit" and known:
        channel = context["channel"]["value"]
        genre = d.get("channel_genre", {}).get(channel.lower(), channel if channel in d["genres"] else None)
        if genre and different(genre, source_genre):
            add("channel", channel, True)
    if context["flags"].get("register_explicit"):
        source_register = d["default_register"].get(source_genre) if known else None
        register = context["register"]["value"]
        add("register", register, (register != source_register) if source_register else None)
    if context.get("audience"):
        add("audience", context["audience"], None)
    # An epoch alone describes the reader's time; it informs notes and slang
    # activation but does not by itself ask for a rewrite.
    for flag, target, key in (("regional_target", "region", "region"), ("community_target", "community", "community"),
                              ("slang_target", "slang", "slang_strength")):
        if context["flags"].get(flag):
            add(target, context["targets"].get(key), None)
    if profile or context["flags"].get("has_voice_samples"):
        add("voice", "author_profile", None)
    if explicit:
        add("explicit_instruction", sorted(explicit), None)
    return targets


def explicit_channel(context: dict) -> str | None:
    """The channel the user named, or None when it only mirrors the genre."""
    return context["channel"]["value"] if context["channel"]["source"] == "explicit" else None
