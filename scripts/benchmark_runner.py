#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from semantic_guard import guard


def load_cases(path: Path):
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))
    return cases


def score_case(case: dict, candidate: str) -> dict:
    original = case["text"]
    lexical = guard(original, candidate)
    explicit_missing = [
        value for value in case.get("must_preserve", [])
        if value not in candidate
    ]
    original_len = max(1, len(original.split()))
    candidate_len = len(candidate.split())
    return {
        "id": case["id"],
        "protected_ok": lexical["ok"],
        "protected_missing": lexical["missing"],
        "explicit_invariants_ok": not explicit_missing,
        "explicit_missing": explicit_missing,
        "length_ratio": round(candidate_len / original_len, 3),
    }


def run(cases_path: Path, outputs_root: Path) -> dict:
    cases = load_cases(cases_path)
    systems = sorted(p.name for p in outputs_root.iterdir() if p.is_dir()) if outputs_root.exists() else []
    report = {"cases": len(cases), "systems": {}}

    for system in systems:
        rows = []
        for case in cases:
            candidate_path = outputs_root / system / f'{case["id"]}.txt'
            if not candidate_path.exists():
                rows.append({"id": case["id"], "missing_output": True})
                continue
            candidate = candidate_path.read_text(encoding="utf-8")
            rows.append(score_case(case, candidate))

        completed = [r for r in rows if not r.get("missing_output")]
        hard_pass = sum(
            1 for r in completed
            if r["protected_ok"] and r["explicit_invariants_ok"]
        )
        report["systems"][system] = {
            "completed": len(completed),
            "hard_pass": hard_pass,
            "hard_pass_rate": round(hard_pass / len(completed), 3) if completed else None,
            "results": rows,
        }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", type=Path)
    parser.add_argument("outputs", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()

    report = run(args.cases, args.outputs)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_path:
        args.json_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
