"""v0.8 CP6: hand-applied mutants of the event rules (events.py, compare._event_issues).

Same method as v08_cp1_mutants.py: a full copy of the tree per mutant, a
control without mutation first (it must pass), tests run with python -B.

    python -B scripts/experiments/v08_cp6_mutants.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MUTANTS = [
    ("CONTROL (no mutation)", "voznativa/events.py", "DATA = Path(", "DATA = Path("),
    ("bare article always a preposition", "voznativa/events.py",
     "            if idx == k + 1 or not following[:1].isupper():\n                continue\n", ""),
    ("time words not skipped", "voznativa/events.py",
     "        if head.isdigit() or head[:1].isdigit() or head in _TIME_WORDS:",
     "        if head.isdigit() or head[:1].isdigit():"),
    ("purpose 'para' + infinitive kept", "voznativa/events.py", "            return None          # \"para entregar\"",
     "            pass          # \"para entregar\""),
    ("auxiliary taken as agent", "voznativa/events.py",
     "    if word in IRREGULAR_INDEX:", "    if False:"),
    ("no inflection tolerance", "voznativa/compare.py",
     "    return len(shorter) >= 5 and longer.startswith(shorter[:-1]) and len(longer) - len(shorter) <= 2",
     "    return False"),
    ("converse ignores the subject", "voznativa/compare.py",
     "converse(f.stem, g.stem) and _same_word(g.agent, f.agent):", "converse(f.stem, g.stem):"),
    ("recipient check on any word", "voznativa/compare.py",
     "            if f.recipient and not any(_same_word(f.recipient, w) for w in near_words):",
     "            if f.recipient and f.recipient not in near_words and False:"),
    ("new issues critical", "voznativa/compare.py",
     "                issues.append(_issue(code, \"major\",", "                issues.append(_issue(code, \"critical\","),
    ("swap check removed", "voznativa/compare.py",
     "            if f.recipient and f.agent and any(g.agent and g.recipient and _same_word(g.agent, f.recipient)",
     "            if False and any(g.agent and g.recipient and _same_word(g.agent, f.recipient)"),
]
TESTS = ["evals.test_v08_events"]

for name, path, old, new in MUTANTS:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        files = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=REPO, capture_output=True,
                               text=True).stdout.splitlines()
        for f in files:
            (root / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / f, root / f)
        target = root / path
        src = target.read_text(encoding="utf-8")
        assert src.count(old) == 1, (name, src.count(old))
        target.write_text(src.replace(old, new), encoding="utf-8")
        r = subprocess.run([sys.executable, "-B", "-m", "unittest", *TESTS], cwd=root, capture_output=True, text=True)
        last = [line for line in r.stderr.splitlines() if line.startswith(("OK", "FAILED"))]
        print(f"{'KILLED' if r.returncode else 'SURVIVED':8} {name}: {last[-1] if last else r.stderr[-200:]}")
