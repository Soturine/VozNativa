#!/usr/bin/env python3
"""Long-document flows of the v0.10.5 fire trial (CP R8): three complete runs on real public-domain text.

1. ``lgpd``: the full Lei 13.709/2018 (about 12 thousand words, institutional), ``rewrite --long-form on --mode
   POLISH`` with a request that forbids normative change; then ``compare`` of the whole document and an
   independent oracle (article numbering, every number, word ratio).
2. ``romance``: chapters of a Machado de Assis novel (literary), ``--mode ADAPT`` for a present-day reader.
3. ``office``: a DOCX built from a Machado short story (heading, paragraphs, a table) rewritten with ``--docx-out``
   and verified by ``docx check``; a PDF rendered from the law text, ``pdf extract`` measured against the source
   words, ``pdf annotate`` writing a new file while the original keeps its hash.

Texts and outputs stay in ``--work`` (outside the repository); the JSON report holds measures and hashes only.

    python scripts/v0105_documents.py --items ~/.voznativa/fire-trial/items.jsonl --root <checkout> \
        --work <dir outside the repo> --out report.json [--model haiku] [--flows lgpd,romance,office]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROVIDER = HERE / "experiments" / "claude_cost_provider.py"
ITEMS = {"lgpd": "ft-0361", "romance": "ft-0254", "story": "ft-0130"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def numbers(text: str) -> Counter:
    return Counter(re.findall(r"\d+(?:[.,]\d+)*", text))


def articles(text: str) -> list[str]:
    return re.findall(r"(?m)^\s*Art\.\s*(\d+)", text)


def oracle(original: str, candidate: str) -> dict:
    on, cn = numbers(original), numbers(candidate)
    return {"words_ratio": round(len(candidate.split()) / max(1, len(original.split())), 3),
            "numbers_lost": sum((on - cn).values()), "numbers_added": sum((cn - on).values()),
            "articles_same_sequence": articles(original) == articles(candidate),
            "articles": len(articles(original))}


class Runner:
    def __init__(self, root: Path, work: Path, model: str):
        self.root, self.work, self.model = root, work, model
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_CODE_", "CLAUDECODE"))}
        self.env["PYTHONIOENCODING"] = "utf-8"
        self.env["PYTHONPATH"] = str(root)

    def vn(self, *args, cost_log: Path | None = None) -> tuple[int, str, float]:
        env = dict(self.env)
        if cost_log:
            env["VN_COST_LOG"] = str(cost_log)
        started = time.time()
        done = subprocess.run([sys.executable, "-m", "voznativa", *args], capture_output=True, env=env,
                              cwd=self.work, timeout=7200)
        return done.returncode, done.stdout.decode("utf-8", "replace"), round(time.time() - started, 1)

    def rewrite(self, src: Path, mode: str, request: str, extra=()) -> dict:
        log = self.work / f"{src.stem}.cost.jsonl"
        log.unlink(missing_ok=True)
        cmd = json.dumps([sys.executable, str(PROVIDER), self.model])
        code, out, secs = self.vn("rewrite", str(src), "--cmd", cmd, "--provider-env", "minimal",
                                  "--provider-env-allow", "VN_COST_LOG", "--provider-env-allow", "PYTHONIOENCODING",
                                  "--mode", mode, "--attr", f"pedido={request}", "--attempts", "2", *extra,
                                  cost_log=log)
        rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()] \
            if log.exists() else []
        try:
            result = json.loads(out)
        except ValueError:
            result = {"raw_tail": out[-300:]}
        return {"exit_code": code, "seconds": secs, "calls": len(rows),
                "cost_usd": round(sum(r.get("cost_usd") or 0 for r in rows), 6), "result": result}


def summary(result: dict) -> dict:
    report = result.get("report") or {}
    lf = result.get("long_form") or {}
    return {"outcome": result.get("outcome"), "status": report.get("status"),
            "issues": dict(Counter(i["code"] for i in report.get("issues", []) if i.get("severity") != "info")),
            "units": lf.get("units") if isinstance(lf.get("units"), int) else len(lf.get("units") or []),
            "unit_outcomes": dict(Counter(u.get("outcome") for u in lf.get("units") or [] if isinstance(u, dict)))}


def flow_text(r: Runner, name: str, text: str, mode: str, request: str) -> dict:
    src = r.work / f"{name}.txt"
    src.write_text(text, encoding="utf-8")
    run = r.rewrite(src, mode, request, ("--long-form", "on", "--max-calls", "80"))
    cand = (run["result"].get("text") or "") if isinstance(run["result"], dict) else ""
    (r.work / f"{name}.candidate.txt").write_text(cand, encoding="utf-8")
    t0 = time.process_time()
    code, out, _ = r.vn("compare", str(src), str(r.work / f"{name}.candidate.txt"))
    compare_cpu = round(time.process_time() - t0, 2)
    rep = json.loads(out) if out.strip().startswith("{") else {}
    return {"flow": name, "words": len(text.split()), "mode": mode, "request": request,
            "exit_code": run["exit_code"], "seconds": run["seconds"], "calls": run["calls"],
            "cost_usd": run["cost_usd"], **summary(run["result"]), "changed": cand.strip() != text.strip(),
            "recompare_status": rep.get("status"), "oracle": oracle(text, cand) if cand else None,
            "source_sha256": sha(text.encode("utf-8")), "compare_cli_cpu_s": compare_cpu}


def flow_office(r: Runner, story: str, law: str) -> dict:
    import docx
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate
    out = {"flow": "office"}
    # DOCX: heading + paragraphs + a table (table cells are protected by the engine)
    paras = [p.strip() for p in re.split(r"\n\s*\n", story) if p.strip()][:40]
    d = docx.Document()
    d.add_heading("Conto (domínio público)", level=1)
    for p in paras:
        d.add_paragraph(" ".join(p.split()))
    table = d.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Edição", "Ano"
    table.cell(1, 0).text, table.cell(1, 1).text = "Primeira", "1884"
    src = r.work / "story.docx"
    d.save(src)
    before = sha(src.read_bytes())
    code, ext, _ = r.vn("docx", "extract", str(src))
    rep = json.loads(ext) if ext.strip().startswith("{") else {}
    out["docx_extract_exit"] = code
    out["docx_summary"] = rep.get("summary")
    run = r.rewrite(src, "PROOFREAD", "Atualize só a ortografia para a norma atual, sem mudar o texto.",
                    ("--docx-out", str(r.work / "story.out.docx"), "--max-calls", "80"))
    out["docx_rewrite"] = {"exit_code": run["exit_code"], "calls": run["calls"], "cost_usd": run["cost_usd"],
                           "seconds": run["seconds"], **summary(run["result"])}
    if (r.work / "story.out.docx").exists():
        code, chk, _ = r.vn("docx", "check", str(src), str(r.work / "story.out.docx"))
        out["docx_check_exit"] = code
        out["docx_check"] = json.loads(chk) if chk.strip().startswith("{") else chk[-300:]
        new = docx.Document(r.work / "story.out.docx")
        out["docx_table_kept"] = [c.text for c in new.tables[0]._cells] == ["Edição", "Ano", "Primeira", "1884"] \
            if new.tables else False
    out["docx_original_unchanged"] = sha(src.read_bytes()) == before
    # PDF: rendered from the law, extracted, measured against the source words; annotated copy
    words = law.split()[:2500]
    pdf = r.work / "lei.pdf"
    styles = getSampleStyleSheet()
    chunks = [" ".join(words[i:i + 120]) for i in range(0, len(words), 120)]
    SimpleDocTemplate(str(pdf), pagesize=A4).build([Paragraph(c, styles["BodyText"]) for c in chunks])
    pdf_before = sha(pdf.read_bytes())
    code, ext, _ = r.vn("pdf", "extract", str(pdf))
    rep = json.loads(ext) if ext.strip().startswith("{") else {}
    got = " ".join(e.get("text", "") for e in rep.get("elements", []) if e.get("type") == "paragraph")
    src_words, got_words = Counter(words), Counter(got.split())
    out["pdf_extract_exit"] = code
    out["pdf_summary"] = rep.get("summary")
    out["pdf_word_recall"] = round(sum((src_words & got_words).values()) / max(1, sum(src_words.values())), 4)
    notes = r.work / "notes.json"
    notes.write_text(json.dumps([{"page": 1, "text": "Nota de revisão de teste"}]), encoding="utf-8")
    code, ann, _ = r.vn("pdf", "annotate", "--out", str(r.work / "lei.annot.pdf"), str(pdf), str(notes))
    out["pdf_annotate_exit"] = code
    out["pdf_annotated_written"] = (r.work / "lei.annot.pdf").exists()
    out["pdf_original_unchanged"] = sha(pdf.read_bytes()) == pdf_before
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--items", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--flows", default="lgpd,romance,office")
    args = ap.parse_args(argv)
    texts = {}
    for line in Path(args.items).expanduser().read_text(encoding="utf-8").splitlines():
        it = json.loads(line)
        texts[it["id"]] = it["text"]
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    r = Runner(Path(args.root).resolve(), work, args.model)
    report = {"kind": "voznativa.fire_trial_documents", "model": args.model, "text_stored": False, "flows": []}
    flows = args.flows.split(",")
    if "lgpd" in flows:
        report["flows"].append(flow_text(r, "lgpd", texts[ITEMS["lgpd"]], "POLISH",
                                         "Revise a redação deste texto legal sem alterar nenhum conteúdo normativo."))
    if "romance" in flows:
        report["flows"].append(flow_text(r, "romance", texts[ITEMS["romance"]], "ADAPT",
                                         "Adapte estes capítulos para um leitor de hoje, mantendo enredo e estilo."))
    if "office" in flows:
        report["flows"].append(flow_office(r, texts[ITEMS["story"]], texts[ITEMS["lgpd"]]))
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
