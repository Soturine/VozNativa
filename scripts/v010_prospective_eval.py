#!/usr/bin/env python3
"""Prospective sets of v0.10 (frozen before the rules; hashes in evals/v010/MANIFEST.json).

* ``semantic``: pairs (original, candidate). ``risk`` is flagged when
  ``compare`` says ``review_required`` or ``fail``; a ``clean`` pair with one
  of those is a false alarm.
* ``diagnose``: single texts with a declared genre/register. ``error`` expects a
  diagnostic whose status is ``ERROR_CONFIRMED``; ``variant`` and ``no_error``
  expect none (and no ``auto_fix``). Code without the v0.10 status field is
  read through the class it reports (``formal_error`` -> ``ERROR_CONFIRMED``),
  so the baseline is measured with the same rule.
* ``context``: texts with explicit, open attributes. Checks the TaskContext
  (v0.10) when the module exists; on older code each case is ``not_applicable``.

The sets were written by the same agent that writes the rules. Development may
be read while writing rules; the holdout split is run once after the rules are
fixed and reported as it comes out. Neither is independent.

    python scripts/v010_prospective_eval.py --split development [--root OTHER_CHECKOUT] [--out run.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "evals" / "v010" / "MANIFEST.json"
LEGACY_STATUS = {"formal_error": "ERROR_CONFIRMED", "possible_contextual_error": "CONTEXT_DEPENDENT",
                 "literary_license": "LITERARY_CHOICE"}


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
        kind = rel.split("/")[2]
        out[kind] = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    return out


def status_of(diagnostic: dict) -> str:
    return diagnostic.get("status") or LEGACY_STATUS.get(diagnostic.get("class"), "OTHER")


def _context_case(case: dict, mod, route) -> dict:
    ctx = route(case["text"], **({"genre": case["explicit"]["genre"]}
                                if isinstance(case["explicit"].get("genre"), str) and case["explicit"]["genre"]
                                in ("whatsapp", "academic", "literary", "technical", "corporate", "news", "social",
                                    "documentation", "email", "enem") else {}))
    task = mod.build(case["text"], ctx, attributes=case["explicit"])
    exp, problems = case["expect"], []
    attrs = {k: v["value"] for k, v in task["attributes"].items()}
    for key, value in (exp.get("attribute") or {}).items():
        if attrs.get(key) != value:
            problems.append(f"attribute {key}={attrs.get(key)!r}, expected {value!r}")
    if "not_genre" in exp and task["genre"]["value"] in exp["not_genre"]:
        problems.append(f"genre {task['genre']['value']} is one of {exp['not_genre']}")
    if exp.get("rubric_applied") is False and task.get("rubric", {}).get("applied"):
        problems.append("a rubric was applied without being requested")
    if exp.get("preserve_line_breaks") and not task["protections"]["preserve_line_breaks"]:
        problems.append("line breaks not protected")
    if exp.get("mixed") and not task["uncertainty"]["mixed"]:
        problems.append("mixed context not reported")
    if "rubric_candidate" in exp and exp["rubric_candidate"] not in task.get("rubric", {}).get("candidates", []):
        problems.append(f"rubric {exp['rubric_candidate']} not offered as a candidate")
    return {"set": "context", "id": case["id"], "correct": not problems, "problems": problems}


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
        kwargs = {k: case[k] for k in ("genre", "register") if case.get(k)}
        try:
            ctx = route(case["text"], **kwargs)
        except ValueError:
            ctx = route(case["text"], **({"register": case["register"]} if case.get("register") else {}))
        diags = diagnose(case["text"], ctx)["diagnostics"]
        statuses = sorted({status_of(x) for x in diags})
        confirmed = "ERROR_CONFIRMED" in statuses
        auto = any(x.get("action") == "auto_fix" for x in diags)
        correct = confirmed if case["expect"] == "error" else not (confirmed or auto)
        rows.append({"set": "diagnose", "id": case["id"], "expect": case["expect"], "kind": case["kind"],
                     "statuses": statuses, "types": sorted({x.get("type", "") for x in diags}),
                     "correct": correct})
    try:
        from voznativa import task_context as mod
    except ImportError:
        mod = None
    for case in sets.get("context", []):
        if mod is None:
            rows.append({"set": "context", "id": case["id"], "correct": None, "problems": ["not_applicable"]})
        else:
            rows.append(_context_case(case, mod, route))

    def tally(name: str, positive: str) -> dict:
        part = [r for r in rows if r["set"] == name]
        pos = [r for r in part if r["expect"] == positive]
        neg = [r for r in part if r["expect"] != positive]
        return {"sensitivity": f"{sum(r['correct'] for r in pos)}/{len(pos)}",
                "false_alarms": f"{sum(not r['correct'] for r in neg)}/{len(neg)}"}

    ctx_rows = [r for r in rows if r["set"] == "context"]
    summary = {"semantic": tally("semantic", "risk"), "diagnose": tally("diagnose", "error"),
               "context": ("not_applicable" if any(r["correct"] is None for r in ctx_rows) else
                           f"{sum(r['correct'] for r in ctx_rows)}/{len(ctx_rows)}")}
    return {"kind": "voznativa.v010_prospective_run", "split": split, "engine_version": __version__,
            "engine_root": engine_root.name, "independent": False, "summary": summary, "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--split", choices=("development", "holdout"), required=True)
    ap.add_argument("--root", default=str(ROOT), help="checkout whose voznativa package is measured")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    result = run(args.split, Path(args.root).resolve())
    text = json.dumps(result, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result["summary"], ensure_ascii=False))
    for r in result["rows"]:
        if r["correct"] is False:
            print("MISS", r["set"], r["id"], r.get("kind", ""), r.get("status", r.get("statuses", r.get("problems"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
