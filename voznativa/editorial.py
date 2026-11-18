"""Editorial consistency across the units of a long document (v0.9 CP3).

Two dogfoods of v0.8.1 showed that units rewritten one at a time can each
improve and still make the document worse: pattern findings fell from 37 to
8 while sentences opening with "Essa X permite/promove/contribui" rose from
3 to 11, because every unit converged on the same fix. Nothing saw it. This
module gives the long-form engine two small tools; neither judges meaning,
neither can change a fact, and both are signals for a person, not proofs.

* ``openings(text)``: how many sentences open with each *anaphoric or
  connective opener* -- a demonstrative followed by a noun ("Essa
  abordagem", "Esse resultado"), "Isso/Isto", a fixed connective ("Além
  disso", "Dessa forma", "Nesse sentido"...), or a sentence-initial gerund.
  Articles are deliberately not counted: cutting a formula ("É importante
  destacar que o relatório...") legitimately leaves "O relatório..." and
  must not look like convergence.
* ``convergence(original, final, units)``: openers the rewrite *added* --
  at least ``MIN_ADDED`` more than the original had, at least twice the
  original count plus one, and spread over at least two units when the units
  are given. An opener the author already used as often is the author's
  voice and is never flagged; repetition that carries content (restrictions,
  caveats, definitions) is not an opener and is not counted.
* ``EditorialMemory``: the state the engine carries from unit to unit --
  how many openers of each kind the rewritten units have added so far and
  which spelling of a variable term (``backend``/``back-end``) the original
  document uses. ``prompt_note()`` turns it into one instruction for the
  next unit. The state is small, versioned and holds labels and spellings,
  never the document's sentences; it does not touch protected values, and
  the gates still validate every unit and the whole document.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache

from .text import sentences

SCHEMA_VERSION = 1
MIN_ADDED = 3
MEMORY_THRESHOLD = 2   # openers already added by earlier units before the next unit is asked to avoid them

_DEMONSTRATIVE = {"esse", "essa", "esses", "essas", "este", "esta", "estes", "estas", "tal", "tais"}
_PRONOUN = {"isso", "isto"}
# Connective openers, longest first so "por outro lado" wins over "por".
_CONNECTIVES = sorted((
    "além disso", "dessa forma", "desse modo", "dessa maneira", "deste modo", "desta forma", "com isso",
    "nesse sentido", "neste sentido", "nesse contexto", "neste contexto", "nesse cenário", "diante disso",
    "por isso", "assim", "portanto", "ademais", "em suma", "por fim", "por outro lado", "em síntese", "sendo assim", "logo", "contudo", "entretanto", "todavia", "no entanto", "ou seja",
    "em outras palavras", "vale dizer", "de fato", "certamente", "consequentemente",
), key=lambda c: -len(c))
_WORD = re.compile(r"[\wÀ-ÿ]+(?:-[\wÀ-ÿ]+)*")
# "Essa abordagem permite...", "Isso contribui para...": a demonstrative opener whose verb (within the
# next three words) states an effect or an evaluation. Verb forms only (present, past, future, imperfect),
# so "representação" or "demonstração" do not count. Fixed by linguistic criterion before measuring.
_EFFECT_VERB = re.compile(
    r"^(?:permit|possibilit|promov|contribu|garant|favorec|proporcion|assegur|viabiliz|facilit|reforç|reforc|"
    r"evidenci|demonstr|torn|represent|ampli|fortalec|otimiz|potencializ|consolid|resum)"
    r"(?:e|em|a|am|i|ui|uem|ou|eu|aram|eram|iu|iram|ará|arão|erá|erão|irá|irão|ia|iam|ava|avam)$")
LABELS = {
    "demonstrative_effect": "frases abertas por demonstrativo + nome + verbo de efeito (\"Essa abordagem "
                            "permite...\", \"Isso contribui...\")",
    "demonstrative": "frases abertas por demonstrativo + nome (\"Essa/Esse/Esta ... \")",
    "pronoun": "frases abertas por \"Isso\"/\"Isto\"",
    "gerund": "frases abertas por gerúndio",
}


def _opener(sentence: str) -> str | None:
    head = sentence.lstrip(" \t\"'“«(—–-*#>").lower()
    for connective in _CONNECTIVES:
        if head.startswith(connective) and (len(head) == len(connective) or not head[len(connective)].isalnum()):
            return f"connective:{connective}"
    words = _WORD.findall(head[:80])
    if not words:
        return None
    first = words[0]
    if (first in _DEMONSTRATIVE or first in _PRONOUN) and any(_EFFECT_VERB.match(w) for w in words[1:4]):
        return "demonstrative_effect"
    if first in _DEMONSTRATIVE and len(words) > 1:
        return "demonstrative"
    if first in _PRONOUN:
        return "pronoun"
    if len(first) > 4 and first.endswith(("ando", "endo", "indo")):
        return "gerund"
    return None


def openings(text: str) -> Counter:
    """Count of sentences per opener kind (prose sentences only)."""
    out: Counter = Counter()
    for s in sentences(text):
        if s.kind != "prose":
            continue
        kind = _opener(s.text)
        if kind:
            out[kind] += 1
    return out


def label(kind: str) -> str:
    if kind.startswith("connective:"):
        return f"frases abertas por \"{kind.split(':', 1)[1].capitalize()}\""
    return LABELS.get(kind, kind)


def _flag(before: int, after: int) -> bool:
    return after - before >= MIN_ADDED and after >= 2 * before + 1


def convergence(original: str, final: str, units: list[tuple[str, str]] | None = None) -> list[dict]:
    """Openers the rewrite added across the document. ``units`` is the list
    of (source, candidate) of the rewritten units, used to require that the
    added openers come from at least two units."""
    before, after = openings(original), openings(final)
    found = []
    for kind in sorted(set(after)):
        if not _flag(before[kind], after[kind]):
            continue
        spread = None
        if units is not None:
            spread = sum(1 for src, cand in units if openings(cand)[kind] > openings(src)[kind])
            if spread < 2:
                continue
        found.append({"kind": "style_convergence", "opening": kind, "label": label(kind),
                      "original": before[kind], "final": after[kind], "units_adding": spread,
                      "severity": "major", "effect": "signal",
                      "message": f"a reescrita acrescentou {after[kind] - before[kind]} {label(kind)} "
                                 f"({before[kind]} no original, {after[kind]} no resultado); varie ou mantenha "
                                 "a forma do autor"})
    return found


@lru_cache(maxsize=1)
def _spelling_groups() -> tuple[tuple[str, ...], ...]:
    """Term spellings known to vary (community pack forms that differ only by a hyphen or a space)."""
    from pathlib import Path

    import yaml
    path = Path(__file__).resolve().parent / "data" / "community_packs" / "tech.yml"
    try:
        items = yaml.safe_load(path.read_text(encoding="utf-8")).get("items", [])
    except (OSError, AttributeError, yaml.YAMLError):
        return ()
    groups = []
    for item in items:
        forms = item.get("forms") or []
        norm = {re.sub(r"[-\s]", "", f.lower()) for f in forms}
        variants = tuple(f for f in forms if re.sub(r"[-\s]", "", f.lower()) in norm)
        if len(norm) == 1 and len(variants) > 1:
            groups.append(variants)
    return tuple(groups)


def document_spellings(original: str) -> dict[str, str]:
    """For each variable term the original uses in exactly one spelling, that spelling."""
    out = {}
    for variants in _spelling_groups():
        used = [v for v in variants if re.search(rf"(?<![\w-]){re.escape(v)}(?![\w-])", original, re.I)]
        if len(used) == 1:
            out[re.sub(r"[-\s]", "", used[0].lower())] = used[0]
    return out


@dataclass
class EditorialMemory:
    """What the rewritten units have done so far (labels and counts, never sentences)."""
    spellings: dict[str, str] = field(default_factory=dict)
    added: Counter = field(default_factory=Counter)
    units_seen: int = 0

    @classmethod
    def for_document(cls, original: str) -> "EditorialMemory":
        return cls(spellings=document_spellings(original))

    def record(self, source: str, candidate: str) -> None:
        self.units_seen += 1
        before, after = openings(source), openings(candidate)
        for kind in after:
            if after[kind] > before[kind]:
                self.added[kind] += after[kind] - before[kind]

    def overused(self) -> list[str]:
        return sorted(k for k, n in self.added.items() if n >= MEMORY_THRESHOLD)

    def prompt_note(self, unit_text: str) -> str | None:
        parts = []
        relevant = {k: v for k, v in self.spellings.items()
                    if re.search(rf"(?<![\w-]){re.escape(v)}(?![\w-])", unit_text, re.I)}
        if relevant:
            parts.append("Grafia dos termos neste documento (use exatamente esta forma): "
                         + ", ".join(sorted(relevant.values())) + ".")
        overused = self.overused()
        if overused:
            parts.append("Os trechos já reescritos deste documento acrescentaram várias "
                         + "; ".join(label(k) for k in overused)
                         + ". Não acrescente outras neste trecho; se o original já começa assim, pode manter.")
        return " ".join(parts) or None

    def state(self) -> dict:
        return {"schema_version": SCHEMA_VERSION, "units_seen": self.units_seen,
                "openers_added": dict(sorted(self.added.items())), "spellings": dict(sorted(self.spellings.items())),
                "avoid": self.overused()}
