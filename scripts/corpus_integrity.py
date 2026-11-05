#!/usr/bin/env python3
"""Integrity run over prepared sources: provenance, deduplication across
sources, stable calibration/evaluation splits and a leakage check.

Reads only the local cache; checks the data policy (PROCESS_LOCAL and
EXPORT_STATISTICS) before reading and before writing the committed report.
The committed report holds aggregate counts only; the per-record manifests
(hashes, groups, splits) stay in the cache next to the data.

    python scripts/corpus_integrity.py ud-portuguese-bosque b2w-reviews01
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.corpus.connectors import LocalFilesConnector, cache_dir  # noqa: E402
from voznativa.corpus.policy import require  # noqa: E402
from voznativa.corpus.processing import assign_splits, cluster, leakage, provenance  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402
from voznativa.corpus.runs import run_file  # noqa: E402

FRACTIONS = {"calibration": 0.5, "evaluation": 0.5}


def load(source_id: str):
    entry = get_source(source_id)
    require(entry, "PROCESS_LOCAL")
    reader = LocalFilesConnector(entry, cache_dir(source_id))
    shas = {a["name"]: a.get("sha256") for a in entry["connector"]["assets"]}
    return entry, provenance(entry, reader.stream_records(), shas), reader.errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", nargs="+")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    started = time.monotonic()
    entries, records, errors = {}, [], {}
    for source_id in args.sources:
        entry, recs, errs = load(source_id)
        entries[source_id], errors[source_id] = entry, len(errs)
        records += recs
    dedup = cluster(records)
    splits = assign_splits(records, FRACTIONS)
    leak = leakage(records, splits)
    by_source = {}
    for sid in args.sources:
        mine = [r for r in records if r.source == sid]
        by_source[sid] = {"records": len(mine), "groups": len({r.group for r in mine}),
                          "read_errors": errors[sid],
                          "split_records": dict(Counter(splits[f"{r.source}:{r.record_id}"] for r in mine)),
                          "split_groups": dict(Counter(splits[f"{r.source}:{r.record_id}"] for r in
                                                       {r.group: r for r in mine}.values())),
                          "asset_sha256": {a["name"]: a.get("sha256") for a in entries[sid]["connector"]["assets"]}}
    manifests = {}
    for sid in args.sources:
        rows = [dict(r.as_manifest(), split=splits[f"{r.source}:{r.record_id}"]) for r in records if r.source == sid]
        path = cache_dir(sid) / f"manifest-{args.date}.jsonl"
        path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")
        manifests[sid] = {"records": len(rows), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "location": "local cache (not committed)"}
    for sid in args.sources:
        require(entries[sid], "EXPORT_STATISTICS")
    report = {"kind": "voznativa.corpus_integrity_run", "date": args.date, "sources": by_source,
              "deduplication": dedup, "split": {"fractions": FRACTIONS, "unit": "group merged with duplicate cluster",
                                                "salt": "voznativa-v0.6"},
              "leakage": {k: (len(v) if isinstance(v, list) else v) for k, v in leak.items()},
              "manifests": manifests, "seconds": round(time.monotonic() - started, 1)}
    out = run_file(ROOT, "integrity", args.date, args.sources)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("deduplication", "leakage", "seconds")}, indent=1))
    print(out.relative_to(ROOT).as_posix())
    return 1 if leak["contaminated"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
