#!/usr/bin/env python3
"""Legacy entry point; the implementation lives in ``voznativa.analyze``."""
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from voznativa.analyze import analyze  # noqa: F401

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: analyze.py TEXT")
    data = Path(sys.argv[1]).read_text(encoding="utf-8")
    print(json.dumps(analyze(data), ensure_ascii=False, indent=2))
