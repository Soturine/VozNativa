"""Prospective predicate-preservation sample (v0.7.0.dev1, H07-006..010).

Runs ``compare`` on ``evals/predicates/cases-h07.jsonl`` (frozen before the
predicate rule existed; sha256 in ``evals/predicates/MANIFEST.json``) and
reports, separately:

* sensitivity: ``risk`` cases whose status is not ``no_deterministic_issues``;
* false alarm: ``clean`` cases whose status is ``review_required`` or ``fail``.

The sample was written by the same agent that wrote the rule. It is a
development set measured before and after the change, not an independent
holdout, and its numbers say nothing about real rewrites.

    python scripts/predicate_eval.py [--out run.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402

CASES = ROOT / "evals" / "predicates" / "cases-h07.jsonl"
MANIFEST = ROOT / "evals" / "predicates" / "MANIFEST.json"


def run() -> dict:
    raw = CASES.read_bytes()
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))["sha256"]
    digest = hashlib.sha256(raw).hexdigest()
    if digest != frozen:
        raise SystemExit(f"cases changed after the freeze: {digest} != {frozen}")
    rows = []
    for line in raw.decode("utf-8").splitlines():
        case = json.loads(line)
        report = compare(case["original"], case["candidate"])
        flagged = report["status"] in ("review_required", "fail")
        rows.append({"id": case["id"], "expect": case["expect"], "kind": case["kind"], "status": report["status"],
                     "codes": sorted({f"{i['code']}:{i['severity']}" for i in report["issues"]}),
                     "correct": flagged if case["expect"] == "risk" else not flagged})
    risk = [r for r in rows if r["expect"] == "risk"]
    clean = [r for r in rows if r["expect"] == "clean"]
    return {"kind": "voznativa.predicate_eval", "cases_sha256": digest, "n_risk": len(risk), "n_clean": len(clean),
            "risk_flagged": sum(r["correct"] for r in risk),
            "clean_false_alarms": sum(not r["correct"] for r in clean),
            "independent": False, "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    result = run()
    for r in result["rows"]:
        print(f"{'ok ' if r['correct'] else 'MISS' if r['expect'] == 'risk' else 'FA  '} {r['id']:6} {r['status']:24} "
              + ", ".join(r["codes"]))
    print(f"risk flagged {result['risk_flagged']}/{result['n_risk']}; "
          f"clean false alarms {result['clean_false_alarms']}/{result['n_clean']}")
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
