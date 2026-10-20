#!/usr/bin/env python3
"""Record a reproducible baseline of the current checkout.

Runs the validator, the unit suite, every semantic eval suite and the router
suite, summarizes recorded real-model runs, and writes the result to
evals/baselines/<label>.json together with the commit and the environment.

    python scripts/baseline.py --label v0.2.1-start
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa import __version__  # noqa: E402
from voznativa.evals import run as run_suite  # noqa: E402
from voznativa.router import infer_genre  # noqa: E402


def sh(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True).stdout.strip()


def unit_tests() -> dict:
    done = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "evals", "-p", "test_*.py"],
                          cwd=ROOT, capture_output=True, text=True)
    tail = done.stderr.strip().splitlines()
    ran = next((line for line in tail if line.startswith("Ran ")), "")
    return {"ok": done.returncode == 0, "summary": ran, "result": tail[-1] if tail else ""}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    validator = subprocess.run([sys.executable, "scripts/validate_package.py"], cwd=ROOT, capture_output=True, text=True)
    suites = {}
    for path in sorted((ROOT / "evals" / "semantic").glob("*.jsonl")):
        report = run_suite(path)
        suites[path.name] = {"passed": report["passed"], "cases": report["cases"],
                             "role": report["provenance"].get("role"),
                             "first_run": report["provenance"].get("first_run"),
                             "failures": [f["id"] for f in report["failures"]]}
    router_cases = [json.loads(line) for line in (ROOT / "evals/router/cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    router_hits = sum(infer_genre(c["text"])["value"] in c["expect"] for c in router_cases)

    integration = {}
    for path in sorted((ROOT / "evals" / "integration").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        integration[path.name] = {"summary": data.get("summary"), "code": data.get("voznativa_code"),
                                  "model": data.get("model_label")}

    baseline = {
        "kind": "voznativa.baseline",
        "label": args.label,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": __version__,
        "commit": sh("git", "rev-parse", "HEAD"),
        "dirty": bool(sh("git", "status", "--porcelain")),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "validator": {"ok": validator.returncode == 0, "output": (validator.stdout or validator.stderr).strip()},
        "unit_tests": unit_tests(),
        "semantic_suites": suites,
        "router": {"passed": router_hits, "cases": len(router_cases)},
        "integration_runs": integration,
    }
    out = ROOT / "evals" / "baselines" / f"{args.label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: baseline[k] for k in ("commit", "dirty", "validator", "unit_tests", "router")}, indent=2))
    print({k: f"{v['passed']}/{v['cases']}" for k, v in suites.items()})
    return 0 if baseline["validator"]["ok"] and baseline["unit_tests"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
