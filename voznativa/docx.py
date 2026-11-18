"""Safe DOCX workflow: extract, rewrite a copy, check (v0.9 CP5, V09-GAP-13).

Scope, stated before the code (docs/releases/v0.9/DOCUMENTS.md):

* **Read** ``word/document.xml`` into an intermediate representation
  (``voznativa.document_ir``): one element per paragraph of the body,
  including table cells, with an id, its type (heading, paragraph, list
  item, table cell), its text, whether it is editable, and the sha256 of its
  XML. Headers, footers, footnotes, comments and every other part are listed
  and left untouched.
* **Editable** means: the paragraph's children are only properties,
  runs and spell-check marks, and every run holds only text with the same
  formatting. A paragraph with a hyperlink, field, tab, line break, image,
  footnote reference, equation, text box, bookmark, tracked change or mixed
  formatting is **protected**, with the reason. Nothing unknown is edited.
* **Apply** writes a *new* file and never opens the original for writing.
  Only the XML text of the edited paragraphs changes (their properties and
  the first run's formatting are kept; the text becomes one run). Every other
  byte of ``document.xml`` and every other part of the package is copied as
  is. No XML library re-serialises the document: the standard library's
  ElementTree renames namespace prefixes, which breaks ``mc:Ignorable`` and
  makes Word report a corrupt file.
* **Check** compares the original and the new package: same parts, same
  bytes outside ``document.xml``, same paragraphs, protected paragraphs
  byte-identical, well-formed XML. Byte identity of the ZIP container itself
  is not claimed (compression and timestamps are rewritten); each part is
  compared by content.

Not supported (reported, never silently changed): tracked changes,
comments, text in headers/footers/footnotes/text boxes, equations, fields,
rich formatting inside a paragraph.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape, unescape

SCHEMA_VERSION = 1
DOCUMENT = "word/document.xml"
_TAG = re.compile(r"<(/?)([\w:]+)([^>]*?)(/?)>", re.S)
_HEADING = re.compile(r"(?i)^(?:heading|ttulo|titulo|título|title)\s*\d*$")
_RUN = re.compile(r"<w:r(?:\s[^>]*)?>(.*?)</w:r>", re.S)
_RPR = re.compile(r"<w:rPr>.*?</w:rPr>|<w:rPr/>", re.S)
_TEXT = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>|<w:t\s*/>", re.S)
# Children of a run that only carry text (anything else protects the paragraph).
_RUN_TEXT_ONLY = re.compile(r"^(?:\s*(?:<w:rPr>.*?</w:rPr>|<w:rPr/>|<w:t(?:\s[^>]*)?>.*?</w:t>|<w:t\s*/>|"
                            r"<w:lastRenderedPageBreak/>))*\s*$", re.S)
_PROTECTING = (("w:hyperlink", "hyperlink"), ("w:fldSimple", "field"), ("w:fldChar", "field"),
               ("w:instrText", "field"), ("w:tab", "tab"), ("w:br", "line break"), ("w:drawing", "image"),
               ("w:pict", "image"), ("w:object", "object"), ("w:footnoteReference", "footnote reference"),
               ("w:endnoteReference", "endnote reference"), ("m:oMath", "equation"), ("w:txbxContent", "text box"),
               ("mc:AlternateContent", "alternate content"), ("w:bookmarkStart", "bookmark"),
               ("w:ins", "tracked change"), ("w:del", "tracked change"), ("w:moveFrom", "tracked change"),
               ("w:moveTo", "tracked change"), ("w:commentRangeStart", "comment"), ("w:sym", "symbol"),
               ("w:smartTag", "smart tag"), ("w:sdt", "content control"))


class DocxError(ValueError):
    """The file is not a DOCX this module can handle, or an edit is unsafe."""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_document(path: Path) -> tuple[str, list[str]]:
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if DOCUMENT not in names:
                raise DocxError(f"{path.name}: no {DOCUMENT} (not a Word document)")
            return z.read(DOCUMENT).decode("utf-8"), names
    except zipfile.BadZipFile as error:
        raise DocxError(f"{path.name}: not a ZIP package ({error})") from None


def _paragraph_spans(xml: str) -> list[dict]:
    """Outermost ``w:p`` elements with their offsets, nesting context and inner XML."""
    spans, stack = [], []          # stack of (tag, start)
    for m in _TAG.finditer(xml):
        closing, tag, _, selfclosing = m.group(1), m.group(2), m.group(3), m.group(4)
        if tag not in ("w:p", "w:tbl", "w:tc", "w:txbxContent"):
            continue
        if selfclosing:
            if tag == "w:p" and not any(t == "w:p" for t, _ in stack):
                spans.append({"start": m.start(), "end": m.end(), "in_table": any(t == "w:tbl" for t, _ in stack),
                              "nested": False})
            continue
        if not closing:
            stack.append((tag, m.start()))
            continue
        while stack and stack[-1][0] != tag:
            stack.pop()
        if not stack:
            continue
        _, start = stack.pop()
        if tag == "w:p" and not any(t == "w:p" for t, _ in stack):
            inner = xml[start:m.end()]
            spans.append({"start": start, "end": m.end(), "in_table": any(t == "w:tbl" for t, _ in stack),
                          "nested": inner.count("<w:p ") + inner.count("<w:p>") > 1})
    return sorted(spans, key=lambda s: s["start"])


def _analyse(xml_p: str) -> dict:
    body = "" if re.fullmatch(r"<w:p(?:\s[^>]*)?/>", xml_p.strip()) else \
        re.sub(r"^<w:p(?:\s[^>]*)?>|</w:p>$", "", xml_p, flags=re.S)
    p_pr = re.match(r"\s*(<w:pPr>.*?</w:pPr>|<w:pPr/>)", body, re.S)
    p_pr_xml = p_pr.group(1) if p_pr else ""
    style = re.search(r'<w:pStyle w:val="([^"]*)"', p_pr_xml)
    numbered = "<w:numPr>" in p_pr_xml
    # the tag name must end there: "<w:ins" is not "<w:instrText"
    reasons = sorted({label for tag, label in _PROTECTING if re.search(rf"<{tag}[\s/>]", body)})
    specific = bool(reasons)
    rest = body[p_pr.end():] if p_pr else body
    runs = list(_RUN.finditer(rest))
    leftover = _RUN.sub("", rest)
    leftover = re.sub(r"<w:proofErr[^>]*/>", "", leftover).strip()
    if leftover:
        reasons.append("unknown content")
    text_parts, formats = [], set()
    for r in runs:
        inner = r.group(1)
        if not _RUN_TEXT_ONLY.match(inner):
            reasons.append("non-text run")
        rpr = _RPR.search(inner)
        formats.add(rpr.group(0) if rpr else "")
        for t in _TEXT.finditer(inner):
            text_parts.append(unescape(t.group(1) or "", {"&quot;": '"', "&apos;": "'"}))
    if len(formats) > 1:
        reasons.append("mixed formatting")
    if specific:      # a named reason already explains the generic ones
        reasons = [r for r in reasons if r not in ("unknown content", "non-text run")]
    text = "".join(text_parts)
    if not text.strip():
        reasons.append("no text")
    return {"text": text, "style": style.group(1) if style else None, "numbered": numbered,
            "reasons": sorted(set(reasons)), "p_pr": p_pr_xml,
            "first_rpr": next(iter(sorted(formats))) if len(formats) == 1 else ""}


def extract(path: str | Path) -> dict:
    """The intermediate representation of a DOCX (no file is written)."""
    path = Path(path)
    raw = path.read_bytes()
    xml, names = _read_document(path)
    elements = []
    for n, span in enumerate(_paragraph_spans(xml)):
        xml_p = xml[span["start"]:span["end"]]
        info = _analyse(xml_p)
        reasons = list(info["reasons"])
        if span["nested"]:
            reasons.append("nested paragraphs")
        kind = ("table_cell" if span["in_table"] else
                "heading" if info["style"] and _HEADING.match(info["style"]) else
                "list_item" if info["numbered"] else "paragraph")
        elements.append({"id": f"p{n}", "type": kind, "style": info["style"], "text": info["text"],
                         "editable": not reasons, "protected_reasons": sorted(set(reasons)),
                         "sha256": _sha(xml_p)})
    return {"kind": "voznativa.document_ir", "schema_version": SCHEMA_VERSION,
            "source": {"format": "docx", "file": path.name, "sha256": hashlib.sha256(raw).hexdigest()},
            "parts": sorted(names), "edited_part": DOCUMENT,
            "untouched_parts": sorted(n for n in names if n != DOCUMENT),
            "elements": elements,
            "summary": {"paragraphs": len(elements), "editable": sum(e["editable"] for e in elements),
                        "protected": sum(not e["editable"] for e in elements)}}


def _new_paragraph(xml_p: str, info: dict, text: str) -> str:
    open_tag = re.match(r"<w:p(?:\s[^>]*)?>", xml_p).group(0)
    attr = ' xml:space="preserve"' if text != text.strip() or "  " in text else ""
    run = f"<w:r>{info['first_rpr']}<w:t{attr}>{escape(text)}</w:t></w:r>"
    return f"{open_tag}{info['p_pr']}{run}</w:p>"


def apply(source: str | Path, edits: dict[str, str], output: str | Path, overwrite: bool = False) -> dict:
    """Write ``output``: ``source`` with the text of the listed editable
    paragraphs replaced. ``edits`` maps element id -> new text. Refuses to
    write over the source, over an existing file (unless ``overwrite``), to
    edit a protected paragraph, or to put a line break inside a paragraph."""
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise DocxError("the output must be a new file; the original is never written")
    if output.exists() and not overwrite:
        raise DocxError(f"{output.name} already exists")
    xml, _ = _read_document(source)
    spans = _paragraph_spans(xml)
    by_id = {f"p{n}": s for n, s in enumerate(spans)}
    replaced = []
    for pid, text in edits.items():
        if pid not in by_id:
            raise DocxError(f"unknown element {pid}")
        if not isinstance(text, str) or not text.strip() or "\n" in text or "\r" in text:
            raise DocxError(f"{pid}: the new text must be one non-empty line (a paragraph)")
        span = by_id[pid]
        xml_p = xml[span["start"]:span["end"]]
        info = _analyse(xml_p)
        if info["reasons"] or span["nested"]:
            raise DocxError(f"{pid} is protected ({', '.join(info['reasons'] or ['nested paragraphs'])})")
        if text != info["text"]:
            replaced.append((span["start"], span["end"], _new_paragraph(xml_p, info, text), pid))
    new_xml = xml
    for start, end, new, _ in sorted(replaced, reverse=True):
        new_xml = new_xml[:start] + new + new_xml[end:]
    try:
        ElementTree.fromstring(new_xml.encode("utf-8"))
    except ElementTree.ParseError as error:          # pragma: no cover - escape() makes this unreachable
        raise DocxError(f"the edited document.xml is not well-formed: {error}") from None
    tmp = output.with_name(output.name + ".tmp")
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for item in zin.infolist():
            data = new_xml.encode("utf-8") if item.filename == DOCUMENT else zin.read(item.filename)
            zout.writestr(item, data, compress_type=item.compress_type)
    shutil.move(str(tmp), str(output))
    return {"output": output.name, "edited": sorted(pid for *_, pid in replaced),
            "unchanged_edits": sorted(set(edits) - {pid for *_, pid in replaced})}


def check(original: str | Path, candidate: str | Path, allowed: list[str] | None = None) -> dict:
    """Integrity of a rewritten copy against its original. ``allowed`` lists
    the element ids that were meant to change (default: any editable one)."""
    original, candidate = Path(original), Path(candidate)
    problems = []
    with zipfile.ZipFile(original) as a, zipfile.ZipFile(candidate) as b:
        names_a, names_b = sorted(a.namelist()), sorted(b.namelist())
        if names_a != names_b:
            problems.append(f"parts differ: {sorted(set(names_a) ^ set(names_b))}")
        for name in sorted(set(names_a) & set(names_b)):
            if name != DOCUMENT and a.read(name) != b.read(name):
                problems.append(f"part changed: {name}")
        xml_a, xml_b = a.read(DOCUMENT).decode("utf-8"), b.read(DOCUMENT).decode("utf-8")
    for label, xml in (("original", xml_a), ("candidate", xml_b)):
        try:
            ElementTree.fromstring(xml.encode("utf-8"))
        except ElementTree.ParseError as error:
            problems.append(f"{label} document.xml is not well-formed: {error}")
    spans_a, spans_b = _paragraph_spans(xml_a), _paragraph_spans(xml_b)
    if len(spans_a) != len(spans_b):
        problems.append(f"paragraph count {len(spans_a)} -> {len(spans_b)}")
    changed = []
    gaps_equal = True
    for n, (sa, sb) in enumerate(zip(spans_a, spans_b)):
        pa, pb = xml_a[sa["start"]:sa["end"]], xml_b[sb["start"]:sb["end"]]
        if pa == pb:
            continue
        pid = f"p{n}"
        changed.append(pid)
        if _analyse(pa)["reasons"] or sa["nested"]:
            problems.append(f"{pid} was protected and changed")
        elif allowed is not None and pid not in allowed:
            problems.append(f"{pid} changed without being listed")
    # Everything between paragraphs (section properties, tables' grid and cell properties...) is identical.
    def gaps(xml, spans):
        out, cursor = [], 0
        for s in spans:
            out.append(xml[cursor:s["start"]])
            cursor = s["end"]
        return out + [xml[cursor:]]
    if len(spans_a) == len(spans_b) and gaps(xml_a, spans_a) != gaps(xml_b, spans_b):
        gaps_equal = False
        problems.append("XML outside the paragraphs changed")
    return {"kind": "voznativa.docx_check", "schema_version": SCHEMA_VERSION, "status": "PASS" if not problems else "FAIL",
            "changed_paragraphs": changed, "parts": len(names_a), "outside_paragraphs_identical": gaps_equal,
            "problems": problems,
            "note": "content compared part by part; the ZIP container itself is rewritten (timestamps, compression)"}


def to_text(ir: dict) -> tuple[str, list[str]]:
    """Text for the long-form engine: editable paragraphs and list items as blocks,
    headings as '## ' lines for context (their changes are never applied). Returns
    the text and the element id of each block, in order."""
    blocks, ids = [], []
    for e in ir["elements"]:
        if e["type"] == "heading" and e["text"].strip():
            blocks.append("## " + " ".join(e["text"].split()))
            ids.append("#" + e["id"])
        elif e["editable"] and e["type"] in ("paragraph", "list_item"):
            blocks.append(" ".join(e["text"].split()))
            ids.append(e["id"])
    return "\n\n".join(blocks) + "\n", ids


def from_text(ir: dict, ids: list[str], text: str) -> dict[str, str]:
    """Map a rewritten text back to element edits. The block count must match;
    headings are skipped. Raises ``DocxError`` when the structure changed."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    if len(blocks) != len(ids):
        raise DocxError(f"the rewrite has {len(blocks)} blocks, the document {len(ids)}: nothing is applied")
    original = {e["id"]: e["text"] for e in ir["elements"]}
    edits = {}
    for pid, block in zip(ids, blocks):
        if pid.startswith("#"):
            continue
        new = " ".join(block.split())
        if new != " ".join(original[pid].split()):
            edits[pid] = new
    return edits
