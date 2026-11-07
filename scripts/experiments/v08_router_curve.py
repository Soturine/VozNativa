"""v0.8 CP8 (V08-GAP-05): coverage x precision curve of the genre router.

Same units and split as scripts/router_audit.py (7 corpora, evaluation split,
windows of <= 150 words). For each unit it keeps the router's ranked scores
(``infer_genre(...)["scores"]``, after the corroboration rule) and replays
the router's decision rule over a grid of thresholds:

    emit top genre  iff  top >= min_score  and  top - runner_up >= min_margin

so the curve shows what each threshold pair would give, per source and in
total, without changing the router. The current pair is marked. Choosing new
thresholds from this curve would need the calibration split (never the
evaluation split it is measured on) and a separate confirmation.

    VOZNATIVA_CORPUS_CACHE=... python -B scripts/experiments/v08_router_curve.py --out curve.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from corpus_crossgenre import SOURCES, pick  # noqa: E402
from voznativa.benchmark import wilson  # noqa: E402
from voznativa.corpus.connectors import LocalFilesConnector, cache_dir  # noqa: E402
from voznativa.corpus.evaluate import split_records, windows  # noqa: E402
from voznativa.corpus.policy import require  # noqa: E402
from voznativa.corpus.processing import assign_splits, cluster, provenance  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402
from voznativa.router import data, infer_genre  # noqa: E402

MIN_SCORES = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)
MARGINS = (0.5, 1.0, 1.5, 2.0, 3.0)


def decide(scores: dict, min_score: float, min_margin: float) -> str:
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    if not ranked or ranked[0][1] < min_score:
        return "unknown"
    runner = ranked[1][1] if len(ranked) > 1 else 0.0
    return ranked[0][0] if ranked[0][1] - runner >= min_margin else "unknown"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-units", type=int, default=1500)
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    records = []
    for sid in SOURCES:
        entry = get_source(sid)
        require(entry, "PROCESS_LOCAL")
        require(entry, "EXPORT_STATISTICS")
        records += provenance(entry, LocalFilesConnector(entry, cache_dir(sid)).stream_records())
    cluster(records)
    splits = assign_splits(records, {"calibration": 0.5, "evaluation": 0.5})
    units = []
    for sid, (_, acceptable, _) in SOURCES.items():
        for u in pick(windows([r for r in split_records(records, splits, "evaluation") if r.source == sid]),
                      args.max_units):
            result = infer_genre(u["text"])
            units.append({"source": sid, "acceptable": acceptable, "scores": result["scores"],
                          "current": result["value"]})
    current = (data()["min_score"], data()["min_margin"])
    rows = []
    for min_score in MIN_SCORES:
        for margin in MARGINS:
            total, per = Counter(), {}
            for u in units:
                g = decide(u["scores"], min_score, margin)
                c = per.setdefault(u["source"], Counter())
                for counter in (total, c):
                    counter["units"] += 1
                    if g != "unknown":
                        counter["emitted"] += 1
                        counter["right" if g in u["acceptable"] else "wrong"] += 1
            rows.append({"min_score": min_score, "min_margin": margin, "current": (min_score, margin) == current,
                         "units": total["units"], "emitted": total["emitted"],
                         "precision": {"k": total["right"], "n": total["emitted"],
                                       "wilson95": wilson(total["right"], total["emitted"])},
                         "useful_coverage": {"k": total["right"], "n": total["units"],
                                             "wilson95": wilson(total["right"], total["units"])},
                         "wrong": total["wrong"],
                         "per_source": {s: {"useful": c["right"], "wrong": c["wrong"], "units": c["units"]}
                                        for s, c in sorted(per.items())}})
    # The replayed rule must reproduce the router at its current thresholds.
    replay = next(r for r in rows if r["current"])
    actual_emitted = sum(u["current"] != "unknown" for u in units)
    for r in sorted(rows, key=lambda r: (-r["useful_coverage"]["k"], r["wrong"])):
        p = r["precision"]
        print(f"min_score {r['min_score']:>3} margin {r['min_margin']:>3}{' *' if r['current'] else '  '} "
              f"emitted {r['emitted']:>5} useful {r['useful_coverage']['k']:>5}/{r['units']} "
              f"({r['useful_coverage']['k'] / r['units']:.1%}) precision "
              f"{(p['k'] / p['n']) if p['n'] else 0:.1%} wrong {r['wrong']}")
    print(f"replay at current thresholds emitted {replay['emitted']}; router emitted {actual_emitted}")
    if args.out:
        Path(args.out).write_text(json.dumps({"kind": "voznativa.router_curve", "schema_version": 1,
                                              "split": "evaluation", "current": current, "rows": rows,
                                              "replay_matches_router": replay["emitted"] == actual_emitted},
                                             ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0 if replay["emitted"] == actual_emitted else 1


if __name__ == "__main__":
    raise SystemExit(main())
