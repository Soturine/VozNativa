#!/usr/bin/env python3
"""Legacy alias kept for v0.1.0 callers.

Despite its name it does not fact-check: it prints the full ledger comparison
(``voznativa compare``), whose best deterministic outcome is
``semantic_equivalence: "unverified"``.
"""
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from voznativa.compare import compare

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: fact_guard.py ORIGINAL CANDIDATE")
    original = Path(sys.argv[1]).read_text(encoding="utf-8")
    candidate = Path(sys.argv[2]).read_text(encoding="utf-8")
    print(json.dumps(compare(original, candidate), ensure_ascii=False, indent=2))
