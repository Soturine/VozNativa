#!/usr/bin/env python3
"""Verify registry sources against their official hosts and record the result.

For each source: fetch the official page (identity terms), then try a capped
data read where the host offers one (GitHub, Hugging Face). Writes the
verification records and the status they justify back into
voznativa/data/corpora/<id>.yml, and a run log with every result, failures
included, to evals/corpus/runs/verify-<date>.json. Network, bounded.

    python scripts/corpus_verify.py [--only id1,id2] [--date 2026-11-05]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.corpus.runs import run_file  # noqa: E402
from voznativa.corpus.registry import REGISTRY_DIR, _load, load_registry, validate_source  # noqa: E402
from voznativa.corpus.verify import apply, verify_access, verify_source  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    wanted = set(args.only.split(",")) if args.only else None
    log = {"kind": "voznativa.corpus_verification_run", "date": args.date, "results": []}
    for entry in load_registry():
        if wanted and entry["id"] not in wanted:
            continue
        source = verify_source(entry, args.date)
        access = verify_access(entry, args.date) if source["result"] == "verified" else None
        updated = apply(entry, source, access)
        problems = validate_source(updated)
        if problems:
            raise SystemExit(f"{entry['id']}: verification produced an invalid entry: {problems}")
        (REGISTRY_DIR / f"{entry['id']}.yml").write_text(
            yaml.safe_dump(updated, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8", newline="\n")
        log["results"].append({"id": entry["id"], "status_before": entry["status"], "status_after": updated["status"],
                               "source": source, "access": access})
        print(f"{entry['id']:24s} {entry['status']:>18s} -> {updated['status']:18s} source={source['result']}"
              f"{' access=' + access['result'] if access else ''}", flush=True)
    _load.cache_clear()
    # A partial run (--only) gets its own file (v0.6 CP10: --only replaced the full CP2 run file).
    out = run_file(ROOT, "verify", args.date, {r["id"] for r in log["results"]})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
