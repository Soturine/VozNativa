"""v0.8 CP1: hand-applied mutants of the GAP-01/GAP-09 fix.

Each mutant runs in a full copy of the tree (tracked and untracked files,
not ignored ones), after a control without mutation that must pass; a copy
missing files makes every mutant "die" on import (see
evals/assurance/runs/2026-11-07-v08-cp1/MUTANTS.md).

    python -B scripts/experiments/v08_cp1_mutants.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MUTANTS = [
    ("CONTROL (no mutation)", "voznativa/document.py", "SCHEMA_VERSION = 1", "SCHEMA_VERSION = 1"),
    ("doc: plan field wins again", "voznativa/document.py",
     "    verse_explicit = _caller_grant(verse_explicit)\n",
     "    verse_explicit = plan.get('verse_explicit', False) if isinstance(plan.get('verse_explicit', False), bool) else False\n"),
    ("doc: no declared/caller check", "voznativa/document.py",
     "    elif declared != verse_explicit:", "    elif False:"),
    ("doc: reassemble ignores caller", "voznativa/document.py",
     "    problems = validate_plan(plan, text, verse_explicit=verse_explicit)\n    if problems:\n        raise ValueError",
     "    problems = validate_plan(plan, text, verse_explicit=plan.get('verse_explicit', False))\n    if problems:\n        raise ValueError"),
    ("engine: no structure check on resume", "voznativa/engine.py",
     "    if structure_of(candidate) != structure_of(source):\n        return None\n", ""),
    ("engine: no gate on resume", "voznativa/engine.py",
     "    gate = _GATE_OUTCOME.get(report[\"status\"])", "    gate = 'needs_judgment'"),
    ("engine: accepted wins the max", "voznativa/engine.py",
     "key=lambda o: OUTCOME_RANK[o])", "key=lambda o: -OUTCOME_RANK[o])"),
    ("engine: record from prior", "voznativa/engine.py",
     "    base = dict(record, resumed=True,", "    base = dict(prior, resumed=True,"),
]
TESTS = ["evals.test_v08_integrity", "evals.test_hardening_cp5b", "evals.test_document_rewrite",
         "evals.test_document_plan_oracles"]

for name, path, old, new in MUTANTS:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        files = subprocess.run(['git', 'ls-files', '-co', '--exclude-standard'], cwd=REPO, capture_output=True,
                               text=True).stdout.splitlines()
        for f in files:
            (root / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / f, root / f)
        target = root / path
        src = target.read_text(encoding="utf-8")
        assert src.count(old) == 1, (name, src.count(old))
        target.write_text(src.replace(old, new), encoding="utf-8")
        r = subprocess.run([sys.executable, "-B", "-m", "unittest", *TESTS], cwd=root, capture_output=True, text=True)
        last = [l for l in r.stderr.splitlines() if l.startswith(("OK", "FAILED"))]
        print(f"{'KILLED' if r.returncode else 'SURVIVED':8} {name}: {last[-1] if last else r.stderr[-200:]}")
