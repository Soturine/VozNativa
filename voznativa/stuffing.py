"""Stuffing guard shared by region, slang and community layers (v0.6.0).

One owner for the question "did the candidate pile up marked forms?": a
regional marker, a slang form or a community term repeated or packed densely
reads as caricature, whatever layer it came from. The thresholds are the
ones the regional baseline guard has used since v0.4 (E0, not calibrated;
the CP6 calibration shows how rarely natural text gets near them).
"""
from __future__ import annotations

from collections import Counter

HIGH_DENSITY, MEDIUM_DENSITY = 0.04, 0.02      # marked forms per token
HIGH_REPEAT, MEDIUM_REPEAT = 4, 3              # the same form this many times


def level(density: float, repeated: int) -> str:
    if density > HIGH_DENSITY or repeated >= HIGH_REPEAT:
        return "high"
    if density > MEDIUM_DENSITY or repeated >= MEDIUM_REPEAT:
        return "medium"
    return "low"


def measure(forms: list[str], token_count: int) -> dict:
    counts = Counter(f.lower() for f in forms)
    density = len(forms) / max(1, token_count)
    repeated = max(counts.values(), default=0)
    return {"count": len(forms), "density": round(density, 4), "max_repeat": repeated, "forms": dict(counts),
            "level": level(density, repeated)}


def compare(layer: str, original_forms: list[str], candidate_forms: list[str], original_tokens: int,
            candidate_tokens: int) -> dict:
    """Stuffing is a rise: a candidate at 'medium' or 'high' from a source at 'low'.
    A source that was already dense is the author's choice, not stuffing."""
    before, after = measure(original_forms, original_tokens), measure(candidate_forms, candidate_tokens)
    order = ("low", "medium", "high")
    stuffed = after["level"] != "low" and order.index(after["level"]) > order.index(before["level"])
    return {"layer": layer, "original": before, "candidate": after, "stuffed": stuffed}
