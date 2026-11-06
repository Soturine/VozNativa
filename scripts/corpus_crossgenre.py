#!/usr/bin/env python3
"""Cross-genre evaluation of VozNativa's instruments on human text (v0.7.0 CP3).

For every integrated source, on both splits of the integrity run (same salt
and units): genre routing out of domain, the editorial detectors' edit rate,
slang lexicon hits and (for Brazilian sources) PT-PT marker false positives.
Aggregate statistics only (policy: PROCESS_LOCAL and EXPORT_STATISTICS are
checked per source). Units are windows of <= 150 words inside one group, at
most ``--max-units`` per source and split, chosen by a stable hash.

    python scripts/corpus_crossgenre.py --date 2026-11-06

The acceptable genres per source are fixed here, before reading any result,
from the source's own description (registry ``genres`` / ``evidence_role``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.corpus.connectors import LocalFilesConnector, cache_dir  # noqa: E402
from voznativa.corpus.evaluate import (documents, pattern_eval, router_eval, slang_eval, split_records,  # noqa: E402
                                       variant_false_positives, windows)
from voznativa.corpus.policy import require  # noqa: E402
from voznativa.corpus.processing import assign_splits, cluster, provenance  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402
from voznativa.corpus.runs import run_file  # noqa: E402

# source -> (router genre used for the detectors, acceptable inferred genres, Brazilian text?)
SOURCES = {
    "ud-portuguese-bosque": ("journalistic", {"journalistic"}, None),          # mixed CF/CP: no BR-only claim
    "b2w-reviews01": ("social", {"social", "whatsapp"}, True),                 # product reviews by customers
    "machado-de-assis-corpus": ("literary", {"literary"}, True),
    "ud-portuguese-gsd": ("journalistic", {"journalistic", "social"}, True),   # blog and news
    "ud-portuguese-petrogold": ("academic", {"academic", "technical"}, True),
    "ud-portuguese-pud": ("journalistic", {"journalistic"}, None),             # translations; variety not stated
    "ud-portuguese-dantestocks": ("social", {"social", "whatsapp"}, True),     # tweets
}


def pick(units: list[dict], limit: int) -> list[dict]:
    keyed = sorted(units, key=lambda u: hashlib.sha256(u["text"].encode("utf-8")).hexdigest())
    return keyed[:limit]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--max-units", type=int, default=1500)
    args = parser.parse_args(argv)
    started = time.monotonic()
    records, entries = [], {}
    for sid in SOURCES:
        entry = get_source(sid)
        require(entry, "PROCESS_LOCAL")
        require(entry, "EXPORT_STATISTICS")
        entries[sid] = entry
        records += provenance(entry, LocalFilesConnector(entry, cache_dir(sid)).stream_records())
    cluster(records)
    splits = assign_splits(records, {"calibration": 0.5, "evaluation": 0.5})
    report = {"kind": "voznativa.corpus_crossgenre_run", "schema_version": 1, "date": args.date,
              "splits": "integrity run splits (salt voznativa-v0.6, unit = group merged with duplicate cluster)",
              "unit": "window of <= 150 words inside one group", "max_units": args.max_units, "sources": {}}
    for sid, (genre, acceptable, brazilian) in SOURCES.items():
        out = report["sources"][sid] = {"detector_genre": genre}
        for split in ("calibration", "evaluation"):
            recs = [r for r in split_records(records, splits, split) if r.source == sid]
            units = pick(windows(recs), args.max_units)
            docs = {f"u{i}": {"text": u["text"]} for i, u in enumerate(units)}
            row = {"records": len(recs), "units": len(units),
                   "router": router_eval(units, acceptable),
                   "patterns": {k: v for k, v in pattern_eval(docs, genre).items()
                                if k in ("documents", "words", "edit_rate", "edit_drivers", "findings_per_1000_words")},
                   "slang": slang_eval(units)}
            if brazilian:
                row["pt_pt_false_positives"] = variant_false_positives(units)
            out[split] = row
    report["seconds"] = round(time.monotonic() - started, 1)
    out_path = run_file(ROOT, "crossgenre", args.date, set(SOURCES))
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for sid, row in report["sources"].items():
        ev = row["evaluation"]
        print(f"{sid:28s} units {ev['units']:5d} router wrong {ev['router']['confident_wrong']['rate']} "
              f"abstain {ev['router']['abstention']['rate']} {ev['router']['confident_wrong_by_genre']} | "
              f"edit {ev['patterns']['edit_rate']['rate']} | slang/1k {ev['slang']['hits_per_1000_words']}"
              + (f" | ptpt {ev['pt_pt_false_positives']['flagged']['rate']}" if "pt_pt_false_positives" in ev else ""))
    print(out_path.relative_to(ROOT).as_posix(), report["seconds"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
