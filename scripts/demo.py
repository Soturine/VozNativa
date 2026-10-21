#!/usr/bin/env python3
"""Before/after demonstration of v0.4.0 (M5), reproducible without a model.

Takes real outputs recorded in the official ptbr-bench-v2 run and recomputes
everything else deterministically: the plan (what should change and why),
the gate (what the rewrite may have broken), editorial findings before and
after, PT-BR checks and source warnings. The one-line-prompt arm is shown
next to it for contrast. Writes examples/v0.4.0-demo.md.

    python scripts/demo.py [--run benchmarks/runs/ptbr-bench-v2-20261021T110338Z.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.planner import OP_LABEL, plan  # noqa: E402
from voznativa.ptbr import candidate_issues  # noqa: E402
from voznativa.router import route  # noqa: E402

CASES = ["bv2-doc-01", "bv2-pt-01", "bv2-em-03", "bv2-li-02", "bv2-inj-01"]
DEFAULT_RUN = ROOT / "benchmarks" / "runs" / "ptbr-bench-v2-20261021T110338Z.json"


def section(case: dict, rows: dict) -> list[str]:
    text = case["text"]
    hints = case.get("hints") or {}
    ctx = route(text, genre=case["genre"], **{k: v for k, v in hints.items() if k in {"channel", "register", "audience"}})
    p = plan(text, ctx)
    v04, v1 = rows.get("B5-voznativa-v040"), rows.get("B1-one-line")
    out = [f"## {case['id']} ({case['kind']}, {case['genre']}{', pedido: ' + case['request'] if case.get('request') else ''})",
           "", "**Original**", "", "> " + text.replace("\n", "\n> "), "",
           f"**Plano** ({p['decision']}, escopo {p['scope']}):", ""]
    for r in p["sentences"]:
        if r["op"] == "keep" and p["scope"] != "document":
            out.append(f"- F{r['index'] + 1}: manter")
        elif r["op"] != "keep":
            why = "; ".join(f"{x['family']} \"{x['text']}\" ({x['priority']})" for x in r["reasons"])
            keep = f" — preservar: {', '.join(r['preserve'][:5])}" if r["preserve"] else ""
            out.append(f"- F{r['index'] + 1}: {OP_LABEL[r['op']]} — {why}{keep}")
    for t in p["targets"]:
        out.append(f"- destino pedido: {t['target']} = {t['value']}")
    for w in p["warnings"]:
        out.append(f"- aviso: {w['message']} (\"{w['text']}\")")
    out.append("")
    for label, row in (("VozNativa v0.4.0", v04), ("Prompt de uma linha (B1)", v1)):
        if not row or "output" not in row:
            continue
        output = row["output"]
        gate = compare(text, output)
        before = detect(text, case["genre"])["summary"]
        after = detect(output, case["genre"])["summary"]
        risks = [f"{i['code']}: {i['message']}" for i in gate["issues"] if i["severity"] != "info"]
        risks += [f"{i['code']}: {i['message']}" for i in candidate_issues(text, output, case["genre"])
                  if i["severity"] != "info"]
        judge = (row.get("score") or {}).get("judge", {}).get("verdict", "—")
        out += [f"**{label}**" + (f" (desfecho do engine: {row['raw']['outcome']})" if row.get("raw") else ""), "",
                "> " + output.replace("\n", "\n> "), "",
                f"- gate: `{gate['status']}`; juiz LLM na execução: {judge}",
                f"- achados editoriais: {before['strong']} fortes / {before['weak']} fracos -> "
                f"{after['strong']} fortes / {after['weak']} fracos"]
        out += [f"- risco: {r}" for r in risks] or ["- risco detectado: nenhum"]
        out.append("")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default=str(DEFAULT_RUN))
    parser.add_argument("--out", default=str(ROOT / "examples" / "v0.4.0-demo.md"))
    args = parser.parse_args()
    run = json.loads(Path(args.run).read_text(encoding="utf-8"))
    cases = {json.loads(l)["id"]: json.loads(l) for l in
             (ROOT / run["manifest"]["cases_file"]).read_text(encoding="utf-8").splitlines() if l.strip()}
    lines = ["# Demonstração v0.4.0: antes e depois", "",
             f"Saídas reais da execução oficial `{Path(args.run).name}` ({run['model']}); plano, gate, achados e "
             "riscos recalculados deterministicamente por `python scripts/demo.py` (não chama modelo). "
             "O juiz LLM é o registrado na execução. Nada aqui é revisão humana.", ""]
    for cid in CASES:
        rows = {r["arm"]: r for r in run["rows"] if r["id"] == cid}
        lines += section(cases[cid], rows)
    Path(args.out).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"written {Path(args.out).relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
