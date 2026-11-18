#!/usr/bin/env python3
"""Targeted mutation of the v0.9 safeguards (CP7.7).

Each mutant changes one condition a v0.9 safeguard depends on; the test
module that should notice runs against the mutated copy. Run inside a
throwaway checkout (it edits files in place and restores them with git):

    git worktree add --detach /tmp/wt HEAD && cd /tmp/wt && python scripts/experiments/v09_cp7_mutants.py

A control run (no mutation) must pass first. Results: killed (the test
failed), survived (the test passed: a gap in the tests or an equivalent
mutant, classified by hand in the record), error (could not apply).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
MUTANTS = [
    ("compare: qualifier never dropped", "voznativa/compare.py",
     "            elif name not in sets_out_near:", "            elif False:", "test_v09_semantic_safeguards"),
    ("compare: event change needs no new class", "voznativa/compare.py",
     "        if missing and e_new:", "        if missing and e_new and False:", "test_v09_semantic_safeguards"),
    ("compare: status governors ignored", "voznativa/compare.py",
     "        if g_added:", "        if not g_added and False:", "test_v09_semantic_safeguards"),
    ("compare: same-class synonym is a loss again", "voznativa/compare.py",
     "            if {events.get(lemma) for lemma in lemmas} & near_classes:\n                continue",
     "            if False:\n                continue", "test_v09_semantic_safeguards"),
    ("compare: noun reading not skipped", "voznativa/compare.py",
     "        if token in table[\"noun_readings\"] and k", "        if False and k", "test_v09_semantic_safeguards"),
    ("engine: same declared model counts as different", "voznativa/engine.py",
     "return \"same_agent\" if a[\"model\"].lower() == b[\"model\"].lower() else \"different_model\"",
     "return \"different_model\"", "test_v09_providers"),
    ("engine: same agent CLI is unknown", "voznativa/engine.py",
     "        return \"same_agent\"\n    return \"unknown\"", "        return \"unknown\"\n    return \"unknown\"",
     "test_v09_providers"),
    ("diagnose: clitic attractors ignored", "voznativa/diagnose.py",
     "(previous in _CLITIC_ATTRACTORS or verb_next)", "(verb_next)", "test_v09_semantic_safeguards"),
    ("diagnose: informal gets a fix", "voznativa/diagnose.py",
     "        elif informal:\n            out.append(_d(\"possible_contextual_error\", kind,",
     "        elif False:\n            out.append(_d(\"possible_contextual_error\", kind,", "test_v09_semantic_safeguards"),
    ("diagnose: à mulher is a crase error", "voznativa/diagnose.py",
     "            if target in _CRASE_FEMININE_ER:\n                continue", "            pass",
     "test_v09_semantic_safeguards"),
    ("docx: mixed formatting is editable", "voznativa/docx.py",
     "    if len(formats) > 1:\n        reasons.append(\"mixed formatting\")", "    pass", "test_v09_docx"),
    ("docx: output may be the source", "voznativa/docx.py",
     "    if source == output:", "    if False:", "test_v09_docx"),
    ("docx: check ignores outside XML", "voznativa/docx.py",
     "gaps(xml_a, spans_a) != gaps(xml_b, spans_b)", "False", "test_v09_docx"),
    ("packs: forbidden keys allowed", "voznativa/packs.py",
     "        if str(key).lower() in FORBIDDEN_KEYS:", "        if False:", "test_v09_packs"),
    ("packs: external needs no licence", "voznativa/packs.py",
     "    target = errors if external else warnings", "    target = warnings", "test_v09_packs"),
    ("config: project may set cmd", "voznativa/config.py",
     "        if scope == \"project\" and not project_ok:", "        if False:", "test_v09_cli_config"),
    ("config: dry run starts the provider", "voznativa/cli.py",
     "    if args.dry_run:\n        return _rewrite_dry_run(args, context, resolved)", "    pass",
     "test_v09_cli_config"),
    ("editorial: no unit spread required", "voznativa/editorial.py",
     "            if spread < 2:", "            if False:", "test_v09_editorial"),
    ("editorial: memory never warns", "voznativa/editorial.py",
     "        return sorted(k for k, n in self.added.items() if n >= MEMORY_THRESHOLD)", "        return []",
     "test_v09_editorial"),
    ("privacy gate: net diff only", "scripts/privacy_gate.py",
     "git(\"log\", \"-p\", \"--no-color\", \"--format=\", f\"{base}..{head}\")", "git(\"diff\", f\"{base}..{head}\")",
     "test_v09_privacy_gate"),
]


def run_tests(module: str) -> bool:
    # v0.10 CP12: no bytecode cache. Two mutants of the same length applied to the same file within one
    # second share the source's mtime (seconds) and size, so a cached .pyc of the previous mutant passed as
    # valid and the wrong code ran (a mutant "survived" that the tests kill when run alone).
    import os
    import shutil
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    done = subprocess.run([sys.executable, "-m", "unittest", f"evals.{module}"], cwd=ROOT, capture_output=True,
                          env=env)
    return done.returncode == 0


def main() -> int:
    results = []
    modules = sorted({m[4] for m in MUTANTS})
    control = {m: run_tests(m) for m in modules}
    if not all(control.values()):
        print("control failed:", control)
        return 2
    for name, rel, old, new, module in MUTANTS:
        path = ROOT / rel
        source = path.read_text(encoding="utf-8")
        if source.count(old) != 1:
            results.append({"mutant": name, "file": rel, "result": "error", "detail": f"pattern found {source.count(old)}x"})
            continue
        path.write_text(source.replace(old, new), encoding="utf-8")
        try:
            passed = run_tests(module)
        finally:
            subprocess.run(["git", "checkout", "--", rel], cwd=ROOT)
        results.append({"mutant": name, "file": rel, "test": module, "result": "survived" if passed else "killed"})
        print(f"{results[-1]['result']:<8} {name}", flush=True)
    summary = {k: sum(r["result"] == k for r in results) for k in ("killed", "survived", "error")}
    print(json.dumps(summary))
    Path("v09_cp7_mutants.json").write_text(json.dumps({"summary": summary, "results": results}, indent=1),
                                           encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
