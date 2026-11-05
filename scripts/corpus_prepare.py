#!/usr/bin/env python3
"""Prepare registry sources for local processing (network, bounded).

For each named source: the data policy must allow DOWNLOAD; its assets are
fetched into the local cache (outside the repository), read in full through
the local-files connector, and the registry entry gets the asset sha256 and
verification.connector. A run report goes to evals/corpus/runs/.

    python scripts/corpus_prepare.py ud-portuguese-bosque b2w-reviews01 [--no-fetch]
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

from voznativa.corpus.prepare import prepare  # noqa: E402
from voznativa.corpus.registry import REGISTRY_DIR, _load, get_source, validate_source  # noqa: E402
from voznativa.corpus.connectors import CONNECTORS  # noqa: E402
from voznativa.corpus.runs import run_file  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", nargs="+")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    reports = []
    for source_id in args.sources:
        updated, report = prepare(get_source(source_id), today=args.date, fetch=not args.no_fetch)
        problems = validate_source(updated, frozenset(CONNECTORS), ROOT)
        if problems:
            raise SystemExit(f"{source_id}: {problems}")
        (REGISTRY_DIR / f"{source_id}.yml").write_text(
            yaml.safe_dump(updated, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8", newline="\n")
        reports.append(report)
        print(f"{source_id}: {report['records_read']} records, {report['read_errors']} read errors, "
              f"status {updated['status']}")
    _load.cache_clear()
    out = run_file(ROOT, "prepare", args.date, args.sources)
    out.write_text(json.dumps({"kind": "voznativa.corpus_prepare_run", "date": args.date, "reports": reports},
                              ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
