"""Deterministic stand-in for a model (NOT a model), for the quickstart only.

`voznativa rewrite --cmd` sends the prompt on stdin and reads the answer on
stdout. This stub reads the TEXTO block of the prompt and removes two
formulas ("É importante destacar que", "Vale ressaltar que"), so the whole
loop (plan, units, gates, global validation, provenance) can be seen without
credentials. Real use replaces it with an agent CLI, e.g. claude -p.
"""
import re
import sys

prompt = sys.stdin.buffer.read().decode("utf-8")
match = re.search(r"<<<TEXTO#(\w+)\n(.*)\nTEXTO#\1>>>", prompt, re.S)
text = match.group(2) if match else ""
for formula in ("É importante destacar que ", "Vale ressaltar que "):
    text = re.sub(re.escape(formula) + r"(\w)", lambda m: m.group(1).upper(), text)
sys.stdout.buffer.write(("<final>" + text + "</final>").encode("utf-8"))
