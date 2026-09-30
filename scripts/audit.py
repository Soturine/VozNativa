#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from analyze import analyze
from region_consistency import inspect as region_inspect
from voice_drift import inspect as drift_inspect

def audit(text: str) -> dict:
    base = analyze(text)
    connector_total = sum(base["connector_counts"].values())
    mechanicality = min(
        1.0,
        round(
            (connector_total + base["mente_count"] + base["gerund_count"])
            / max(10, base["sentences"] * 2),
            3,
        ),
    )
    return {
        "mechanicality": mechanicality,
        "formulaicity": None,
        "voice_drift": drift_inspect(text),
        "regional": region_inspect(text),
        "register_mismatch": None,
        "semantic_loss": None,
        "note": "baseline audit; null fields require contextual/generative evaluation",
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py TEXT")
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    print(json.dumps(audit(text), ensure_ascii=False, indent=2))
