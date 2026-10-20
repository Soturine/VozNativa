#!/usr/bin/env python3
"""Experiment (v0.3.0 M1.6): do spaCy dependency parses catch role changes
that the heuristic layer misses, without adding false reds?

Not part of the package. Needs `pip install spacy` and
`python -m spacy download pt_core_news_sm` (CC BY-SA 4.0, UD Bosque).

For every case of the semantic suites it extracts role facts from both
texts (subject/object/agent of each verb, and noun-modifier links such as
"proposta do fornecedor"), and flags a case when a role fact of the
original appears in the candidate with the two arguments swapped. The
result is compared with what the deterministic layer already reports.

    python scripts/experiments/syntax_roles.py --out evals/experiments/syntax_roles.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import spacy  # noqa: E402

from voznativa.compare import compare  # noqa: E402

NLP = spacy.load("pt_core_news_sm")
SUITES = ["cases.jsonl", "relations.jsonl", "holdout.jsonl", "holdout2.jsonl", "holdout-relations.jsonl",
          "holdout-v030.jsonl"]


def facts(text: str) -> set[tuple[str, str, str, str]]:
    """(relation, head lemma, role-A lemma, role-B lemma) facts."""
    out = set()
    for tok in NLP(text):
        if tok.pos_ in {"VERB", "AUX"}:
            subj = [c for c in tok.children if c.dep_ == "nsubj"]
            obj = [c for c in tok.children if c.dep_ == "obj"]
            psubj = [c for c in tok.children if c.dep_ == "nsubj:pass"]
            agent = [c for c in tok.children if c.dep_ == "obl:agent"]
            for s in subj:
                for o in obj:
                    out.add(("act", tok.lemma_.lower(), s.lemma_.lower(), o.lemma_.lower()))
            for p in psubj:  # passive normalized to active order: agent, patient
                for a in agent:
                    out.add(("act", tok.lemma_.lower(), a.lemma_.lower(), p.lemma_.lower()))
        if tok.dep_ == "nmod" and tok.head.pos_ in {"NOUN", "PROPN"}:
            out.add(("nmod", "", tok.head.lemma_.lower(), tok.lemma_.lower()))
    return out


def swapped(src: set, out: set) -> list:
    hits = []
    for rel, head, a, b in src:
        if a != b and (rel, head, b, a) in out and (rel, head, a, b) not in out:
            hits.append([rel, head, a, b])
        if rel == "nmod":  # "proposta do fornecedor" -> "proposta do cliente" with the owners exchanged
            for rel2, head2, a2, b2 in out:
                if rel2 == "nmod" and a2 == a and b2 != b and (("nmod", "", a, b2) in src) is False \
                        and any(f[0] == "act" and b in f[2:] for f in out) and any(f[0] == "act" and b2 in f[2:] for f in src):
                    hits.append([rel, a, b, b2])
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out")
    args = parser.parse_args()
    rows = []
    for name in SUITES:
        for line in (ROOT / "evals" / "semantic" / name).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            case = json.loads(line)
            hits = swapped(facts(case["original"]), facts(case["candidate"]))
            status = compare(case["original"], case["candidate"])["status"]
            rows.append({"suite": name, "id": case["id"], "category": case["category"], "deterministic": status,
                         "syntax_flag": bool(hits), "hits": hits})
    false_reds = [r for r in rows if r["syntax_flag"] and r["category"] in {"false_red", "no_change"}]
    new_detections = [r for r in rows if r["syntax_flag"] and r["deterministic"] in {"no_deterministic_issues", "identical"}
                      and r["category"] not in {"false_red", "no_change"}]
    summary = {
        "model": f"pt_core_news_sm {NLP.meta['version']} ({NLP.meta.get('license')})",
        "cases": len(rows),
        "flagged": sum(r["syntax_flag"] for r in rows),
        "false_reds_on_valid_rewrites": [(r["suite"], r["id"], r["hits"]) for r in false_reds],
        "new_detections_over_deterministic": [(r["suite"], r["id"], r["hits"]) for r in new_detections],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
