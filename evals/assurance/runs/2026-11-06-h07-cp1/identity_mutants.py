"""Apply each of the 12 surviving ==/!= -> is/is not mutants of the v0.7 run
(rows/cols from mut-v07b/temporal.sqlite) to a clean archive and run the suite."""
import json
import subprocess
import sys
from pathlib import Path

WORK = Path(sys.argv[1])            # git archive of the revision under test
OUT = Path(sys.argv[2])
SUITE = sys.argv[3].split(",")
MUTANTS = [  # (row, col, from, to) exactly as Cosmic Ray recorded them (1-based row, 0-based col)
    (71, 37, "!=", "is not"), (91, 36, "==", "is"), (109, 46, "!=", "is not"), (149, 49, "!=", "is not"),
    (188, 47, "==", "is"), (226, 17, "==", "is"), (229, 67, "==", "is"), (235, 48, "!=", "is not"),
    (243, 44, "!=", "is not"), (249, 64, "==", "is"), (262, 12, "==", "is"), (303, 38, "!=", "is not"),
]
target = WORK / "voznativa" / "temporal.py"
pristine = target.read_text(encoding="utf-8")
lines = pristine.split("\n")
rows = []
for row, col, old, new in MUTANTS:
    line = lines[row - 1]
    at = line.find(old, col)
    assert at >= 0, (row, col, line)
    mutated = lines[:]
    mutated[row - 1] = line[:at] + new + line[at + len(old):]
    target.write_text("\n".join(mutated), encoding="utf-8")
    # Two mutants of the same size written within the mtime resolution reuse the previous
    # mutant's .pyc (seen in dev1 CP1: line 149 "killed" by line 109's bytecode). No bytecode.
    for pyc in WORK.rglob("__pycache__"):
        for f in pyc.iterdir():
            f.unlink()
    done = subprocess.run([sys.executable, "-B", "-W", "ignore", "-m", "unittest", *SUITE], cwd=WORK,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    failing = sorted({ln.split(" (")[1].rstrip(")") for ln in done.stderr.splitlines()
                      if ln.startswith(("FAIL:", "ERROR:")) and " (" in ln})
    rows.append({"row": row, "col": col, "mutation": f"{old} -> {new}", "line": mutated[row - 1].strip(),
                 "outcome": "KILLED" if done.returncode else "SURVIVED", "killed_by": failing,
                 "tail": done.stderr.strip().splitlines()[-1]})
    print(row, rows[-1]["outcome"], failing[:3])
target.write_text(pristine, encoding="utf-8")
OUT.write_text(json.dumps({"suite": SUITE, "python": sys.version, "mutants": rows}, indent=1) + "\n",
               encoding="utf-8", newline="\n")
