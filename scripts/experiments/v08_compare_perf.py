"""v0.8 CP7 (V08-GAP-12): time of compare() on well-formed long documents.

Whole Markdown files of the repository (README, SKILL, docs/*.md, MIT
material) are concatenated until each size is reached; the candidate appends
one plain sentence. Run it from a checkout of the revision to measure:

    python -B scripts/experiments/v08_compare_perf.py --sizes 5000,10000,20000,30000 --out run.json
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def documents(sizes: list[int]) -> list[str]:
    files = [ROOT / "README.md", ROOT / "SKILL.md", *sorted((ROOT / "docs").glob("*.md"))]
    out, doc, wanted = [], "", sorted(sizes)
    for f in files:
        doc += f.read_text(encoding="utf-8").replace("\r\n", "\n") + "\n\n"
        while wanted and len(doc.split()) >= wanted[0]:
            out.append(doc)
            wanted.pop(0)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="5000,10000,20000,30000")
    ap.add_argument("--root", help="checkout whose voznativa is measured (default: this one)")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    sys.path.insert(0, str(Path(args.root).resolve() if args.root else ROOT))
    from voznativa.compare import compare
    rows = []
    for doc in documents([int(s) for s in args.sizes.split(",")]):
        started = time.perf_counter()
        report = compare(doc, doc + "\n\nUma frase nova no fim do documento.\n")
        rows.append({"words": len(doc.split()), "seconds": round(time.perf_counter() - started, 2),
                     "status": report["status"]})
        print(f"{rows[-1]['words']:>7} words {rows[-1]['seconds']:>7.2f} s  {rows[-1]['status']}", flush=True)
    if args.out:
        Path(args.out).write_text(json.dumps({"kind": "voznativa.perf_compare_curve", "schema_version": 1,
                                              "python": platform.python_version(),
                                              "platform": platform.platform(terse=True), "rows": rows},
                                             indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
