"""Text primitives shared by every VozNativa component.

Everything here is deterministic and stdlib-only so the semantic layer runs in
any agent sandbox without installing packages.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

WORD_RE = re.compile(r"\w+(?:[-'’]\w+)*", re.UNICODE)

# Abbreviations that end with a period but rarely end a sentence.
ABBREVIATIONS = frozenset({
    "dr", "dra", "drs", "sr", "sra", "srta", "srs", "prof", "profa", "eng", "adv",
    "jr", "sto", "sta", "av", "r", "art", "arts", "inc", "cap", "fig", "tab", "vol",
    "pág", "pag", "pp", "p", "ex", "obs", "aprox", "máx", "max", "mín", "min", "nº",
    "n", "no", "ltda", "cia", "vs", "séc", "sec", "ed", "op", "cit", "tel", "cel",
})

STOPWORDS = frozenset({
    "a", "à", "às", "ao", "aos", "as", "o", "os", "um", "uma", "uns", "umas", "de", "da",
    "das", "do", "dos", "em", "na", "nas", "no", "nos", "num", "numa", "por", "pela",
    "pelas", "pelo", "pelos", "para", "pra", "pro", "com", "e", "ou", "que", "se", "é",
    "ser", "foi", "são", "era", "está", "estão", "estar", "ter", "tem", "têm", "isso",
    "isto", "esse", "essa", "este", "esta", "aquele", "aquela", "eu", "tu", "ele", "ela",
    "nós", "vocês", "eles", "elas", "você", "lhe", "me", "te", "nos", "vos", "seu", "sua",
    "seus", "suas", "meu", "minha", "nosso", "nossa", "já", "também", "mas", "como",
    "mais", "muito", "bem", "lá", "aqui", "então", "quando", "onde", "qual", "quais",
    "há", "vai", "vão", "ainda", "sobre", "entre", "até", "sem", "após", "depois", "antes",
})


def fold(text: str) -> str:
    """Lower-case and strip diacritics ("Não" -> "nao") for robust matching."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_surface(text: str) -> str:
    """Normalize differences that change neither meaning nor rendering: quote
    glyphs, NBSP, CRLF, runs of spaces inside a line, trailing spaces and
    repeated blank lines.

    Line breaks are kept: collapsing them would merge paragraphs and turn a
    Markdown list into one line, which is a real change.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ").replace(" ", " ")
    text = re.sub(r"[“”«»„]", '"', text)
    text = re.sub(r"[‘’‚]", "'", text)
    lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def contains_word(text: str, phrase: str) -> bool:
    """Whole-word, case-insensitive containment ("Ana" is not in "banana")."""
    if not phrase:
        return False
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.IGNORECASE) is not None


def words(text: str) -> list[str]:
    return WORD_RE.findall(text)


_SUFFIXES = ("amente", "mente", "ções", "coes", "ção", "cao", "ando", "endo", "indo", "ados", "idos",
             "adas", "idas", "ado", "ido", "ada", "ida", "ar", "er", "ir", "s")


def stem(token: str) -> str:
    """Crude stem used only for overlap estimates, never for meaning: strip one
    common inflectional/derivational suffix, then keep a 5-letter prefix
    ("validação"/"validar" -> "valid", "causar"/"causa" -> "causa")."""
    folded = fold(token)
    for suffix in _SUFFIXES:
        if folded.endswith(suffix) and len(folded) - len(suffix) >= 4:
            folded = folded[: -len(suffix)]
            break
    return folded[:5]


def content_stems(text: str) -> list[str]:
    return [stem(t) for t in words(text) if fold(t) not in _FOLDED_STOPWORDS and len(t) > 2]


_FOLDED_STOPWORDS = frozenset(fold(w) for w in STOPWORDS)


@dataclass(frozen=True)
class Sentence:
    index: int
    start: int
    end: int
    text: str
    paragraph: int
    kind: str = "prose"  # prose | list_item | heading | code


_LIST_RE = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+")
_HEADING_RE = re.compile(r"^\s*#{1,6}\s+")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_BOUNDARY_RE = re.compile(r"([.!?…]+)([\"'”»)\]]*)(\s+)")


def _blocks(text: str):
    """Yield (start, end, kind, paragraph) blocks: fenced code, list items, headings, paragraphs."""
    lines = text.splitlines(keepends=True)
    offset = 0
    paragraph = 0
    para_start = None
    para_end = None
    in_fence = None
    fence_start = 0

    def flush():
        nonlocal para_start, para_end, paragraph
        if para_start is not None:
            yield (para_start, para_end, "prose", paragraph)
            paragraph += 1
        para_start = para_end = None

    for line in lines:
        start, end = offset, offset + len(line)
        offset = end
        stripped = line.strip()
        if in_fence is not None:
            if stripped.startswith(in_fence):
                yield (fence_start, end, "code", paragraph)
                paragraph += 1
                in_fence = None
            continue
        fence = _FENCE_RE.match(line)
        if fence:
            yield from flush()
            in_fence = fence.group(1)
            fence_start = start
            continue
        if not stripped:
            yield from flush()
            continue
        if _LIST_RE.match(line) or _HEADING_RE.match(line):
            yield from flush()
            yield (start, end, "list_item" if _LIST_RE.match(line) else "heading", paragraph)
            continue
        if para_start is None:
            para_start = start
        para_end = end
    if in_fence is not None:  # unterminated fence: treat the rest as code
        yield (fence_start, offset, "code", paragraph)
        paragraph += 1
    yield from flush()


def _is_abbreviation(chunk: str) -> bool:
    found = re.search(r"(\w+)\.$", chunk)
    return bool(found) and fold(found.group(1)) in {fold(a) for a in ABBREVIATIONS}


def sentences(text: str) -> list[Sentence]:
    """Split PT-BR text into sentences without breaking abbreviations, decimals,
    URLs, list items or fenced code."""
    out: list[Sentence] = []
    for start, end, kind, paragraph in _blocks(text):
        block = text[start:end]
        if kind != "prose":
            stripped = block.strip()
            if stripped:
                lead = len(block) - len(block.lstrip())
                out.append(Sentence(len(out), start + lead, start + lead + len(stripped), stripped, paragraph, kind))
            continue
        cursor = 0
        for match in _BOUNDARY_RE.finditer(block):
            piece_end = match.end(2)
            if match.group(1) == "." and _is_abbreviation(block[cursor:match.end(1)]):
                continue
            _append(out, text, start + cursor, start + piece_end, paragraph)
            cursor = match.end(3)
        _append(out, text, start + cursor, end, paragraph)
    return out


def _append(out, text, start, end, paragraph):
    raw = text[start:end]
    stripped = raw.strip()
    if not stripped:
        return
    lead = len(raw) - len(raw.lstrip())
    out.append(Sentence(len(out), start + lead, start + lead + len(stripped), stripped, paragraph))
