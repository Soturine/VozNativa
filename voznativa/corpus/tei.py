"""TEI P5 / XML reader (v0.7.0 CP2): safe, metadata-preserving, structure-aware.

Safety (a corpus file is untrusted data):

* any ``<!DOCTYPE`` or ``<!ENTITY`` is refused before parsing, so neither
  external entities (XXE) nor entity expansion bombs can be reached; TEI P5
  documents do not need a DTD;
* the whole document is read through the capped stream of
  ``connectors.open_text`` (size and decompression-ratio limits) and then
  checked against ``max_bytes`` here;
* processing instructions and comments are ignored; nothing is executed.

What is kept, per ``<TEI>`` document (a ``<teiCorpus>`` yields one record per
member): title, author(s), dates (``when`` or text), edition, ``idno``,
licence (``availability/licence@target`` and text, normalised to a code by
``policy.license_from_url``), typology (``textClass`` terms, ``catRef``,
``classCode``), language, and the counts of structural elements.

The text is rebuilt with the structure that matters downstream: blocks
(paragraph, heading, utterance, quote, list item) separated by a blank line,
verse lines (``<l>``) one per line inside their ``<lg>``. Notes are kept out
of the running text and counted. The original bytes are never modified;
``meta["structure"]`` says what was found, so a dropped element is visible.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from .connectors import AccessError
from .policy import license_from_url

FORBIDDEN = re.compile(rb"<!\s*(?:DOCTYPE|ENTITY)", re.I)
BLOCKS = {"p", "head", "u", "quote", "item", "ab", "speaker", "stage", "closer", "opener", "salute", "signed",
          "byline", "dateline", "trailer"}
VERSE_GROUP, VERSE_LINE = "lg", "l"
SKIP = {"note", "teiHeader", "fw", "figDesc", "interp"}


def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _find(el, *path):
    """First descendant following local names (namespace-agnostic)."""
    current = [el]
    for name in path:
        current = [c for parent in current for c in parent.iter() if _local(c.tag) == name and c is not parent]
        if not current:
            return None
    return current[0]


def _all(el, name):
    return [c for c in el.iter() if _local(c.tag) == name] if el is not None else []


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def _attr(el, name):
    if el is None:
        return None
    for key, value in el.attrib.items():
        if key == name or key.endswith("}" + name):
            return value
    return None


def header_meta(tei) -> dict:
    header = _find(tei, "teiHeader")
    meta: dict = {}
    if header is None:
        return {"header": "missing"}
    title_stmt = _find(header, "titleStmt")
    meta["title"] = _text(_find(title_stmt, "title")) if title_stmt is not None else None
    authors = [_text(a) for a in _all(title_stmt, "author")] or [_text(a) for a in _all(_find(header, "sourceDesc"), "author")]
    meta["authors"] = [a for a in authors if a]
    meta["edition"] = _text(_find(header, "editionStmt")) or None
    idno = _find(header, "idno")
    meta["idno"] = _text(idno) or None
    dates = []
    for d in _all(_find(header, "sourceDesc"), "date") + _all(_find(header, "publicationStmt"), "date"):
        value = _attr(d, "when") or _attr(d, "notBefore") or _text(d)
        if value:
            dates.append(value)
    meta["dates"] = dates[:5]
    availability = _find(header, "availability")
    licence = _find(availability, "licence") if availability is not None else None
    target = _attr(licence, "target")
    meta["licence"] = {"target": target, "text": _text(licence)[:300] or None,
                       "status": _attr(availability, "status"),
                       "code": license_from_url(target) if target else ("unknown" if availability is not None
                                                                      else "not_stated")}
    text_class = _find(header, "textClass")
    terms = [_text(t) for t in _all(text_class, "term")]
    terms += [_attr(c, "target") for c in _all(text_class, "catRef") if _attr(c, "target")]
    terms += [_text(c) for c in _all(text_class, "classCode")]
    meta["typology"] = [t for t in terms if t][:20]
    language = _find(header, "language")
    meta["language"] = _attr(language, "ident")
    return meta


def body_text(tei) -> tuple[str, dict]:
    """Running text with structural separators, and counts of what was seen."""
    text_el = next((c for c in tei if _local(c.tag) == "text"), None)
    if text_el is None:   # Element truthiness counts children; compare with None explicitly
        text_el = _find(tei, "text")
    counts: dict[str, int] = {}
    blocks: list[str] = []
    if text_el is None:
        return "", {"text": 0}

    def walk(el):
        name = _local(el.tag)
        if name in SKIP:
            counts[name] = counts.get(name, 0) + 1
            return
        if name == VERSE_GROUP:
            lines = [_text(line) for line in el.iter() if _local(line.tag) == VERSE_LINE]
            counts["lg"] = counts.get("lg", 0) + 1
            counts["l"] = counts.get("l", 0) + len(lines)
            if any(lines):
                blocks.append("\n".join(x for x in lines if x))
            return
        if name in BLOCKS or (name == VERSE_LINE):
            counts[name] = counts.get(name, 0) + 1
            value = _text_without_notes(el, counts)
            if value:
                blocks.append(value)
            return
        for child in el:
            walk(child)

    walk(text_el)
    return "\n\n".join(blocks), counts


def _text_without_notes(el, counts) -> str:
    parts = [el.text or ""]
    for child in el:
        if _local(child.tag) in SKIP:
            counts[_local(child.tag)] = counts.get(_local(child.tag), 0) + 1
        else:
            parts.append(_text_without_notes(child, counts))
        parts.append(child.tail or "")
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def read_tei(stream, errors: list[dict], max_bytes: int):
    """Yield (record_id, text, meta) per TEI document in the stream."""
    data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise AccessError("too_large", f"XML document larger than {max_bytes} bytes")
    if FORBIDDEN.search(data):
        raise AccessError("unsafe_xml", "DOCTYPE/ENTITY declarations are refused (XXE and expansion bombs)")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise AccessError("malformed", f"XML: {error}") from error
    if _local(root.tag) == "teiCorpus":
        documents = [c for c in root if _local(c.tag) in {"TEI", "teiCorpus"}]
    elif _local(root.tag) == "TEI":
        documents = [root]
    else:
        raise AccessError("malformed", f"root element <{_local(root.tag)}> is neither TEI nor teiCorpus")
    for index, tei in enumerate(documents):
        meta = header_meta(tei)
        text, counts = body_text(tei)
        meta["structure"] = counts
        record_id = _attr(tei, "id") or meta.get("idno") or f"doc-{index}"
        if not text:
            errors.append({"record": record_id, "error": "TEI document without running text"})
            continue
        yield record_id, text, meta
