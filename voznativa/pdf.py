"""PDF with an honest scope: traceable extraction and annotated copies (v0.9 CP5, V09-GAP-13).

What this module does:

* **extract**: text per page with ``pypdf`` (optional dependency,
  ``pip install pypdf``), paragraphs rebuilt from lines, end-of-line
  hyphenation joined only when the joined word is used elsewhere in the
  document (otherwise kept and reported), typographic ligatures (ﬁ, ﬂ, ﬀ)
  normalised. Lines that look like display equations or code are
  **protected**: they are replaced in the text by a placeholder
  (``[[EQ-3-1]]``, ``[[CODE-5-2]]``) and listed with their original text, so
  nothing downstream can edit them silently. Every paragraph keeps its page.
* **annotate**: a *new* PDF with one sticky note per page that has
  suggestions; the original is never written.

What it does not do (reported in docs/releases/v0.9/DOCUMENTS.md): map
suggestions to word boxes, highlight words, rewrite or re-typeset the PDF,
read scanned pages (no OCR), recover reading order of multi-column layouts
reliably, or recognise inline math inside a sentence.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path

SCHEMA_VERSION = 1
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}
_MATH = re.compile(r"[=+−∑∫√∂∆∇≤≥≈≠±×÷∞∈∉⊂⊆∀∃λμσπθαβγΣΠΩ^_]")
# Code: a line ending in a brace or a semicolon, a keyword at the start followed by code punctuation, or
# operators prose does not use. A call at the end of a line ("(SILVA, 2020)") is not code.
_CODE = re.compile(r"(?:[{}]\s*$|;\s*$|^\s*(?:def|class|return|import|#include|//|/\*|void|int|float|double|"
                   r"public|private|static)\b.*[(){};=]|==|!=|->|::|\+\+|\w\[\w*\]\s*=)")


class PdfUnavailable(RuntimeError):
    """``pypdf`` is not installed."""


def _pypdf():
    try:
        import pypdf
    except ImportError as error:
        raise PdfUnavailable("PDF support needs the optional dependency pypdf: python -m pip install pypdf") \
            from error
    return pypdf


def _line_kind(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "blank"
    letters = sum(c.isalpha() for c in stripped)
    symbols = len(_MATH.findall(stripped))
    if symbols >= 2 and (symbols >= 4 or letters <= 2 * symbols) and len(stripped.split()) <= 14:
        return "equation"
    if _CODE.search(stripped) and not re.search(r"[.!?]\s*$", stripped):
        return "code"
    return "text"


def normalise(text: str) -> str:
    for lig, plain in LIGATURES.items():
        text = text.replace(lig, plain)
    return unicodedata.normalize("NFC", text)


def extract(path: str | Path) -> dict:
    """Intermediate representation of a PDF (no file is written)."""
    pypdf = _pypdf()
    path = Path(path)
    raw = path.read_bytes()
    try:
        reader = pypdf.PdfReader(str(path))
        if reader.is_encrypted:
            raise ValueError(f"{path.name}: encrypted PDF (decrypt it first; no password is tried)")
        pages = [normalise(page.extract_text() or "") for page in reader.pages]
    except ValueError:
        raise
    except Exception as error:  # noqa: BLE001 - pypdf raises many types on a malformed file
        raise ValueError(f"{path.name}: unreadable PDF ({type(error).__name__})") from None
    vocabulary = Counter(w.lower() for page in pages for w in re.findall(r"[^\W\d_]+", page))
    elements, protected, hyphen_kept, empty_pages = [], [], [], []
    for number, page_text in enumerate(pages, 1):
        if not page_text.strip():
            empty_pages.append(number)
            continue
        lines = page_text.splitlines()
        paragraph: list[str] = []
        counts = Counter()

        def flush():
            if paragraph:
                text = " ".join(paragraph).strip()
                text = re.sub(r"\s+", " ", text)
                if text:
                    elements.append({"id": f"pg{number}-p{len([e for e in elements if e['page'] == number])}",
                                     "page": number, "type": "paragraph", "text": text, "editable": True})
                paragraph.clear()

        for line in lines:
            kind = _line_kind(line)
            if kind == "blank":
                flush()
                continue
            if kind in ("equation", "code"):
                flush()
                counts[kind] += 1
                tag = f"[[{'EQ' if kind == 'equation' else 'CODE'}-{number}-{counts[kind]}]]"
                protected.append({"placeholder": tag, "page": number, "kind": kind, "text": line.strip()})
                elements.append({"id": tag.strip("[]"), "page": number, "type": kind, "text": tag, "editable": False})
                continue
            line = line.strip()
            if paragraph and paragraph[-1].endswith("-") and re.match(r"[a-zà-ú]", line):
                head = re.findall(r"[^\W\d_]+-$", paragraph[-1])
                tail = re.match(r"[^\W\d_]+", line)
                joined = (head[0][:-1] + tail.group(0)).lower() if head and tail else None
                if joined and vocabulary[joined] > 0:
                    paragraph[-1] = paragraph[-1][:-1] + line
                    continue
                if joined:
                    hyphen_kept.append({"page": number, "word": joined})
            paragraph.append(line)
            if re.search(r"[.!?:]\s*$", line) and len(line) < 60:
                flush()
        flush()
    return {"kind": "voznativa.document_ir", "schema_version": SCHEMA_VERSION,
            "source": {"format": "pdf", "file": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
                       "pages": len(pages)},
            "elements": elements, "protected": protected,
            "hyphenation_kept": hyphen_kept, "pages_without_text": empty_pages,
            "summary": {"pages": len(pages), "paragraphs": sum(e["type"] == "paragraph" for e in elements),
                        "protected": len(protected), "pages_without_text": len(empty_pages)},
            "limits": ["no word boxes: suggestions become page notes", "no OCR: scanned pages have no text",
                       "multi-column reading order follows the PDF's text order",
                       "inline math inside a sentence is not recognised"]}


def to_text(ir: dict) -> str:
    """Paragraphs as blocks; protected lines stay as their placeholders."""
    return "\n\n".join(e["text"] for e in ir["elements"]) + "\n"


def annotate(source: str | Path, notes: list[dict], output: str | Path, overwrite: bool = False) -> dict:
    """A new PDF with one sticky note per page listed in ``notes``
    (``[{"page": 3, "text": "..."}]``, pages from 1)."""
    pypdf = _pypdf()
    from pypdf.annotations import Text
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError("the output must be a new file; the original is never written")
    if output.exists() and not overwrite:
        raise ValueError(f"{output.name} already exists")
    reader = pypdf.PdfReader(str(source))
    writer = pypdf.PdfWriter(clone_from=reader)
    by_page: dict[int, list[str]] = {}
    for note in notes:
        page = int(note["page"])
        if not 1 <= page <= len(reader.pages):
            raise ValueError(f"page {page} does not exist (1-{len(reader.pages)})")
        by_page.setdefault(page, []).append(str(note["text"]))
    for page, texts in sorted(by_page.items()):
        box = reader.pages[page - 1].mediabox
        rect = (float(box.left) + 10, float(box.top) - 40, float(box.left) + 30, float(box.top) - 20)
        writer.add_annotation(page - 1, Text(rect=rect, text="\n\n".join(texts), open=False))
    tmp = output.with_name(output.name + ".tmp")
    with open(tmp, "wb") as fh:
        writer.write(fh)
    shutil.move(str(tmp), str(output))
    return {"output": output.name, "pages_annotated": sorted(by_page), "notes": len(notes)}
