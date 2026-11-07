"""Re-apply survivors recorded in a published Cosmic Ray JSON (row + mutated
line) to a clean copy of the module and run a suite without bytecode.

    python -B replay_recorded_survivors.py record.json workdir module out.json test.module ...

The unmutated module must pass the suite first (otherwise a "kill" means
nothing); the script refuses to continue if it does not. A record row whose
source line no longer matches the module is reported as STALE, never replayed
on another line."""
import json
import subprocess
import sys
from pathlib import Path

record, work, module, out = sys.argv[1:5]
suite = sys.argv[5:]
target = Path(work) / module
pristine = target.read_bytes().decode("utf-8")
newline = "\r\n" if "\r\n" in pristine else "\n"
lines = pristine.split(newline)


def run_suite() -> int:
    for d in Path(work).rglob("__pycache__"):
        for f in d.iterdir():
            f.unlink()
    return subprocess.run([sys.executable, "-B", "-m", "unittest", *suite], cwd=work, capture_output=True,
                          stdin=subprocess.DEVNULL, env={**__import__("os").environ,
                                                         "PYTHONDONTWRITEBYTECODE": "1"}).returncode


if run_suite() != 0:
    raise SystemExit("the unmutated module fails the suite: replay would be meaningless")
data = json.loads(Path(record).read_text(encoding="utf-8"))
results = []
try:
    for m in sorted((m for m in data["mutants"] if m["outcome"] == "SURVIVED"), key=lambda m: (m["row"], m["operator"])):
        original = lines[m["row"] - 1]
        indent = original[: len(original) - len(original.lstrip())]
        mutated = indent + m["mutant"]
        entry = {k: m[k] for k in ("row", "col", "operator", "occurrence", "mutant")}
        if mutated == original or not m["mutant"]:
            entry["outcome"] = "STALE"
        else:
            changed = list(lines)
            changed[m["row"] - 1] = mutated
            target.write_bytes(newline.join(changed).encode("utf-8"))
            entry["outcome"] = "KILLED" if run_suite() else "SURVIVED"
        results.append(entry)
        print(m["row"], m["operator"].split("/")[1], entry["outcome"], flush=True)
finally:
    target.write_bytes(pristine.encode("utf-8"))
Path(out).write_text(json.dumps({"record": Path(record).name, "module": module, "suite": suite,
                                 "results": results}, indent=1) + "\n", encoding="utf-8", newline="\n")
