#!/usr/bin/env python3
"""Legacy entry point; the implementation lives in ``voznativa.audit``."""
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from voznativa.audit import audit  # noqa: F401

if __name__ == "__main__":
    if len(sys.argv) not in {2, 3}:
        raise SystemExit("usage: audit.py TEXT [ORIGINAL]")
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    original = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) == 3 else None
    print(json.dumps(audit(text, original), ensure_ascii=False, indent=2))
