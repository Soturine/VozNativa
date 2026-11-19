#!/usr/bin/env python3
"""Blind judge and independent protected-value oracle for the v0.10.5 live arms.

For each (task, rep) it gathers the outputs of every arm of every version label, deduplicates identical texts,
adds the original as one more anonymous candidate (control A0), shuffles them and labels them X1..Xn. The judge
model never sees an arm, a version or the word VozNativa. Per candidate it scores, 1-5:

* ``fidelity``: meaning, facts, names, numbers, dates, negations, conditions and exceptions kept;
* ``request``: does what the request asked (for "revise" with nothing to fix, leaving it alone is right);
* ``naturalness``: PT-BR that reads natural for the genre, author's voice kept where it should be;
* ``critical_error``: true when the candidate changes a fact/claim or breaks the text.

The judge is ``same_vendor`` as the writer (Anthropic models on both sides): MODEL_JUDGED, partial independence.

The **independent oracle** does not use the engine: it extracts numbers, capitalised names (not opening a
sentence) and quoted spans from the original and reports which ones a candidate lost. It is a signal, not a
verdict (an adaptation may legitimately drop a name).

Texts stay outside the repository; the report keeps labels, scores and hashes only.

    python scripts/v0105_judge.py --tasks evals/v0105/live_tasks.json --items ~/.voznativa/fire-trial/items.jsonl \
        --runs <dir with label subdirs> --labels v0100,v0105 --out judged.json [--model sonnet] [--split development]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import tempfile
from pathlib import Path

RUBRIC = """Você é um revisor editorial de português brasileiro. Abaixo está um TEXTO ORIGINAL, o PEDIDO feito \
sobre ele e várias CANDIDATAS anônimas (X1, X2...). Uma das candidatas pode ser idêntica ao original.

Avalie cada candidata de forma independente, de 1 (péssimo) a 5 (excelente), em:
- fidelity: preserva sentido, fatos, nomes, números, datas, negações, condições e exceções do original;
- request: atende ao PEDIDO (se o pedido é só "revise" e não há nada a corrigir, não mudar é o correto; mudar à toa é ruim);
- naturalness: português brasileiro natural para o gênero, mantendo a voz do autor quando o pedido pede isso.
Marque critical_error=true se a candidata muda um fato/afirmação, inverte sentido ou quebra o texto.

Responda SOMENTE com JSON, sem comentário: {"X1": {"fidelity": n, "request": n, "naturalness": n, \
"critical_error": false, "note": "até 20 palavras"}, ...}

PEDIDO: {request}

TEXTO ORIGINAL:
<<<
{original}
>>>
"""

_NAME = re.compile(r"(?<![.!?]\s)(?<!^)\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{2,}(?:\s+(?:de|da|do|dos|das)?\s*"
                   r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{2,})*)", re.M)


def protected(text: str) -> set[str]:
    nums = set(re.findall(r"\d+(?:[.,]\d+)*", text))
    names = {m.group(1) for m in _NAME.finditer(text)}
    quotes = {q.strip() for q in re.findall(r"[“\"«]([^”\"»\n]{3,80})[”\"»]", text)}
    return nums | names | quotes


def lost(original: str, candidate: str) -> list[str]:
    flat = " ".join(candidate.split())
    return sorted(v for v in protected(original) if " ".join(v.split()) not in flat)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def ask(prompt: str, model: str) -> tuple[dict, float]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_CODE_", "CLAUDECODE"))}
    with tempfile.TemporaryDirectory() as cwd:
        done = subprocess.run(["claude", "-p", "--model", model, "--output-format", "json", "--tools", ""],
                              input=prompt.encode("utf-8"), capture_output=True, env=env, cwd=cwd, timeout=900)
    try:
        outer = json.loads(done.stdout.decode("utf-8", "replace"))
    except ValueError:
        raise JudgeUnavailable(f"exit {done.returncode}, no JSON from the judge") from None
    body = outer.get("result") or ""
    m = re.search(r"\{.*\}", body, re.S)
    if done.returncode != 0 or outer.get("is_error") or not m:
        # quota, auth or a non-JSON answer: not a judgment; the row is not written and resume retries it
        raise JudgeUnavailable(f"exit {done.returncode}: {body[:120]!r}")
    return json.loads(m.group(0)), float(outer.get("total_cost_usd") or 0.0)


class JudgeUnavailable(RuntimeError):
    pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--items", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--split", default="development")
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args(argv)
    tasks = [t for t in json.loads(Path(args.tasks).read_text(encoding="utf-8"))["tasks"] if t["split"] == args.split]
    texts = {}
    for line in Path(args.items).expanduser().read_text(encoding="utf-8").splitlines():
        it = json.loads(line)
        texts[it["id"]] = it["text"]
    out_path = Path(args.out)
    report = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {
        "kind": "voznativa.fire_trial_blind_judgment", "judge_model": args.model, "relation": "same_vendor",
        "evidence": "MODEL_JUDGED", "text_stored": False, "rows": []}
    done_keys = {(r["task"], r["rep"]) for r in report["rows"]}
    labels = args.labels.split(",")
    for task in tasks:
        original = texts[task["item"]]
        for rep in range(1, args.reps + 1):
            if (task["task"], rep) in done_keys:
                continue
            cands = {sha(original): {"text": original, "arms": ["A0_original"]}}
            for label in labels:
                for f in sorted((Path(args.runs) / label).glob(f"{task['task']}-r{rep}-*.json")):
                    run = json.loads(f.read_text(encoding="utf-8"))
                    text = (run.get("output") or "").strip() or original
                    cands.setdefault(sha(text), {"text": text, "arms": []})["arms"].append(f"{label}:{run['arm']}")
            keys = sorted(cands)
            random.Random(f"judge-{task['task']}-{rep}").shuffle(keys)
            names = {k: f"X{i + 1}" for i, k in enumerate(keys)}
            prompt = RUBRIC.replace("{request}", task["request"]).replace("{original}", original) + "".join(
                f"\nCANDIDATA {names[k]}:\n<<<\n{cands[k]['text']}\n>>>\n" for k in keys)
            try:
                scores, cost = ask(prompt, args.model)
            except JudgeUnavailable as exc:
                print(task["task"], rep, "JUDGE_UNAVAILABLE (not written; retried on resume):", exc, flush=True)
                return 75
            rows = []
            for k in keys:
                s = scores.get(names[k]) or {}
                rows.append({"label": names[k], "sha": k, "arms": cands[k]["arms"], "identical_to_original":
                             cands[k]["text"] == original, "scores": {a: s.get(a) for a in
                                                                      ("fidelity", "request", "naturalness")},
                             "critical_error": s.get("critical_error"), "note": s.get("note"),
                             "oracle_lost": lost(original, cands[k]["text"])})
            report["rows"].append({"task": task["task"], "rep": rep, "expect": task["expect"],
                                   "mode": task["engine_mode"], "cost_usd": cost, "candidates": rows})
            out_path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(task["task"], rep, len(keys), round(cost, 4), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
