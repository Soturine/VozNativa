#!/usr/bin/env python3
"""Reproducible timing of ``compare`` on synthetic documents (v0.9 CP0, release criterion R9).

The method is fixed before any v0.9 change so the baseline (v0.8.1) and the
candidate are measured the same way:

* the documents are the generator of ``evals/test_v08_compare_perf.py``
  (one distinct name per block, a negation and a number per block), at
  100, 400 and 800 blocks (about 3k, 11k and 22k words);
* the candidate is the document plus one appended sentence (the case that
  used to be quadratic and gave the long-document false red);
* each size is timed ``--repeat`` times in this process, alternating sizes
  so a burst of machine load hits all of them; the report keeps every
  sample, the minimum and the median of wall time and of CPU time
  (``time.process_time``, which other processes' load does not inflate);
* the environment (Python, platform, CPU count, revision, dirty tree) is
  recorded with the samples.

    python scripts/perf_compare.py --out perf.json            # this checkout
    python scripts/perf_compare.py --root /other/checkout     # another revision, same method
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SIZES = (100, 400, 800)


def name(k: int) -> str:
    letters = ""
    k += 1
    while True:
        k, r = divmod(k, 26)
        letters += "abcdefghijklmnopqrstuvwxyz"[r]
        if not k:
            return "Mar" + letters


def document(blocks: int) -> str:
    out = []
    for k in range(blocks):
        out.append(f"No bloco {k}, {name(k)} revisou o contrato e {name(k + 1)} enviou o parecer "
                   f"ao comitê. O prazo não pode passar de {k + 1} dias.")
    return "\n\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent),
                    help="checkout whose voznativa package is timed")
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    sys.path.insert(0, str(root))
    from voznativa import __version__
    from voznativa.compare import compare

    docs = {n: document(n) for n in SIZES}
    compare(docs[SIZES[0]], docs[SIZES[0]] + "\nUma frase nova.\n")  # warm-up: imports, caches
    samples = {n: {"wall": [], "cpu": []} for n in SIZES}
    for _ in range(args.repeat):
        for n in SIZES:
            w0, c0 = time.perf_counter(), time.process_time()
            compare(docs[n], docs[n] + "\nUma frase nova.\n")
            samples[n]["cpu"].append(round(time.process_time() - c0, 4))
            samples[n]["wall"].append(round(time.perf_counter() - w0, 4))

    def git(*a):
        done = subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True)
        return done.stdout.strip()

    result = {
        "kind": "voznativa.perf_compare", "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": __version__, "revision": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain")),
        "environment": {"python": platform.python_version(), "platform": platform.platform(terse=True),
                        "cpus": os.cpu_count()},
        "repeat": args.repeat,
        "sizes": {str(n): {"words": len(docs[n].split()), **samples[n],
                           "wall_min": min(samples[n]["wall"]), "wall_median": statistics.median(samples[n]["wall"]),
                           "cpu_min": min(samples[n]["cpu"]), "cpu_median": statistics.median(samples[n]["cpu"])}
                  for n in SIZES},
    }
    small, large = result["sizes"][str(SIZES[0])], result["sizes"][str(SIZES[-1])]
    result["ratio_800_100_cpu_min"] = round(large["cpu_min"] / max(small["cpu_min"], 1e-3), 2)
    text = json.dumps(result, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
