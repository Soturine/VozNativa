#!/usr/bin/env python3
"""ptbr-bench-v4 (v0.6.0 context suite): deterministic arm.

Checks each frozen case's `expect` against what VozNativa decides without a
model: route + Voice Contract + plan (temporal, community, literary,
regional), the editorial report, the engine review of a given candidate, and
long-text segmentation. The model arms are NOT_RUN (no approved budget); the
manifest records them.

    python scripts/bench_v4.py            # writes benchmarks/runs/ptbr-bench-v4-<UTC>.json
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa import __version__  # noqa: E402
from voznativa.community import apply_to_report  # noqa: E402
from voznativa.contract import resolve  # noqa: E402
from voznativa.corpus.evaluate import _rate  # noqa: E402
from voznativa.engine import validate_candidate  # noqa: E402
from voznativa.longform import boundary_report, segment  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.planner import plan  # noqa: E402
from voznativa.router import explicit_channel, route  # noqa: E402

CASES = ROOT / "benchmarks" / "cases" / "ptbr-bench-v4.jsonl"
MANIFEST = ROOT / "benchmarks" / "manifests" / "ptbr-bench-v4.json"
ARM = "D-voznativa-v060-deterministic"
HINTS = ("slang_strength", "epoch", "community", "region", "region_strength", "register", "audience")


def check_case(case: dict) -> dict:
    text = case["text"]
    hints = {k: v for k, v in (case.get("hints") or {}).items() if k in HINTS}
    ctx = route(text, genre=case.get("genre"), channel=case.get("channel"), **hints)
    contract = resolve(ctx, None, None, text)
    report = apply_to_report(detect(text, ctx["genre"]["value"], explicit_channel(ctx), ctx["register"]["value"]),
                             ctx, text)
    p = plan(text, ctx, report=report)
    findings = report["findings"]
    review = validate_candidate(text, case["candidate"], ctx, None) if case.get("candidate") else None
    checks = []

    def add(name, expected, observed, ok):
        checks.append({"check": name, "expected": expected, "observed": observed, "pass": bool(ok)})

    for key, want in case["expect"].items():
        if key == "temporal_keep":
            got = sorted(p["temporal"]["keep"])
            add(key, sorted(want), got, got == sorted(want))
        elif key == "plan_decision":
            add(key, want, p["decision"], p["decision"] == want)
        elif key == "plan_decision_not":
            add(key, f"not {want}", p["decision"], p["decision"] != want)
        elif key == "slang_effective":
            got = contract["slang_strength"]["effective"]
            add(key, want, got, got == want)
        elif key == "slang_allowed":
            got = contract["temporal"]["allowed"]
            add(key, want, got, got == want)
        elif key == "review_codes":
            # every severity an issue code has (one code can appear several times:
            # 'deploy' info and 'call' major; first run kept only the last one)
            got: dict[str, set] = {}
            for i in (review or {}).get("issues", []):
                got.setdefault(i["code"], set()).add(i["severity"])
            for code, severity in want.items():
                add(f"review:{code}", severity, sorted(got.get(code, ())), severity in got.get(code, ()))
        elif key == "epoch_notes":
            got = sorted({n["id"] for n in contract["temporal"]["epoch_notes"]})
            add(key, sorted(want), got, got == sorted(want))
        elif key == "withdrawn_ids":
            got = sorted({f["id"] for f in report.get("withdrawn", [])})
            add(key, want, got, set(want) <= set(got))
        elif key == "community_keep":
            got = sorted(p["community"]["keep"])
            add(key, sorted(want), got, got == sorted(want))
        elif key == "finding_ids_include":
            got = sorted({f["id"] for f in findings})
            add(key, want, got, set(want) <= set(got))
        elif key == "contract_warning_contains":
            add(key, want, contract["warnings"], any(want in w for w in contract["warnings"]))
        elif key == "segmentation":
            max_words = case.get("segment_max_words", 900)
            rep = boundary_report(text, max_words)
            seg = segment(text, max_words)
            cuts = [s["paragraphs"][0] for s in seg["segments"][1:]]
            if "unreported" in want:
                add("segmentation:unreported", want["unreported"], rep["unreported"],
                    rep["unreported"] == want["unreported"])
            if "no_cut_before_paragraphs" in want:
                bad = sorted(set(cuts) & set(want["no_cut_before_paragraphs"]))
                add("segmentation:no_cut_before", want["no_cut_before_paragraphs"], {"cuts": cuts, "violations": bad},
                    not bad)
            if want.get("lossless"):
                joined = "".join(text[s["start"]:s["end"]] for s in seg["segments"])
                add("segmentation:lossless", True, joined == text, joined == text)
        elif key == "literary_policy":
            add(key, want, p["literary"]["policy"], p["literary"]["policy"] == want)
        elif key == "no_strong_ids":
            got = sorted({f["id"] for f in findings if f["strength"] == "strong"})
            add(key, f"none of {want}", got, not set(want) & set(got))
        elif key == "absent_ids":
            got = sorted({f["id"] for f in findings})
            add(key, f"none of {want}", got, not set(want) & set(got))
        elif key == "strong_ids_include":
            got = sorted({f["id"] for f in findings if f["strength"] == "strong"})
            add(key, want, got, set(want) <= set(got))
        elif key == "regional_status":
            add(key, want, p["regional"]["status"], p["regional"]["status"] == want)
        else:
            add(key, want, "unknown expectation key", False)
    return {"id": case["id"], "kind": case["kind"], "pass": all(c["pass"] for c in checks), "checks": checks}


def main() -> int:
    raw = CASES.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["cases_sha256"] != sha:
        raise SystemExit(f"cases changed after freezing: {sha} != {manifest['cases_sha256']}")
    cases = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    rows = [check_case(c) for c in cases]
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip())
    passed = sum(r["pass"] for r in rows)
    by_kind: dict[str, list] = {}
    for r in rows:
        by_kind.setdefault(r["kind"], []).append(r["pass"])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = {"kind": "voznativa.benchmark_run", "benchmark": "ptbr-bench-v4", "arm": ARM, "recorded_at": stamp,
           "voznativa_version": __version__, "revision": revision, "dirty": dirty, "cases_sha256": sha,
           "model_called": False, "summary": {"cases": len(rows), "passed": passed, "rate": _rate(passed, len(rows)),
                                              "by_kind": {k: f"{sum(v)}/{len(v)}" for k, v in sorted(by_kind.items())}},
           "not_run": manifest["not_run_arms"], "rows": rows}
    out = ROOT / "benchmarks" / "runs" / f"ptbr-bench-v4-{stamp}.json"
    out.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for r in rows:
        if not r["pass"]:
            print("FAIL", r["id"], [c for c in r["checks"] if not c["pass"]])
    print(f"{passed}/{len(rows)} cases pass ({ARM}); revision {revision[:12]}{' dirty' if dirty else ''}")
    print(out.relative_to(ROOT).as_posix())
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
