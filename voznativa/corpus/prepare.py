"""Prepare a source: policy-checked download into the local cache, a full
read through its connector, and the evidence that justifies CONNECTOR_READY.

The local copy stays outside the repository (``connectors.cache_dir``); the
registry records only sha256, sizes, counts and the read errors.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from .connectors import LocalFilesConnector, ReadLimits, cache_dir, download


def prepare(entry: dict, root: Path | None = None, today: str | None = None, fetch: bool = True,
            limits: ReadLimits = ReadLimits()) -> tuple[dict, dict]:
    """Return (updated entry, report). ``fetch=False`` reads an existing copy."""
    root = Path(root or cache_dir(entry["id"]))
    connector = entry.get("connector") or {}
    if connector.get("id") != "local-files":
        raise ValueError(f"{entry['id']}: prepare reads through the local-files connector")
    downloads = [download(entry, asset, root) for asset in connector.get("assets", [])] if fetch else []
    reader = LocalFilesConnector(entry, root, limits)
    access = reader.validate_access()
    if not access["ok"]:
        raise FileNotFoundError(f"{entry['id']}: assets missing in the cache: {access['missing']}")
    counts = {}
    for record in reader.stream_records():
        counts[record.asset] = counts.get(record.asset, 0) + 1
    integrity = reader.validate_integrity()
    by_name = {d["asset"]: d for d in downloads}
    assets = []
    for asset in connector.get("assets", []):
        found = next(a for a in integrity["assets"] if a["name"] == asset["name"])
        assets.append(dict(asset, sha256=found["sha256"],
                           **({"partial": True} if by_name.get(asset["name"], {}).get("partial") else {})))
    report = {"source": entry["id"], "date": today or date.today().isoformat(), "connector": "local-files",
              "records_by_asset": counts, "records_read": sum(counts.values()),
              "read_errors": len(reader.errors), "read_error_examples": reader.errors[:5],
              "downloads": [{k: v for k, v in d.items() if k != "policy"} for d in downloads],
              "policy": [d["policy"] for d in downloads][:1]}
    updated = dict(entry)
    updated["connector"] = dict(connector, assets=assets)
    verification = dict(updated.get("verification") or {})
    verification["connector"] = {"date": report["date"], "connector": "local-files",
                                 "records_read": report["records_read"], "read_errors": report["read_errors"],
                                 "result": "read" if report["records_read"] else "empty"}
    updated["verification"] = verification
    if updated["status"] in {"ACCESS_VERIFIED", "CONNECTOR_READY"} and report["records_read"]:
        updated["status"] = "CONNECTOR_READY"
    return updated, report
