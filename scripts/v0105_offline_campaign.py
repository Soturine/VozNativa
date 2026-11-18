#!/usr/bin/env python3
"""Offline fire-trial campaign (v0.10.5 CP2): the engine of one checkout on every corpus item.

Per item (text read from ``items.jsonl`` outside the repository; only ids and measures are written):

* ``route`` genre, ``ptbr.language_of`` (when present), ``diagnose`` statuses and types, ``plan`` decision;
* **metamorphic pairs with a known oracle**, built on copies of the real text: a meaning change the gate must
  flag (negation added/removed, a number changed, a contrast turned into a consequence, an exception clause
  deleted, a middle sentence deleted) and benign changes it should not flag (line wrapping redone inside
  paragraphs, Unicode NFD). The oracle is the transformation itself, not the engine's own output.

    python scripts/v0105_offline_campaign.py --items ~/.voznativa/fire-trial/items.jsonl --root <checkout> \
        --out run.json [--max-words 4000]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path


def perturbations(text: str) -> list[tuple[str, str, str]]:
    """(kind, expected, candidate). expected: 'flag' or 'clean'."""
    out = []
    m = re.search(r"(?<=\s)(é|foi|era|são|será|pode|deve|tem|há)(?=\s)", text)
    if m:
        out.append(("negation_added", "flag", text[:m.start()] + "não " + text[m.start():]))
    m = re.search(r"\bnão\s+", text)
    if m:
        out.append(("negation_removed", "flag", text[:m.start()] + text[m.end():]))
    m = re.search(r"(?<![\d.,/])(\d{1,4})(?![\d.,/])", text)
    if m:
        new = str(int(m.group(1)) + 7)
        out.append(("number_changed", "flag", text[:m.start(1)] + new + text[m.end(1):]))
    m = re.search(r"\b(mas|porém|contudo|entretanto)\b", text)
    if m:
        out.append(("contrast_to_consequence", "flag", text[:m.start()] + "portanto" + text[m.end():]))
    m = re.search(r",?\s*(?:exceto|salvo|desde que|somente se)\b[^.;]*", text)
    if m and len(m.group(0).split()) >= 3:
        out.append(("exception_deleted", "flag", text[:m.start()] + text[m.end():]))
    sents = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ—])", text)
    if len(sents) >= 4:
        mid = len(sents) // 2
        if len(sents[mid].split()) >= 6:
            out.append(("sentence_deleted", "flag", " ".join(sents[:mid] + sents[mid + 1:])))
    paras = re.split(r"\n\s*\n", text)
    # A single line break is structure, not wrapping, in verse and in lists (incisos "I -", "§", "Art.", bullets):
    # joining those lines is not a benign change (oracle corrected after the first baseline run; both versions
    # were re-measured with the corrected oracle).
    structural = re.search(r"(?m)^\s*(?:[IVXLC]+\s*[-–.]|§|Art\.|Parágrafo|[a-z]\)|[*•]\s|-\s+[a-zà-ú])", text)
    if any("\n" in p for p in paras) and not _verse(text) and not structural:
        out.append(("rewrapped", "clean", "\n\n".join(" ".join(p.split()) for p in paras)))
    nfd = unicodedata.normalize("NFD", text)
    if nfd != text:
        out.append(("unicode_nfd", "clean", nfd))
    return out


def _verse(text: str) -> bool:
    lines = [x for x in text.splitlines() if x.strip()]
    return len(lines) >= 4 and sum(len(x) <= 55 for x in lines) / len(lines) >= 0.85


def run(items_path: Path, root: Path, max_words: int) -> dict:
    sys.path.insert(0, str(root))
    from voznativa import __version__
    from voznativa.compare import compare
    from voznativa.diagnose import diagnose
    from voznativa.planner import plan
    from voznativa.router import route
    try:
        from voznativa.ptbr import language_of
    except ImportError:
        language_of = None
    legacy = {"formal_error": "ERROR_CONFIRMED", "possible_contextual_error": "CONTEXT_DEPENDENT",
              "literary_license": "LITERARY_CHOICE", "legitimate_choice": "ACCEPTABLE_VARIANT"}
    rows = []
    started = time.process_time()
    for line in items_path.read_text(encoding="utf-8").splitlines():
        it = json.loads(line)
        text = it["text"]
        t0 = time.process_time()
        ctx = route(text)
        diags = diagnose(text, ctx)["diagnostics"]
        p = plan(text, ctx)
        row = {"id": it["id"], "genre": it["genre"], "family": it["family"], "band": it["band"], "words": it["words"],
               "rights": it["rights"], "routed_genre": ctx["genre"]["value"],
               "language": language_of(text)["value"] if language_of else None,
               "statuses": dict(Counter(d.get("status") or legacy.get(d["class"], d["class"]) for d in diags)),
               "confirmed_types": sorted({d["type"] for d in diags
                                          if (d.get("status") or legacy.get(d["class"])) == "ERROR_CONFIRMED"}),
               "plan": p["decision"], "plan_reasons": sorted({r.get("id", r.get("family", "?")) for s in p["sentences"]
                                                              for r in s.get("reasons", [])})[:12]}
        meta = []
        if it["words"] <= max_words:
            for kind, expected, candidate in perturbations(text):
                rep = compare(text, candidate)
                flagged = rep["status"] in ("review_required", "fail")
                meta.append({"kind": kind, "expected": expected, "status": rep["status"],
                             "codes": sorted({i["code"] for i in rep["issues"] if i["severity"] != "info"})[:8],
                             "correct": flagged if expected == "flag" else not flagged})
        row["metamorphic"] = meta
        row["cpu_s"] = round(time.process_time() - t0, 3)
        rows.append(row)
    return {"kind": "voznativa.fire_trial_offline_run", "engine_version": __version__, "engine_root": root.name,
            "items": len(rows), "cpu_s": round(time.process_time() - started, 1), "text_stored": False, "rows": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--items", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-words", type=int, default=4000)
    args = ap.parse_args(argv)
    report = run(Path(args.items).expanduser(), Path(args.root).resolve(), args.max_words)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    meta = [m for r in report["rows"] for m in r["metamorphic"]]
    print(json.dumps({"items": report["items"], "cpu_s": report["cpu_s"],
                      "metamorphic": f"{sum(m['correct'] for m in meta)}/{len(meta)}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
