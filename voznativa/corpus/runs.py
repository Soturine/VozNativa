"""Where a corpus run report is written, without replacing another run's evidence.

Registry entries cite run files as evidence (processing_runs, evaluations).
A run over the same sources on the same date refreshes its own file; a run
over other sources gets a name with their ids, so it can never overwrite a
file another entry cites. Found in v0.6 CP10, when ``corpus_verify --only``
replaced the full CP2 verification record.
"""
from __future__ import annotations

import json
from pathlib import Path

RUNS = Path("evals") / "corpus" / "runs"


def sources_of(report: dict) -> set[str]:
    if isinstance(report.get("sources"), dict):
        return set(report["sources"])
    for key in ("reports", "results"):
        if isinstance(report.get(key), list):
            return {r.get("id") or r.get("source") for r in report[key]}
    return set()


def run_file(root: Path, kind: str, date: str, sources: set[str] | list[str]) -> Path:
    sources = set(sources)
    base = root / RUNS / f"{kind}-{date}.json"
    if not base.exists():
        return base
    try:
        same = sources_of(json.loads(base.read_text(encoding="utf-8"))) == sources
    except (OSError, ValueError):
        same = False
    return base if same else root / RUNS / f"{kind}-{date}-{'-'.join(sorted(sources))}.json"
