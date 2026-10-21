#!/usr/bin/env python3
"""Run one VozNativa engine rewrite from a given checkout (v0.4.0 M4).

ptbr-bench-v2 compares the v0.3.0 engine with the current one. The v0.3.0
`voznativa rewrite` command crashes before calling the engine (fixed in
568e35a), so both arms call rewrite() in-process from their own checkout,
with the same arguments, the way v0.3.0's recorded runs did. Prints the
result as JSON.

    python scripts/bench_engine_driver.py CHECKOUT TEXT_FILE GENRE HINTS_JSON CMD_JSON
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    checkout, text_file, genre, hints, cmd = sys.argv[1:6]
    sys.path.insert(0, str(Path(checkout).resolve()))
    for name in [m for m in sys.modules if m == "voznativa" or m.startswith("voznativa.")]:
        del sys.modules[name]
    from voznativa.engine import rewrite
    from voznativa.providers import CommandProvider
    from voznativa.router import route
    import voznativa
    text = Path(text_file).read_text(encoding="utf-8")
    context = route(text, genre=genre, **json.loads(hints))
    writer, judge = CommandProvider.from_string(cmd), CommandProvider.from_string(cmd)
    result = rewrite(text, context, writer, attempts=3, judge_provider=judge, judge_votes=2)
    result["engine_file"] = str(Path(voznativa.__file__).resolve())
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
