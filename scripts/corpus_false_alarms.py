#!/usr/bin/env python3
"""Diagnose false alarms on edited real text (v0.10 CP7).

Reads a CoNLL-U file (``# text =`` lines) that you obtained under its own
licence, runs ``diagnose`` on every sentence and reports **aggregate counts**
per status and type, plus the sentence ids of findings for local triage.
Sentence text is never written to the report: the corpus stays where its
licence allows it to be (outside this repository).

Edited published text (news, encyclopedic prose) is mostly standard written
Portuguese, so every ``ERROR_CONFIRMED`` there is either a real slip of the
source or a false alarm; ``--show`` prints the flagged sentences to the
terminal for a person to triage (do not commit that output).

    python scripts/corpus_false_alarms.py CORPUS.conllu [--genre news] [--root CHECKOUT] [--out report.json] [--show]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sentences(path: Path):
    sid = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# sent_id = "):
            sid = line.split("=", 1)[1].strip()
        elif line.startswith("# text = "):
            yield sid, line.split("=", 1)[1].strip()


def run(path: Path, genre: str | None, engine_root: Path, show: bool) -> dict:
    sys.path.insert(0, str(engine_root))
    from voznativa import __version__
    from voznativa.diagnose import diagnose
    from voznativa.router import route
    legacy = {"formal_error": "ERROR_CONFIRMED", "possible_contextual_error": "CONTEXT_DEPENDENT",
              "literary_license": "LITERARY_CHOICE"}
    by_status, by_type, flagged_ids, n = Counter(), Counter(), [], 0
    for sid, text in sentences(path):
        n += 1
        ctx = route(text, **({"genre": genre} if genre else {}))
        for d in diagnose(text, ctx)["diagnostics"]:
            status = d.get("status") or legacy.get(d["class"], "OTHER")
            by_status[status] += 1
            by_type[f"{status}:{d['type']}"] += 1
            if status == "ERROR_CONFIRMED":
                flagged_ids.append({"sent_id": sid, "type": d["type"]})
                if show:
                    print(f"[{sid}] {d['type']}: {d['text']!r} | {text}", file=sys.stderr)
    return {"kind": "voznativa.corpus_false_alarm_run", "engine_version": __version__,
            "corpus_file": path.name, "corpus_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "sentences": n, "genre": genre or "inferred", "by_status": dict(by_status),
            "by_type": dict(sorted(by_type.items())), "error_confirmed_ids": flagged_ids,
            "note": "aggregate counts only; sentence text is not stored. Triage of each ERROR_CONFIRMED is "
                    "recorded separately (true slip of the source / false alarm)."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus")
    ap.add_argument("--genre")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out")
    ap.add_argument("--show", action="store_true", help="print flagged sentences to stderr (local triage only)")
    args = ap.parse_args(argv)
    report = run(Path(args.corpus), args.genre, Path(args.root).resolve(), args.show)
    text = json.dumps(report, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("sentences", "by_status")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
