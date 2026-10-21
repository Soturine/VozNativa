#!/usr/bin/env python3
"""Latency of the deterministic pipeline (v0.4.0 M4): detect, plan and
compare on documents of growing length, plus adversarial inputs for regex
backtracking. Run from any checkout; prints JSON.

    python scripts/perf_probe.py [--out evals/perf/v0.4.0.json]
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa import __version__  # noqa: E402
from voznativa.compare import compare  # noqa: E402
from voznativa.patterns import detect  # noqa: E402

PARAGRAPHS = [
    "É importante destacar que a migração do banco acontece no sábado, 14 de novembro de 2026, das 22h às 2h.",
    "Durante a janela, o painel fica fora do ar, mas a API pública continua respondendo em modo somente leitura.",
    "Antes da janela, cada time deve congelar os deploys a partir das 18h e conferir o backup das 20h.",
    "Se a restauração falhar, a migração é adiada e o canal #incidentes recebe o aviso, porque não há outra janela.",
    "Depois da migração, o time acompanha a latência por 48 horas; se o p95 passar de 300 ms, o rollback leva 30 minutos.",
]
ADVERSARIAL = {
    "commas": ("a, " * 4000) + "b.",
    "long_word": "x" * 50000,
    "no_spaces_numbers": "1" * 20000,
    "nested_quotes": ("\"" + "palavra " * 50) * 200,
    "many_triads": "eficiência, agilidade e inovação. " * 800,
}


def doc(words: int) -> str:
    out, n, i = [], 0, 0
    while n < words:
        p = PARAGRAPHS[i % len(PARAGRAPHS)]
        out.append(p)
        n += len(p.split())
        i += 1
    return "\n\n".join(out)


def timed(fn, *args, repeat: int = 3) -> float:
    best = float("inf")
    for _ in range(repeat):
        start = time.perf_counter()
        fn(*args)
        best = min(best, time.perf_counter() - start)
    return round(best, 4)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        from voznativa.planner import plan
        from voznativa.router import route
    except ImportError:  # older checkouts have no planner
        plan = route = None
    rows = []
    for words in (100, 500, 2000, 8000):
        text = doc(words)
        candidate = text.replace("É importante destacar que a", "A")
        row = {"words": len(text.split()), "detect_s": timed(detect, text, "technical"),
               "compare_s": timed(compare, text, candidate, repeat=1)}
        if plan:
            row["plan_s"] = timed(lambda t: plan(t, route(t, genre="technical")), text, repeat=1)
        rows.append(row)
    adversarial = {}
    for name, text in ADVERSARIAL.items():
        adversarial[name] = {"chars": len(text), "detect_s": timed(detect, text, "unknown", repeat=1),
                             "compare_s": timed(compare, text, text + " fim", repeat=1)}
    result = {"kind": "voznativa.perf_probe", "version": __version__, "python": platform.python_version(),
              "platform": platform.platform(), "documents": rows, "adversarial": adversarial,
              "note": "best of 3 for detect, single run otherwise; wall-clock on one machine"}
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
