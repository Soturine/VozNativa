#!/usr/bin/env python3
"""Long-text evaluation on public-domain Brazilian literature (v0.6.0 CP10).

Source: machado-de-assis-corpus (registry), an explicit 6 MB prefix with 12
complete works (Project Gutenberg editions, pre-reform orthography) and 297
Wikisource pages (modern orthography). The segmentation rules were adjusted
on the Gutenberg works; the Wikisource pages were not used to adjust them.

Measures (aggregate counts only):
* segmentation at 900 and 400 words: cuts, cuts on a visible adjacent
  dependency, forced cuts (reported), unreported cuts, oversize segments;
  every segmentation is checked lossless;
* verse share per complete work;
* literary control: the editorial detector on each 900-word segment, read as
  `literary` and as `unknown` (a request that does not say it is literature);
* PT-PT markers on Brazilian literature in both orthographies.

    python scripts/corpus_longform.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa import longform  # noqa: E402
from voznativa.corpus.connectors import LocalFilesConnector, cache_dir  # noqa: E402
from voznativa.corpus.evaluate import _rate  # noqa: E402
from voznativa.corpus.policy import require  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402
from voznativa.corpus.runs import run_file  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.ptbr import variant_markers  # noqa: E402

SOURCE = "machado-de-assis-corpus"


TUNING_TITLES: set[str] = set()


def _title_key(title: str) -> str:
    from voznativa.text import fold
    return fold(title.split("/")[0]).strip()


def subset(record) -> str:
    """Gutenberg works (rules adjusted on them); Wikisource chapters of those
    same works (same text, other edition: not independent); other Wikisource
    pages (held out)."""
    if "Gutenberg" in (record.meta.get("fonte") or ""):
        return "gutenberg_tuning"
    if _title_key(record.meta.get("titulo") or "") in TUNING_TITLES:
        return "wikisource_same_works"
    return "wikisource_heldout"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    started = time.monotonic()
    entry = get_source(SOURCE)
    require(entry, "PROCESS_LOCAL")
    require(entry, "EXPORT_STATISTICS")
    reader = LocalFilesConnector(entry, cache_dir(SOURCE))
    records = list(reader.stream_records())
    TUNING_TITLES.update(_title_key(r.meta.get("titulo") or "") for r in records
                         if "Gutenberg" in (r.meta.get("fonte") or ""))
    report = {"kind": "voznativa.longform_run", "date": args.date, "source": SOURCE, "sources": {SOURCE: {}},
              "records": len(records), "read_errors": len(reader.errors), "segmentation": {}, "verse_share": {},
              "literary_control": {}, "variant_markers": {}}
    for max_words in (900, 400):
        agg: dict[str, Counter] = {}
        for r in records:
            c = agg.setdefault(subset(r), Counter())
            rep = longform.boundary_report(r.text, max_words)   # asserts lossless
            c["documents"] += 1
            c.update({k: v for k, v in rep.items()})
        report["segmentation"][str(max_words)] = {k: dict(v) for k, v in agg.items()}
    for r in records:
        if subset(r) == "gutenberg_tuning":
            report["verse_share"][r.meta.get("titulo")] = longform.verse_share(r.text)
    held = [r for r in records if subset(r) != "gutenberg_tuning"]
    report["verse_share_heldout"] = {"pages": len(held),
                                     "pages_mostly_verse": sum(longform.verse_share(r.text) >= 0.5 for r in held)}
    report["subsets"] = dict(Counter(subset(r) for r in records))
    for name in ("gutenberg_tuning", "wikisource_same_works", "wikisource_heldout"):
        segs = []
        for r in records:
            if subset(r) != name:
                continue
            seg = longform.segment(r.text, 900)
            segs += [r.text[s["start"]:s["end"]] for s in seg["segments"]]
        segs = [s for s in segs if len(s.split()) >= 50]
        control = {}
        for genre in ("literary", "unknown"):
            decisions, drivers, findings, words = Counter(), Counter(), 0, 0
            for s in segs:
                rep = detect(s, genre)
                decisions[rep["decision"]] += 1
                findings += len(rep["findings"])
                words += len(s.split())
                if rep["decision"] == "edit":
                    strong = {f["id"] for f in rep["findings"] if f["strength"] == "strong"}
                    drivers.update(sorted(strong) or ["weak_accumulation"])
            control[genre] = {"segments": len(segs), "words": words, "edit_rate": _rate(decisions["edit"], len(segs)),
                              "findings_per_1000_words": round(1000 * findings / max(1, words), 3),
                              "edit_drivers": dict(drivers.most_common(10))}
        # What the router infers when the request names no genre (the `unknown` row
        # only matters when inference misses the literature).
        from voznativa.router import infer_genre
        control["router_inferred_genre"] = dict(Counter(infer_genre(s)["value"] for s in segs).most_common())
        report["literary_control"][name] = control
        flagged, markers = 0, Counter()
        for s in segs:
            found = variant_markers(s)
            if found:
                flagged += 1
                markers.update(m["text"].lower() for m in found)
        report["variant_markers"][name] = {"segments": len(segs), "segments_with_pt_pt_marker": _rate(flagged, len(segs)),
                                           "markers": dict(markers.most_common(15))}
    report["seconds"] = round(time.monotonic() - started, 1)
    out = run_file(ROOT, "longform", args.date, {SOURCE})
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("segmentation", "verse_share_heldout")}, indent=1))
    for name, c in report["literary_control"].items():
        print(name, {g: (v["edit_rate"]["k"], v["edit_rate"]["n"], v["edit_drivers"]) for g, v in c.items()})
        print("  pt-pt", report["variant_markers"][name]["segments_with_pt_pt_marker"],
              report["variant_markers"][name]["markers"])
    print(out.relative_to(ROOT).as_posix(), report["seconds"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
