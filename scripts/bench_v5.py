#!/usr/bin/env python3
"""ptbr-bench-v5 (v0.7.0 OOD conformance): deterministic arm.

Every expectation of a frozen case is one check in a *family* (routing,
protections, decision, semantic_gate, slang, variety, long_form, diagnosis).
Results are reported per family and, inside each family, per group of each
axis (genre, epoch, variety, length, task) with n and a Wilson 95% interval.
There is no combined score. Model and human arms are NOT_RUN.

    python scripts/bench_v5.py      # writes benchmarks/runs/ptbr-bench-v5-<UTC>.json
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa import __version__  # noqa: E402
from voznativa.community import apply_to_report  # noqa: E402
from voznativa.compare import compare  # noqa: E402
from voznativa.corpus.evaluate import _rate  # noqa: E402
from voznativa.diagnose import diagnose  # noqa: E402
from voznativa.document import build_plan, reassemble  # noqa: E402
from voznativa.longform import literary_policy  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.planner import plan  # noqa: E402
from voznativa.ptbr import findings as ptbr_findings  # noqa: E402
from voznativa.router import explicit_channel, route  # noqa: E402
from voznativa.temporal import observe  # noqa: E402

CASES = ROOT / "benchmarks" / "cases" / "ptbr-bench-v5.jsonl"
MANIFEST = ROOT / "benchmarks" / "manifests" / "ptbr-bench-v5.json"
ARM = "D-voznativa-v070-deterministic"
FAMILY = {"genre_in": "routing", "genre_not": "routing", "structure": "routing", "time_of_text": "routing",
          "protections_local": "protections", "decision_in": "decision", "gate": "semantic_gate",
          "codes_in": "semantic_gate", "slang": "slang", "ptpt_strong": "variety", "language_variant": "variety",
          "doc_lossless": "long_form", "doc_protected_kinds": "long_form", "diagnose_has": "diagnosis",
          "diagnose_not_class": "diagnosis"}
GATE = {"fail": {"fail"}, "not_fail": {"no_deterministic_issues", "review_required", "identical"},
        "review": {"review_required"}}


def check_case(case: dict) -> list[dict]:
    text, exp = case["text"], case["expect"]
    hints = case.get("hints") or {}
    ctx = route(text, channel=hints.get("channel"))
    checks = []

    def add(key, expected, observed, ok):
        checks.append({"check": key, "family": FAMILY[key], "expected": expected, "observed": observed,
                       "pass": bool(ok)})

    genre = ctx["genre"]["value"]
    if "genre_in" in exp:
        add("genre_in", exp["genre_in"], genre, genre in exp["genre_in"])
    if "genre_not" in exp:
        add("genre_not", exp["genre_not"], genre, genre not in exp["genre_not"])
    if "structure" in exp:
        got = ctx["dimensions"]["structure"]["value"]
        add("structure", exp["structure"], got, got == exp["structure"])
    if "time_of_text" in exp:
        got = ctx["dimensions"]["time_of_text"]["value"]
        add("time_of_text", exp["time_of_text"], got, got == exp["time_of_text"])
    if "protections_local" in exp:
        got = literary_policy(text, genre, conservative=ctx["protections"]["conservative"])["max_scope"]
        add("protections_local", "local", got, (got == "local") == exp["protections_local"])
    if "decision_in" in exp:
        report = apply_to_report(detect(text, genre, explicit_channel(ctx), ctx["register"]["value"]), ctx, text)
        got = plan(text, ctx, report=report)["decision"]
        add("decision_in", exp["decision_in"], got, got in exp["decision_in"])
    if "gate" in exp or "codes_in" in exp:
        r = compare(text, case["candidate"])
        if "gate" in exp:
            add("gate", exp["gate"], r["status"], r["status"] in GATE[exp["gate"]])
        if "codes_in" in exp:
            codes = sorted({i["code"] for i in r["issues"]})
            add("codes_in", exp["codes_in"], codes, set(exp["codes_in"]) <= set(codes))
    if "slang" in exp:
        got = sorted({h["id"] for h in observe(text) if h["sense"] == "slang"})
        add("slang", sorted(exp["slang"]), got, got == sorted(exp["slang"]))
    if "ptpt_strong" in exp:
        strong = [f for f in ptbr_findings(text, genre) if f["family"] == "variante PT-PT" and not f.get("note_only")]
        add("ptpt_strong", exp["ptpt_strong"], len(strong), bool(strong) == exp["ptpt_strong"])
    if "language_variant" in exp:
        got = ctx["dimensions"]["language_variant"]["value"]
        add("language_variant", exp["language_variant"], got, got == exp["language_variant"])
    if "doc_lossless" in exp or "doc_protected_kinds" in exp:
        p = build_plan(text, ctx)
        if "doc_lossless" in exp:
            add("doc_lossless", True, reassemble(text, p) == text, reassemble(text, p) == text)
        if "doc_protected_kinds" in exp:
            got = sorted({k for u in p["units"] if u["action"] == "protect" for k in u["kinds"]})
            add("doc_protected_kinds", sorted(exp["doc_protected_kinds"]), got,
                set(exp["doc_protected_kinds"]) <= set(got))
    if "diagnose_has" in exp or "diagnose_not_class" in exp:
        d = diagnose(text, ctx)["diagnostics"]
        got = sorted({f'{x["class"]}:{x["type"]}' for x in d})
        if "diagnose_has" in exp:
            add("diagnose_has", exp["diagnose_has"], got, set(exp["diagnose_has"]) <= set(got))
        if "diagnose_not_class" in exp:
            classes = {x["class"] for x in d}
            add("diagnose_not_class", exp["diagnose_not_class"], sorted(classes),
                not classes & set(exp["diagnose_not_class"]))
    return checks


def main() -> int:
    raw = CASES.read_bytes()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if hashlib.sha256(raw).hexdigest() != manifest["cases_sha256"]:
        print("cases file differs from the frozen manifest: refusing to run", file=sys.stderr)
        return 1
    cases = [json.loads(x) for x in raw.decode("utf-8").splitlines() if x.strip()]
    rows = []
    for case in cases:
        checks = check_case(case)
        rows.append({"id": case["id"], "axes": case["axes"], "pass": all(c["pass"] for c in checks), "checks": checks})
    families = defaultdict(lambda: {"all": [0, 0], "groups": defaultdict(lambda: [0, 0])})
    for row in rows:
        for c in row["checks"]:
            f = families[c["family"]]
            f["all"][0] += c["pass"]
            f["all"][1] += 1
            for axis, value in row["axes"].items():
                g = f["groups"][f"{axis}={value}"]
                g[0] += c["pass"]
                g[1] += 1
    summary = {}
    for name, f in sorted(families.items()):
        groups = {k: _rate(*v) for k, v in sorted(f["groups"].items())}
        worst = min(groups.items(), key=lambda kv: (kv[1]["rate"], -kv[1]["n"]))
        summary[name] = {"checks": _rate(*f["all"]), "worst_group": {"group": worst[0], **worst[1]},
                         "groups": groups}
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    report = {"kind": "voznativa.benchmark_run", "benchmark": "ptbr-bench-v5", "arm": ARM, "version": __version__,
              "revision": head, "dirty": dirty, "cases_sha256": manifest["cases_sha256"],
              "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "cases_passed": _rate(sum(r["pass"] for r in rows), len(rows)), "families": summary,
              "failures": [{"id": r["id"], "checks": [c for c in r["checks"] if not c["pass"]]}
                           for r in rows if not r["pass"]],
              "not_run_arms": manifest["not_run_arms"]}
    out = ROOT / "benchmarks" / "runs" / f"ptbr-bench-v5-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{report['cases_passed']['k']}/{report['cases_passed']['n']} cases pass ({ARM}); revision {head[:12]}"
          f"{' dirty' if dirty else ''}")
    for name, s in summary.items():
        print(f"  {name:14s} {s['checks']['k']}/{s['checks']['n']}  worst {s['worst_group']['group']} "
              f"{s['worst_group']['k']}/{s['worst_group']['n']}")
    for f in report["failures"]:
        print("  FAIL", f["id"], [(c["check"], c["expected"], c["observed"]) for c in f["checks"]])
    print(out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
