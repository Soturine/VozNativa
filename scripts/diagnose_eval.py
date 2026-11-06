#!/usr/bin/env python3
"""Diagnostics on published human text (v0.7.0 CP9D): how often does
``diagnose`` call something an error in text that editors already published?

Same units as scripts/corpus_crossgenre.py (windows of <= 150 words, stable
hash selection, evaluation split). Aggregate counts only.

    python scripts/diagnose_eval.py --date 2026-11-06
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from corpus_crossgenre import SOURCES, pick  # noqa: E402
from voznativa.corpus.connectors import LocalFilesConnector, cache_dir  # noqa: E402
from voznativa.corpus.evaluate import split_records, windows  # noqa: E402
from voznativa.corpus.policy import require  # noqa: E402
from voznativa.corpus.processing import assign_splits, cluster, provenance  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402
from voznativa.diagnose import diagnose  # noqa: E402
from voznativa.router import route  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--max-units", type=int, default=600)
    args = parser.parse_args(argv)
    records = []
    for sid in SOURCES:
        entry = get_source(sid)
        require(entry, "PROCESS_LOCAL")
        require(entry, "EXPORT_STATISTICS")
        records += provenance(entry, LocalFilesConnector(entry, cache_dir(sid)).stream_records())
    cluster(records)
    splits = assign_splits(records, {"calibration": 0.5, "evaluation": 0.5})
    report = {"kind": "voznativa.diagnose_eval_run", "schema_version": 1, "date": args.date,
              "split": "evaluation", "unit": "window of <= 150 words", "sources": {}}
    for sid, (genre, _, _) in SOURCES.items():
        units = pick(windows([r for r in split_records(records, splits, "evaluation") if r.source == sid]),
                     args.max_units)
        by_class, by_type, words = Counter(), Counter(), 0
        for u in units:
            ctx = route(u["text"])            # inferred, as a user would get it
            for d in diagnose(u["text"], ctx)["diagnostics"]:
                by_class[d["class"]] += 1
                by_type[f'{d["class"]}:{d["type"]}'] += 1
            words += u["words"]
        report["sources"][sid] = {"units": len(units), "words": words,
                                  "per_1000_words": {k: round(1000 * v / max(1, words), 3) for k, v in by_class.items()},
                                  "by_type": dict(by_type.most_common(10))}
        print(sid, len(units), report["sources"][sid]["per_1000_words"])
    out = ROOT / "evals" / "linguistics" / "runs" / f"diagnose-{args.date}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
