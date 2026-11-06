"""Keep only some mutants of a Cosmic Ray session (after `init`, before `exec`).

    python cr_select.py session.sqlite rows 76-76,429-583
    python cr_select.py session.sqlite sample 120 20261106

Prints the denominator before and after so the selection is never hidden."""
import random
import sqlite3
import sys

db, mode, arg = sys.argv[1], sys.argv[2], sys.argv[3]
c = sqlite3.connect(db)
specs = list(c.execute("select job_id, start_pos_row from mutation_specs"))
total = len(specs)
if mode == "rows":
    ranges = [tuple(int(x) for x in r.split("-")) for r in arg.split(",")]
    keep = {j for j, row in specs if any(a <= row <= b for a, b in ranges)}
elif mode == "sample":
    rng = random.Random(int(sys.argv[4]))
    ids = sorted(j for j, _ in specs)
    keep = set(rng.sample(ids, min(int(arg), len(ids))))
else:
    raise SystemExit("mode: rows | sample")
drop = [(j,) for j, _ in specs if j not in keep]
c.executemany("delete from mutation_specs where job_id = ?", drop)
c.executemany("delete from work_items where job_id = ?", drop)
c.commit()
print(f"{db}: {total} mutants generated, {len(keep)} kept ({mode} {arg}), {len(drop)} not run")
