#!/usr/bin/env python3
"""External detector benchmark runner (v0.7.0 CP11). Opt-in, never in CI.

    python scripts/detector_bench.py                       # no upload: every live call LIVE_NOT_RUN
    python scripts/detector_bench.py --allow-upload        # live only for items with upload_permission
                                                           # and a key in the environment

Writes evals/external_detection/runs/baseline_vs_after-<date>.json with the
per-item states (no text, no raw payload by default) and the summary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evals"))

from external_detection.adapters import CopyleaksAdapter, GPTZeroAdapter, OriginalityAdapter  # noqa: E402
from external_detection.protocol import run, summarize, validate_manifest  # noqa: E402

MANIFEST = ROOT / "evals" / "external_detection" / "manifest.json"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(MANIFEST))
    parser.add_argument("--allow-upload", action="store_true",
                        help="authorise uploads for this run (each item still needs upload_permission)")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    problems = validate_manifest(manifest)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    adapters = [CopyleaksAdapter(), GPTZeroAdapter(), OriginalityAdapter()]
    measurements = [m for a in adapters for m in run(a, manifest, args.allow_upload)]
    for m in measurements:
        m.pop("raw_score", None) if m.get("kind") == "live" and not args.allow_upload else None
    report = {"kind": "voznativa.external_detection_run", "schema_version": 1, "date": args.date,
              "manifest_sha256": hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest(),
              "items": len(manifest.get("items", [])), "allow_upload": args.allow_upload,
              "adapters": [{"name": a.caps.name, "contract": a.caps.contract, "source_url": a.caps.source_url,
                            "last_verified": a.caps.last_verified} for a in adapters],
              "status": "LIVE_NOT_RUN" if not args.allow_upload or not manifest.get("items") else "LIVE_ATTEMPTED",
              "measurements": [{k: v for k, v in m.items() if k != "text"} for m in measurements],
              "summary": summarize(measurements)}
    out = ROOT / "evals" / "external_detection" / "runs" / f"baseline_vs_after-{args.date}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(report["status"], out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
