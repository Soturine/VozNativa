"""Regional overfit / dialect-mixing guard.

Baseline only: it counts a tiny E0 fixture list of markers to catch stuffing
("uai uai uai") and unsupported mixing. It is not a dialect classifier and
must never be used to infer where a writer is from.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from .analyze import data


def _norm(token: str) -> str:
    """Lower-case and NFC, keeping accents: accent folding turned the common
    word "só" into the marker "sô" (found in a real model run)."""
    return unicodedata.normalize("NFC", token.lower())


def _markers() -> dict[str, set[str]]:
    raw = data()["regional_baseline_markers"]
    return {region: {_norm(m) for m in items} for region, items in raw.items() if not region.startswith("_")}


def inspect(text: str, requested_region: str | None = None) -> dict:
    tokens = [_norm(t) for t in re.findall(r"\w+", text)]
    table = _markers()
    found, regions = [], Counter()
    for token in tokens:
        for region, markers in table.items():
            if token in markers:
                found.append(token)
                regions[region] += 1
    counts = Counter(found)
    density = len(found) / max(1, len(tokens))
    repeated = max(counts.values(), default=0)
    active = sorted(regions)

    if density > 0.04 or repeated >= 4:
        overfit = "high"
    elif density > 0.02 or repeated >= 3:
        overfit = "medium"
    else:
        overfit = "low"
    mixing = "high" if len(active) >= 3 else "medium" if len(active) == 2 else "low"
    requested = requested_region.lower() if requested_region else None
    return {
        "marker_count": len(found),
        "token_count": len(tokens),
        "density": round(density, 4),
        "markers": dict(counts),
        "regions_observed": dict(regions),
        "regional_overfit": overfit,
        "dialect_mixing": mixing,
        "requested_region_mismatch": bool(requested and active and any(r != requested for r in active)),
        "evidence_level": "E0",
        "note": "baseline heuristic; not a dialect classifier",
    }
