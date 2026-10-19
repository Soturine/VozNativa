#!/usr/bin/env python3
"""Legacy entry point; the implementation lives in ``voznativa.profile`` (schema v2)."""
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from voznativa.profile import build


def profile(texts: list[str]) -> dict:
    """v0.1.0 signature: a list of sample texts without channel metadata."""
    return build([{"text": t} for t in texts])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: voice_profile.py SAMPLE [SAMPLE ...]")
    samples = [Path(path).read_text(encoding="utf-8") for path in sys.argv[1:]]
    print(json.dumps(profile(samples), ensure_ascii=False, indent=2))
