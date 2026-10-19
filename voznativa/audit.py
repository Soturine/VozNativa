"""Audit mode: descriptive diagnostics, never an authorship or "AI" score.

With ``original`` the audit also reports semantic risk through the ledger
comparison. Without it, semantic loss is unknowable and stays ``None``.
"""
from __future__ import annotations

from . import drift, region
from .analyze import analyze, per_100
from .compare import compare


def audit(text: str, original: str | None = None, profile: dict | None = None) -> dict:
    base = analyze(text)
    words = base["words"]
    connector_total = sum(base["connector_counts"].values())
    semantic = None
    if original is not None:
        report = compare(original, text)
        semantic = {"status": report["status"], "semantic_equivalence": report["semantic_equivalence"],
                    "summary": report["summary"], "issues": report["issues"]}
    return {
        "mechanicality": {
            "connector_openers_per_100w": per_100(connector_total, words),
            "metadiscourse_per_100w": per_100(base["metadiscourse_count"], words),
            "gerundism_count": base["gerundism_count"],
            "repeated_openers": base["repeated_openers"],
            "sentence_length_stdev": base["sentence_words_stdev"],
            "note": "descriptive counts, uncalibrated; ordinary gerunds are not counted; never an optimization target",
        },
        "formulaicity": None,
        "voice_drift": drift.inspect(text, profile=profile),
        "regional": region.inspect(text),
        "register_mismatch": None,
        "semantic_loss": semantic,
        "note": "null fields require context (register) or a judge (formulaicity); semantic_loss requires the original",
    }
