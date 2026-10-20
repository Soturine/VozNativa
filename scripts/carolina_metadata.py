#!/usr/bin/env python3
"""Corpus Carolina pilot, metadata only (v0.3.0 M5.1).

Streams TEI files (xml.gz) and keeps AGGREGATES of document metadata:
licenses (document and source), typology categories, source year, region
and token counts. It never stores text, titles, author names or URLs: the
headers carry usernames and source links, which are personal data and not
needed for evidence about the corpus.

    python scripts/carolina_metadata.py FILE.xml.gz [...] --hf-commit SHA --out evals/corpus/carolina-pilot.json
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TEI = "{http://www.tei-c.org/ns/1.0}"


def _text(el) -> str:
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


def scan(path: Path) -> dict:
    stats = {"documents": 0, "tokens": 0, "document_license": Counter(), "source_license": Counter(),
             "typology": Counter(), "source_year": Counter(), "region": Counter(), "corpus_version": None}
    with gzip.open(path, "rb") as handle:
        for event, el in ET.iterparse(handle, events=("end",)):
            tag = el.tag.replace(TEI, "")
            if tag == "title" and stats["corpus_version"] is None and (el.get("type") == "sub"):
                stats["corpus_version"] = _text(el)
            if tag != "TEI":
                continue
            header = el.find(f"{TEI}teiHeader")
            stats["documents"] += 1
            measure = header.find(f"{TEI}fileDesc/{TEI}extent/{TEI}measure[@unit='tokens']") if header is not None else None
            if measure is not None and measure.get("quantity", "").lstrip("-").isdigit():
                stats["tokens"] += max(0, int(measure.get("quantity")))
            doc_license = header.find(f"{TEI}fileDesc/{TEI}publicationStmt/{TEI}availability/{TEI}license")
            stats["document_license"][_text(doc_license) or "missing"] += 1
            src_pub = header.find(f".//{TEI}biblFull/{TEI}fileDesc/{TEI}publicationStmt")
            src_license = src_pub.find(f"{TEI}availability/{TEI}license") if src_pub is not None else None
            stats["source_license"][_text(src_license) or "missing"] += 1
            date = _text(src_pub.find(f"{TEI}date")) if src_pub is not None else ""
            year = re.search(r"(19|20)\d{2}", date)
            stats["source_year"][year.group(0)[:3] + "0s" if year else "unknown"] += 1
            region = _text(src_pub.find(f"{TEI}address/{TEI}region")) if src_pub is not None else ""
            stats["region"][region or "unspecified"] += 1
            for cat in header.iter(f"{TEI}catRef"):
                for target in (cat.get("target") or "").split():
                    stats["typology"][target.lstrip("#")] += 1
            el.clear()  # streaming: never keep text in memory
    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--hf-commit", required=True, help="Hugging Face commit the files were downloaded from")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    total = {"documents": 0, "tokens": 0}
    merged = {k: Counter() for k in ("document_license", "source_license", "typology", "source_year", "region")}
    files, versions = [], set()
    for path in args.files:
        s = scan(path)
        files.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "documents": s["documents"]})
        versions.add(s["corpus_version"])
        total["documents"] += s["documents"]
        total["tokens"] += s["tokens"]
        for key in merged:
            merged[key].update(s[key])
    report = {
        "kind": "voznativa.corpus_metadata_pilot",
        "corpus": "Corpus Carolina",
        "source": "https://huggingface.co/datasets/carolina-c4ai/corpus-carolina",
        "hf_commit": args.hf_commit,
        "corpus_version_in_files": sorted(v for v in versions if v),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": files,
        "scope": "a pilot sample of whole taxonomy files, not the corpus",
        "stored": "aggregates only; no text, titles, author names or URLs",
        **total,
        **{key: dict(counter.most_common()) for key, counter in merged.items()},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("corpus_version_in_files", "documents", "tokens")}, ensure_ascii=False))
    print("document_license:", report["document_license"])
    print("source_license (top):", dict(list(report["source_license"].items())[:8]))
    print("typology (top):", dict(list(report["typology"].items())[:8]))
    print("source_year:", report["source_year"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
