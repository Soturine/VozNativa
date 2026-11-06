"""Corpus Registry: one versioned YAML file per source, strictly validated.

A source's ``status`` states what has been *proven*, not what is intended:

    CATALOGUED            named and described from secondary references
    SOURCE_VERIFIED       an official page was fetched and identifies the source
    ACCESS_VERIFIED       the data (or its official metadata) was actually reached
    CONNECTOR_READY       a registered connector reads it within limits
    LOCALLY_VALIDATED     a recorded processing run validated a local copy
    EVALUATION_INTEGRATED an evaluator in this repository consumes its derived data
    RESTRICTED            access exists but its terms forbid the uses we need
    AWAITING_PERMISSION   access requires a permission that was requested/not granted
    UNAVAILABLE           no working access path could be found
    DEPRECATED            superseded; kept for lineage

The ladder statuses require the evidence of every lower rung; the other
statuses require a reason. A file that fails validation is never loaded
partially: ``load_registry`` raises with every problem it found.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

SCHEMA_VERSION = 1
KIND = "voznativa.corpus_source"
REGISTRY_DIR = Path(__file__).resolve().parent.parent / "data" / "corpora"
ROOT = Path(__file__).resolve().parent.parent.parent

LADDER = ("CATALOGUED", "SOURCE_VERIFIED", "ACCESS_VERIFIED", "CONNECTOR_READY", "LOCALLY_VALIDATED",
          "EVALUATION_INTEGRATED")
OTHER_STATUSES = ("RESTRICTED", "AWAITING_PERMISSION", "UNAVAILABLE", "DEPRECATED")
STATUSES = LADDER + OTHER_STATUSES
MODALITIES = ("written", "spoken_transcribed", "spoken_audio", "mixed")
ACCESS_TYPES = ("open_download", "open_query", "registration", "request", "restricted", "unknown")
# What the official URL is: only a project's own site or its data host can
# back SOURCE_VERIFIED; a citation or a containing corpus only shows the
# source is referenced.
OFFICIAL_KINDS = ("project_site", "data_host", "citation", "containing_corpus")
RELATIONS = ("contains", "part_of", "derived_from", "overlaps", "supersedes", "superseded_by", "sister")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,60}$")

REQUIRED = ("schema_version", "kind", "id", "name", "maintainer", "urls", "modality", "genres", "regions", "period",
            "license", "access", "relations", "status", "evidence_role", "notes")


def _rung(status: str) -> int:
    return LADDER.index(status) if status in LADDER else -1


def validate_source(entry: dict, known_connectors: frozenset | None = None, root: Path = ROOT) -> list[str]:
    """Every problem with one registry entry (empty list = valid)."""
    problems = [f"missing field {k}" for k in REQUIRED if k not in entry]
    if problems:
        return problems
    if entry["schema_version"] != SCHEMA_VERSION or entry["kind"] != KIND:
        problems.append("unsupported schema_version or kind")
    if not ID_RE.match(str(entry["id"])):
        problems.append(f"id {entry['id']!r} must be lower-case letters, digits and hyphens")
    if entry["modality"] not in MODALITIES:
        problems.append(f"modality must be one of {MODALITIES}")
    if entry["status"] not in STATUSES:
        problems.append(f"status must be one of {STATUSES}")
    if not isinstance(entry["urls"], dict) or not entry["urls"].get("official"):
        problems.append("urls.official is required (use the citation URL when no site exists)")
    elif entry["urls"].get("official_kind") not in OFFICIAL_KINDS:
        problems.append(f"urls.official_kind must be one of {OFFICIAL_KINDS}")
    period = entry["period"]
    if not isinstance(period, dict) or "from" not in period or "to" not in period:
        problems.append("period needs from and to (null when unknown)")
    lic = entry["license"]
    if not isinstance(lic, dict) or "code" not in lic or "per_document" not in lic or "evidence" not in lic:
        problems.append("license needs code, per_document and evidence")
    elif lic.get("text_rights", "covered") not in ("covered", "unclear"):
        problems.append("license.text_rights must be covered or unclear")
    elif lic.get("text_rights") == "unclear" and not lic.get("text_rights_note"):
        problems.append("license.text_rights unclear needs text_rights_note")
    access = entry["access"]
    if not isinstance(access, dict) or access.get("type") not in ACCESS_TYPES:
        problems.append(f"access.type must be one of {ACCESS_TYPES}")
    privacy = entry.get("privacy")
    if privacy is not None and privacy.get("personal_data") not in (True, False, "possible", "unknown"):
        problems.append("privacy.personal_data must be true, false, possible or unknown")
    for rel in entry["relations"] or []:
        if rel.get("type") not in RELATIONS or not rel.get("target"):
            problems.append(f"relation {rel} needs type in {RELATIONS} and a target")
    problems += _status_evidence(entry, known_connectors, root)
    return problems


def _status_evidence(entry: dict, known_connectors, root: Path) -> list[str]:
    """A status is a claim; each rung needs its own evidence."""
    status, problems = entry["status"], []
    verification = entry.get("verification") or {}
    if status in OTHER_STATUSES and not entry.get("status_reason"):
        problems.append(f"status {status} needs status_reason")
    rung = _rung(status)
    if rung >= 1:
        if (entry.get("urls") or {}).get("official_kind") not in {"project_site", "data_host"}:
            problems.append("SOURCE_VERIFIED needs an official project site or data host, not a citation")
        src = verification.get("source") or {}
        if not (src.get("date") and src.get("url") and src.get("method") and src.get("result")):
            problems.append("SOURCE_VERIFIED needs verification.source with date, url, method and result")
    if rung >= 2:
        acc = verification.get("access") or {}
        if not (acc.get("date") and acc.get("method") and acc.get("result")):
            problems.append("ACCESS_VERIFIED needs verification.access with date, method and result")
    if rung >= 3:
        connector = (entry.get("connector") or {}).get("id")
        if not connector:
            problems.append("CONNECTOR_READY needs connector.id")
        elif known_connectors is not None and connector not in known_connectors:
            problems.append(f"connector {connector!r} is not registered")
        conn = verification.get("connector") or {}
        if not (conn.get("date") and conn.get("records_read") and conn.get("result") == "read"):
            problems.append("CONNECTOR_READY needs verification.connector with date, records_read and result read")
    if rung >= 4:
        runs = entry.get("processing_runs") or []
        if not runs:
            problems.append("LOCALLY_VALIDATED needs processing_runs")
        if has_evidence_tree(root):
            problems += [f"processing run {r} not found" for r in runs if not (root / r).is_file()]
    if rung >= 5:
        evals = entry.get("evaluations") or []
        if not evals:
            problems.append("EVALUATION_INTEGRATED needs evaluations")
        if has_evidence_tree(root):
            problems += [f"evaluation {e} not found" for e in evals if not (root / e).is_file()]
    return problems


def has_evidence_tree(root: Path) -> bool:
    """Evidence files (evals/, scripts/) live in the repository, not in an
    installed wheel: there the status claims are checked for shape only, and
    the checkout (tests, validate_package, qualify) checks that each file
    exists. Found in v0.6 CP9: the installed smoke refused the registry."""
    return (root / "evals").is_dir() and (root / "scripts").is_dir()


def _connector_ids() -> frozenset:
    from .connectors import CONNECTORS
    return frozenset(CONNECTORS)


@lru_cache(maxsize=4)
def _load(directory: str) -> tuple[dict, ...]:
    entries, problems, seen = [], [], {}
    known = _connector_ids()
    for path in sorted(Path(directory).glob("*.yml")):
        entry = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(entry, dict):
            problems.append(f"{path.name}: not a mapping")
            continue
        found = validate_source(entry, known)
        if entry.get("id") and path.stem != entry["id"]:
            found.append(f"file name must be {entry['id']}.yml")
        if entry.get("id") in seen:
            found.append(f"duplicate id (also in {seen[entry['id']]})")
        seen[entry.get("id")] = path.name
        problems += [f"{path.name}: {p}" for p in found]
        entries.append(entry)
    ids = {e["id"] for e in entries}
    for e in entries:
        for rel in e.get("relations") or []:
            if rel.get("target") not in ids:
                problems.append(f"{e['id']}.yml: relation target {rel.get('target')!r} is not registered")
    if problems:
        raise ValueError("invalid corpus registry:\n  " + "\n  ".join(problems))
    return tuple(entries)


def load_registry(directory: Path | None = None) -> tuple[dict, ...]:
    return _load(str(directory or REGISTRY_DIR))


def get_source(source_id: str, directory: Path | None = None) -> dict:
    for entry in load_registry(directory):
        if entry["id"] == source_id:
            return entry
    raise KeyError(f"unknown corpus source {source_id!r}")


def independent_groups(entries: tuple[dict, ...] | None = None) -> list[set[str]]:
    """Sources that can share records (contains / part_of / derived_from /
    overlaps) in one group: observations from two members of a group are
    not independent replications (E3) without record-level proof."""
    entries = entries if entries is not None else load_registry()
    parent = {e["id"]: e["id"] for e in entries}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in entries:
        for rel in e.get("relations") or []:
            if rel["type"] in {"contains", "part_of", "derived_from", "overlaps"}:
                parent[find(e["id"])] = find(rel["target"])
    groups: dict[str, set[str]] = {}
    for e in entries:
        groups.setdefault(find(e["id"]), set()).add(e["id"])
    return sorted(groups.values(), key=lambda g: sorted(g))


def summary(entries: tuple[dict, ...] | None = None) -> dict:
    entries = entries if entries is not None else load_registry()
    counts = {s: sum(e["status"] == s for e in entries) for s in STATUSES}
    reached = {s: sum(_rung(e["status"]) >= _rung(s) for e in entries) for s in LADDER[1:]}
    return {"sources": len(entries), "by_status": {k: v for k, v in counts.items() if v},
            "at_least": reached}
