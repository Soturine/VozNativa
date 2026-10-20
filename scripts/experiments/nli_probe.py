#!/usr/bin/env python3
"""Experiment (v0.3.0 M1.7): does a PT-BR NLI model add useful signal?

Run it in an isolated container: the model weights are a pickle
(pytorch_model.bin) and the model card declares no license, so they are
evaluated locally, never redistributed or made a dependency.

For each case of the semantic suites and each recorded real-model rewrite,
it computes P(entailment) original -> candidate and candidate -> original
with ruanchaves/bert-base-portuguese-cased-assin2-entailment (BERTimbau
fine-tuned on ASSIN2, label 1 = entailment). A case is "NLI-flagged" when
either direction falls below the threshold. Equivalence is never inferred
from a high score.

    python nli_probe.py --repo /src --out /out/nli_probe.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MODEL = "ruanchaves/bert-base-portuguese-cased-assin2-entailment"
SUITES = ["cases.jsonl", "relations.jsonl", "holdout.jsonl", "holdout2.jsonl", "holdout-relations.jsonl",
          "holdout-v030.jsonl"]
VIOLATION_CATEGORIES = {"negation", "modality", "causality", "causal_direction", "addition", "factual", "antonym",
                        "agent_swap", "relation", "attribution", "omission"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    repo = Path(args.repo)
    sys.path.insert(0, str(repo))

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from voznativa.compare import compare
    from voznativa.engine import parse_candidate

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL).eval()

    def entail(premise: str, hypothesis: str) -> float:
        batch = tok(premise, hypothesis, return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            return float(torch.softmax(model(**batch).logits, dim=-1)[0, 1])

    rows = []
    for name in SUITES:
        for line in (repo / "evals" / "semantic" / name).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            if c["original"] == c["candidate"]:
                continue
            fwd, bwd = entail(c["original"], c["candidate"]), entail(c["candidate"], c["original"])
            rows.append({"source": name, "id": c["id"], "category": c["category"],
                         "deterministic": compare(c["original"], c["candidate"])["status"],
                         "p_forward": round(fwd, 3), "p_backward": round(bwd, 3)})
    for path in sorted((repo / "evals" / "integration").glob("*.json")):
        if "prefix" in path.name:
            continue
        for row in json.loads(path.read_text(encoding="utf-8"))["results"]:
            for call in [x for x in row["calls"] if x["role"] == "writer"]:
                cand, no_change = parse_candidate(call["answers"][0], row["original"])
                if no_change or cand == row["original"]:
                    continue
                rows.append({"source": "real:" + path.name, "id": row["id"], "category": "real_rewrite",
                             "deterministic": compare(row["original"], cand)["status"],
                             "p_forward": round(entail(row["original"], cand), 3),
                             "p_backward": round(entail(cand, row["original"]), 3)})

    flag = lambda r: min(r["p_forward"], r["p_backward"]) < args.threshold  # noqa: E731
    valid = [r for r in rows if r["category"] in {"false_red", "no_change"}]
    violations = [r for r in rows if r["category"] in VIOLATION_CATEGORIES]
    limits = [r for r in rows if r["category"] == "known_limitation"]
    real = [r for r in rows if r["category"] == "real_rewrite"]
    summary = {
        "model": MODEL, "threshold": args.threshold,
        "violations_flagged": f"{sum(map(flag, violations))}/{len(violations)}",
        "violations_flagged_that_deterministic_missed": [r["id"] for r in violations if flag(r)
                                                         and r["deterministic"] in {"no_deterministic_issues"}],
        "violations_missed_by_nli": [r["id"] for r in violations if not flag(r)],
        "known_limitations_flagged": [r["id"] for r in limits if flag(r)],
        "known_limitations_not_flagged": [r["id"] for r in limits if not flag(r)],
        "false_reds_on_valid_dev_rewrites": f"{sum(map(flag, valid))}/{len(valid)}",
        "false_reds_on_real_rewrites": f"{sum(map(flag, real))}/{len(real)}",
    }
    Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
