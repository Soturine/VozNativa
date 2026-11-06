#!/usr/bin/env python3
"""Router abstention audit (v0.7.0, pre-merge review). Read-only measurement.

Same units and split as scripts/corpus_crossgenre.py (evaluation split,
windows of <= 150 words). For each source and length bin it separates:

* emitted:   the router named a genre (not unknown);
* precision: emitted decisions that are in the source's acceptable set;
* useful coverage: acceptable emitted decisions / all units;
* wrong:     emitted decisions outside the acceptable set.

Abstention is not counted as an error: it keeps the conservative
protections. The audit does not change any threshold.

    python scripts/router_audit.py --date 2026-11-06
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from corpus_crossgenre import SOURCES, pick  # noqa: E402
from voznativa.corpus.connectors import LocalFilesConnector, cache_dir  # noqa: E402
from voznativa.corpus.evaluate import _rate, split_records, windows  # noqa: E402
from voznativa.corpus.policy import require  # noqa: E402
from voznativa.corpus.processing import assign_splits, cluster, provenance  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402
from voznativa.router import infer_genre  # noqa: E402

BINS = ((0, 20), (20, 50), (50, 100), (100, 10**9))


def bin_of(words: int) -> str:
    lo, hi = next(b for b in BINS if b[0] <= words < b[1])
    return f"{lo}+" if hi == 10**9 else f"{lo}-{hi - 1}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--max-units", type=int, default=1500)
    args = parser.parse_args(argv)
    records = []
    for sid in SOURCES:
        entry = get_source(sid)
        require(entry, "PROCESS_LOCAL")
        require(entry, "EXPORT_STATISTICS")
        records += provenance(entry, LocalFilesConnector(entry, cache_dir(sid)).stream_records())
    cluster(records)
    splits = assign_splits(records, {"calibration": 0.5, "evaluation": 0.5})
    report = {"kind": "voznativa.router_audit_run", "schema_version": 1, "date": args.date, "split": "evaluation",
              "unit": "window of <= 150 words", "note": "abstention keeps conservative protections; not an error",
              "sources": {}}
    totals = Counter()
    for sid, (_, acceptable, _) in SOURCES.items():
        units = pick(windows([r for r in split_records(records, splits, "evaluation") if r.source == sid]),
                     args.max_units)
        per_bin = defaultdict(Counter)
        for u in units:
            g = infer_genre(u["text"])["value"]
            b = per_bin[bin_of(u["words"])]
            b["units"] += 1
            if g != "unknown":
                b["emitted"] += 1
                b["right" if g in acceptable else "wrong"] += 1
        row = {"acceptable": sorted(acceptable), "bins": {}}
        agg = Counter()
        for name, c in sorted(per_bin.items(), key=lambda kv: int(kv[0].split("-")[0].rstrip("+"))):
            agg.update(c)
            row["bins"][name] = {"units": c["units"], "abstention": _rate(c["units"] - c["emitted"], c["units"]),
                                 "precision_of_emitted": _rate(c["right"], c["emitted"]) if c["emitted"] else None,
                                 "useful_coverage": _rate(c["right"], c["units"])}
        row.update(units=agg["units"], abstention=_rate(agg["units"] - agg["emitted"], agg["units"]),
                   precision_of_emitted=_rate(agg["right"], agg["emitted"]) if agg["emitted"] else None,
                   useful_coverage=_rate(agg["right"], agg["units"]), wrong=_rate(agg["wrong"], agg["units"]))
        totals.update(agg)
        report["sources"][sid] = row
        p = row["precision_of_emitted"]
        print(f"{sid:28s} units {row['units']:5d} abstain {row['abstention']['rate']} "
              f"precision {p['rate'] if p else None} (n={agg['emitted']}) useful {row['useful_coverage']['rate']} "
              f"| by length " + " ".join(f"{k}:{v['abstention']['rate']}" for k, v in row["bins"].items()))
    report["all"] = {"units": totals["units"], "emitted": totals["emitted"],
                     "precision_of_emitted": _rate(totals["right"], totals["emitted"]),
                     "useful_coverage": _rate(totals["right"], totals["units"]),
                     "wrong": _rate(totals["wrong"], totals["units"])}
    out = ROOT / "evals" / "corpus" / "runs" / f"router-audit-{args.date}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("ALL", report["all"])
    print(out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
