#!/usr/bin/env python3
"""Build examples/README.md from recorded real-model runs (v0.3.0 M6.3).

Every example comes from a committed run file and says which one, so the
page cannot drift into invented demos. The semantic report is recomputed
with the current gates; the judge verdict is the one recorded in the run.

    python scripts/make_examples.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402
from voznativa.patterns import detect  # noqa: E402

BENCH_OFFICIAL = "benchmarks/runs/ptbr-bench-v1-20261020T060615Z.json"
BENCH_RERUN = "benchmarks/runs/ptbr-bench-v1-20261020T061509Z.json"
INTEGRATION = "evals/integration/20261020T060212Z-claude-sonnet-5-5-ptbr-ai-drafts-v1.json"

PICKS = [
    ("Reescrita aceita (e-mail corporativo)", INTEGRATION, "ai-corp-001", None, ""),
    ("Nova tentativa depois da recusa do juiz (LinkedIn)", BENCH_RERUN, "pb-04", "B5b-voznativa-engine",
     "Na primeira tentativa o juiz recusou a saída; o engine refez a reescrita com o motivo da recusa."),
    ("Texto natural: nenhuma chamada ao modelo (WhatsApp)", BENCH_OFFICIAL, "pb-08", "B5b-voznativa-engine",
     "Sem achados editoriais, o engine devolve NO_CHANGE sem chamar o modelo."),
    ("Saída de outra skill barrada: hedge removido (acadêmico)", BENCH_OFFICIAL, "pb-03", "B2-blader",
     "\"Os resultados sugerem\" virou afirmação categórica: mudança real de grau de certeza."),
    ("Saída de outra skill barrada (jurídico)", BENCH_OFFICIAL, "pb-10", "B2-blader",
     "Nem todo alerta aqui é mudança real: \"sem prejuízo das obrigações\" → \"mantidas as obrigações\" "
     "é paráfrase fiel, e o gate é conservador nesse ponto. O juiz também recusou a saída."),
]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def pick(path: str, case_id: str, arm: str | None) -> tuple[str, str, str, dict]:
    run = load(path)
    if "results" in run:  # integration run
        row = next(r for r in run["results"] if r["id"] == case_id)
        genre = next(json.loads(line)["genre"] for line in
                     (ROOT / run["cases_file"]).read_text(encoding="utf-8").splitlines()
                     if line.strip() and json.loads(line)["id"] == case_id)
        return row["original"], row["final_text"], genre, {"outcome": row["outcome"], "judgments": row["judgments"]}
    rows = {(r["arm"], r["id"]): r for r in run["rows"] if "output" in r}
    original = rows[("B0-original", case_id)]["output"]
    row = rows[(arm, case_id)]
    genre = next(json.loads(line)["genre"] for line in
                 (ROOT / run["manifest"]["cases_file"]).read_text(encoding="utf-8").splitlines()
                 if line.strip() and json.loads(line)["id"] == case_id)
    meta = {"arm": arm, "judge": row.get("score", {}).get("judge", {}).get("verdict")}
    if isinstance(row.get("raw"), dict):
        meta["outcome"] = row["raw"].get("outcome")
    return original, row["output"], genre, meta


def block(text: str) -> str:
    return "\n".join("> " + line if line else ">" for line in text.splitlines())


def main() -> int:
    parts = [
        "# Exemplos reais",
        "",
        "Gerado por `scripts/make_examples.py` a partir de execuções gravadas com `claude-sonnet-5-5`. "
        "Os textos de entrada são sintéticos (escritos para os benchmarks). O relatório semântico é recalculado "
        "com o código atual; o veredito do juiz é o registrado na execução. Nada aqui é revisão humana.",
        "",
    ]
    for title, path, case_id, arm, note in PICKS:
        original, final, genre, meta = pick(path, case_id, arm)
        report = compare(original, final)
        before, after = detect(original, genre)["summary"], detect(final, genre)["summary"]
        issues = [i for i in report["issues"] if i["severity"] in {"critical", "major"}]
        parts += [f"## {title}", "", f"Fonte: `{path}`, caso `{case_id}`" + (f", braço `{arm}`" if arm else "") + ".",
                  "", "**Antes**", "", block(original), "", "**Depois**", "", block(final), "",
                  "**O que foi verificado**", "",
                  f"- Gate determinístico: `{report['status']}`" + (" (texto inalterado)" if report["status"] == "identical" else ""),
                  f"- Achados editoriais: {before['strong']} fortes + {before['weak']} fracos → "
                  f"{after['strong']} fortes + {after['weak']} fracos"]
        for issue in issues[:6]:
            parts.append(f"- `{issue['code']}` ({issue['severity']}): {issue['message']}")
        if meta.get("outcome"):
            parts.append(f"- Desfecho do engine: `{meta['outcome']}`")
        if meta.get("judge"):
            parts.append(f"- Juiz LLM (registrado): `{meta['judge']}`")
        for j in meta.get("judgments") or []:
            parts.append(f"- Juiz LLM (registrado): `{j['verdict']}`")
        if note:
            parts.append(f"- Nota: {note}")
        parts.append("")
    out = ROOT / "examples" / "README.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print("wrote", out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
