#!/usr/bin/env python3
"""Privacy gate for a range of commits that is about to be pushed (v0.9 CP0).

The v0.8.1 round published, and later removed, a five-word fragment of a
private document. This gate is the check that has to pass *before* a push.
It never pushes anything itself: run it, read the verdict, then push as a
separate command.

    python scripts/privacy_gate.py --base origin/main --head HEAD \
        --private /outside/the/repo/doc.pdf --private /outside/other.docx \
        --terms-file /outside/the/repo/terms.txt --out /tmp/privacy.json

What it scans, for every commit in ``BASE..HEAD``:

* the added lines of **each commit's patch** (a line added and removed again
  before the push is still published inside the first commit) and the commit
  messages (author and committer lines too, so a wrong identity is caught
  before it is public);
* with ``--tree``, every tracked text file at HEAD as well (the whole
  history to be integrated, not only the last diff).

What it looks for:

* **private documents** (``--private``, PDF/DOCX/TXT/MD; read in memory,
  never copied): shared word 5-grams, and distinctive tokens of the document
  (long numbers, all-caps identifiers, camelCase, snake_case) that do not
  already occur in the repository at BASE;
* **sensitive terms** (``--terms-file``, one per line: names, ids,
  institution-specific words), matched case-insensitively on word boundaries;
* **credentials** (the patterns of ``voznativa.redact``);
* **personal paths and addresses**: ``C:\\Users\\<name>``, ``/home/<name>``,
  ``/Users/<name>`` and e-mail addresses other than GitHub noreply ones.

The private documents and the terms list must live outside the repository;
the report records counts and the matches themselves only for paths and
credentials found in the public diff (so the report is safe to read), and
for document matches the shared 5-grams (already in the public diff by
definition). Exit 0 PASS, 1 FINDINGS, 2 usage error (a file cannot be read,
a private input lives inside the repository).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:  # in-repo package importable when run from a checkout
    sys.path.insert(0, str(ROOT))
from voznativa.redact import SECRET_VALUES  # noqa: E402
WORD = re.compile(r"[\wÀ-ÿ]+")
DISTINCT = re.compile(r"\b(?:\d{3,}(?:[.,]\d+)?|\d+,\d+|[A-ZÀ-Ú][A-ZÀ-Ú0-9_]{2,}|[a-z]+_[A-Za-z]+|[A-Z][a-z]+[A-Z]\w*)\b")
PERSONAL_PATH = re.compile(r"(?i)(?:[A-Z]:[\\/]+Users[\\/]+|/home/|/Users/)(?!<)([A-Za-z0-9._-]+)")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Addresses that are public by design (placeholders and GitHub noreply identities).
EMAIL_OK = re.compile(r"(?i)@(?:users\.noreply\.github\.com|example\.(?:com|org|net)|anthropic\.com)$|^noreply@")
# Path owners that are not personal (CI runners, generic placeholders).
PATH_OK = {"runner", "runneradmin", "user", "usuario", "usuário", "username", "you", "me", "name", "nome",
           "public", "default", "shared", "<user>", "voce", "você", "fulano", "alice", "bob"}


def git(*args: str, repo: Path | None = None) -> str:
    done = subprocess.run(["git", "-C", str(repo or ROOT), *args], capture_output=True)
    if done.returncode != 0:
        raise SystemExit(f"privacy_gate: git {' '.join(args)} failed: {done.stderr.decode('utf-8', 'replace').strip()}")
    return done.stdout.decode("utf-8", "replace")


def read_private(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = " ".join(z.read(n).decode("utf-8", "replace") for n in z.namelist()
                           if n.startswith("word/") and n.endswith(".xml"))
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", "", xml)
    if suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
            return "\n".join(page.get_text() for page in fitz.open(str(path)))
        except ImportError:
            try:
                from pypdf import PdfReader
            except ImportError as error:  # pragma: no cover - environment dependent
                raise SystemExit("privacy_gate: reading a PDF needs PyMuPDF or pypdf") from error
            return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="replace")


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def grams(ws: list[str], n: int = 5) -> set[str]:
    return {" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def public_text(base: str, head: str, tree: bool) -> tuple[dict, str]:
    commits = [c for c in git("rev-list", f"{base}..{head}").split() if c]
    # The patch of every commit, not the net diff: a line added in one commit and
    # removed in the next is absent from base..head but still published with the push.
    added = [line[1:] for line in git("log", "-p", "--no-color", "--format=", f"{base}..{head}").splitlines()
             if line.startswith("+") and not line.startswith("+++")]
    meta = git("log", f"{base}..{head}", "--format=%an <%ae>%n%cn <%ce>%n%B")
    parts = added + meta.splitlines()
    tree_files = 0
    if tree:
        for name in git("ls-files", "-z").split("\0"):
            p = ROOT / name
            if not name or not p.is_file() or p.stat().st_size > 2_000_000:
                continue
            raw = p.read_bytes()
            if b"\0" in raw[:4096]:
                continue
            parts.append(raw.decode("utf-8", "replace"))
            tree_files += 1
    return {"commits": len(commits), "added_lines": len(added), "tree_files": tree_files}, "\n".join(parts)


_NUMBER = re.compile(r"[\d.,]+")
_NEIGHBOUR = re.compile(r"[^\W\d_]{2,}")


def _neighbours(text: str, token: str) -> set[str]:
    """Words right before and after each occurrence of ``token`` (lower case)."""
    out = set()
    for m in re.finditer(rf"(?<![\w.,]){re.escape(token)}(?!\w)", text):
        before = _NEIGHBOUR.findall(text[max(0, m.start() - 40):m.start()])
        after = _NEIGHBOUR.findall(text[m.end():m.end() + 40])
        out |= {w.lower() for w in before[-1:] + after[:1]}
    return out


def _shared(token: str, doc: str, public: str) -> bool:
    """A distinctive token of the private document appears in the public text. v0.10.5 (V105-GAP-04): a bare
    number ("2,60", "4417") counts only next to a word that is also next to it in the document; numbers are
    common, so a number alone in a regex quantifier or a word count is not evidence of a leak. Tokens with
    letters (identifiers, acronyms) keep the presence rule."""
    if not re.search(rf"(?<![\w.,]){re.escape(token)}(?!\w)", public):
        return False
    if not _NUMBER.fullmatch(token):
        return True
    return bool(_neighbours(doc, token) & _neighbours(public, token))


def scan(public: str, base: str, privates: list[Path], terms: list[str]) -> dict:
    findings: dict[str, list] = {}
    pub_words = words(public)
    pub_grams = grams(pub_words)
    base_text = git("grep", "-h", "-I", "-e", ".", base, "--", ".").lower() if privates else ""
    for path in privates:
        doc = re.sub(r"-\n(?=[a-zà-ú])", "", read_private(path)).replace("\n", " ")
        shared = sorted(pub_grams & grams(words(doc)))
        tokens = {t for t in DISTINCT.findall(doc) if t.lower() not in base_text}
        distinct = sorted(t for t in tokens if _shared(t, doc, public))
        if shared:
            findings.setdefault("private_5grams", []).append({"document": path.name, "count": len(shared),
                                                              "shared": shared[:50]})
        if distinct:
            # The tokens are distinctive of a private document; report how many, not which.
            findings.setdefault("private_tokens", []).append({"document": path.name, "count": len(distinct)})
    term_hits = 0
    for term in terms:
        if re.search(rf"(?i)(?<!\w){re.escape(term)}(?!\w)", public):
            term_hits += 1
    if term_hits:
        findings["sensitive_terms"] = [{"count": term_hits}]
    secrets = sorted({m.group(0)[:12] + "…" for pat in SECRET_VALUES for m in pat.finditer(public)})
    if secrets:
        findings["credentials"] = secrets
    paths = sorted({m.group(0) for m in PERSONAL_PATH.finditer(public) if m.group(1).lower() not in PATH_OK})
    if paths:
        findings["personal_paths"] = paths
    mails = sorted({m.group(0) for m in EMAIL.finditer(public) if not EMAIL_OK.search(m.group(0))})
    if mails:
        findings["emails"] = mails
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True, help="last published revision (e.g. origin/main)")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--private", action="append", default=[], help="private document outside the repository")
    ap.add_argument("--terms-file", help="sensitive terms, one per line, outside the repository")
    ap.add_argument("--tree", action="store_true", help="also scan every tracked text file at HEAD")
    ap.add_argument("--allow", action="append", default=[],
                    help="exact finding string accepted after review (path/e-mail already public)")
    ap.add_argument("--out", help="write the JSON report here")
    args = ap.parse_args(argv)

    privates = [Path(p).resolve() for p in args.private]
    inputs = privates + ([Path(args.terms_file).resolve()] if args.terms_file else [])
    for p in inputs:
        if not p.is_file():
            print(f"privacy_gate: cannot read {p.name}", file=sys.stderr)
            return 2
        # Both sides resolved: on Windows a short 8.3 path (C:\Users\RUNNER~1\...) and its long form are
        # the same folder, and comparing a resolved file with an unresolved root missed it (CI #129).
        if ROOT.resolve() in p.parents:
            print(f"privacy_gate: {p.name} lives inside the repository; private inputs must stay outside",
                  file=sys.stderr)
            return 2
    terms = []
    if args.terms_file:
        terms = [t.strip() for t in Path(args.terms_file).read_text(encoding="utf-8").splitlines()
                 if t.strip() and not t.startswith("#")]

    scope, public = public_text(args.base, args.head, args.tree)
    findings = scan(public, args.base, privates, terms)
    allowed = set(args.allow)
    for key in ("personal_paths", "emails"):
        if key in findings:
            findings[key] = [f for f in findings[key] if f not in allowed]
            if not findings[key]:
                del findings[key]
    verdict = "FINDINGS" if findings else "PASS"
    report = {"tool": "privacy_gate", "base": git("rev-parse", args.base).strip(),
              "head": git("rev-parse", args.head).strip(), **scope,
              "private_documents": len(privates), "terms": len(terms), "tree": args.tree,
              "findings": findings, "verdict": verdict}
    text = json.dumps(report, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
