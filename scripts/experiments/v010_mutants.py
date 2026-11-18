#!/usr/bin/env python3
"""Targeted mutation of the v0.10 safeguards (CP12, release criterion R10).

Each mutant changes one condition a v0.10 safeguard depends on; the test module that should
notice runs against the mutated copy. Run inside a throwaway checkout (files are edited in place
and restored with git):

    git worktree add --detach /tmp/wt HEAD && cd /tmp/wt && python scripts/experiments/v010_mutants.py --out m.json

A control run (no mutation) must pass first. killed = the test failed; survived = the test passed
(a gap in the tests or an equivalent mutant, classified by hand in the record).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
MUTANTS = [
    # judge relation (CP6, D-02)
    ("judge: unknown accepts again", "voznativa/compare.py",
     'ACCEPTING_RELATIONS = {"different_model", "different_provider", "independence_verified", "same_vendor"}',
     'ACCEPTING_RELATIONS = {"different_model", "different_provider", "independence_verified", "same_vendor", '
     '"unknown"}', "test_v08_judge_relation"),
    ("judge: same model accepts", "voznativa/compare.py",
     'ACCEPTING_RELATIONS = {"different_model", "different_provider", "independence_verified", "same_vendor"}',
     'ACCEPTING_RELATIONS = {"different_model", "different_provider", "independence_verified", "same_vendor", '
     '"same_model"}', "test_v08_judge_relation"),
    ("engine: same model reported as different", "voznativa/engine.py",
     '            return "same_model"', '            return "different_model"', "test_v09_providers"),
    ("engine: vendor ignored", "voznativa/engine.py",
     '            return "same_vendor" if va == vb else "different_provider"', '            return "different_provider"',
     "test_v09_providers"),
    ("judge: verified independence without evidence", "voznativa/judge.py",
     '    if relation == "independence_verified" and not', '    if False and not', "test_v010_judge_independence"),
    # discourse (CP5)
    ("discourse: opposed families not reported", "voznativa/discourse.py",
     "        for other in sorted(gained & OPPOSED.get(family, set())):", "        for other in []:",
     "test_v010_discourse"),
    ("discourse: invented causal not reported", "voznativa/discourse.py",
     '    if "causal" in gained and "causal" not in reported:', "    if False:", "test_v010_discourse"),
    ("discourse: 'Como' causal not read", "voznativa/discourse.py",
     "    for m in _COMO_CAUSAL.finditer(text):", "    for m in []:", "test_v010_discourse"),
    ("compare: causal swap not demoted", "voznativa/compare.py",
     '                out[i] = dict(item, severity="info", demoted=', '                out[i] = dict(item, demoted=',
     "test_v010_discourse"),
    ("compare: coordinated action never dropped", "voznativa/compare.py",
     "                if len(missing) == 1:", "                if False:", "test_v010_discourse"),
    ("compare: scheduled present always skipped", "voznativa/compare.py",
     '            if len(pair) == 2 and pair <= _FUTURES | {"pres_ind"} and "pres_ind" in pair and (',
     '            if len(pair) == 2 and pair <= _FUTURES | {"pres_ind"} and "pres_ind" in pair or (',
     "test_v010_discourse"),
    ("compare: code marking of any content is info", "voznativa/compare.py",
     "inner and contains_word(src.text, inner) and", "inner and", "test_v010_discourse"),
    # diagnostics (CP4, CP7, CP11)
    ("diagnose: variant becomes context dependent", "voznativa/diagnose.py",
     '        return "ACCEPTABLE_VARIANT" if informal and d["type"] in VARIANT_IN_INFORMAL else "CONTEXT_DEPENDENT"',
     '        return "CONTEXT_DEPENDENT"', "test_v010_diagnose_status"),
    ("diagnose: recommend_edit always true", "voznativa/diagnose.py",
     '        d["recommend_edit"] = d["status"] == "ERROR_CONFIRMED"', '        d["recommend_edit"] = True',
     "test_v010_diagnose_status"),
    ("diagnose: pronoun determiner before verb flagged", "voznativa/diagnose.py",
     '                continue        # the determiner is a pronoun subject: "outros tenham", "esses foram"',
     "                pass", "test_v010_plural_real_text"),
    ("diagnose: English checked as Portuguese", "voznativa/diagnose.py",
     '    if language["value"] != "en":', "    if True:", "test_v010_language_guard"),
    ("planner: English planned for edits", "voznativa/planner.py",
     '    if language["value"] == "en" and decision == "edit":', "    if False:", "test_v010_language_guard"),
    # task context (CP2) and knowledge (CP3)
    ("task_context: reserved fields accepted", "voznativa/task_context.py",
     "        if key in RESERVED:", "        if False:", "test_v010_task_context"),
    ("task_context: proposal overrides the user", "voznativa/task_context.py",
     "    for layer in (proposed, explicit):", "    for layer in (explicit, proposed):", "test_v010_task_context"),
    ("task_context: provenance rank inverted", "voznativa/task_context.py",
     '            if not prior or _RANK[attr["source"]] <= _RANK[prior["source"]]:',
     '            if not prior or _RANK[attr["source"]] >= _RANK[prior["source"]]:', "test_v010_task_context"),
    ("knowledge: instruction-like entry accepted", "voznativa/knowledge.py",
     "        elif _instruction_like(statement):", "        elif False:", "test_v010_knowledge"),
    ("knowledge: rubric entry without applied standard", "voznativa/knowledge.py",
     '            if entry.get("requires_rubric") and not _rubric_applied(context, entry["requires_rubric"]):',
     "            if False:", "test_v010_knowledge"),
    # watcher (CP8)
    ("watcher: private address allowed", "voznativa/corpus/connectors.py",
     "        if block_private and resolves_to_private(parts.hostname or \"\", resolver):", "        if False:",
     "test_v010_watcher"),
    ("watcher: licence change not escalated", "voznativa/watcher.py",
     '    licence_changed = diff.get("field") in ("licence", "license")', "    licence_changed = False",
     "test_v010_watcher"),
    ("watcher: report mode writes", "voznativa/watcher.py",
     '    propose = mode == "propose"', "    propose = True", "test_v010_watcher"),
]


def run_test(module: str) -> bool:
    done = subprocess.run([sys.executable, "-m", "unittest", f"evals.{module}"], cwd=ROOT, capture_output=True)
    return done.returncode == 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    modules = sorted({m[4] for m in MUTANTS})
    control = {m: run_test(m) for m in modules}
    if not all(control.values()):
        print("control failed:", [m for m, ok in control.items() if not ok])
        return 2
    results = []
    for name, path, old, new, module in MUTANTS:
        file = ROOT / path
        source = file.read_text(encoding="utf-8")
        if source.count(old) != 1:
            results.append({"mutant": name, "result": "error", "reason": f"pattern found {source.count(old)} times"})
            continue
        file.write_text(source.replace(old, new), encoding="utf-8", newline="\n")
        try:
            killed = not run_test(module)
        finally:
            subprocess.run(["git", "checkout", "--", path], cwd=ROOT, check=True)
        results.append({"mutant": name, "file": path, "test": module, "result": "killed" if killed else "survived"})
        print(results[-1]["result"], name, flush=True)
    summary = {k: sum(r["result"] == k for r in results) for k in ("killed", "survived", "error")}
    report = {"kind": "voznativa.v010_mutants", "control": "pass", "summary": summary, "results": results}
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
