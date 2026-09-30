#!/usr/bin/env python3
import json, sys
from pathlib import Path
from semantic_guard import guard

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: fact_guard.py ORIGINAL CANDIDATE")
    original = Path(sys.argv[1]).read_text(encoding="utf-8")
    candidate = Path(sys.argv[2]).read_text(encoding="utf-8")
    print(json.dumps(guard(original, candidate), ensure_ascii=False, indent=2))
