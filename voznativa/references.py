"""Reference Selector: progressive disclosure under a word budget.

Reads ``references/index.yml`` and picks the references that match the
Context Contract, in priority order, until the budget is spent. Everything
not loaded is reported with the reason, so an agent can ask for more.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .paths import home

DEFAULT_BUDGET = 6000


def load_index(path: Path | None = None) -> list[dict]:
    path = path or home() / "references" / "index.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = data.get("entries", [])
    for entry in entries:
        for key in ("path", "purpose", "when", "priority"):
            if key not in entry:
                raise ValueError(f"{path}: entry missing '{key}': {entry}")
    return entries


def _matches(entry: dict, contract: dict) -> tuple[bool, str]:
    when = entry["when"]
    task = contract["task"]
    tasks = when.get("tasks", ["*"])
    if "*" not in tasks and task not in tasks:
        return False, f"task {task} not in {tasks}"
    genres = when.get("genres")
    genre = contract["genre"]["value"]
    if genres and genre not in genres:
        candidates = contract["genre"].get("candidates", [])
        if not any(c in genres for c in candidates):
            return False, f"genre {genre} not in {genres}"
    required = when.get("requires_any")
    if required and not any(contract["flags"].get(flag) for flag in required):
        return False, f"needs one of {required}"
    return True, "matches " + ", ".join(
        part for part in (f"task={task}", f"genre={genre}" if genres else "",
                          f"flags={required}" if required else "") if part)


def select(contract: dict, budget_words: int = DEFAULT_BUDGET, root: Path | None = None,
           index: Path | None = None) -> dict:
    root = root or home()
    selected, skipped, used = [], [], 0
    for entry in sorted(load_index(index), key=lambda e: e["priority"]):
        ok, reason = _matches(entry, contract)
        path = root / entry["path"]
        if not ok:
            skipped.append({"path": entry["path"], "reason": reason})
            continue
        if not path.exists():
            skipped.append({"path": entry["path"], "reason": "file missing"})
            continue
        words = len(path.read_text(encoding="utf-8").split())
        if used + words > budget_words:
            skipped.append({"path": entry["path"], "reason": f"over budget ({words} words)", "matched": True})
            continue
        used += words
        selected.append({"path": entry["path"], "purpose": entry["purpose"], "words": words, "reason": reason})
    return {
        "kind": "voznativa.reference_selection",
        "budget_words": budget_words,
        "used_words": used,
        "selected": selected,
        "skipped": skipped,
        "note": "load only 'selected'; matched-but-over-budget items can be requested explicitly",
    }
