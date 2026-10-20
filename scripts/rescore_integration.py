#!/usr/bin/env python3
"""Re-score the candidates recorded in real-model runs with the current gates.

Model outputs are fixed data and the gates are deterministic, so this
measures how a code change moves real decisions without calling a model.
Judgments are not re-run.

    python scripts/rescore_integration.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.engine import parse_candidate, validate_candidate  # noqa: E402
from voznativa.router import route  # noqa: E402


def rescore(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        run = json.loads(path.read_text(encoding="utf-8"))
        for row in run["results"]:
            writers = [c for c in row["calls"] if c["role"] == "writer"]
            for k, call in enumerate(writers, 1):
                candidate, no_change = parse_candidate(call["answers"][0], row["original"])
                if no_change:
                    continue
                recorded = row["attempts"][k - 1]["status"] if k - 1 < len(row["attempts"]) else None
                report = validate_candidate(row["original"], candidate, route(row["original"]), None)
                rows.append({"run": path.name, "id": row["id"], "attempt": k, "recorded": recorded,
                             "now": report["status"],
                             "codes": sorted({i["code"] for i in report["issues"] if i["severity"] != "info"})})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", dest="json_path")
    args = parser.parse_args()
    paths = sorted(p for p in (ROOT / "evals" / "integration").glob("*.json") if "prefix" not in p.name)
    rows = rescore(paths)
    for r in rows:
        mark = "" if r["recorded"] == r["now"] else "  <- changed"
        print(f"{r['id']:20s} #{r['attempt']} {str(r['recorded']):25s} -> {r['now']:25s} {r['codes']}{mark}")
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
