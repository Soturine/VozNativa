"""Event frames for one sentence: who does what to whom (v0.8 CP6, V08-GAP-04).

A frame is extracted only when the sentence is simple enough to read without
guessing; otherwise the extractor abstains (returns no frame) and the checks
built on it say nothing. A frame carries:

* ``predicate``: the verb form, its lemma(s) and stem (``voznativa.morph``);
* ``agent``: the head word of the subject right before the verb, when there
  is one (no subject, a clitic or a long stretch: ``None``);
* ``recipient``: the head word of a complement introduced by *a/ao/à/aos/às/
  para/pra/pro* after a **transfer verb** (enviar, entregar, devolver,
  informar, pagar...), skipping time ("às 14h", "à noite"), purpose ("para"
  + infinitive) and fixed phrases ("a partir", "ao longo");
* ``passive``: "foi/foram/é/será + participle", in which case ``agent`` comes
  from "por/pelo/pela";
* ``offsets`` and ``confidence`` (``high`` only for one finite verb and an
  agent within three words of it).

Verb classes live in ``data/verb_relations.json`` (transfer verbs and
converse pairs), written for this module and versioned; they are general
classes, not the sentences of any test.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .text import fold

DATA = Path(__file__).resolve().parent / "data" / "verb_relations.json"
_WORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*|\d+[\w:]*", re.U)
_DETERMINERS = frozenset("o a os as um uma uns umas meu minha meus minhas seu sua seus suas nosso nossa nossos "
                         "nossas esse essa esses essas este esta estes estas aquele aquela aqueles aquelas todo toda "
                         "todos todas".split())
_RECIPIENT_PREPS = {"a", "ao", "aos", "as", "para", "pra", "pro", "pros", "pras"}
_TIME_WORDS = frozenset("noite tarde manha madrugada hora horas meia vez vezes tempo vista prazo partir longo vivo "
                        "custa medida respeito favor fim frente cerca beira tona mao mesa disposicao".split())
_PASSIVE_AUX = frozenset("foi foram e sao sera serao era eram sendo sido estava estavam fica ficou".split())


@lru_cache(maxsize=1)
def relations() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def transfer_stems() -> frozenset[str]:
    return frozenset(lemma[:-2] for lemma in relations()["transfer_verbs"])


@lru_cache(maxsize=1)
def converse_stems() -> dict[str, frozenset[str]]:
    out: dict[str, set] = {}
    for left, right in relations()["converse_pairs"]:
        for a in left:
            for b in right:
                out.setdefault(a[:-2], set()).add(b[:-2])
                out.setdefault(b[:-2], set()).add(a[:-2])
    return {k: frozenset(v) for k, v in out.items()}


@dataclass
class Frame:
    verb: str
    lemmas: tuple
    stem: str
    start: int
    end: int
    agent: str | None = None
    recipient: str | None = None
    passive: bool = False
    confidence: str = "low"
    notes: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"verb": self.verb, "lemmas": list(self.lemmas), "stem": self.stem, "start": self.start,
                "end": self.end, "agent": self.agent, "recipient": self.recipient, "passive": self.passive,
                "confidence": self.confidence, "notes": self.notes}


def _tokens(sentence: str) -> list[tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in _WORD.finditer(sentence)]


def _stem_of(lemmas) -> str | None:
    stems = {fold(lemma)[:-2] for lemma in lemmas}
    return next(iter(stems)) if len(stems) == 1 else None


def _head_before(tokens, k: int) -> tuple[str | None, int]:
    """Head of the noun phrase that ends right before token ``k``: the last
    token that is not a determiner, within three tokens; ``None`` if a
    preposition, a verb-like clitic or punctuation context gets in the way."""
    j = k - 1
    while j >= 0 and fold(tokens[j][0]) in {"nao", "ja", "tambem", "so", "ainda", "nunca"}:
        j -= 1
    if j < 0:
        return None, 0
    word = fold(tokens[j][0])
    if word in _DETERMINERS or word in _NOT_A_SUBJECT or word.isdigit():
        return None, 0
    from .morph import IRREGULAR_INDEX
    if word in IRREGULAR_INDEX:      # "vou mandar", "pode enviar": an auxiliary, the subject is further back
        return None, 0
    return word, k - j


# Clitics, conjunctions and prepositions: never the head of a subject.
_NOT_A_SUBJECT = frozenset("se me te lhe nos vos lhes que e ou mas de em por para com sem sobre ate apos entre "
                           "a ao aos as".split())


def _recipient_after(sentence: str, tokens, k: int) -> str | None:
    """Head of the first recipient complement after the verb at ``k``."""
    for idx in range(k + 1, min(len(tokens), k + 9)):
        word, start, _ = tokens[idx]
        f = fold(word)
        if f not in _RECIPIENT_PREPS:
            continue
        if word.lower() in {"a", "as"}:
            # Bare "a"/"as" is usually the object's article ("entregou a planilha"). It is a
            # preposition only after the object and before a name ("pagou o aluguel a Paula").
            following = tokens[idx + 1][0] if idx + 1 < len(tokens) else ""
            if idx == k + 1 or not following[:1].isupper():
                continue
        rest = tokens[idx + 1: idx + 4]
        heads = [fold(t[0]) for t in rest if fold(t[0]) not in _DETERMINERS]
        if not heads:
            return None
        head = heads[0]
        if head.isdigit() or head[:1].isdigit() or head in _TIME_WORDS:
            return None
        if f in {"para", "pra", "pro"} and re.fullmatch(r"\w+(?:ar|er|ir|or)", head) and rest and \
                fold(rest[0][0]) == head:
            return None          # "para entregar": purpose, not a recipient
        return head
    return None


def frames(sentence: str) -> list[Frame]:
    """Frames of the transfer and converse verbs of ``sentence`` (abstains on
    anything ambiguous)."""
    from .morph import verbs
    tokens = _tokens(sentence)
    index = {start: n for n, (_, start, _) in enumerate(tokens)}
    found = verbs(sentence)
    finite = [v for v in found if any(a.get("VerbForm") == "Fin" for a in v.analyses)]
    out = []
    interesting = transfer_stems() | set(converse_stems())
    for v in found:
        k = index.get(v.start)
        # After "foi/foram/é/será...", a participle reading wins: "enviado" is also read as a present of
        # "enviadar", and with several stems the verb used to be dropped, so a singular passive had no
        # frame at all (CP14, found by mutation: the passive branch was never reached by a test).
        # A bare "e" counts too, as it always did for an unambiguous participle: before a participle it
        # coordinates a passive ("foi revisado e enviado à diretoria").
        part = [a for a in v.analyses if a.get("VerbForm") == "Part"]
        after_aux = k is not None and k > 0 and fold(tokens[k - 1][0]) in _PASSIVE_AUX
        participle = bool(part) and (after_aux or len(part) == len(v.analyses))
        lemmas = {a["lemma"] for a in part} if participle else v.lemmas
        stem = _stem_of(lemmas)
        if stem is None or not any(stem.startswith(s) and len(stem) - len(s) <= 1 for s in interesting):
            continue
        if k is None:
            continue
        frame = Frame(v.form, tuple(sorted(lemmas)), stem, v.start, v.end)
        if participle and k > 0 and fold(tokens[k - 1][0]) in _PASSIVE_AUX:
            frame.passive = True
            by = next((i for i in range(k + 1, min(len(tokens), k + 8))
                       if fold(tokens[i][0]) in {"por", "pelo", "pela", "pelos", "pelas"}), None)
            if by is not None:
                heads = [fold(t[0]) for t in tokens[by + 1: by + 4] if fold(t[0]) not in _DETERMINERS]
                frame.agent = heads[0] if heads else None
        else:
            frame.agent, distance = _head_before(tokens, k)
            if frame.agent and distance <= 3 and len(finite) == 1:
                frame.confidence = "high"
        if any(stem.startswith(s) and len(stem) - len(s) <= 1 for s in transfer_stems()):
            frame.recipient = _recipient_after(sentence, tokens, k)
        out.append(frame)
    return out


def converse(stem_a: str, stem_b: str) -> bool:
    """``stem_b`` is a converse of ``stem_a`` (comprar/vender, enviar/receber)."""
    for s, others in converse_stems().items():
        if stem_a.startswith(s) and len(stem_a) - len(s) <= 1:
            if any(stem_b.startswith(o) and len(stem_b) - len(o) <= 1 for o in others):
                return True
    return False
