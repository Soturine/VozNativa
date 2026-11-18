#!/usr/bin/env python3
"""Prospective sets of v0.9 CP4 (frozen before the rules; hashes in evals/v09/MANIFEST.json).

* ``semantic``: pairs (original, candidate). ``risk`` is flagged when
  ``compare`` says ``review_required`` or ``fail``; a ``clean`` pair with one
  of those is a false alarm.
* ``diagnose``: single texts. ``error`` is flagged when ``diagnose`` reports a
  ``formal_error`` or ``possible_contextual_error``; a ``clean`` text with one
  is a false alarm.

The sets were written by the same agent that writes the rules. The
development split may be read while writing rules; the holdout split is run
after the rules are fixed and reported as it comes out. Neither is
independent, and no number here says anything about real rewrites.

    python scripts/v09_prospective_eval.py --split development [--root OTHER_CHECKOUT] [--out run.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "evals" / "v09" / "MANIFEST.json"


def load(split: str) -> dict[str, list[dict]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = {}
    for rel, meta in manifest["files"].items():
        if meta["split"] != split:
            continue
        raw = (ROOT / rel).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != meta["sha256"]:
            raise SystemExit(f"{rel} changed after the freeze: {digest} != {meta['sha256']}")
        kind = "semantic" if "/semantic/" in rel else "diagnose"
        out[kind] = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    return out


def run(split: str, engine_root: Path) -> dict:
    sys.path.insert(0, str(engine_root))
    from voznativa import __version__
    from voznativa.compare import compare
    from voznativa.diagnose import diagnose
    from voznativa.router import route

    sets = load(split)
    rows = []
    for case in sets.get("semantic", []):
        report = compare(case["original"], case["candidate"])
        flagged = report["status"] in ("review_required", "fail")
        rows.append({"set": "semantic", "id": case["id"], "expect": case["expect"], "kind": case["kind"],
                     "status": report["status"],
                     "codes": sorted({f"{i['code']}:{i['severity']}" for i in report["issues"]}),
                     "correct": flagged if case["expect"] == "risk" else not flagged})
    for case in sets.get("diagnose", []):
        found = [d for d in diagnose(case["text"], route(case["text"]))["diagnostics"]
                 if d["class"] in ("formal_error", "possible_contextual_error")]
        flagged = bool(found)
        rows.append({"set": "diagnose", "id": case["id"], "expect": case["expect"], "kind": case["kind"],
                     "codes": sorted({f"{d['class']}:{d['type']}" for d in found}),
                     "correct": flagged if case["expect"] == "error" else not flagged})

    def score(name, positive):
        pos = [r for r in rows if r["set"] == name and r["expect"] == positive]
        neg = [r for r in rows if r["set"] == name and r["expect"] == "clean"]
        return {"positives": len(pos), "flagged": sum(r["correct"] for r in pos),
                "clean": len(neg), "false_alarms": sum(not r["correct"] for r in neg)}

    return {"kind": "voznativa.v09_prospective_eval", "split": split, "engine_version": __version__,
            "engine_root": str(engine_root), "independent": False,
            "semantic": score("semantic", "risk"), "diagnose": score("diagnose", "error"), "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--split", choices=["development", "holdout"], required=True)
    ap.add_argument("--root", default=str(ROOT), help="checkout whose engine is measured (sets come from this one)")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    result = run(args.split, Path(args.root).resolve())
    for r in result["rows"]:
        mark = "ok " if r["correct"] else "MISS" if r["expect"] != "clean" else "FA  "
        print(f"{mark} {r['id']:<6} {r['kind']:<32} {r.get('status', ''):<24} {' '.join(r['codes'])[:110]}")
    print(f"semantic: {result['semantic']} | diagnose: {result['diagnose']}")
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
