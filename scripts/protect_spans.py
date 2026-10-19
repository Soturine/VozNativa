#!/usr/bin/env python3
"""Legacy alias of ``semantic_guard.py TEXT``: list protected spans."""
import json
import sys
from pathlib import Path

from semantic_guard import extract

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: protect_spans.py TEXT")
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    print(json.dumps(extract(text), ensure_ascii=False, indent=2))
