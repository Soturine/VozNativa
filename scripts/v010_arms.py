#!/usr/bin/env python3
"""Ablation arms for v0.10 CP10: the same model and texts, measured the same way.

    python scripts/v010_arms.py --cmd '["claude", "-p", "--model", "haiku", "--tools", ""]' \
        --base /path/to/v0.9.0/checkout --out run.json

Texts: ``evals/v010/arms/texts.jsonl`` (frozen before any run; genres the router does not map,
mixed registers, four texts that need no change). Arms:

* ``A0_original`` — the text unchanged;
* ``A1_llm_direct`` — one call with a plain instruction, no plan, no gate;
* ``B3_v090`` — ``voznativa rewrite`` of the v0.9.0 checkout (same flags as B4);
* ``B4_v010_bare`` — v0.10 without open attributes and with the knowledge block removed;
* ``B5_v010_full`` — v0.10 with the text's open attributes (``--attr``) and the knowledge block.

Measured per arm and never summed: ``compare`` (v0.10) against the original, relation changes,
texts changed that needed no change, formula findings left, and checks specific to a text (line
breaks of the poem, conditions of the ad, the contrast of the report, informality of the chat).
``compare`` is the engine's own instrument: engine arms are favoured on that axis by construction.
One run per arm (n = 1 per text): differences of one or two texts are not evidence of an effect.
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

from voznativa import discourse  # noqa: E402
from voznativa.compare import compare  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.providers import CommandProvider  # noqa: E402

DIRECT = ("Reescreva o texto abaixo em português brasileiro para soar natural e direto, sem mudar nenhum fato, "
          "número, data, condição ou negação. Se o texto já estiver bom, devolva-o igual. Responda só com o texto.\n\n"
          "TEXTO:\n{text}")
BARE = ("import sys; from voznativa import knowledge as k; "
        "k.for_text = lambda *a, **kw: {'selected': [], 'skipped': [], 'used_chars': 0, 'budget_chars': 0, "
        "'registry_errors': []}; from voznativa.cli import main; sys.exit(main(sys.argv[1:]))")
SPECIFIC = {
    "t03": lambda out: "somente" in out.lower() or "só " in out.lower() or "apenas" in out.lower(),
    "t06": lambda out: discourse.profile(out)["counter"] >= 1,
    "t07": lambda out: out.count("\n") >= 3,
    "t08": lambda out: "cê" in out.lower() or "avisa" in out.lower(),
    "t09": lambda out: ("desde que" in out.lower() or "contanto" in out.lower() or "somente" in out.lower())
    and ("exceto" in out.lower() or "salvo" in out.lower() or "não vale" in out.lower() or "menos" in out.lower()),
}


def formulas(text: str) -> int:
    return sum(1 for f in detect(text, "unknown")["findings"]
               if "formula" in (f.get("family") or "") or "metadiscourse" in f.get("id", ""))


def measure(tid: str, original: str, output: str) -> dict:
    report = compare(original, output)
    codes = [i["code"] for i in report["issues"] if i["severity"] != "info"]
    out = {"changed": output.strip() != original.strip(), "status": report["status"],
           "critical": report["summary"]["critical"], "major": report["summary"]["major"],
           "relation_issues": sum(c.startswith("relation_") for c in codes), "formulas_left": formulas(output)}
    if tid in SPECIFIC:
        out["specific_ok"] = bool(SPECIFIC[tid](output))
    return out


def run_engine(cwd: Path, src: Path, cmd: str, extra: list[str], bare: bool = False) -> dict:
    head = [sys.executable, "-c", BARE] if bare else [sys.executable, "-m", "voznativa"]
    done = subprocess.run(head + ["rewrite", str(src), "--cmd", cmd, "--provider-env", "minimal",
                                  "--attempts", "2", *extra], capture_output=True, cwd=cwd)
    try:
        return json.loads(done.stdout.decode("utf-8"))
    except ValueError:
        return {"outcome": "harness_error", "text": src.read_text(encoding="utf-8"),
                "error": done.stderr.decode("utf-8", "replace")[-400:]}


def attr_flags(attrs: dict) -> list[str]:
    flags = []
    for key, value in attrs.items():
        flags += ["--attr", f"{key}={','.join(value) if isinstance(value, list) else value}"]
    return flags


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cmd", required=True, help="model command (JSON array), the same for every arm")
    ap.add_argument("--base", required=True, help="v0.9.0 checkout for arm B3")
    ap.add_argument("--only", action="append")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    texts = [json.loads(line) for line in (ROOT / "evals" / "v010" / "arms" / "texts.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    if args.only:
        texts = [t for t in texts if t["id"] in args.only]
    direct = CommandProvider.from_string(args.cmd, 300, env="minimal")
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for t in texts:
            src = Path(tmp) / f"{t['id']}.txt"
            src.write_text(t["text"], encoding="utf-8")
            row = {"id": t["id"], "needs_change": t["needs_change"], "attrs": t["attrs"],
                   "A0_original": measure(t["id"], t["text"], t["text"])}
            started = time.time()
            answer = direct.generate(DIRECT.format(text=t["text"]))[0].strip()
            row["A1_llm_direct"] = {**measure(t["id"], t["text"], answer), "calls": 1,
                                    "seconds": round(time.time() - started, 1), "output": answer}
            for arm, cwd, extra, bare in (("B3_v090", Path(args.base), [], False),
                                          ("B4_v010_bare", ROOT, [], True),
                                          ("B5_v010_full", ROOT, attr_flags(t["attrs"]), False)):
                started = time.time()
                result = run_engine(cwd, src, args.cmd, extra, bare)
                row[arm] = {**measure(t["id"], t["text"], result["text"]), "outcome": result["outcome"],
                            "calls": len(result.get("attempts", [])), "seconds": round(time.time() - started, 1),
                            "output": result["text"],
                            **({"knowledge": [k["id"] for k in result.get("knowledge", {}).get("selected", [])]}
                               if arm == "B5_v010_full" else {}),
                            **({"error": result["error"]} if "error" in result else {})}
            rows.append(row)
            print(t["id"], {a: {k: v for k, v in row[a].items() if k in ("changed", "status", "outcome", "calls",
                                                                          "specific_ok", "relation_issues")}
                            for a in ("A1_llm_direct", "B3_v090", "B4_v010_bare", "B5_v010_full")}, flush=True)

    arms = ("A0_original", "A1_llm_direct", "B3_v090", "B4_v010_bare", "B5_v010_full")

    def summary(arm):
        good = [r[arm] for r in rows if not r["needs_change"]]
        need = [r[arm] for r in rows if r["needs_change"]]
        allr = [r[arm] for r in rows]
        spec = [x["specific_ok"] for x in allr if "specific_ok" in x]
        return {"texts": len(rows), "unnecessary_edits": f"{sum(x['changed'] for x in good)}/{len(good)}",
                "changed_when_needed": f"{sum(x['changed'] for x in need)}/{len(need)}",
                "texts_with_major_or_critical": sum(1 for x in allr if x["critical"] or x["major"]),
                "relation_issues": sum(x["relation_issues"] for x in allr),
                "formulas_left_in_texts_needing_change": sum(x["formulas_left"] for x in need),
                "specific_checks_ok": f"{sum(spec)}/{len(spec)}", "calls": sum(x.get("calls", 0) for x in allr)}
    report = {"kind": "voznativa.v010_arms", "command": json.loads(args.cmd),
              "summary": {arm: summary(arm) for arm in arms},
              "caveat": "compare is the engine's own instrument (engine arms favoured on that axis); specific checks "
                        "are string tests written before the run; one run per arm, n = 1 per text; the model's "
                        "answers vary between runs; not an independent or human evaluation",
              "rows": rows}
    text = json.dumps(report, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
