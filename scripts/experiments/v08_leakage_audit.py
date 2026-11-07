"""v0.8 CP5 (V08-GAP-08): shared texts across every evaluation set in the repository.

Reads the semantic, relation, predicate, decision, router and slang suites,
every benchmark case file and the quickstart examples, and reports exact and
near duplicates between different files (``evaluation.leakage``). Also checks
that every frozen benchmark still has the sha256 its manifest recorded.

    python -B scripts/experiments/v08_leakage_audit.py --out leakage.json

Only ids, files, kinds and scores are written; no text.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from voznativa.evals import sha256_lf  # noqa: E402
from voznativa.evaluation import leakage  # noqa: E402

GROUPS = {
    "evals/semantic/*.jsonl": "semantic",
    "evals/predicates/*.jsonl": "predicates",
    "evals/events/*.jsonl": "events",
    "evals/decision/*.jsonl": "decision",
    "evals/router/*.jsonl": "router",
    "evals/slang/*.jsonl": "slang",
    "benchmarks/cases/*.jsonl": "benchmark",
}


def entries() -> list[dict]:
    out = []
    for pattern, group in GROUPS.items():
        for path in sorted(ROOT.glob(pattern)):
            rel = path.relative_to(ROOT).as_posix()
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                text = row.get("original") or row.get("text")
                if isinstance(text, str):
                    out.append({"id": f"{path.stem}:{row.get('id')}", "source": rel, "split": group,
                                "text": text, "pair": row.get("candidate")})
    for path in sorted((ROOT / "examples" / "quickstart").glob("*.txt")):
        out.append({"id": f"quickstart:{path.stem}", "source": path.relative_to(ROOT).as_posix(),
                    "split": "examples", "text": path.read_text(encoding="utf-8"), "pair": None})
    return out


def frozen_benchmarks() -> list[dict]:
    rows = []
    for manifest in sorted((ROOT / "benchmarks" / "manifests").glob("*.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        cases = data.get("cases_file")
        expected = data.get("cases_sha256")
        if not cases or not expected:
            rows.append({"manifest": manifest.name, "status": "NO_HASH_RECORDED"})
            continue
        actual = sha256_lf(ROOT / cases)
        rows.append({"manifest": manifest.name, "cases": cases,
                     "status": "IDENTICAL" if actual == expected else "CHANGED"})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    found = entries()
    report = leakage(found)
    by_files = Counter(tuple(sorted({l["a"].split(":")[0], l["b"].split(":")[0]})) for l in report["links"])
    result = {"kind": "voznativa.leakage_audit", "schema_version": 1, "texts": len(found),
              "files": len({e["source"] for e in found}), "links": len(report["links"]),
              "same_pair": sum(l["same_pair"] for l in report["links"]),
              "by_file_pair": [{"files": list(k), "links": v} for k, v in sorted(by_files.items())],
              "pairs": [{k: l[k] for k in ("a", "b", "kind", "score", "same_pair")} for l in report["links"]],
              "frozen_benchmarks": frozen_benchmarks()}
    print(f"{result['texts']} texts in {result['files']} files: {result['links']} cross-file links "
          f"({result['same_pair']} identical cases)")
    for row in result["by_file_pair"]:
        print(f"  {row['links']:>3}  {' <-> '.join(row['files'])}")
    for row in result["frozen_benchmarks"]:
        print(f"  frozen {row['manifest']}: {row['status']}")
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 1 if any(r["status"] == "CHANGED" for r in result["frozen_benchmarks"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
