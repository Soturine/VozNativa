#!/usr/bin/env python3
"""Inventory of the documentation (v0.8 CP12): every Markdown file under docs/,
the root documents and the example/reference READMEs, with its title, size,
the version it belongs to, and who depends on it.

A dependency is a Markdown link from another document, or a mention of the
path (or the file name) in code, tests, scripts, manifests or evidence
records. A file mentioned by code or evidence is not moved without updating
those consumers; a file nobody links is not "obsolete" for that reason alone.

    python scripts/doc_inventory.py --out <scratch>/inventory.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
VERSION = re.compile(r"(?i)(?:v|_v|plan_v|as_is_v|v0)(\d)[._]?(\d)|V(\d)(\d)_")


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True).stdout.decode("utf-8")
    return [p for p in out.split("\0") if p]


def docs(files: list[str]) -> list[str]:
    roots = {"README.md", "SKILL.md", "ROADMAP.md", "CHANGELOG.md"}
    return sorted(p for p in files if p.endswith(".md") and (p.startswith("docs/") or p in roots
                                                              or p in ("examples/README.md", "benchmarks/README.md")))


def version_of(path: str) -> str | None:
    name = Path(path).name
    folder = re.match(r"docs/releases/v(\d+\.\d+)/", path)
    if folder:
        return folder.group(1)
    m = re.search(r"v(\d)\.(\d)", name) or re.search(r"_v(\d)\.(\d)", name)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.match(r"V(\d)(\d)_", name)
    return f"{m.group(1)}.{m.group(2)}" if m else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    files = tracked()
    texts = {}
    for p in files:
        if p.endswith((".md", ".py", ".json", ".yml", ".yaml", ".toml", ".txt", ".jsonl")) and (ROOT / p).is_file():
            try:
                texts[p] = (ROOT / p).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
    rows = []
    for doc in docs(files):
        text = texts.get(doc, "")
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), "")
        linked_by, mentioned_by = set(), set()
        for other, body in texts.items():
            if other == doc:
                continue
            if other.endswith(".md"):
                for target in LINK.findall(body):
                    if (ROOT / other).parent.joinpath(target).resolve() == (ROOT / doc).resolve():
                        linked_by.add(other)
            if doc in body or (not other.endswith(".md") and Path(doc).name in body):
                mentioned_by.add(other)
        consumers = sorted(p for p in mentioned_by | linked_by
                           if not p.endswith(".md") or p.startswith("evals/assurance/"))
        rows.append({"path": doc, "title": title, "words": len(text.split()), "version": version_of(doc),
                     "linked_by": sorted(linked_by), "code_or_evidence_consumers": consumers})
    result = {"kind": "voznativa.docs_inventory", "schema_version": 1, "documents": rows}
    for r in rows:
        print(f"{r['path']:<48} v{r['version'] or '-':<4} {r['words']:>6}w  links {len(r['linked_by']):>2}  "
              f"code/evidence {len(r['code_or_evidence_consumers']):>2}  {r['title'][:50]}")
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
