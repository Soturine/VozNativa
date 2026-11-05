"""Regional Evidence Packs (v0.5.0): regionality only where evidence exists.

A pack (``data/regional_packs/*.yml``, contract in docs/REGIONAL_EVIDENCE.md)
records forms observed for one referent in a documented scope, epoch and
modality, with its sources, licence, confusions and activation conditions.

The module answers three questions, always with reasons:

* ``activate``: for a request that names a region, which pack features may
  inform the rewrite, or why the system abstains. Abstention is the default:
  no region requested, no pack for it, a context the evidence does not cover,
  a referent the text never mentions, or a form the author already uses
  (the author's observed voice wins over a regional default).
* ``referent_swaps``: forms of one feature that a pack records as changing the
  referent in its scope ("macaxeira" -> "mandioca" in the North), for the
  Semantic Ledger.
* ``introduced_forms``: pack forms a candidate added that the source did not
  have and the activation did not license, for the overfit and mixing guards.

Nothing here infers where a person is from; the region is only ever the one
the request names.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from .text import fold

SCHEMA_VERSION = 1
PACKS_DIR = Path(__file__).resolve().parent / "data" / "regional_packs"

MACRO_REGIONS = {
    "norte": {"AC", "AM", "AP", "PA", "RO", "RR", "TO"},
    "nordeste": {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"},
    "centro-oeste": {"DF", "GO", "MS", "MT"},
    "sudeste": {"ES", "MG", "RJ", "SP"},
    "sul": {"PR", "RS", "SC"},
}
STATES = set().union(*MACRO_REGIONS.values())
REQUIRED = ("schema_version", "kind", "id", "version", "status", "human_reviewed", "scope", "epoch", "modality",
            "sources", "license", "features", "activation")
FEATURE_REQUIRED = ("id", "level", "referent", "forms", "total_answers", "contexts_legitimate", "confusions",
                    "confidence", "evidence_level", "limitations")
STATUSES = ("pilot", "experimental", "calibrated")
# One owner for the decision fields other layers expose (contract, plan) and
# for the pack summary the CLI lists.
DECISION_FIELDS = ("pack", "feature", "keep", "suggest", "replaces", "why")
SUMMARY_FIELDS = ("id", "version", "status", "human_reviewed", "scope", "epoch", "modality")


def decision_view(feature_decision: dict) -> dict:
    return {k: feature_decision.get(k) for k in DECISION_FIELDS}


def pack_summary(pack: dict) -> dict:
    return {**{k: pack[k] for k in SUMMARY_FIELDS}, "features": [f["id"] for f in pack["features"]],
            "sources": [s["citation"] for s in pack["sources"]]}


def normalize_region(code: str | None) -> dict | None:
    """``"Norte"``/``"norte"`` -> macro region; ``"am"``/``"AM"`` -> state.
    Unknown codes are kept and match nothing (abstention, never a guess)."""
    if not code:
        return None
    raw = fold(code.strip()).replace(" ", "-")
    if raw in MACRO_REGIONS:
        return {"code": raw, "kind": "macro_region", "states": sorted(MACRO_REGIONS[raw])}
    if raw.upper() in STATES:
        macro = next(m for m, s in MACRO_REGIONS.items() if raw.upper() in s)
        return {"code": raw.upper(), "kind": "state", "states": [raw.upper()], "macro_region": macro}
    return {"code": raw, "kind": "unknown", "states": []}


def validate_pack(pack: dict) -> list[str]:
    problems = [f"missing field {k}" for k in REQUIRED if k not in pack]
    if problems:
        return problems
    if pack["schema_version"] != SCHEMA_VERSION or pack["kind"] != "voznativa.regional_evidence_pack":
        problems.append("unsupported schema_version or kind")
    if pack["status"] not in STATUSES:
        problems.append(f"status must be one of {STATUSES}")
    if not pack["sources"] or any(not s.get("citation") or not s.get("url") for s in pack["sources"]):
        problems.append("every source needs a citation and a url")
    scope = pack["scope"]
    unknown_states = set(scope.get("states", [])) - STATES
    if unknown_states or not scope.get("states"):
        problems.append(f"scope.states must be Brazilian state codes (unknown: {sorted(unknown_states)})")
    epoch = pack["epoch"]
    if not isinstance(epoch.get("collected_from"), int) or not isinstance(epoch.get("collected_to"), int):
        problems.append("epoch.collected_from/collected_to must be years")
    activation = pack["activation"]
    if not activation.get("requires_explicit_region") or not activation.get("author_form_wins"):
        problems.append("activation must require an explicit region and let the author's form win")
    if not 0 < float(activation.get("max_strength", 0)) <= 0.25 and pack["status"] != "calibrated":
        problems.append("an uncalibrated pack may not exceed strength 0.25")
    for feature in pack["features"]:
        problems += [f"feature {feature.get('id')}: missing {k}" for k in FEATURE_REQUIRED if k not in feature]
        if "forms" in feature and "total_answers" in feature:
            counted = sum(f.get("count", 0) for f in feature["forms"])
            if counted != feature["total_answers"]:
                problems.append(f"feature {feature['id']}: form counts {counted} != total_answers "
                                f"{feature['total_answers']}")
        forms = {f["form"] for f in feature.get("forms", [])}
        for confusion in feature.get("confusions", []):
            if not set(confusion.get("forms", [])) <= forms:
                problems.append(f"feature {feature['id']}: confusion names a form the feature does not list")
    return problems


@lru_cache(maxsize=4)
def _load(directory: str) -> tuple[dict, ...]:
    packs = []
    for path in sorted(Path(directory).glob("*.yml")):
        pack = yaml.safe_load(path.read_text(encoding="utf-8"))
        problems = validate_pack(pack)
        if problems:
            raise ValueError(f"{path.name}: invalid regional evidence pack: {problems}")
        packs.append(pack)
    return tuple(packs)


def load_packs(directory: Path | None = None) -> tuple[dict, ...]:
    return _load(str(directory or PACKS_DIR))


def _form_re(form: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + re.escape(fold(form)) + r"(?!\w)")


def forms_in(text: str, feature: dict) -> list[str]:
    folded = fold(text or "")
    return [f["form"] for f in feature["forms"] if _form_re(f["form"]).search(folded)]


def author_forms(profile: dict | None, feature: dict) -> list[str]:
    """Forms of this feature the author's Voice Profile observed (habit
    ``regional_form.<form>``); the profile stores counts, never text."""
    habits = {h.get("id") for h in (profile or {}).get("habits", [])}
    return [f["form"] for f in feature["forms"] if f"regional_form.{fold(f['form'])}" in habits]


def _scope_match(pack: dict, region: dict) -> str | None:
    states = set(pack["scope"]["states"])
    if region["kind"] == "macro_region" and region["code"] == pack["scope"].get("macro_region"):
        return "macro_region"
    if region["kind"] == "state" and region["code"] in states:
        return "state"
    return None


def activate(context: dict, text: str | None = None, profile: dict | None = None,
             directory: Path | None = None) -> dict:
    """Which pack features may inform this rewrite, or why none may.

    ``text`` None evaluates only the scope (for the Voice Contract); with a
    text, each feature also needs its referent in the text."""
    target = (context.get("targets") or {}).get("region") or {}
    requested = float(target.get("strength") or 0.0)
    region = normalize_region(target.get("code"))
    genre = (context.get("genre") or {}).get("value", "unknown")
    out = {"kind": "voznativa.regional_activation", "schema_version": SCHEMA_VERSION,
           "requested": {"region": region, "strength": requested}, "status": "abstain", "reasons": [],
           "packs": [], "features": [], "effective_strength": 0.0}
    if region is None or requested <= 0:
        out["reasons"].append("no region requested: VozNativa never infers a region from the text or the author")
        return out
    if region["kind"] == "unknown":
        out["reasons"].append(f"unknown region code {region['code']!r}; use a macro region or a state code")
        return out
    packs = [(p, _scope_match(p, region)) for p in load_packs(directory)]
    packs = [(p, m) for p, m in packs if m]
    if not packs:
        out["reasons"].append(f"no evidence pack covers {region['code']}: regional strength stays 0")
        return out
    for pack, match in packs:
        entry = {"id": pack["id"], "version": pack["version"], "status": pack["status"], "match": match,
                 "human_reviewed": pack["human_reviewed"], "epoch": pack["epoch"], "modality": pack["modality"]}
        out["packs"].append(entry)
        if genre not in pack["activation"].get("allowed_genres", []):
            out["reasons"].append(f"{pack['id']}: genre {genre!r} is outside the contexts its evidence covers")
            continue
        for feature in pack["features"]:
            excepted = [e for e in feature.get("exceptions", []) if e["scope"] in region["states"]]
            if region["kind"] == "state" and excepted:
                out["reasons"].append(f"{pack['id']}/{feature['id']}: {region['code']} is a recorded exception "
                                      f"({excepted[0]['note']})")
                continue
            in_text = forms_in(text, feature) if text is not None else None
            if text is not None and pack["activation"].get("requires_referent_in_text") and not in_text:
                out["reasons"].append(f"{pack['id']}/{feature['id']}: the text never mentions the referent")
                continue
            out["features"].append(_decide(pack, feature, author_forms(profile, feature), in_text, excepted))
    if out["features"]:
        out["status"] = "active"
        caps = [p["activation"]["max_strength"] for p, _ in packs]
        out["effective_strength"] = round(min(requested, *caps), 3)
    elif not out["reasons"]:
        out["reasons"].append("no applicable feature")
    return out


def _decide(pack: dict, feature: dict, by_author: list[str], in_text: list[str] | None, excepted: list) -> dict:
    """One feature's decision. Order: the author's documented form (Voice
    Profile) wins; a form whose swap could change the referent is kept; the
    region's form already present needs nothing; otherwise the region's most
    frequent form is offered as an option for an explicitly requested region."""
    preferred = feature.get("preferred_in_scope")
    risky = {form for c in feature["confusions"] if preferred in c["forms"] for form in c["forms"]} - {preferred}
    decision = {"pack": pack["id"], "feature": feature["id"], "referent": feature["referent"],
                "forms": [f["form"] for f in feature["forms"]], "confusions": feature["confusions"],
                "confidence": feature["confidence"], "evidence_level": feature["evidence_level"],
                "exceptions_in_scope": [e["scope"] for e in excepted], "suggest": None}
    in_text = in_text or []
    if by_author:
        decision.update(keep=sorted(set(by_author) | set(in_text)),
                        why=f"the author's profile shows {sorted(by_author)}: the author's form wins over "
                            f"the regional default {preferred!r}")
    elif set(in_text) & risky:
        decision.update(keep=sorted(in_text),
                        why=f"{sorted(set(in_text) & risky)} may name another referent in this region; "
                            "replacing it could change the meaning")
    elif preferred in in_text or not in_text:
        decision.update(keep=sorted(in_text), why="the text already uses the region's form" if in_text
                        else "no form in the text; scope-level activation only")
    else:
        epoch = pack["epoch"]
        decision.update(keep=[], suggest=preferred, replaces=sorted(in_text),
                        why=f"{preferred!r} is the most frequent form for this referent in the evidence "
                            f"({epoch['collected_from']}-{epoch['collected_to']}, {pack['modality']}, confidence "
                            f"{feature['confidence']}); an option for the requested region, never forced")
    return decision


def referent_swaps(original: str, candidate: str, directory: Path | None = None) -> list[dict]:
    """Pairs a pack marks as changing the referent somewhere in its scope:
    the original used one, the candidate replaced it with the other."""
    found = []
    for pack in load_packs(directory):
        for feature in pack["features"]:
            src, out = set(forms_in(original, feature)), set(forms_in(candidate, feature))
            for confusion in feature["confusions"]:
                a, b = confusion["forms"]
                for old, new in ((a, b), (b, a)):
                    if old in src and old not in out and new in out and new not in src:
                        found.append({"pack": pack["id"], "feature": feature["id"], "from": old, "to": new,
                                      "risk": confusion["risk"]})
    return found


def introduced_forms(original: str, candidate: str, activation: dict | None = None,
                     directory: Path | None = None) -> list[dict]:
    """Pack forms the candidate added that the source did not have and the
    activation did not suggest: regional decoration the request did not license."""
    licensed = {(f["feature"], f.get("suggest")) for f in (activation or {}).get("features", []) if f.get("suggest")}
    out = []
    for pack in load_packs(directory):
        for feature in pack["features"]:
            src = set(forms_in(original, feature))
            for form in forms_in(candidate, feature):
                if form not in src and (feature["id"], form) not in licensed:
                    out.append({"pack": pack["id"], "feature": feature["id"], "form": form})
    return out
