"""Standards Registry and Applicability Resolver (v0.8 CP10, ST-01..ST-04).

Follows the Corpus Registry's conventions (one YAML per source in
``data/standards/``, strict validation, a status that needs evidence) for
editais, manuals, norms, rubrics and exam guides. Nothing here grades a
document; it answers "which rules apply to this document, from which source,
in which edition, and how sure are we".

* **Registry entry** (``voznativa.standard_source``): authority, series, title,
  official URL, edition, publication date, validity, the event and year it
  governs, document types, rights over the text (never redistributed),
  verification, and criteria (each with its own verification).
* **Verification ladder:** ``CATALOGUED`` (named, unchecked) ->
  ``SOURCE_CITED`` (official URL and publication date seen on the official
  page, dated) -> ``VERIFIED`` (also the sha256 of the official file, dated).
  ``STALE``, ``CONFLICTED`` and ``BLOCKED`` are explicit.
* **Applicability Resolver:** picks the edition *valid on the submission
  date* for the given authority, series, event year and document type -
  never the latest by default. Two valid editions of one series, or a
  source the resolver cannot date, give ``CONFLICTED`` or ``UNKNOWN`` with
  the reason; a source below ``SOURCE_CITED`` cannot make a rule applicable.

Without a ``document_profile`` nothing here runs: the plain analysis of a text
is unchanged (ST-04).
"""
from __future__ import annotations

import re
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

KIND = "voznativa.standard_source"
SCHEMA_VERSION = 1
REGISTRY_DIR = Path(__file__).resolve().parent / "data" / "standards"
CATEGORIES = ("edital", "manual", "norma", "rubrica", "template", "cartilha", "diretriz")
VERIFICATION = ("CATALOGUED", "SOURCE_CITED", "VERIFIED", "STALE", "CONFLICTED", "BLOCKED")
APPLICABLE_FROM = ("SOURCE_CITED", "VERIFIED")
TEXT_RIGHTS = ("metadata_only", "paraphrase_only", "open_licence", "unknown")
CRITERION_KINDS = ("objective", "subjective")
DECISIONS = ("APPLICABLE", "APPLICABLE_UNVERIFIED", "UNKNOWN", "CONFLICTED", "STALE", "BLOCKED", "NOT_APPLICABLE")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,80}$")
REQUIRED = ("schema_version", "kind", "id", "authority", "series", "category", "title", "urls", "edition",
            "published", "validity", "applies_to", "rights", "verification", "criteria")


def _date(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return date.fromisoformat(value)
    return None


def validate_entry(entry: dict) -> list[str]:
    """Problems that make an entry unusable (empty = usable)."""
    problems = [f"missing {k}" for k in REQUIRED if k not in entry]
    if problems:
        return problems
    if entry["kind"] != KIND or entry["schema_version"] != SCHEMA_VERSION:
        problems.append("unsupported kind or schema_version")
    if not isinstance(entry["id"], str) or not ID_RE.fullmatch(entry["id"]):
        problems.append("id must be lowercase letters, digits and hyphens")
    if entry["category"] not in CATEGORIES:
        problems.append(f"category must be one of {CATEGORIES}")
    official = (entry["urls"] or {}).get("official")
    if not isinstance(official, str) or not official.startswith("https://"):
        problems.append("urls.official must be an https URL")
    if _date(entry["published"]) is None:
        problems.append("published must be an ISO date")
    validity = entry["validity"] or {}
    start, end = _date(validity.get("from")), validity.get("until")
    if start is None:
        problems.append("validity.from must be an ISO date")
    if end is not None and _date(end) is None:
        problems.append("validity.until must be an ISO date or null")
    if start and _date(end) and _date(end) < start:
        problems.append("validity.until is before validity.from")
    applies = entry["applies_to"] or {}
    if not isinstance(applies.get("document_types"), list) or not applies["document_types"]:
        problems.append("applies_to.document_types must be a non-empty list")
    if applies.get("event_year") is not None and not isinstance(applies.get("event_year"), int):
        problems.append("applies_to.event_year must be an integer or null")
    rights = entry["rights"] or {}
    if rights.get("text") not in TEXT_RIGHTS:
        problems.append(f"rights.text must be one of {TEXT_RIGHTS}")
    if rights.get("text") != "open_licence" and entry.get("text"):
        problems.append("the source's text is not redistributable: keep metadata and paraphrased criteria only")
    ver = entry["verification"] or {}
    status = ver.get("status")
    if status not in VERIFICATION:
        problems.append(f"verification.status must be one of {VERIFICATION}")
    if status in ("SOURCE_CITED", "VERIFIED"):
        if _date(ver.get("checked_at")) is None:
            problems.append(f"{status} needs verification.checked_at")
        if not ver.get("evidence"):
            problems.append(f"{status} needs verification.evidence (what was seen, where)")
    if status == "VERIFIED" and not re.fullmatch(r"[0-9a-f]{64}", str(ver.get("sha256") or "")):
        problems.append("VERIFIED needs the sha256 of the official file")
    if not isinstance(entry["criteria"], list):
        problems.append("criteria must be a list")
    else:
        seen = set()
        for n, c in enumerate(entry["criteria"]):
            where = f"criteria[{n}]"
            if not isinstance(c, dict) or not isinstance(c.get("id"), str):
                problems.append(f"{where} needs an id")
                continue
            if c["id"] in seen:
                problems.append(f"{where}: duplicate id {c['id']}")
            seen.add(c["id"])
            if c.get("kind") not in CRITERION_KINDS:
                problems.append(f"{where}: kind must be one of {CRITERION_KINDS}")
            if c.get("verification") not in VERIFICATION:
                problems.append(f"{where}: verification must be one of {VERIFICATION}")
            if c.get("weight") is not None and not c.get("weight_official"):
                problems.append(f"{where}: a weight is allowed only when the source states it (weight_official)")
            if c.get("kind") == "objective" and c.get("check") is not None and not isinstance(c["check"], dict):
                problems.append(f"{where}: check must be an object")
    return problems


def _iso_dates(value):
    """YAML reads 2026-09-18 as a date; keep ISO strings so entries are JSON-ready."""
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _iso_dates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_iso_dates(v) for v in value]
    return value


def load(directory: Path | None = None) -> tuple[dict, ...]:
    directory = directory or REGISTRY_DIR
    return _load(str(directory))


@lru_cache(maxsize=4)
def _load(directory: str) -> tuple[dict, ...]:
    entries, problems = [], []
    for path in sorted(Path(directory).glob("*.yml")):
        entry = _iso_dates(yaml.safe_load(path.read_text(encoding="utf-8")))
        found = validate_entry(entry) if isinstance(entry, dict) else ["not a mapping"]
        if isinstance(entry, dict) and entry.get("id") != path.stem:
            found.append("id must equal the file name")
        problems += [f"{path.name}: {p}" for p in found]
        entries.append(entry)
    ids = [e.get("id") for e in entries if isinstance(e, dict)]
    if len(ids) != len(set(ids)):
        problems.append("duplicate ids in the standards registry")
    if problems:
        raise ValueError("invalid standards registry: " + "; ".join(problems))
    return tuple(entries)


def _valid_on(entry: dict, day: date) -> bool:
    start = _date(entry["validity"]["from"])
    end = _date(entry["validity"].get("until"))
    return start <= day and (end is None or day <= end)


def resolve(profile: dict, entries: tuple[dict, ...] | None = None, today: date | None = None) -> dict:
    """Which registered sources apply to a document described by ``profile``:
    ``authority`` and ``series`` (or ``institution``), ``document_type``,
    ``event_year`` (optional) and ``submission_date`` (ISO; required - the
    edition is chosen by the date the document is for, never by recency)."""
    entries = load() if entries is None else entries
    day = _date(profile.get("submission_date"))
    if day is None:
        return {"decision": "UNKNOWN", "selected": [], "reason": "submission_date is required to pick an edition",
                "candidates": []}
    doc_type = profile.get("document_type")
    candidates = []
    for e in entries:
        applies = e["applies_to"]
        if doc_type not in applies["document_types"]:
            continue
        if profile.get("authority") and e["authority"] != profile["authority"]:
            continue
        if profile.get("series") and e["series"] != profile["series"]:
            continue
        if profile.get("event_year") is not None and applies.get("event_year") not in (None, profile["event_year"]):
            continue
        candidates.append(e)
    trail = [{"id": e["id"], "edition": e["edition"], "validity": e["validity"],
              "verification": e["verification"]["status"]} for e in candidates]
    if not candidates:
        return {"decision": "NOT_APPLICABLE", "selected": [], "candidates": [],
                "reason": "no registered source governs this document type for this authority, series and year"}
    valid = [e for e in candidates if _valid_on(e, day)]
    if not valid:
        return {"decision": "UNKNOWN", "selected": [], "candidates": trail,
                "reason": f"no registered edition was valid on {day.isoformat()}; the newest edition is not "
                          "assumed to apply to an earlier or later document"}
    by_series: dict[tuple, list[dict]] = {}
    for e in valid:
        by_series.setdefault((e["authority"], e["series"]), []).append(e)
    conflicts = {k: v for k, v in by_series.items() if len(v) > 1}
    if conflicts:
        return {"decision": "CONFLICTED", "selected": [], "candidates": trail,
                "reason": "more than one edition of the same series is valid on that date: "
                          + "; ".join(f"{a}/{s}: {[e['id'] for e in v]}" for (a, s), v in conflicts.items())
                          + "; a person must decide (no silent choice)"}
    selected = [v[0] for v in by_series.values()]
    statuses = {e["verification"]["status"] for e in selected}
    if statuses & {"BLOCKED"}:
        decision = "BLOCKED"
    elif statuses & {"CONFLICTED"}:
        decision = "CONFLICTED"
    elif statuses & {"STALE"}:
        decision = "STALE"
    elif statuses <= {"VERIFIED"}:
        decision = "APPLICABLE"
    elif statuses <= set(APPLICABLE_FROM):
        decision = "APPLICABLE_UNVERIFIED"
    else:
        decision = "UNKNOWN"
    applicable = decision in ("APPLICABLE", "APPLICABLE_UNVERIFIED")
    return {"decision": decision, "selected": [e["id"] for e in selected] if applicable else [],
            "edition_found": [e["id"] for e in selected], "candidates": trail,
            "reason": {"APPLICABLE": "edition valid on the date, official file verified by hash",
                       "APPLICABLE_UNVERIFIED": "edition valid on the date, cited from the official page; the "
                                                "official file was not hashed, so criteria are not enforced as rules",
                       "UNKNOWN": "the only valid edition is merely catalogued: not enough evidence to apply it",
                       "STALE": "the source's verification is stale", "CONFLICTED": "the source is marked conflicted",
                       "BLOCKED": "the source is blocked"}[decision],
            "date": day.isoformat()}
