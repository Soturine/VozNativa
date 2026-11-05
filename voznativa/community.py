"""Community Evidence Packs (v0.6.0): vocabulary of a context of practice.

A pack (``data/community_packs/*.yml``, contract in references/communities/README.md)
describes terms and discourse habits observed in a *context of practice*
(software teams, academia, offices, games), never a person's identity. Each
item is classified by a fixed taxonomy so a technical term is not handled
like a meme:

* ``terminology``: the field's names for things ("deploy", "pull request");
  translating them makes the text less precise.
* ``jargon``: insider shorthand, legitimate among peers, opaque outside.
* ``borrowing``: a foreign word with a common Portuguese equivalent.
* ``slang``, ``meme``: informal and temporal (see voznativa/temporal.py).
* ``discourse_habit``: a recurrent way of saying things ("alinhar", "subir").

Behaviours: ``preserve`` (keep it where the author wrote it; editorial
anglicism findings on it are withdrawn), ``avoid_outside`` (keep it, but do
not add it outside the listed channels), ``never_add``.

``activate`` answers, with reasons, which items to keep and which editorial
findings the community context withdraws. No pack licenses adding a term in
this version: generation needs a non-draft pack with evidence >= E2.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from .text import fold

SCHEMA_VERSION = 2
PACKS_DIR = Path(__file__).resolve().parent / "data" / "community_packs"
CATEGORIES = ("terminology", "jargon", "borrowing", "slang", "meme", "discourse_habit")
BEHAVIOURS = ("preserve", "avoid_outside", "never_add")
STATUSES = ("draft", "experimental", "calibrated")
EVIDENCE = ("E0", "E1", "E2", "E3", "E4")
REQUIRED = ("schema_version", "kind", "id", "name", "status", "context_of_practice", "evidence", "period", "items",
            "generation")
ITEM_REQUIRED = ("term", "forms", "category", "behaviour", "legitimate_in", "false_positive", "evidence")
# Editorial findings a community context may withdraw for its preserved terms.
WITHDRAWABLE = ("anglicism_out_of_domain",)


def validate_pack(pack: dict) -> list[str]:
    pid = pack.get("id", "?")
    problems = [f"{pid}: missing {k}" for k in REQUIRED if k not in pack]
    if problems:
        return problems
    if pack["schema_version"] != SCHEMA_VERSION:
        problems.append(f"{pid}: schema_version must be {SCHEMA_VERSION}")
    if pack["kind"] != "voznativa.community_pack":
        problems.append(f"{pid}: kind must be voznativa.community_pack")
    if pack["status"] not in STATUSES:
        problems.append(f"{pid}: status must be one of {STATUSES}")
    level = (pack["evidence"] or {}).get("level")
    if level not in EVIDENCE:
        problems.append(f"{pid}: evidence.level must be one of {EVIDENCE}")
    if pack["status"] != "draft" and level in ("E0", "E1"):
        problems.append(f"{pid}: a {pack['status']} pack needs evidence E2 or higher")
    if pack["status"] != "draft" and not (pack["evidence"] or {}).get("sources"):
        problems.append(f"{pid}: a non-draft pack needs evidence.sources")
    if (pack["generation"] or {}).get("allowed") and (pack["status"] == "draft" or level in ("E0", "E1")):
        problems.append(f"{pid}: generation needs a non-draft pack with evidence E2 or higher")
    seen = set()
    for item in pack["items"] or []:
        term = item.get("term", "?")
        problems += [f"{pid}/{term}: missing {k}" for k in ITEM_REQUIRED if k not in item]
        if item.get("category") not in CATEGORIES:
            problems.append(f"{pid}/{term}: category must be one of {CATEGORIES}")
        if item.get("behaviour") not in BEHAVIOURS:
            problems.append(f"{pid}/{term}: behaviour must be one of {BEHAVIOURS}")
        if item.get("evidence") not in EVIDENCE:
            problems.append(f"{pid}/{term}: evidence must be one of {EVIDENCE}")
        if item.get("category") in ("slang", "meme") and item.get("behaviour") == "preserve" \
                and "temporal" not in (item.get("note") or ""):
            problems.append(f"{pid}/{term}: slang or meme items are temporal; say so in note or use avoid_outside")
        for form in item.get("forms") or []:
            if fold(form) in seen:
                problems.append(f"{pid}/{term}: form {form!r} listed twice")
            seen.add(fold(form))
    return problems


@lru_cache(maxsize=4)
def _load(directory: str) -> tuple[dict, ...]:
    packs, problems = [], []
    for path in sorted(Path(directory).glob("*.yml")):
        pack = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        problems += validate_pack(pack)
        if pack.get("id") != path.stem:
            problems.append(f"{path.name}: id must match the file name")
        packs.append(pack)
    if problems:
        raise ValueError("invalid community packs: " + "; ".join(problems))
    return tuple(packs)


def load_packs(directory: Path | None = None) -> tuple[dict, ...]:
    return _load(str(directory or PACKS_DIR))


def get_pack(pack_id: str, directory: Path | None = None) -> dict | None:
    return next((p for p in load_packs(directory) if p["id"] == pack_id), None)


def all_terms(directory: Path | None = None) -> set[str]:
    """Folded forms of every pack item (the profile keeps them as the author's words)."""
    return {fold(f) for p in load_packs(directory) for i in p["items"] for f in i["forms"]}


def _rx(forms: list[str]) -> re.Pattern:
    alts = sorted({fold(f) for f in forms}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(a) for a in alts) + r")(?!\w)")


def items_in(text: str, pack: dict) -> list[dict]:
    plain = fold(text or "")
    found = []
    for item in pack["items"]:
        hits = [m.group(0) for m in _rx(item["forms"]).finditer(plain)]
        if hits:
            found.append({"term": item["term"], "forms": sorted(set(hits)), "count": len(hits),
                          "category": item["category"], "behaviour": item["behaviour"]})
    return found


def activate(context: dict, text: str | None = None, directory: Path | None = None) -> dict:
    """What the requested community context changes for this text, and why."""
    requested = (context.get("targets") or {}).get("community")
    out = {"kind": "voznativa.community_activation", "schema_version": SCHEMA_VERSION, "requested": requested,
           "status": "abstain", "pack": None, "keep": [], "withdraw_findings_for": [], "reasons": [],
           "may_add": []}
    if not requested:
        out["reasons"].append("no community requested: VozNativa never infers one from the text or the author")
        return out
    pack = get_pack(requested, directory)
    if pack is None:
        known = sorted(p["id"] for p in load_packs(directory))
        out["reasons"].append(f"unknown community pack {requested!r}; known: {known}")
        return out
    out["pack"] = {"id": pack["id"], "status": pack["status"], "evidence": pack["evidence"]["level"],
                   "context_of_practice": pack["context_of_practice"]}
    if pack["status"] == "draft":
        out["reasons"].append(f"pack {pack['id']!r} is a draft ({pack['evidence']['level']}): its terms are kept "
                              "where the author wrote them and never added")
    found = items_in(text, pack) if text is not None else []
    out["keep"] = [f for f in found if f["behaviour"] in ("preserve", "avoid_outside")]
    out["withdraw_findings_for"] = sorted({form for f in found if f["behaviour"] == "preserve" for form in f["forms"]})
    if out["keep"] or text is None:
        out["status"] = "active"
    else:
        out["reasons"].append("the text uses none of the pack's terms")
    return out


def withdraw(findings: list[dict], activation: dict | None) -> tuple[list[dict], list[dict]]:
    """Split editorial findings into (kept, withdrawn by the community context).
    Only WITHDRAWABLE findings on preserved terms are withdrawn."""
    forms = set((activation or {}).get("withdraw_findings_for") or [])
    if not forms:
        return list(findings), []
    kept, withdrawn = [], []
    for f in findings:
        if f.get("id") in WITHDRAWABLE and fold(f.get("text", "")) in forms:
            withdrawn.append(dict(f, withdrawn_by=f"community:{activation['pack']['id']}"))
        else:
            kept.append(f)
    return kept, withdrawn


def apply_to_report(report: dict, context: dict, text: str, directory: Path | None = None) -> dict:
    """An editorial report with the community context applied: anglicism
    findings on terms the requested pack preserves are withdrawn (listed in
    ``withdrawn``) and the decision is recomputed with the same rule.
    Without a requested community the report is returned unchanged."""
    if not (context.get("targets") or {}).get("community"):
        return report
    kept, withdrawn = withdraw(report["findings"], activate(context, text, directory))
    if not withdrawn:
        return report
    from .patterns import with_findings
    return with_findings(report, kept, withdrawn, text)


def introduced_terms(original: str, candidate: str, directory: Path | None = None) -> list[dict]:
    """Pack terms the candidate added that the source lacked. No pack licenses
    additions in this version, so every one is reported; the caller grades
    severity by category (terminology minor; jargon, borrowing, slang major)."""
    out = []
    for pack in load_packs(directory):
        before = {f["term"] for f in items_in(original, pack)}
        for f in items_in(candidate, pack):
            if f["term"] not in before:
                out.append({"pack": pack["id"], "term": f["term"], "forms": f["forms"], "category": f["category"]})
    return out
