#!/usr/bin/env python3
"""Legacy entry point; the implementation lives in ``voznativa.region``."""
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from voznativa.region import inspect  # noqa: F401

if __name__ == "__main__":
    if len(sys.argv) not in {2, 3}:
        raise SystemExit("usage: region_consistency.py TEXT [REGION_CODE]")
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    region = sys.argv[2] if len(sys.argv) == 3 else None
    print(json.dumps(inspect(text, region), ensure_ascii=False, indent=2))
