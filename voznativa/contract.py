"""Voice Contract resolver: implements references/VOICE_STACK.md precedence.

Layers, highest first:
  1. semantic preservation + mandatory genre constraints (never overridden)
  2. explicit user instruction
  3. author profile for this channel
  4. author general profile
  5. genre/channel preferences
  6. register
  7. community and temporal slang (evidence packs; the author's own forms win)
  8. regionality
  9. pt-BR default

Every resolved feature records the layer that set it and a confidence, so the
Rewrite Engine receives a contract instead of "write like a Brazilian", and
evals can reproduce the decision. Low evidence with high stylistic impact
resolves to ``follow_source``: keep the original's style.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from .drift import DEFAULT_FLOOR, SCALE_FLOOR
from .profile import confidence as habit_confidence

DATA = Path(__file__).resolve().parent / "data" / "voice_defaults.yml"

REGISTER_PREFERENCES = {
    "colloquial": {"contractions": "high"},
    "casual": {"contractions": "medium"},
    "professional-natural": {"contractions": "low", "emoji": "none"},
    "professional-formal": {"contractions": "none", "abbreviations": "none", "emoji": "none", "exclamation": "none"},
    "technical": {"contractions": "none", "emoji": "none"},
    "academic": {"contractions": "none", "emoji": "none", "exclamation": "none"},
    "journalistic": {"contractions": "none", "emoji": "none"},
    "marketing": {},
    "spoken": {"contractions": "high", "sentence_rhythm": "short-mixed"},
    "personalized": {},
}

# Explicit requests that conflict with a mandatory constraint.
CONSTRAINT_CONFLICTS = {
    "no_slang": {"slang_strength": lambda v: v and float(v) > 0},
}

DO_NOT = [
    "alterar valores protegidos (números, datas, valores, código, caminhos, citações, nomes)",
    "alterar negação, modalidade, quantificadores, condições, causalidade ou compromissos",
    "inventar fatos, experiências, fontes, clientes, motivos ou benefícios",
    "inserir marcas regionais ou gírias para sinalizar identidade",
    "inferir idade, gênero, origem, classe ou personalidade do autor",
    "otimizar para score de detector de IA",
]


@lru_cache(maxsize=1)
def defaults() -> dict:
    return yaml.safe_load(DATA.read_text(encoding="utf-8"))


def _bucket(feature: str, value: float) -> str:
    if feature == "sentence_rhythm":
        return "short" if value < 10 else "mixed" if value <= 18 else "long"
    if feature == "em_dash":
        return "none" if value == 0 else "occasional" if value < 0.5 else "frequent"
    if feature == "contractions":
        return "none" if value == 0 else "low" if value < 1 else "medium" if value < 3 else "high"
    if feature == "abbreviations":
        return "none" if value == 0 else "author_list"
    if feature == "emoji":
        return "none" if value == 0 else "occasional" if value < 1 else "frequent"
    if feature == "exclamation":
        return "none" if value == 0 else "rare" if value < 0.15 else "frequent"
    if feature == "first_person":
        return "used" if value >= 0.5 else "rare"
    if feature == "lowercase_starts":
        return "true" if value > 0.5 else "false"
    if feature == "lists":
        return "frequent" if value > 0.2 else "when_enumerative"
    return str(value)


def _profile_layer(profile: dict, stats: dict, scope: str) -> dict:
    mapping = defaults()["profile_features"]
    n = profile["source"]["sample_count"]
    out = {}
    for feature, stat in mapping.items():
        if stat not in stats:
            continue
        mean, stdev = stats[stat]["mean"], stats[stat]["stdev"]
        value = _bucket(feature, mean)
        # Confidence grows with sample count and halves when the feature is
        # unstable across windows (spread larger than its meaningful scale).
        scale = max(SCALE_FLOOR.get(stat, DEFAULT_FLOOR), abs(mean))
        stable = stdev is None or stdev <= scale
        out[feature] = {"value": value, "source": scope,
                        "confidence": round(habit_confidence(n, n) * (1.0 if stable else 0.5), 3)}
    abbreviations = [h["id"].split(".", 1)[1] for h in profile.get("habits", [])
                     if h["id"].startswith("abbreviation.") and h["confidence"] >= 0.5]
    if abbreviations and "abbreviations" in out:
        out["abbreviations"]["allowed"] = abbreviations
    return out


def resolve(context: dict, profile: dict | None = None, explicit: dict | None = None, text: str | None = None) -> dict:
    d = defaults()
    genre = context["genre"]["value"]
    genre_spec = d["genres"].get(genre, d["genres"]["unknown"])
    register = (explicit or {}).get("register") or context["register"]["value"] or d["pt_br_default"]["register"]
    features: dict[str, dict] = {}
    trace, warnings, conflicts = [], [], []

    def apply(layer: str, values: dict, conf=None):
        for key, value in values.items():
            entry = value if isinstance(value, dict) else {"value": value, "source": layer, "confidence": conf}
            features[key] = entry
        if values:
            trace.append(layer)

    # 9 -> 5: defaults up to genre preferences (later layers overwrite earlier ones)
    apply("pt_br_default", d["pt_br_default"])
    region = context["targets"]["region"]
    requested_region = float(region.get("strength") or 0.0)
    # Regionality only through an evidence pack (v0.5.0): with no pack for the
    # requested region, a context its evidence does not cover, or nothing in
    # the text to apply it to, the effective strength stays 0.
    from .regional import activate, decision_view
    regional = activate(context, text, profile)
    if requested_region > 0 and regional["status"] != "active":
        warnings.append("regional strength stays 0.0: " + "; ".join(regional["reasons"]))
    # Community context (v0.6.0 packs): terms of the requested context of
    # practice that the author wrote are kept; no pack adds terms.
    from .community import activate as community_activate
    community = community_activate(context, text)
    community_terms = sorted({f["term"] for f in community["keep"]})
    if community["requested"] and community["pack"] is None:
        warnings.append("; ".join(community["reasons"]))
    elif community["pack"] and community["pack"]["status"] == "draft":
        warnings.append(f"community pack '{community['pack']['id']}' is a draft; terms are preserved, never inserted")
    apply("register", REGISTER_PREFERENCES.get(register, {}))
    apply("genre_preferences", genre_spec.get("preferences", {}))

    # 4 -> 3: author profile, general then same channel
    maturity = profile.get("maturity") if profile else None
    if profile:
        if maturity == "explicit_only":
            warnings.append("profile has too little evidence (explicit_only); author-dependent features "
                            "follow the source text instead of the profile")
        else:
            apply("author_profile", _profile_layer(profile, profile["style"], "author_profile"))
            channel = context["channel"]["value"]
            if channel in profile.get("channels", {}):
                apply("author_channel_profile",
                      _profile_layer(profile, profile["channels"][channel], f"author_channel_profile:{channel}"))

    # Unresolved "per_author" preferences fall back to the source style.
    for key, entry in features.items():
        if entry["value"] == "per_author":
            features[key] = {"value": "follow_source", "source": "no_author_evidence", "confidence": None}
        elif entry["source"].startswith("author") and (entry.get("confidence") or 0) < 0.5:
            features[key] = {"value": "follow_source", "source": f"{entry['source']} (confidence "
                             f"{entry['confidence']} < 0.5)", "confidence": entry["confidence"]}

    # 2: explicit instruction
    explicit = dict(explicit or {})
    slang_requested = float(explicit.get("slang_strength", context["targets"].get("slang_strength") or 0.0))
    constraints = list(genre_spec.get("constraints", []))
    for constraint in constraints:
        for key, violates in CONSTRAINT_CONFLICTS.get(constraint, {}).items():
            if key in explicit and violates(explicit[key]):
                conflicts.append({"request": {key: explicit[key]}, "constraint": constraint,
                                  "resolution": "constraint wins (precedence level 1)"})
                explicit.pop(key)
    explicit.pop("slang_strength", None)
    # Temporal slang (v0.6.0): the author's forms are kept; new forms only
    # with evidence for the requested epoch, genre and register.
    from .temporal import activate as temporal_activate
    slang_context = dict(context, targets=dict(context["targets"], slang_strength=slang_requested))
    temporal = temporal_activate(slang_context, text)
    if slang_requested > 0 and temporal["status"] != "active":
        warnings.append("slang strength stays 0.0: " + temporal["reasons"][-1])
    for note in temporal["epoch_notes"]:
        warnings.append(f"'{note['text']}' has no attestation in the requested epoch "
                        f"(attested: {', '.join(note['attested']) or 'none'}); kept as the author's form")
    apply("explicit_instruction", {k: v for k, v in explicit.items() if k != "register"})

    return {
        "schema_version": 1,
        "kind": "voznativa.voice_contract",
        "locale": "pt-BR",
        "genre": genre,
        "channel": context["channel"]["value"],
        "register": register,
        "constraints": ["semantic_preservation", *constraints],
        "features": features,
        "community_terms_preserve": community_terms,
        "regional_strength": {"requested": requested_region, "effective": regional["effective_strength"],
                              "code": region.get("code")},
        "regional": {"status": regional["status"], "reasons": regional["reasons"],
                     "packs": [p["id"] for p in regional["packs"]],
                     "features": [decision_view(f) for f in regional["features"]]},
        "slang_strength": {"requested": slang_requested, "effective": temporal["effective_strength"]},
        "temporal": {"status": temporal["status"], "epoch": temporal["requested"]["epoch"],
                     "keep": temporal["keep"], "allowed": temporal["allowed"], "reasons": temporal["reasons"],
                     "epoch_notes": temporal["epoch_notes"]},
        "community": {"status": community["status"], "pack": community["pack"], "keep": community["keep"],
                      "withdraw_findings_for": community["withdraw_findings_for"], "reasons": community["reasons"]},
        "profile": {"used": bool(profile) and maturity != "explicit_only", "maturity": maturity,
                    "id": (profile or {}).get("profile", {}).get("id")},
        "do_not": DO_NOT,
        "conflicts": conflicts,
        "warnings": warnings,
        "trace": trace,
    }


def compact(contract: dict) -> dict:
    """Flat feature -> value view for prompts."""
    view = {"register": contract["register"], "constraints": contract["constraints"]}
    for key, entry in contract["features"].items():
        view[key] = entry["value"] if "allowed" not in entry else {"value": entry["value"],
                                                                   "allowed": entry["allowed"]}
    view["regional_strength"] = contract["regional_strength"]["effective"]
    regional = contract.get("regional") or {}
    if regional.get("status") == "active":
        view["regional"] = [{k: v for k, v in f.items() if v} for f in regional["features"]]
    view["slang_strength"] = contract["slang_strength"]["effective"]
    if contract["community_terms_preserve"]:
        view["preserve_terms"] = contract["community_terms_preserve"]
    keep_slang = (contract.get("temporal") or {}).get("keep")
    if keep_slang:
        view["keep_author_slang"] = keep_slang
    return view
