"""Voice Drift: style change across windows of a long text, or against a profile.

Uses length-normalized features (see ``features``). Each feature difference is
scaled by a per-feature floor so raw magnitudes (e.g. sentence length in
words vs. commas per 100 words) do not dominate. Thresholds are uncalibrated
and reported as such; drift is a review signal, never an automatic rejection.
"""
from __future__ import annotations

import re

from . import features

# Minimum meaningful difference per feature, used as the scale denominator.
SCALE_FLOOR = {
    "sentence_words_mean": 4.0, "sentence_words_stdev": 3.0, "question_per_sentence": 0.15,
    "exclamation_per_sentence": 0.15, "lowercase_start_ratio": 0.25, "list_line_ratio": 0.25,
}
DEFAULT_FLOOR = 1.0  # per-100-word rates
FLAG_AT = 2.0


def _scale(name: str, stdev: float | None = None) -> float:
    floor = SCALE_FLOOR.get(name, DEFAULT_FLOOR)
    return max(floor, stdev or 0.0)


def compare_vectors(a: dict, b: dict, profile_stats: dict | None = None) -> dict:
    scores = {}
    for name in features.FEATURES:
        stdev = profile_stats.get(name, {}).get("stdev") if profile_stats else None
        scores[name] = round(abs(a[name] - b[name]) / _scale(name, stdev), 3)
    flagged = {k: v for k, v in scores.items() if v >= FLAG_AT}
    return {"max": max(scores.values(), default=0.0), "flagged": flagged}


def inspect(text: str, size: int | None = None, profile: dict | None = None) -> dict:
    """Without a profile: compare consecutive windows. With a profile: compare
    each window to the profile's per-feature means.

    ``size`` (legacy) groups that many paragraphs per window; by default
    windows hold ~120 words.
    """
    if size:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks = ["\n\n".join(paragraphs[i:i + size]) for i in range(0, len(paragraphs), size)]
    else:
        chunks = features.windows(text)
    vecs = [features.vector(c) for c in chunks]
    result = {"window_count": len(chunks), "method": "length-normalized features; threshold uncalibrated",
              "flag_threshold": FLAG_AT}
    if profile:
        stats = profile.get("style", {})
        means = {k: v["mean"] for k, v in stats.items()}
        if set(means) >= set(features.FEATURES):
            per_window = [compare_vectors(v, means, stats) for v in vecs]
            result.update(reference="voice_profile", windows=per_window,
                          max_distance=max((w["max"] for w in per_window), default=0.0))
            result["drift"] = any(w["flagged"] for w in per_window)
            return result
        result["profile_warning"] = "profile has no style statistics; fell back to window-to-window"
    pairs = [compare_vectors(vecs[i - 1], vecs[i]) for i in range(1, len(vecs))]
    result.update(reference="adjacent_windows", distances=[p["max"] for p in pairs],
                  flagged=[p["flagged"] for p in pairs],
                  max_distance=max((p["max"] for p in pairs), default=0.0))
    result["drift"] = any(p["flagged"] for p in pairs)
    result["note"] = "baseline stylistic distance; not calibrated voice identity"
    return result
