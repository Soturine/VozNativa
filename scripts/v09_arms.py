#!/usr/bin/env python3
"""Fair arm comparison for v0.9 CP7: the same model, the same texts, measured the same way.

    python scripts/v09_arms.py --cmd '["claude", "-p", "--tools", ""]' --out run.json

Arms (each text of ``evals/v09/arms/texts.jsonl``):

* ``A0_original``: the text unchanged (the floor every metric is read against);
* ``A1_llm_direct``: one call to the model with a plain instruction (make it
  natural, keep every fact), no plan, no gate, no retry;
* ``A2_engine``: ``voznativa rewrite`` with the same command (plan,
  NO_CHANGE without a call, gates, retries, original returned when nothing
  passes).

Measured per arm, separately (never summed): semantic signals of
``compare`` against the original (critical, major), texts changed that did
not need a change (unnecessary edit), formula findings left in texts that
needed a change, calls made. ``compare`` is the engine's own instrument, so
arm A2 is favoured on that axis by construction: the report says so, and the
outputs are kept for a judge or a person. Not an independent evaluation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.providers import CommandProvider  # noqa: E402

DIRECT = ("Reescreva o texto abaixo em português brasileiro para soar natural e direto, sem mudar nenhum fato, "
          "número, data, condição ou negação. Se o texto já estiver bom, devolva-o igual. Responda só com o texto.\n\n"
          "TEXTO:\n{text}")
FORMULAS = {"formula", "metadiscourse"}


def formulas(text: str, genre: str) -> int:
    return sum(1 for f in detect(text, genre)["findings"] if f.get("family") in FORMULAS
               or "formula" in f.get("id", "") or "metadiscourse" in f.get("id", ""))


def measure(original: str, output: str, genre: str) -> dict:
    report = compare(original, output)
    return {"changed": output.strip() != original.strip(), "status": report["status"],
            "critical": report["summary"]["critical"], "major": report["summary"]["major"],
            "formulas_left": formulas(output, genre)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cmd", required=True, help="model command (JSON array), the same for both arms")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    texts = [json.loads(l) for l in (ROOT / "evals" / "v09" / "arms" / "texts.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    direct = CommandProvider.from_string(args.cmd, 300, env="minimal")
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for t in texts:
            row = {"id": t["id"], "needs_change": t["needs_change"], "genre": t["genre"],
                   "A0_original": measure(t["text"], t["text"], t["genre"])}
            started = time.time()
            answer = direct.generate(DIRECT.format(text=t["text"]))[0].strip()
            row["A1_llm_direct"] = {**measure(t["text"], answer, t["genre"]), "calls": 1,
                                    "seconds": round(time.time() - started, 1), "output": answer}
            src = Path(tmp) / f"{t['id']}.txt"
            src.write_text(t["text"], encoding="utf-8")
            started = time.time()
            done = subprocess.run([sys.executable, "-m", "voznativa", "rewrite", str(src), "--cmd", args.cmd,
                                   "--provider-env", "minimal", "--genre", t["genre"], "--attempts", "2"],
                                  capture_output=True, cwd=ROOT)
            result = json.loads(done.stdout.decode("utf-8"))
            row["A2_engine"] = {**measure(t["text"], result["text"], t["genre"]), "outcome": result["outcome"],
                                "calls": len(result.get("attempts", [])), "seconds": round(time.time() - started, 1),
                                "output": result["text"]}
            rows.append(row)
            print(t["id"], {a: {k: v for k, v in row[a].items() if k not in ("output",)} for a in
                            ("A1_llm_direct", "A2_engine")}, flush=True)

    def summary(arm):
        need = [r[arm] for r in rows if r["needs_change"]]
        good = [r[arm] for r in rows if not r["needs_change"]]
        allr = [r[arm] for r in rows]
        return {"texts": len(rows), "critical_signals": sum(x["critical"] for x in allr),
                "texts_with_major_or_critical": sum(1 for x in allr if x["critical"] or x["major"]),
                "unnecessary_edits": f"{sum(x['changed'] for x in good)}/{len(good)}",
                "formulas_left_in_texts_needing_change": sum(x["formulas_left"] for x in need),
                "calls": sum(x.get("calls", 0) for x in allr)}
    report = {"kind": "voznativa.v09_arms", "command": json.loads(args.cmd)[:1] + ["..."],
              "summary": {arm: summary(arm) for arm in ("A0_original", "A1_llm_direct", "A2_engine")},
              "caveat": "compare is the engine's own instrument: A2 is favoured on the semantic axis by design; "
                        "outputs are kept for a judge or a person; one run per arm, not independent",
              "rows": rows}
    text = json.dumps(report, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
