"""Brazilian Portuguese number words: "vinte e três" = 23, "dois mil e
trezentos" = 2300, "cento e vinte" = 120, "meia dúzia" = 6, "meia hora" = 0.5 h.

``find()`` returns maximal numeral sequences with their value. A lone "um" or
"uma" is skipped (it is usually an article); it counts inside a compound
("vinte e um") or before a multiplier ("uma dúzia", "um milhão").
"""
from __future__ import annotations

import re
from decimal import Decimal

from .text import fold

UNITS = {
    "zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6,
    "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "treze": 13, "catorze": 14,
    "quatorze": 14, "quinze": 15, "dezesseis": 16, "dezasseis": 16, "dezessete": 17, "dezoito": 18,
    "dezenove": 19, "vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50, "sessenta": 60,
    "setenta": 70, "oitenta": 80, "noventa": 90, "cem": 100, "cento": 100, "duzentos": 200,
    "duzentas": 200, "trezentos": 300, "trezentas": 300, "quatrocentos": 400, "quatrocentas": 400,
    "quinhentos": 500, "quinhentas": 500, "seiscentos": 600, "seiscentas": 600, "setecentos": 700,
    "setecentas": 700, "oitocentos": 800, "oitocentas": 800, "novecentos": 900, "novecentas": 900,
}
SCALES = {"mil": 1000, "milhao": 10**6, "milhoes": 10**6, "bilhao": 10**9, "bilhoes": 10**9}
DOZEN = {"duzia": 12, "duzias": 12}
HALF = "meia"
AMBIGUOUS_ALONE = {"um", "uma"}

_TOKEN = re.compile(r"\w+", re.UNICODE)


def _value(words: list[str]) -> Decimal:
    total, group = Decimal(0), Decimal(0)
    for w in words:
        if w == "e":
            continue
        if w == HALF:
            group += Decimal("0.5")
        elif w in UNITS:
            group += UNITS[w]
        elif w in DOZEN:
            group = (group or 1) * DOZEN[w]
        elif w in SCALES:
            total += (group or 1) * SCALES[w]
            group = Decimal(0)
    return total + group


def _is_numeric(word: str) -> bool:
    return word in UNITS or word in SCALES or word in DOZEN


def _joins(last: str, nxt: str) -> bool:
    """'e' joins a smaller component after a round one (tens, hundreds,
    scales): "vinte e três" yes, "três e quatro" (a range) no."""
    big = SCALES.get(last) or UNITS.get(last)
    small = UNITS.get(nxt)
    if big is None or small is None:
        return False
    return big % 10 == 0 and big >= 20 and small < big


def find(text: str) -> list[tuple[int, int, Decimal]]:
    """(start, end, value) for each numeral sequence in ``text``."""
    tokens = [(fold(m.group(0)), m.start(), m.end()) for m in _TOKEN.finditer(text)]
    out, i = [], 0
    while i < len(tokens):
        word = tokens[i][0]
        starts_half = word == HALF and i + 1 < len(tokens) and tokens[i + 1][0] in {*DOZEN, "hora"}
        if not (_is_numeric(word) or starts_half):
            i += 1
            continue
        j = i + 1
        while j < len(tokens):
            nxt, last = tokens[j][0], tokens[j - 1][0]
            if nxt in SCALES or nxt in DOZEN:  # "dois mil", "duas dúzias"
                j += 1
            elif nxt == "e" and j + 1 < len(tokens) and _joins(last, tokens[j + 1][0]):
                j += 2  # "vinte e três", "cento e vinte", "mil e quinhentos"
            else:
                break
        words = [t[0] for t in tokens[i:j]]
        previous = tokens[i - 1][0] if i else ""
        if words[0] in SCALES and previous.isdigit():
            i = j  # "5 milhões", "3 mil": the scale belongs to the digit
            continue
        if words == ["cento"]:
            i = j  # "por cento"; cento is a numeral only in compounds (cento e vinte)
            continue
        if words == [HALF]:  # "meia hora": the unit follows; value 0.5
            out.append((tokens[i][1], tokens[i][2], Decimal("0.5")))
        elif not (len(words) == 1 and words[0] in AMBIGUOUS_ALONE):
            out.append((tokens[i][1], tokens[j - 1][2], _value(words)))
        i = j
    return out


def as_text(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text
