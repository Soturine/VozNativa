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


def infer_genre(text: str) -> dict:
    d = data()
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
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    if not ranked or ranked[0][1] < d["min_score"]:
        return {"value": "unknown", "source": "inferred", "confidence": "low",
                "scores": dict(ranked), "reason": "no genre reached the minimum score"}
    top, top_score = ranked[0]
    runner = ranked[1][1] if len(ranked) > 1 else 0.0
    if top_score - runner < d["min_margin"]:
        return {"value": "unknown", "source": "inferred", "confidence": "low", "scores": dict(ranked),
                "reason": f"ambiguous between {top} and {ranked[1][0]}", "candidates": [top, ranked[1][0]]}
    confidence = "high" if top_score - runner >= 3 else "medium"
    return {"value": top, "source": "inferred", "confidence": confidence, "scores": dict(ranked),
            "evidence": evidence.get(top, [])}


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
          spoken: bool | None = None, fact_sources: list[str] | None = None,
          voice_samples: list[str] | None = None, voice_channel: str | None = None,
          repo: str | None = None) -> dict:
    from .text import canonical
    text = canonical(text)
    if task not in TASKS:
        raise ValueError(f"task must be one of {TASKS}")
    if register and register not in REGISTERS:
        raise ValueError(f"register must be one of {REGISTERS}")
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
        "spoken": bool(spoken),
        "register_explicit": bool(register),
        "register_conflict": bool(register and default_register and register != default_register),
        "has_code": bool(re.search(r"```|`[^`\n]+`", text)),
        "has_markdown": bool(re.search(r"(?m)^#{1,6} |^\s*[-*] |\*\*[^*]+\*\*", text)),
    }
    return {
        "schema_version": 1,
        "kind": "voznativa.context_contract",
        "task": task,
        "genre": genre_info,
        "channel": {"value": channel or genre_info["value"], "source": "explicit" if channel else "genre"},
        "audience": audience,
        "register": register_info,
        "targets": {"region": {"code": region.lower() if region else None, "strength": region_strength},
                    "community": community, "slang_strength": slang_strength},
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
    for flag, target in (("regional_target", "region"), ("community_target", "community"),
                         ("slang_target", "slang")):
        if context["flags"].get(flag):
            add(target, context["targets"].get(target if target != "slang" else "slang_strength"), None)
    if profile or context["flags"].get("has_voice_samples"):
        add("voice", "author_profile", None)
    if explicit:
        add("explicit_instruction", sorted(explicit), None)
    return targets


def explicit_channel(context: dict) -> str | None:
    """The channel the user named, or None when it only mirrors the genre."""
    return context["channel"]["value"] if context["channel"]["source"] == "explicit" else None
