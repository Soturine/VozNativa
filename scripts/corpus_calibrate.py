#!/usr/bin/env python3
"""Measure VozNativa's detectors on prepared human-written corpora (M5).

Uses the splits of the integrity run (calibration / evaluation): numbers are
reported for both so a decision taken on calibration is checked on
evaluation. Aggregate statistics only (policy: EXPORT_STATISTICS).

    python scripts/corpus_calibrate.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.corpus.connectors import LocalFilesConnector, cache_dir  # noqa: E402
from voznativa.corpus.evaluate import (by_label, documents, pattern_eval, split_records,  # noqa: E402
                                       variant_documents, variant_eval)
from voznativa.corpus.policy import require  # noqa: E402
from voznativa.corpus.processing import assign_splits, cluster, provenance  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402

# Genre each source is read as: the closest router genre to how the texts were published.
GENRE = {"ud-portuguese-bosque": "journalistic", "b2w-reviews01": "social"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    started = time.monotonic()
    entries, records = {}, []
    for sid in GENRE:
        entry = get_source(sid)
        require(entry, "PROCESS_LOCAL")
        require(entry, "EXPORT_STATISTICS")
        entries[sid] = entry
        reader = LocalFilesConnector(entry, cache_dir(sid))
        records += provenance(entry, reader.stream_records())
    cluster(records)
    splits = assign_splits(records, {"calibration": 0.5, "evaluation": 0.5})
    report = {"kind": "voznativa.corpus_calibration_run", "date": args.date, "splits": "integrity run splits "
              "(same salt and units)", "sources": {}}
    bosque = entries["ud-portuguese-bosque"]
    label = by_label(bosque)
    for split in ("calibration", "evaluation"):
        recs = [r for r in split_records(records, splits, split) if r.source == "ud-portuguese-bosque"]
        report.setdefault("variant", {})[split] = variant_eval(recs, label)
        report.setdefault("variant_documents", {})[split] = variant_documents(recs, label)
    for sid, genre in GENRE.items():
        report["sources"][sid] = {"genre": genre}
        for split in ("calibration", "evaluation"):
            recs = [r for r in split_records(records, splits, split) if r.source == sid]
            if sid == "ud-portuguese-bosque":   # Brazilian documents only (CF): the detector targets PT-BR
                recs = [r for r in recs if label(r) == "pt-BR"]
            report["sources"][sid][split] = pattern_eval(documents(recs), genre)
    report["seconds"] = round(time.monotonic() - started, 1)
    out = ROOT / "evals" / "corpus" / "runs" / f"calibration-{args.date}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for split in ("calibration", "evaluation"):
        v = report["variant"][split]
        print(split, "PT-PT recall", v["recall_pt_pt"]["rate"], "PT-BR FPR", v["false_positive_rate_pt_br"]["rate"],
              "precision", v["precision"]["rate"], "| documents", {k: x["rate"] for k, x in
                                                               report["variant_documents"][split].items()})
        for sid in GENRE:
            p = report["sources"][sid][split]
            print("  ", sid, "docs", p["documents"], "edit_rate", p["edit_rate"]["rate"], p["threshold"])
    print(out.relative_to(ROOT).as_posix(), report["seconds"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
