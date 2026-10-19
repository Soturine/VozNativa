#!/usr/bin/env python3
"""Legacy entry point; the implementation lives in ``voznativa.benchmark``."""
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from voznativa.benchmark import load_cases, run, score_case, summarize  # noqa: F401


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", type=Path)
    parser.add_argument("outputs", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()

    report = run(args.cases, args.outputs)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_path:
        args.json_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
