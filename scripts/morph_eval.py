#!/usr/bin/env python3
"""Measure voznativa.morph against UD gold features (v0.7.0 CP9L).

Reads the CoNLL-U test files of prepared treebanks from the local cache
(policy: PROCESS_LOCAL and EXPORT_STATISTICS), aligns each word to the
sentence text, runs ``morph.verbs`` on the sentence and reports aggregate
counts only:

* coverage: gold VERB/AUX words with a VerbForm that receive an analysis;
* unique: share of analysed verbs with a single tense label (the rest abstain);
* accuracy: unique labels whose UD features agree with the gold
  (VerbForm, Mood, and Tense when both sides give one);
* false verbs: gold non-verbs (NOUN, ADJ, PROPN, ADV, ADP, DET, PRON, NUM)
  that receive a verb analysis, per 1,000 such words.

    python scripts/morph_eval.py --date 2026-11-06
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

from voznativa.corpus.connectors import cache_dir  # noqa: E402
from voznativa.corpus.evaluate import _rate  # noqa: E402
from voznativa.corpus.policy import require  # noqa: E402
from voznativa.corpus.registry import get_source  # noqa: E402
from voznativa.morph import TENSES, verbs  # noqa: E402

SOURCES = {"ud-portuguese-bosque": "pt_bosque-ud-test.conllu", "ud-portuguese-gsd": "pt_gsd-ud-test.conllu",
           "ud-portuguese-petrogold": "pt_petrogold-ud-test.conllu",
           "ud-portuguese-dantestocks": "pt_dantestocks-ud-test.conllu"}
NON_VERB = {"NOUN", "ADJ", "PROPN", "ADV", "ADP", "DET", "PRON", "NUM"}


def sentences(path: Path):
    text, words = None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# text ="):
            text = line.split("=", 1)[1].strip()
        elif not line.strip():
            if text is not None:
                yield text, words
            text, words = None, []
        elif not line.startswith("#"):
            cols = line.split("\t")
            if len(cols) == 10 and cols[0].isdigit():
                feats = dict(x.split("=", 1) for x in cols[5].split("|") if "=" in x)
                words.append((cols[1], cols[3], feats))
    if text is not None:
        yield text, words


def agrees(label: str, gold: dict) -> bool:
    mine = TENSES[label][1]
    if mine.get("VerbForm") != gold.get("VerbForm"):
        return False
    if "Mood" in mine and mine["Mood"] != gold.get("Mood"):
        return False
    return not ("Tense" in mine and gold.get("Tense") and mine["Tense"] != gold["Tense"])


def evaluate(path: Path) -> dict:
    c = Counter()
    confusion = Counter()
    for text, words in sentences(path):
        analysed = {(v.start, v.end): v for v in verbs(text)}
        position = 0
        for form, upos, feats in words:
            at = text.find(form, position)
            if at < 0:
                c["unaligned"] += 1
                continue
            position = at + len(form)
            v = analysed.get((at, at + len(form)))
            if upos in ("VERB", "AUX") and feats.get("VerbForm"):
                c["gold_verbs"] += 1
                if v is None:
                    continue
                c["covered"] += 1
                if v.unique:
                    c["unique"] += 1
                    label = next(iter(v.tenses))
                    ok = agrees(label, feats)
                    c["correct"] += ok
                    if not ok:
                        confusion[(label, feats.get("VerbForm"), feats.get("Mood"), feats.get("Tense"))] += 1
            elif upos in NON_VERB:
                c["gold_non_verbs"] += 1
                c["false_verbs"] += v is not None
                c["false_unique_verbs"] += v is not None and v.unique
    return {"gold_verbs_with_features": c["gold_verbs"], "coverage": _rate(c["covered"], c["gold_verbs"]),
            "unique_among_covered": _rate(c["unique"], c["covered"]),
            "accuracy_of_unique": _rate(c["correct"], c["unique"]),
            "false_verbs_per_1000_non_verbs": round(1000 * c["false_verbs"] / max(1, c["gold_non_verbs"]), 2),
            "false_unique_verbs_per_1000_non_verbs": round(1000 * c["false_unique_verbs"] / max(1, c["gold_non_verbs"]), 2),
            "unaligned_words": c["unaligned"],
            "top_errors": [{"label": k[0], "gold": "|".join(str(x) for x in k[1:]), "n": n}
                           for k, n in confusion.most_common(8)]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = {"kind": "voznativa.morph_eval_run", "schema_version": 1, "date": args.date,
              "analyzer": "voznativa.morph-rules@1", "split": "UD test files (rules are hand-written, not trained)",
              "sources": {}}
    for sid, name in SOURCES.items():
        entry = get_source(sid)
        require(entry, "PROCESS_LOCAL")
        require(entry, "EXPORT_STATISTICS")
        report["sources"][sid] = evaluate(cache_dir(sid) / name)
        r = report["sources"][sid]
        print(f"{sid:28s} verbs {r['gold_verbs_with_features']:5d} coverage {r['coverage']['rate']} unique "
              f"{r['unique_among_covered']['rate']} acc {r['accuracy_of_unique']['rate']} "
              f"false/1k {r['false_verbs_per_1000_non_verbs']} (unique {r['false_unique_verbs_per_1000_non_verbs']})")
    out = ROOT / "evals" / "linguistics" / "runs" / f"morph-{args.date}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
