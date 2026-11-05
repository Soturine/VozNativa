#!/usr/bin/env python3
"""Attest slang lexicon forms in dated corpora (v0.6.0 CP7).

Counts each lexicon entry's detection pattern on the *calibration* split of
prepared, EVALUATION_INTEGRATED sources (the evaluation split stays unseen),
then writes:

* ``evals/corpus/runs/slang-attestation-<date>.json``: the run (counts only);
* ``voznativa/data/slang/attestations.yml``: per entry, the attestations with
  the source's own period (from the Corpus Registry) and the evidence level.

Evidence rule: E2 when a source with provenance attests the form at least
MIN_COUNT times and the form is unambiguous or detected by context; an
ambiguous form detected by surface stays E0 (the counts may be other senses).
Counts are never sense-checked here (``sense_checked: false``).

    python scripts/slang_attest.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa import temporal  # noqa: E402
from voznativa.corpus.connectors import LocalFilesConnector, cache_dir  # noqa: E402
from voznativa.corpus.evaluate import by_label  # noqa: E402
from voznativa.corpus.policy import require  # noqa: E402
from voznativa.corpus.processing import assign_splits, cluster, provenance  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402

SOURCES = {"ud-portuguese-bosque": "pt-BR sentences only (CF)", "b2w-reviews01": "all records in the prefix"}
MIN_COUNT = 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    entries, records = {}, []
    for sid in SOURCES:
        entry = get_source(sid)
        require(entry, "PROCESS_LOCAL")
        require(entry, "EXPORT_STATISTICS")
        entries[sid] = entry
        records += provenance(entry, LocalFilesConnector(entry, cache_dir(sid)).stream_records())
    cluster(records)
    splits = assign_splits(records, {"calibration": 0.5, "evaluation": 0.5})
    label = by_label(entries["ud-portuguese-bosque"])
    texts = {sid: [] for sid in SOURCES}
    for r in records:
        if splits[f"{r.source}:{r.record_id}"] != "calibration":
            continue
        if r.source == "ud-portuguese-bosque" and label(r) != "pt-BR":
            continue
        texts[r.source].append(temporal._norm(r.text))
    words = {sid: sum(len(t.split()) for t in ts) for sid, ts in texts.items()}
    run_rel = f"evals/corpus/runs/slang-attestation-{args.date}.json"
    lexicon = temporal.load_lexicon()
    counts = {}
    for entry, rx in lexicon["_rx"]:
        counts[entry["id"]] = {sid: sum(len(rx.findall(t)) for t in ts) for sid, ts in texts.items()}
    out = {}
    for entry, _ in lexicon["_rx"]:
        eid, amb = entry["id"], entry["ambiguity"]
        atts = []
        for sid in SOURCES:
            period = entries[sid]["period"]
            n = counts[eid][sid]
            atts.append({"source": sid, "from": int(period["from"]), "to": int(period["to"]),
                         "genre": entries[sid]["genres"][0], "split": "calibration", "words": words[sid],
                         "count": n, "per_million_words": round(1e6 * n / max(1, words[sid]), 2),
                         "sense_checked": False, "run": run_rel})
        hit_years = [y for a in atts if a["count"] > 0 for y in (a["from"], a["to"])]
        reliable = not amb.get("ambiguous") or amb.get("detection") == "context"
        strong = [a for a in atts if a["count"] >= MIN_COUNT]
        level = "E2" if strong and reliable else "E0"
        notes = []
        if strong and not reliable:
            notes.append("attested by surface form only; the form has other senses, so counts may not be this one")
        if not hit_years:
            notes.append("not attested in the available corpora")
        out[eid] = {"period": {"attestations": atts, "observed_from": min(hit_years) if hit_years else None,
                               "observed_until": max(hit_years) if hit_years else None,
                               "last_verified_at": args.date},
                    "evidence": {"level": level, "sources": [a["source"] for a in strong], "notes": notes}}
    header = ("# Written by scripts/slang_attest.py; do not edit by hand.\n"
              "# Surface-form counts on the calibration split; sense_checked: false.\n")
    att_path = temporal.LEXICON.parent / temporal.ATTESTATIONS
    att_path.write_text(header + yaml.safe_dump({"schema_version": 2, "kind": "voznativa.slang_attestations",
                                                 "date": args.date, "entries": out},
                                                allow_unicode=True, sort_keys=False, width=110),
                        encoding="utf-8", newline="\n")
    temporal._load.cache_clear()
    temporal.load_lexicon()          # the merged lexicon must still validate
    run = {"kind": "voznativa.slang_attestation_run", "date": args.date, "split": "calibration",
           "sources": {sid: {"words": words[sid], "documents_or_sentences": len(texts[sid]), "scope": SOURCES[sid],
                             "period": entries[sid]["period"]} for sid in SOURCES},
           "counts": counts, "min_count_for_e2": MIN_COUNT,
           "levels": {eid: v["evidence"]["level"] for eid, v in out.items()}}
    (ROOT / run_rel).write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for eid, c in counts.items():
        print(f"{eid:14} {c}  {out[eid]['evidence']['level']}")
    print(run_rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
