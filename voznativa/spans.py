"""Protected-span extraction for PT-BR text.

A span is a piece of content that a rewrite must keep verbatim or with an
equivalent normalized value: numbers, money, dates, times, quantities,
versions, identifiers, URLs, code, paths, quotes and named entities.

Each span carries a normalized ``key`` so that equivalent surface forms
compare equal ("R$ 1.500,00" == "R$1.500,00", "18/10/2026" == "18 de outubro
de 2026", "18h30" == "18:30", "três" == "3"). Keys are what the comparison
layer counts; ``text`` is what reports show.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from . import numerals
from .text import STOPWORDS, fold

MONTHS = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}
_MONTH_ALT = "janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro"

NUMBER_WORDS = {
    "zero": 0, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6,
    "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "treze": 13,
    "catorze": 14, "quatorze": 14, "quinze": 15, "dezesseis": 16, "dezessete": 17,
    "dezoito": 18, "dezenove": 19, "vinte": 20, "trinta": 30, "quarenta": 40,
    "cinquenta": 50, "sessenta": 60, "setenta": 70, "oitenta": 80, "noventa": 90,
    "cem": 100, "duzentos": 200, "duzentas": 200, "trezentos": 300, "quinhentos": 500,
    "dobro": "x2", "metade": "x0.5", "triplo": "x3",
}
MULTIPLIERS = {"mil": 1000, "milhao": 10**6, "milhoes": 10**6, "bilhao": 10**9, "bilhoes": 10**9,
               "mi": 10**6, "bi": 10**9}
_MULT_ALT = r"mil|milh(?:ão|ões|ao|oes)|bilh(?:ão|ões|ao|oes)|mi|bi"

UNITS = {
    "ms": "ms", "milissegundo": "ms", "milissegundos": "ms",
    "s": "s", "seg": "s", "segundo": "s", "segundos": "s",
    "min": "min", "minuto": "min", "minutos": "min",
    "h": "h", "hora": "h", "horas": "h",
    "dia": "d", "dias": "d", "semana": "wk", "semanas": "wk",
    "mes": "mo", "meses": "mo", "ano": "y", "anos": "y",
    "kb": "kb", "mb": "mb", "gb": "gb", "tb": "tb", "kib": "kib", "mib": "mib", "gib": "gib",
    "km": "km", "m": "m", "cm": "cm", "mm": "mm", "kg": "kg", "g": "g", "mg": "mg",
    "l": "l", "ml": "ml", "°c": "c", "ºc": "c", "graus": "deg",
    "req/s": "rps", "rps": "rps", "requisicoes por segundo": "rps", "requisicao por segundo": "rps",
    "x": "x", "vezes": "times", "pontos": "pt", "pp": "pp", "usuarios": "users",
}
_UNIT_ALT = (r"requisi[cç](?:ões|oes|ão|ao) por segundo|milissegundos?|segundos?|minutos?|horas?|"
             r"dias?|semanas?|m[eê]s|meses|anos?|req/s|rps|kib|mib|gib|kb|mb|gb|tb|km|cm|mm|kg|mg|ml|"
             r"[°º]c|graus|ms|seg|min|h|s|m|g|l|x|vezes|pontos|pp")

WEEKDAYS = {"segunda": "mon", "terca": "tue", "quarta": "wed", "quinta": "thu", "sexta": "fri",
            "sabado": "sat", "domingo": "sun"}

RELATIVE_TIME = {
    "hoje": "today", "amanha": "tomorrow", "ontem": "yesterday", "anteontem": "day_before_yesterday",
    "depois de amanha": "day_after_tomorrow", "semana que vem": "next_week",
    "proxima semana": "next_week", "mes que vem": "next_month", "proximo mes": "next_month",
    "ano que vem": "next_year", "proximo ano": "next_year", "fim do mes": "end_of_month",
    "final do mes": "end_of_month", "fim de semana": "weekend", "agora": "now",
    "meio-dia": "time:12:00", "meio dia": "time:12:00", "meia-noite": "time:00:00",
}

# Types whose loss or unsupported addition is a hard failure.
HARD_TYPES = frozenset({
    "code_block", "inline_code", "command", "url", "email", "path", "quote", "date", "time",
    "weekday", "relative_time", "money", "percent", "quantity", "version", "identifier",
    "number", "ordinal", "protected_term",
})


@dataclass
class Span:
    type: str
    text: str
    start: int
    end: int
    key: str
    anchors: tuple = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"type": self.type, "text": self.text, "start": self.start, "end": self.end,
                "key": self.key}


def _dec(raw: str) -> str:
    """Parse a PT-BR or EN number to a canonical decimal string.

    "1.500" -> 1500 (dot + three digits is a thousands separator in PT-BR),
    "1.500,25" -> 1500.25, "3,5" -> 3.5, "2.75" -> 2.75.
    """
    s = raw.strip().replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        value = Decimal(s).normalize()
    except InvalidOperation:
        return raw
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _scaled(number: str, multiplier: str | None) -> str:
    base = _dec(number)
    if not multiplier:
        return base
    factor = MULTIPLIERS.get(fold(multiplier))
    try:
        return format((Decimal(base) * factor).normalize(), "f")
    except (InvalidOperation, TypeError):
        return base


_NUM = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?"

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("code_block", re.compile(r"(```|~~~)[^\n]*\n.*?\n\s*\1", re.S)),
    ("inline_code", re.compile(r"`[^`\n]+`")),
    ("command", re.compile(r"(?m)^\s*[$>]\s+\S.*$")),
    ("url", re.compile(r"\bhttps?://[^\s<>\"'`]+[^\s<>\"'`.,;:!?)\]}]")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("quote", re.compile(r"“[^”\n]{1,300}”|«[^»\n]{1,300}»|\"[^\"\n]{1,300}\"")),
    ("date", re.compile(r"\b\d{4}-\d{2}-\d{2}\b")),
    ("date", re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b")),
    ("date", re.compile(
        rf"\b(?:\d{{1,2}}|1º|1°)\s+de\s+(?:{_MONTH_ALT})(?:\s+de\s+\d{{4}})?\b", re.I)),
    ("date", re.compile(rf"\b(?:{_MONTH_ALT})\s+de\s+\d{{4}}\b", re.I)),
    ("date", re.compile(r"\b(?:0?[1-9]|[12]\d|3[01])/(?:0?[1-9]|1[0-2])\b(?!/)")),
    # "2 da tarde" is 14:00, the same time as "14h" (H4: false red when a
    # rewrite switched between the two clock styles).
    ("time", re.compile(r"\b(?:[01]?\d)(?:h|\s+horas?)?\s+da\s+(?:manh[ãa]|tarde|noite|madrugada)\b", re.I)),
    ("time", re.compile(r"\b(?:[01]?\d|2[0-3])(?::[0-5]\d|h[0-5]\d|h(?:rs?)?)(?![\w:])", re.I)),
    # "N horas" is a clock time only after às/das/pelas; "leva 2 horas" is a duration.
    ("time", re.compile(r"\b(?:[àa]s|das|pelas)\s+(?P<v>(?:[01]?\d|2[0-3])\s+horas)\b", re.I)),
    ("path", re.compile(
        r"(?<![\w/])(?:[A-Za-z]:\\[\w\\.-]+|(?:~|\.{1,2})?/[\w.-]+(?:/[\w.-]+)*|"
        r"[\w-]+(?:/[\w.-]+)+\.\w+|[\w.-]+/[\w.-]+/[\w./-]+|"
        r"[\w-]+\.(?:py|js|mjs|ts|tsx|jsx|md|yml|yaml|json|toml|txt|sh|ps1|cfg|ini|html|css|go|rs|"
        r"java|rb|php|sql|csv|lock|env|xml|ipynb))(?![\w/])")),
    ("money", re.compile(rf"(?:R\$|US\$|U\$|€|£|\$)\s?(?:{_NUM})(?:\s+(?:{_MULT_ALT})\b)?", re.I)),
    ("money", re.compile(rf"\b(?:{_NUM})(?:\s+(?:{_MULT_ALT})\b)?\s+(?:de\s+)?(?:reais|real|d[oó]lares|euros)\b", re.I)),
    ("percent", re.compile(rf"(?<![\w.,])(?:{_NUM})\s?%|\b(?:{_NUM})\s+por\s+cento\b", re.I)),
    ("version", re.compile(r"(?<![\w.])v?\d+(?:\.\d+){2,}(?:-[0-9A-Za-z.]+)?\b|\bv\d+(?:\.\d+)?\b")),
    ("identifier", re.compile(r"\b[A-Z][A-Z0-9]+(?:[-_][A-Z0-9]+)*[-_]\d+[A-Z0-9]*\b")),
    ("identifier", re.compile(r"\b(?:HTTP|RFC|ISO|NBR|ABNT|CVE|PEP|ADR|LGPD|PL|PR|CPU|GPU)\s?-?\d[\d.:/-]*\b")),
    ("identifier", re.compile(r"(?<![\w.])(?:[a-z]+(?:_[a-z0-9]+)+|[a-z]+(?:[A-Z][a-z0-9]+)+)(?:\(\))?(?![\w])")),
    ("identifier", re.compile(r"\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b")),
    ("quantity", re.compile(
        rf"(?<![\w.,])(?:{_NUM})(?:\s+(?:{_MULT_ALT})\b)?\s?(?:{_UNIT_ALT})(?![\w/])", re.I)),
    ("ordinal", re.compile(r"\b\d+[ºª°]")),
    ("number", re.compile(rf"(?<![\w.,])(?:{_NUM})(?:\s+(?:{_MULT_ALT})\b)?(?![\w])", re.I)),
    ("number", re.compile(r"\b(?:dobro|metade|triplo)\b", re.I)),
    # Multiplier verbs state a value ("a receita triplicou" = x3; ho-007).
    # "dobrar" also means to fold or to turn a corner: it counts as x2 only
    # without an object right after it ("a receita dobrou", "dobrou em 2025"),
    # never in "dobrou a esquina" / "dobrou o papel".
    ("number", re.compile(
        r"\b(?:duplic|triplic|quadruplic)(?:a|ou|aram|am|ar|ará|arão|ando|ado|ada|ados|adas|aria|ariam)\b", re.I)),
    ("number", re.compile(
        r"\bdobr(?:a|ou|aram|am|ará|arão|aria|ariam)\b(?!\s+(?:[ao]s?|um|uma|seu|sua|meu|minha)\b)", re.I)),
    ("weekday", re.compile(r"\b(?:segunda|ter[cç]a|quarta|quinta|sexta)-feira\b|\bs[aá]bado\b|\bdomingo\b", re.I)),
    ("weekday", re.compile(
        r"\b(?:at[eé]|na|nesta|pr[oó]xima|esta|toda|de|pra|para)\s+(?:a\s+)?(?P<v>segunda|ter[cç]a|quarta|quinta|sexta)\b",
        re.I)),
    # Chat style drops the preposition ("reunião segue quinta às 10h"); a clock
    # time right after the bare day name makes it a weekday, not an ordinal.
    ("weekday", re.compile(
        r"\b(?P<v>segunda|ter[cç]a|quarta|quinta|sexta)(?=,?\s+(?:[àa]s?\s+)?\d{1,2}(?:h|:\d{2}))", re.I)),
    # A bare day name in a temporal slot ("começo segunda no time", "o prazo é
    # sexta.") is a weekday: nothing follows it that it could number, and no
    # article precedes it. Ordinals keep a noun after them ("segunda opção",
    # "terça parte") or an article before ("a segunda é melhor"). Without this,
    # "começo segunda" -> "começo na segunda" was span_added (false red seen in
    # ptbr-bench-v2 bv2-li-02, and the "é sexta" limitation of PLAN_v0.4.0).
    ("weekday", re.compile(
        r"(?<![\w-])(?<!\b[aoAO]\s)(?<!\b[aoAO]s\s)(?<!\bum\s)(?<!\buma\s)(?<!\bd[aoe]\s)(?<!\bn[ao]\s)"
        r"(?P<v>segunda|ter[cç]a|quarta|quinta|sexta)"
        r"(?=\s*(?:[.,;:!?)]|$)|\s+(?:no|na|nos|nas|em|e|ou|que|pela|pelo|cedo|[àa]\s+(?:tarde|noite)|de\s+manh[ãa])\b)",
        re.I)),
    ("relative_time", re.compile(
        r"\b(?:depois de amanh[aã]|anteontem|amanh[aã]|hoje|ontem|semana que vem|pr[oó]xima semana|"
        r"m[eê]s que vem|pr[oó]ximo m[eê]s|ano que vem|pr[oó]ximo ano|(?:fim|final) do m[eê]s|"
        r"meio-dia|meio dia|meia-noite)\b", re.I)),
]

# Number words run after structural spans (code, URLs, quotes, dates, paths)
# and before digit values, so "R$ 1.500" and "mil e quinhentos reais" both win.
_NUMERALS_AT = next(i for i, (kind, _) in enumerate(PATTERNS) if kind == "money")

_ENTITY_RE = re.compile(r"\b[A-ZÀ-Ý][\wÀ-ÿ]*(?:[A-Z][\wÀ-ÿ]*)+\b|\b[A-Z]{2,}[0-9]*\b|\b[A-ZÀ-Ý][a-zà-ÿ]+\b")


def _key(kind: str, raw: str) -> str:
    low = fold(raw)
    if kind in {"code_block", "inline_code", "command", "path", "identifier", "version", "email"}:
        return kind + ":" + re.sub(r"\s+", " ", raw.strip())
    if kind == "url":
        return "url:" + raw.rstrip("/")
    if kind == "quote":
        inner = raw[1:-1]
        return "quote:" + re.sub(r"\s+", " ", fold(inner)).strip()
    if kind == "date":
        return "date:" + _date_key(raw)
    if kind == "time":
        if low.strip() in RELATIVE_TIME:
            return RELATIVE_TIME[low.strip()]
        m = re.match(r"(\d{1,2})\s*(?::|h(?:rs?)?|\s+horas?)?\s*(\d{2})?", low)
        hour, minute = (int(m.group(1)), int(m.group(2) or 0)) if m else (0, 0)
        if re.search(r"\bda noite\b", low) and hour == 12:
            hour = 0
        elif re.search(r"\bda (?:tarde|noite)\b", low) and hour < 12:
            hour += 12
        return f"time:{hour:02d}:{minute:02d}"
    if kind == "money":
        currency = "BRL"
        if re.search(r"us\$|u\$|d[oó]lar|dolar", low) or low.startswith("$"):
            currency = "USD"
        elif "€" in raw or "euro" in low:
            currency = "EUR"
        elif "£" in raw:
            currency = "GBP"
        m = re.search(rf"({_NUM})(?:\s+({_MULT_ALT})\b)?", raw, re.I)
        return f"money:{currency}:{_scaled(m.group(1), m.group(2)) if m else raw}"
    if kind == "percent":
        m = re.search(_NUM, raw)
        return f"percent:{_dec(m.group(0))}"
    if kind == "quantity":
        m = re.match(rf"({_NUM})(?:\s+({_MULT_ALT})\b)?\s?(.+)$", raw.strip(), re.I)
        if m:
            value = _scaled(m.group(1), m.group(2))
            unit_raw = m.group(3)
        else:  # number word + unit ("dois anos")
            word, unit_raw = raw.strip().split(None, 1)
            value = str(NUMBER_WORDS.get(fold(word), fold(word)))
        unit = UNITS.get(fold(unit_raw).strip(), fold(unit_raw).strip())
        return _quantity_key(value, unit)
    if kind == "ordinal":
        return "ordinal:" + re.match(r"\d+", raw).group(0)
    if kind == "number":
        for prefix, factor in (("duplic", "x2"), ("dobr", "x2"), ("triplic", "x3"), ("quadruplic", "x4")):
            if low.startswith(prefix):
                return f"number:{factor}"
        if low in NUMBER_WORDS:
            return f"number:{NUMBER_WORDS[low]}"
        m = re.match(rf"({_NUM})(?:\s+({_MULT_ALT}))?", raw, re.I)
        return f"number:{_scaled(m.group(1), m.group(2))}"
    if kind == "weekday":
        return "weekday:" + WEEKDAYS.get(low.split("-")[0].replace("ç", "c"), low)
    if kind == "relative_time":
        value = RELATIVE_TIME.get(low, RELATIVE_TIME.get(low.replace("-", " "), low))
        return value if value.startswith("time:") else "relative_time:" + value
    if kind == "entity":
        return "entity:" + low
    return f"{kind}:{low}"


SECONDS = {"ms": Decimal("0.001"), "s": 1, "min": 60, "h": 3600, "d": 86400, "wk": 604800}


def _quantity_key(value: str, unit: str) -> str:
    if unit in SECONDS:
        try:
            seconds = (Decimal(value) * SECONDS[unit]).normalize()
            return f"quantity:{numerals.as_text(seconds)}:s"
        except InvalidOperation:
            pass
    return f"quantity:{value}:{unit}"


class _Occupied:
    """Character ranges already claimed by a span (v0.8, V08-GAP-02).

    Replaces a list scanned in full for every candidate match, which made
    ``extract`` quadratic (18.6 s for 40k words, 2026-11-07). One byte per
    character answers the same question: ``overlaps(start, end)`` is True iff
    some claimed range ``(s, e)`` has ``start < e and end > s``. Claimed ranges
    may overlap each other (``_numeral_spans`` extends a range over "reais" or
    a unit after checking it), which an index of disjoint intervals would get
    wrong; a byte map does not care.

    Two degenerate cases of the old expression are kept exactly, although no
    caller produces them today (every claim and query is a non-empty match):
    an empty query ``(p, p)`` overlapped a single range with ``s < p < e``
    (the byte map cannot tell one range from two adjacent ones, so it is
    answered by the old scan), and an empty claim ``(p, p)`` overlapped any
    query with ``start < p < end``."""

    __slots__ = ("_map", "_ranges", "_points")

    def __init__(self, size: int):
        self._map = bytearray(size)
        self._ranges: list[tuple[int, int]] = []
        self._points: list[int] = []

    def overlaps(self, start: int, end: int) -> bool:
        if start >= end:
            return any(start < e and end > s for s, e in self._ranges)
        return 1 in self._map[start:end] or any(start < p < end for p in self._points)

    def add(self, start: int, end: int) -> None:
        self._ranges.append((start, end))
        if start < end:
            self._map[start:end] = b"\x01" * (end - start)
        else:
            self._points.append(start)


_CURRENCY_AFTER = re.compile(r"\s+(?:de\s+)?(reais|real|d[oó]lares|d[oó]lar|euros|euro)\b", re.I)
_UNIT_AFTER = re.compile(rf"\s+({_UNIT_ALT})(?![\w/])", re.I)


def _numeral_spans(text: str, occupied: _Occupied) -> list[Span]:
    """Number words ("vinte e três", "mil e quinhentos reais", "meia hora")."""
    out = []
    for start, end, value in numerals.find(text):
        if occupied.overlaps(start, end):
            continue
        number = numerals.as_text(value)
        rest = text[end:]
        currency = _CURRENCY_AFTER.match(rest)
        unit = _UNIT_AFTER.match(rest)
        if currency:
            end += currency.end()
            code = "USD" if "lar" in fold(currency.group(1)) else "EUR" if "euro" in fold(currency.group(1)) else "BRL"
            kind, key = "money", f"money:{code}:{number}"
        elif unit:
            end += unit.end()
            unit_key = UNITS.get(fold(unit.group(1)), fold(unit.group(1)))
            kind, key = "quantity", _quantity_key(number, unit_key)
        elif value == Decimal("0.5"):
            continue  # a bare "meia" is not a number ("meia noite" is handled elsewhere)
        else:
            kind, key = "number", f"number:{number}"
        occupied.add(start, end)
        out.append(Span(kind, text[start:end], start, end, key, _anchors(text, start, end)))
    return out


def _date_key(raw: str) -> str:
    low = fold(raw)
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", low)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", low)
    if m:
        year = m.group(3)
        year = f"20{year}" if len(year) == 2 else year
        return f"{year}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})", low)
    if m:
        return f"----{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.fullmatch(r"(\d{1,2}|1º|1°)\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?", low)
    if m:
        day = 1 if not m.group(1).isdigit() else int(m.group(1))
        month = MONTHS.get(m.group(2), 0)
        year = m.group(3) or "----"
        return f"{year}-{month:02d}-{day:02d}"
    m = re.fullmatch(r"(\w+)\s+de\s+(\d{4})", low)
    if m:
        return f"{m.group(2)}-{MONTHS.get(m.group(1), 0):02d}"
    return low


_SENTENCE_START_RE = re.compile(r"(?:^|[.!?…:]\s+|\n\s*(?:[-*+•]\s+|\d+[.)]\s+|#+\s+)?)$")
# Every character a match of _SENTENCE_START_RE can contain (the ^ branch is empty).
_SENTENCE_START_CHAR = re.compile(r"[\s\d.!?…:\-*+•#)]")


def _sentence_start(text: str, start: int) -> bool:
    """``bool(_SENTENCE_START_RE.search(text[:start]))`` without copying or
    scanning the whole prefix (v0.8, V08-GAP-02).

    A match ends at ``start`` (or before a final newline there) and consists
    only of characters in ``_SENTENCE_START_CHAR``, so it cannot begin before
    the run of such characters that ends at ``start``. Searching from there
    with ``endpos=start`` keeps the semantics of the slice: ``$`` sees
    ``start`` as the end of the string and ``^`` still matches only at 0."""
    low = start
    while low > 0 and _SENTENCE_START_CHAR.match(text, low - 1):
        low -= 1
    return _SENTENCE_START_RE.search(text, low, start) is not None


def _entities(text: str, occupied: _Occupied) -> list[Span]:
    """Named-entity candidates: CamelCase/ALLCAPS tokens anywhere, Capitalized
    tokens only when they are not sentence-initial (PT-BR capitalizes proper
    nouns, not common nouns)."""
    out = []
    for m in _ENTITY_RE.finditer(text):
        start, end = m.span()
        if occupied.overlaps(start, end):
            continue
        token = m.group(0)
        simple_capitalized = token[0].isupper() and token[1:].islower()
        if simple_capitalized:
            if _sentence_start(text, start) or fold(token) in _FOLDED_STOP:
                continue
        out.append(Span("entity", token, start, end, _key("entity", token)))
    return out


_FOLDED_STOP = frozenset(fold(w) for w in STOPWORDS)
_ANCHOR_WORD_RE = re.compile(r"\w+(?:-\w+)*", re.UNICODE)


def _anchors(text: str, start: int, end: int) -> tuple:
    """Nearest content word before and after a span, used to detect values
    that were swapped between entities ("17 casos e 71 erros")."""
    before = [w for w in _ANCHOR_WORD_RE.findall(text[max(0, start - 60):start])
              if fold(w) not in _FOLDED_STOP and not w[0].isdigit()]
    after = [w for w in _ANCHOR_WORD_RE.findall(text[end:end + 60])
             if fold(w) not in _FOLDED_STOP and not w[0].isdigit()]
    out = []
    if before:
        out.append(("prev", fold(before[-1])[:6]))
    if after:
        out.append(("next", fold(after[0])[:6]))
    return tuple(out)


def extract(text: str, include_entities: bool = True, protect: list[str] | tuple = ()) -> list[Span]:
    """``protect``: user terms that must survive verbatim (product names,
    internal acronyms, fixed expressions). They are matched first, by whole
    word and case-insensitively, and count as hard spans."""
    occupied = _Occupied(len(text))
    out: list[Span] = []
    for term in sorted({t.strip() for t in protect if t and t.strip()}, key=len, reverse=True):
        for match in re.finditer(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.IGNORECASE):
            start, end = match.span()
            if occupied.overlaps(start, end):
                continue
            occupied.add(start, end)
            out.append(Span("protected_term", match.group(0), start, end, "protected_term:" + fold(term),
                            _anchors(text, start, end)))
    for index, (kind, pattern) in enumerate(PATTERNS):
        if index == _NUMERALS_AT:
            out.extend(_numeral_spans(text, occupied))
        for match in pattern.finditer(text):
            group = "v" if "v" in pattern.groupindex else 0
            start, end = match.span(group)
            raw = match.group(group)
            if kind == "command":
                raw_stripped = raw.strip()
                start += len(raw) - len(raw.lstrip())
                raw = raw_stripped
                end = start + len(raw)
            if start == end or occupied.overlaps(start, end):
                continue
            occupied.add(start, end)
            out.append(Span(kind, raw, start, end, _key(kind, raw), _anchors(text, start, end)))
    if include_entities:
        out.extend(_entities(text, occupied))
    return sorted(out, key=lambda span: span.start)
