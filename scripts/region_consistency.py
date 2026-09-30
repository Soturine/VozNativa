#!/usr/bin/env python3
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Baseline markers exist only to exercise the guard. Production regional packs
# must be evidence-backed, versioned and contextual.
BASELINE_MARKERS = {
    "mg": {"uai", "sô"},
    "rs": {"bah", "guri", "tchê"},
    "pe": {"oxe", "oxente", "visse"},
    "rj": {"mermão"},
    "sp": {"mano"},
}

def inspect(text: str, requested_region: str | None = None) -> dict:
    tokens = re.findall(r"\b[\wÀ-ÿ]+\b", text.lower(), re.UNICODE)
    found = []
    regions = Counter()

    for token in tokens:
        for region, markers in BASELINE_MARKERS.items():
            if token in markers:
                found.append(token)
                regions[region] += 1

    counts = Counter(found)
    density = len(found) / max(1, len(tokens))
    repeated = max(counts.values(), default=0)
    active_regions = [region for region, count in regions.items() if count > 0]

    if density > 0.04 or repeated >= 4:
        overfit = "high"
    elif density > 0.02 or repeated >= 3:
        overfit = "medium"
    else:
        overfit = "low"

    mixing = "low"
    if len(active_regions) >= 3:
        mixing = "high"
    elif len(active_regions) == 2:
        mixing = "medium"

    mismatch = False
    if requested_region and active_regions:
        mismatch = any(region != requested_region for region in active_regions)

    return {
        "marker_count": len(found),
        "token_count": len(tokens),
        "density": round(density, 4),
        "markers": dict(counts),
        "regions_observed": dict(regions),
        "regional_overfit": overfit,
        "dialect_mixing": mixing,
        "requested_region_mismatch": mismatch,
        "note": "baseline heuristic; not a dialect classifier",
    }

if __name__ == "__main__":
    if len(sys.argv) not in {2, 3}:
        raise SystemExit("usage: region_consistency.py TEXT [REGION_CODE]")
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    region = sys.argv[2] if len(sys.argv) == 3 else None
    print(json.dumps(inspect(text, region), ensure_ascii=False, indent=2))
