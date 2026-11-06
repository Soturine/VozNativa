"""Re-apply surviving Cosmic Ray mutants (from their recorded diffs) to a clean
copy and run a suite without bytecode.

    python replay_survivors.py session.sqlite workdir module rows(a-b,c) out.json test.module ..."""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

db, work, module, rows, out = sys.argv[1:6]
suite = sys.argv[6:]
ranges = [tuple(int(x) for x in r.split("-")) for r in rows.split(",")]
target = Path(work) / module
pristine = target.read_text(encoding="utf-8")
c = sqlite3.connect(db)
results = []
for job, row, op, diff in c.execute("select s.job_id, s.start_pos_row, s.operator_name, r.diff from mutation_specs s "
                                    "join work_results r using(job_id) where r.test_outcome = 'SURVIVED' "
                                    "order by s.start_pos_row"):
    if not any(a <= row <= b for a, b in ranges):
        continue
    minus = [l[1:] for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
    plus = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    lines = pristine.split("\n")
    idx = row - 1
    assert lines[idx].rstrip("\r") == minus[0].rstrip("\r"), (row, lines[idx], minus[0])
    lines[idx] = plus[0]
    target.write_text("\n".join(lines), encoding="utf-8")
    for d in Path(work).rglob("__pycache__"):
        for f in d.iterdir():
            f.unlink()
    done = subprocess.run([sys.executable, "-B", "-m", "unittest", *suite], cwd=work, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    results.append({"job_id": job, "row": row, "operator": op, "mutant": plus[0].strip(),
                    "outcome": "KILLED" if done.returncode else "SURVIVED"})
    print(row, op.split("/")[1], results[-1]["outcome"])
target.write_text(pristine, encoding="utf-8")
Path(out).write_text(json.dumps({"suite": suite, "results": results}, indent=1) + "\n", encoding="utf-8", newline="\n")
