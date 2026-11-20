"""Knowledge Watcher (v0.10 CP8): notice changes in sources the project depends on, and propose.

Sources are declared in ``data/watch_sources.yml`` (official hosts only, cost
and access stated). ``check`` asks each due source whether it changed
(conditional GET with ETag/Last-Modified where the server supports it),
normalizes what it read into a short summary, compares it with the last
snapshot and turns each difference into a **Change Proposal**.

What it never does (decision D-04): edit code, rules, gates, packs or the
knowledge registry; install or upgrade a package; run or download a binary;
activate a model; publish anything. A proposal is a record for a person:
state, evidence, licence check, what it may affect, which tests would prove it
and how to roll back. Fetched content is untrusted data: it is truncated,
stripped of control characters, never interpreted as instructions.

Modes: ``report`` (read and compare, write nothing) and ``propose`` (also
store snapshots and proposals in the state directory, outside the repository).
Offline, nothing is fetched: the status of each source comes from its last
snapshot and its age.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

KIND = "voznativa.watch_sources"
SCHEMA_VERSION = 1
DATA = Path(__file__).resolve().parent / "data" / "watch_sources.yml"
ENV_DIR = "VOZNATIVA_WATCH_DIR"
SOURCE_KINDS = ("pypi", "github_commits", "crossref", "http_page")
PIPELINE = ("DISCOVERED", "SOURCE_VERIFIED", "LICENSE_CHECKED", "DIFFERENCE_ANALYZED", "RELEVANCE_TRIAGED",
            "CANDIDATE", "ISOLATED_EVAL", "APPROVED", "REJECTED", "NEEDS_HUMAN", "VERSIONED_ACTIVATION")
MAX_SUMMARY = 4000
MAX_TITLE = 200
MAX_RETRY_AFTER_S = 30
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class WatchError(ValueError):
    pass


def state_dir() -> Path:
    base = os.environ.get(ENV_DIR)
    return Path(base) if base else Path.home() / ".voznativa" / "watch"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean(text, limit: int = MAX_TITLE) -> str:
    return _CONTROL.sub("", " ".join(str(text or "").split()))[:limit]


def load_sources(path: Path | None = None) -> list[dict]:
    data = yaml.safe_load((path or DATA).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("kind") != KIND or data.get("schema_version") != SCHEMA_VERSION:
        raise WatchError(f"watch source file must be {KIND} schema {SCHEMA_VERSION}")
    out, seen = [], set()
    for src in data.get("sources") or []:
        sid = str(src.get("id", ""))
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", sid) or sid in seen:
            raise WatchError(f"bad or repeated source id: {sid!r}")
        if src.get("kind") not in SOURCE_KINDS:
            raise WatchError(f"{sid}: kind must be one of {SOURCE_KINDS}")
        url = str(src.get("url", ""))
        if not url.startswith("https://"):
            raise WatchError(f"{sid}: url must be https")
        hosts = {h.lower() for h in src.get("hosts") or []}
        from urllib.parse import urlsplit
        if not hosts or (urlsplit(url).hostname or "").lower() not in hosts:
            raise WatchError(f"{sid}: the url host must be listed in hosts")
        for field in ("affects", "access", "cost", "licence_note"):
            if not src.get(field):
                raise WatchError(f"{sid}: {field} is required")
        seen.add(sid)
        out.append(dict(src, hosts=sorted(hosts)))
    return out


# --- normalization: what each kind of source says, as a short comparable summary -----------

def _summary(source: dict, response: dict) -> dict:
    kind, text = source["kind"], response.get("text") or ""
    if kind == "pypi":
        data = json.loads(text)
        info = data.get("info") or {}
        version = _clean(info.get("version"), 40)
        files = (data.get("releases") or {}).get(version) or []
        uploaded = min((f.get("upload_time_iso_8601") or "" for f in files), default="") if files else ""
        return {"version": version, "uploaded": _clean(uploaded, 40),
                "licence": _clean(info.get("license_expression") or info.get("license"), 80),
                "requires_python": _clean(info.get("requires_python"), 40)}
    if kind == "github_commits":
        data = json.loads(text)
        head = data[0] if isinstance(data, list) and data else {}
        commit = head.get("commit") or {}
        return {"sha": _clean(head.get("sha"), 40), "date": _clean((commit.get("committer") or {}).get("date"), 40),
                "message": _clean((commit.get("message") or "").splitlines()[0] if commit.get("message") else "")}
    if kind == "crossref":
        data = json.loads(text)
        items = (data.get("message") or {}).get("items") or []
        works = []
        for item in items[:20]:
            licences = sorted({_clean(lic.get("URL"), 120) for lic in item.get("license") or []})
            works.append({"doi": _clean(item.get("DOI"), 120), "title": _clean((item.get("title") or [""])[0]),
                          "licence": licences})
        return {"total": int((data.get("message") or {}).get("total-results") or 0), "works": works}
    # http_page: the page is compared by hash of its visible text; the title helps a person
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    visible = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", text, flags=re.S | re.I)
    return {"sha256": hashlib.sha256(" ".join(visible.split()).encode("utf-8")).hexdigest(),
            "title": _clean(title.group(1) if title else "")}


def _differences(old: dict | None, new: dict, source: dict) -> list[dict]:
    if old is None:
        return [{"field": "*", "change": "first_snapshot"}]
    diffs = []
    if source["kind"] == "crossref":
        before = {w["doi"] for w in old.get("works", [])}
        added = [w for w in new.get("works", []) if w["doi"] not in before]
        if added:
            # one proposal per check: a reading list for a person, not one record per work
            diffs.append({"field": "works", "change": "new_works", "count": len(added),
                          "works": [{"doi": w["doi"], "title": w["title"], "licence": w["licence"]} for w in added]})
        return diffs
    for key in sorted(set(old) | set(new)):
        if old.get(key) != new.get(key):
            diffs.append({"field": key, "change": "changed", "old": old.get(key), "new": new.get(key)})
    return diffs


def _proposal(source: dict, diff: dict, summary: dict, checked_at: str) -> dict:
    licence_changed = diff.get("field") in ("licence", "license")
    needs_human = licence_changed or source.get("kind") == "http_page"
    pid = hashlib.sha256(json.dumps([source["id"], diff], sort_keys=True, ensure_ascii=False)
                         .encode("utf-8")).hexdigest()[:16]
    return {
        "kind": "voznativa.change_proposal", "schema_version": 1, "id": f"cp-{source['id']}-{pid}",
        "source_id": source["id"], "discovered_at": checked_at,
        "state": "NEEDS_HUMAN" if needs_human else "CANDIDATE",
        "trail": list(PIPELINE[:5]) + ["NEEDS_HUMAN" if needs_human else "CANDIDATE"],
        "difference": diff, "summary_sha256": hashlib.sha256(json.dumps(summary, sort_keys=True).encode()).hexdigest(),
        "licence_check": ("licence changed: a person must re-check what the new terms allow" if licence_changed
                          else source["licence_note"]),
        "affects": source["affects"], "tests": source.get("tests") or [],
        "apply": "never automatic: a person evaluates in isolation and changes the repository through a reviewed "
                 "commit; data changes need the release gates",
        "rollback": "nothing was changed by the watcher; discard the proposal",
        "untrusted_content": True,
    }


def _due(source: dict, snapshot: dict | None, now: datetime) -> bool:
    if not snapshot or not snapshot.get("checked_at"):
        return True
    last = datetime.fromisoformat(snapshot["checked_at"])
    return (now - last).total_seconds() >= float(source.get("min_interval_hours", 24)) * 3600


def _load_snapshot(directory: Path, sid: str) -> dict | None:
    path = directory / "snapshots" / f"{sid}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def check(sources: list[dict] | None = None, mode: str = "report", offline: bool = False, force: bool = False,
          only: list[str] | None = None, fetcher=None, directory: Path | None = None, sleep=time.sleep) -> dict:
    """Check due sources; ``report`` writes nothing, ``propose`` stores snapshots and proposals."""
    if mode not in ("report", "propose"):
        raise WatchError("mode must be report or propose (the watcher never applies changes)")
    from .corpus.connectors import AccessError, HttpLimits, fetch
    sources = sources if sources is not None else load_sources()
    if only:
        unknown = set(only) - {s["id"] for s in sources}
        if unknown:
            raise WatchError(f"unknown source ids: {sorted(unknown)}")
        sources = [s for s in sources if s["id"] in only]
    directory = directory or state_dir()
    fetcher = fetcher or (lambda url, hosts, headers: fetch(url, hosts, HttpLimits(max_bytes=2_000_000),
                                                             headers=headers, block_private=True))
    now = _now()
    checked_at = now.isoformat(timespec="seconds")
    results, proposals = [], []
    for source in sources:
        snapshot = _load_snapshot(directory, source["id"])
        row = {"source_id": source["id"], "kind": source["kind"], "enabled": bool(source.get("enabled", True))}
        if not source.get("enabled", True):
            results.append(dict(row, status="disabled", reason=_clean(source.get("disabled_reason"), 200)))
            continue
        if offline:
            age = None
            if snapshot and snapshot.get("checked_at"):
                age = round((now - datetime.fromisoformat(snapshot["checked_at"])).total_seconds() / 3600, 1)
            stale = age is None or age > float(source.get("stale_after_hours", 24 * 14))
            results.append(dict(row, status="offline", last_checked=snapshot.get("checked_at") if snapshot else None,
                                age_hours=age, stale=stale))
            continue
        if not force and not _due(source, snapshot, now):
            results.append(dict(row, status="not_due", last_checked=snapshot.get("checked_at")))
            continue
        url = source["url"].replace("{since}", (snapshot or {}).get("checked_at", "2026-01-01T00:00:00+00:00")[:10]) \
            .replace("{until}", checked_at[:10])
        headers = {}
        if snapshot and source["kind"] != "crossref":
            if snapshot.get("etag"):
                headers["If-None-Match"] = snapshot["etag"]
            if snapshot.get("last_modified"):
                headers["If-Modified-Since"] = snapshot["last_modified"]
        response, error = _fetch_with_retry(fetcher, url, source, headers, sleep, AccessError)
        row, found = _evaluate(source, row, snapshot, response, error, directory, mode, checked_at)
        results.append(row)
        proposals += found
    if mode == "propose":
        for prop in proposals:
            path = directory / "proposals" / f"{prop['id']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(json.dumps(prop, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"kind": "voznativa.watch_report", "mode": mode, "offline": offline, "checked_at": checked_at,
            "state_dir": str(directory) if mode == "propose" else None, "results": results,
            "proposals": [p["id"] for p in proposals],
            "policy": "report/propose only; nothing in the repository, the rules or the installation was changed"}


def _fetch_with_retry(fetcher, url: str, source: dict, headers: dict, sleep, access_error):
    """One request, and one more only for 429 (after Retry-After, capped) or 5xx."""
    error = None
    for attempt in (1, 2):
        try:
            return fetcher(url, set(source["hosts"]), headers), None
        except access_error as exc:
            status = getattr(exc, "status", None)
            error = {"kind": exc.kind, "status": status, "message": _clean(str(exc), 200)}
            if attempt == 2 or not (status == 429 or (status is not None and 500 <= status < 600)):
                break
            wait = 2.0
            if status == 429:
                try:
                    wait = min(float(getattr(exc, "retry_after", None) or 5), MAX_RETRY_AFTER_S)
                except ValueError:
                    wait = 5.0
            sleep(wait)
    return None, error


def _evaluate(source, row, snapshot, response, error, directory, mode, checked_at) -> tuple[dict, list[dict]]:
    """Result row and proposals for one fetched (or failed) source; stores the snapshot in propose mode."""
    propose = mode == "propose"
    if response is None:
        removed = bool(error) and error.get("status") in (404, 410)
        found = [_proposal(source, {"field": "*", "change": "source_removed", "status": error.get("status")}, {},
                           checked_at)] if removed and propose else []
        return dict(row, status="source_removed" if removed else "error", error=error), found
    if response["status"] == 304:
        if propose and snapshot:
            _store_snapshot(directory, source["id"], dict(snapshot, checked_at=checked_at))
        return dict(row, status="unchanged", via="304"), []
    try:
        summary = _summary(source, response)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        return dict(row, status="error", error={"kind": "unparseable", "message": _clean(exc, 200)}), []
    if len(json.dumps(summary, ensure_ascii=False)) > MAX_SUMMARY:
        return dict(row, status="error", error={"kind": "summary_too_large"}), []
    diffs = _differences((snapshot or {}).get("summary"), summary, source)
    status = "changed" if diffs and snapshot else "first_snapshot" if not snapshot else "unchanged"
    found = []
    if propose:
        _store_snapshot(directory, source["id"], {"checked_at": checked_at, "summary": summary,
                                                  "etag": response.get("etag"),
                                                  "last_modified": response.get("last_modified")})
        if snapshot:
            found = [_proposal(source, d, summary, checked_at) for d in diffs]
    return dict(row, status=status, differences=diffs, summary=summary), found


def _store_snapshot(directory: Path, sid: str, data: dict) -> None:
    path = directory / "snapshots" / f"{sid}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def list_proposals(directory: Path | None = None) -> list[dict]:
    folder = (directory or state_dir()) / "proposals"
    out = []
    for path in sorted(folder.glob("*.json")) if folder.exists() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        out.append({k: data.get(k) for k in ("id", "source_id", "state", "discovered_at", "difference", "affects")})
    return out
