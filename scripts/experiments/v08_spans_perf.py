"""v0.8 CP2 (V08-GAP-02): growth curve and equality check for spans.extract.

Input: the repository's own Portuguese Markdown (README, SKILL, docs/*.md),
concatenated and cut to N words, so the text has the dates, names, numbers,
paths and code a real document has. MIT material, no corpus text.

    python -B scripts/experiments/v08_spans_perf.py curve --sizes 5000,10000,20000,40000 --out run.json
    python -B scripts/experiments/v08_spans_perf.py profile --words 20000
    python -B scripts/experiments/v08_spans_perf.py digest --words 40000   # sha256 of the full output

``digest`` hashes every field of every span (type, text, start, end, key,
anchors) so two revisions can be compared byte for byte.
"""
from __future__ import annotations

import argparse
import cProfile
import hashlib
import json
import platform
import pstats
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from voznativa.spans import extract  # noqa: E402


def source_text() -> str:
    paths = [ROOT / "README.md", ROOT / "SKILL.md", *sorted((ROOT / "docs").glob("*.md"))]
    return "\n\n".join(p.read_text(encoding="utf-8") for p in paths)


def text_of(words: int) -> str:
    base = source_text()
    tokens = base.split(" ")
    out, n = [], 0
    while n < words:
        out.extend(tokens)
        n = sum(len(t.split()) for t in out)
    # Cut on a space boundary at roughly ``words`` words.
    acc, count = [], 0
    for t in out:
        acc.append(t)
        count += len(t.split())
        if count >= words:
            break
    return " ".join(acc)


def digest(spans) -> str:
    h = hashlib.sha256()
    for s in spans:
        h.update(json.dumps([s.type, s.text, s.start, s.end, s.key, list(map(list, s.anchors))],
                            ensure_ascii=False).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def measure(words: int) -> dict:
    text = text_of(words)
    tracemalloc.start()
    started = time.perf_counter()
    spans = extract(text)
    seconds = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"words": len(text.split()), "chars": len(text), "spans": len(spans), "seconds": round(seconds, 3),
            "peak_mib": round(peak / 2**20, 1), "sha256": digest(spans)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("curve")
    c.add_argument("--sizes", default="2500,5000,10000,20000,40000")
    c.add_argument("--out")
    p = sub.add_parser("profile")
    p.add_argument("--words", type=int, default=20000)
    d = sub.add_parser("digest")
    d.add_argument("--words", type=int, default=40000)
    args = ap.parse_args(argv)
    if args.cmd == "curve":
        rows = [measure(int(n)) for n in args.sizes.split(",")]
        for r in rows:
            print(f"{r['words']:>8} words {r['spans']:>7} spans {r['seconds']:>9.3f} s {r['peak_mib']:>7} MiB")
        if args.out:
            Path(args.out).write_text(json.dumps({
                "kind": "voznativa.perf_spans_curve", "schema_version": 1, "python": platform.python_version(),
                "platform": platform.platform(terse=True), "processor": platform.processor(), "rows": rows},
                indent=2), encoding="utf-8")
    elif args.cmd == "profile":
        text = text_of(args.words)
        prof = cProfile.Profile()
        prof.enable()
        extract(text)
        prof.disable()
        pstats.Stats(prof).sort_stats("cumulative").print_stats(14)
    else:
        print(measure(args.words)["sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
