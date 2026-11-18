"""Original-error awareness and editorial modes (v0.7.0 CP9D).

The original is evidence of what the author meant, not proof that it is
correct. ``diagnose`` reports what may be wrong *in the source*, typed, with
offsets, severity, confidence and the action the editorial mode allows. It
never edits by itself; ``proofread`` applies only high-confidence formal
fixes, and only in a mode that authorises them.

Classes (the addendum's seven):

* ``formal_error``           clearly identifiable form error ("o o")
* ``possible_contextual_error`` may be an error; a person decides
* ``internal_contradiction`` the document disagrees with itself
* ``source_mismatch``        a value disagrees with an authorised source
* ``legitimate_choice``      looks unusual, is legitimate (pre-reform spelling)
* ``literary_license``       repetition or form that is the author's art
* ``unresolved_ambiguity``   cannot be decided; no correction

Absence of evidence is never falsity: a value not found in the sources is
``no_evidence`` (information), not a mismatch. Fiction and poetry are not
checked against external facts.

Editorial modes extend the existing tasks instead of a parallel API:
PRESERVE and REVIEW never change the text; PROOFREAD applies formal fixes;
POLISH edits form without content; ADAPT changes a requested destination
(genre, channel, register, audience: ``router.transformation_targets``);
CREATE is the ``create`` task.
"""
from __future__ import annotations

import re

SCHEMA_VERSION = 1
CLASSES = ("formal_error", "possible_contextual_error", "internal_contradiction", "source_mismatch",
           "legitimate_choice", "literary_license", "unresolved_ambiguity", "no_evidence")
MODES = {
    "PRESERVE": {"task": "audit", "rewrite": False, "authorized": []},
    "REVIEW": {"task": "audit", "rewrite": False, "authorized": []},
    "PROOFREAD": {"task": "rewrite", "rewrite": False, "authorized": ["formal_error"]},
    "POLISH": {"task": "rewrite", "rewrite": True, "authorized": ["formal_error", "style", "formula"]},
    "ADAPT": {"task": "rewrite", "rewrite": True,
              "authorized": ["formal_error", "style", "formula", "destination"]},
    "CREATE": {"task": "create", "rewrite": True, "authorized": ["new_text_from_sources"]},
}
NEVER_AUTO = ("facts", "plot", "causality", "intent", "commitments")
# Spaces only between the two words: a heading followed by a paragraph that starts with
# the same word ("Registro\n\nRegistro é...") is not a typo (v0.7.0 CP9D, human-text check).
_REPEATED_WORD = re.compile(r"(?<![\w-])([^\W\d_]{1,12})[ \t]+\1\b", re.I | re.U)
_ACRONYM_DEF = re.compile(r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w ÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç-]{3,80}?)\s*\(([A-Z]{2,8})\)")
# Reduplication that is Portuguese, not a typo.
LEGIT_REPEATS = {"bem", "muito", "pouco", "corre", "pisca", "quase", "agora", "não", "nao", "sim", "já", "ja",
                 "logo", "devagar", "bate", "pega", "lambe", "puxa", "mata", "quebra", "tão", "tao", "mais",
                 "se", "que",   # "se se deixar" (conjunction + reflexive), "o que que é" (colloquial)
                 "bla", "blá", "ai", "ok", "ha", "há", "he", "hum", "oi", "ei", "tchau", "bora", "pois", "tá", "ta"}


_EXPANSION_STOP = {"de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "em", "na", "no", "nas", "nos", "por",
                   "para", "via", "com", "the", "of", "and", "for", "to", "in", "on"}


def _expansion(words: str, acronym: str) -> str | None:
    """The expansion an acronym definition introduces, or None when the words
    before the parenthesis cannot spell it (v0.8.1 DF-07).

    The shortest run of trailing words whose initials (content words, hyphen
    parts included, any order: "Gestão de Estoques Integrada (GEI)")
    cover the acronym's letters, with their counts. Comparing those runs
    instead of the last six words keeps "Implantação do Sistema de Gestão
    de Estoques (SGE)" the same expansion as "Sistema de Gestão de Estoques
    (SGE)", and "Rotina de cálculo de frete (SQL)" is no definition."""
    from collections import Counter

    from .text import fold
    need = Counter(acronym.lower())
    tokens = [t for t in re.split(r"[\s/]+", words.strip()) if t]
    for k in range(1, min(len(tokens), 12) + 1):
        tail = tokens[-k:]
        content = [p for t in tail for p in t.lower().split("-") if p and p not in _EXPANSION_STOP]
        if not need - Counter(fold(p[0]) for p in content):     # "Águas" spells the A of ANA
            return " ".join(content)
    # v0.9 CP4 (V09-GAP-11): acronyms that take inner letters ("Radio Detection And
    # Ranging (RADAR)", "Sound Navigation And Ranging (SONAR)").
    # Read the acronym as the in-order concatenation of a prefix of each word (each word
    # gives at least its initial, at most three letters), over all words of the tail.
    for k in range(1, min(len(tokens), 8) + 1):
        parts = [fold(p) for t in tokens[-k:] for p in t.lower().split("-") if p]
        if parts and _prefix_spelling(fold(acronym.lower()), parts):
            return " ".join(p for p in parts if p not in _EXPANSION_STOP) or None
    return None


def _prefix_spelling(acronym: str, parts: list[str]) -> bool:
    """True when ``acronym`` is prefix(parts[0]) + ... + prefix(parts[-1]), every
    content word contributing 1-3 letters from its start and stopwords 0 or 1."""
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def match(a: int, w: int) -> bool:
        if w == len(parts):
            return a == len(acronym)
        word = parts[w]
        low = 0 if word in _EXPANSION_STOP else 1
        high = 1 if word in _EXPANSION_STOP else 3
        for n in range(low, high + 1):
            if n > len(word) or a + n > len(acronym):
                break
            if word[:n] == acronym[a:a + n] and match(a + n, w + 1):
                return True
        return False
    return match(0, 0)


def mode_policy(mode: str | None) -> dict:
    """What a mode authorises (None: the tool's default rewrite behaviour)."""
    if mode is None:
        return {"mode": None, "rewrite": True, "authorized": ["formal_error", "style", "formula", "destination"],
                "never_automatic": list(NEVER_AUTO)}
    key = mode.upper()
    if key not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    return {"mode": key, **MODES[key], "never_automatic": list(NEVER_AUTO)}


def _d(cls, kind, severity, confidence, start, end, text, message, impact, action, **extra) -> dict:
    return {"class": cls, "type": kind, "severity": severity, "confidence": confidence, "start": start, "end": end,
            "text": text, "message": message, "impact": impact, "action": action, **extra}


def _artistic(context: dict | None, text: str) -> bool:
    from .longform import literary_policy
    genre = ((context or {}).get("genre") or {}).get("value", "unknown")
    conservative = bool(((context or {}).get("protections") or {}).get("conservative"))
    return literary_policy(text, genre, conservative=conservative)["policy"] != "default"


def diagnose(text: str, context: dict | None = None, facts: list[str] | None = None) -> dict:
    """Typed diagnostics of the source. Each says what action is allowed:
    ``auto_fix`` (formal, high confidence; applied only by PROOFREAD and up),
    ``suggest`` (a person decides) or ``preserve``."""
    from . import ledger as ledger_mod
    from .planner import _weekday_conflicts
    from .router import infer_time_of_text
    out = []
    artistic = _artistic(context, text)
    genre = ((context or {}).get("genre") or {}).get("value")
    register = ((context or {}).get("register") or {}).get("value")
    informal = genre in ("whatsapp", "social") or register in ("colloquial", "casual") or bool(
        re.search(r"\b(?:vc|pq|tbm|kkk+|rs|blz|vlw)\b", text, re.I))

    for m in _REPEATED_WORD.finditer(text):
        word = m.group(1).lower()
        second = m.group(0).split()[-1]
        symbol = len(word) == 1 and word not in "oaeéà"
        # v0.8.1 DF-06: a one-letter label and the conjunction or article after it
        # ("os lotes C, E e G", "o lote A a ser enviado") differ in case; auto_fix
        # deleted the conjunction.
        label = len(word) == 1 and m.group(1) != second
        if word in LEGIT_REPEATS or symbol or label or (m.group(1)[:1].isupper() and second[:1].isupper()):
            # reduplicated names ("Dee Dee", "Boutros Boutros-Ghali"), grammatical pairs, symbols ("x x")
            continue
        if artistic:
            out.append(_d("literary_license", "repetition", "info", "medium", m.start(), m.end(), m.group(0),
                          "repeated word in literary or verse text: may be the author's choice", "none", "preserve"))
        elif informal:
            # "ruim ruim" in a review is emphasis as often as a slip: a person decides.
            out.append(_d("possible_contextual_error", "repeated_word", "info", "low", m.start(), m.end(), m.group(0),
                          f"'{m.group(1)}' repeated in informal text: emphasis or slip", "form only", "suggest"))
        else:
            out.append(_d("formal_error", "repeated_word", "minor", "high", m.start(), m.end(), m.group(0),
                          f"'{m.group(1)}' repeated", "form only", "auto_fix", fix=m.group(1)))

    led = ledger_mod.build(text)
    for w in _weekday_conflicts(led):
        sentence = led.entries[w["sentence"]].sentence
        out.append(_d("internal_contradiction", "weekday_date_mismatch", "major", "high", sentence.start,
                      sentence.end, sentence.text, w.get("message", "weekday does not match the date"),
                      "facts", "suggest"))

    defs: dict[str, set] = {}
    positions: dict[str, tuple] = {}
    for m in _ACRONYM_DEF.finditer(text):
        expansion = _expansion(m.group(1), m.group(2))
        if expansion is None:      # the words before the parenthesis do not spell the acronym
            continue
        defs.setdefault(m.group(2), set()).add(expansion)
        positions.setdefault(m.group(2), (m.start(), m.end()))
    for acronym, expansions in defs.items():
        if len(expansions) > 1:
            start, end = positions[acronym]
            out.append(_d("internal_contradiction", "acronym_redefined", "major", "medium", start, end, acronym,
                          f"{acronym} is introduced with different expansions: {sorted(expansions)}",
                          "terminology", "suggest"))

    seen: dict[str, tuple] = {}
    for entry in led.entries:
        key = " ".join(entry.sentence.text.lower().split())
        if len(key.split()) >= 6 and key in seen:
            cls = "literary_license" if artistic else "possible_contextual_error"
            out.append(_d(cls, "repeated_sentence", "info" if artistic else "minor", "high", entry.sentence.start,
                          entry.sentence.end, entry.sentence.text, "the same sentence appears twice",
                          "none" if artistic else "redundancy", "preserve" if artistic else "suggest"))
        seen.setdefault(key, (entry.sentence.start, entry.sentence.end))

    time_info = infer_time_of_text(text)
    if time_info["value"] == "pre_reform_orthography":
        out.append(_d("legitimate_choice", "historical_spelling", "info", "medium", 0, 0, ", ".join(time_info["evidence"]),
                      "pre-reform spelling: the text's time, not an error to modernise without a request",
                      "none", "preserve"))

    out += _grammar(text, informal, artistic)
    out += _tense_mix(text, artistic)
    grounding = _grounding(text, facts, context)
    out += grounding["diagnostics"]
    out.sort(key=lambda d: (d["start"], d["class"]))
    counts = {c: sum(d["class"] == c for d in out) for c in CLASSES}
    return {"kind": "voznativa.diagnosis", "schema_version": SCHEMA_VERSION, "diagnostics": out,
            "counts": {k: v for k, v in counts.items() if v}, "grounding": grounding["status"],
            "note": "diagnostics of the source; none is applied automatically except formal fixes in an "
                    "authorising mode"}


# v0.9 CP4 (V09-GAP-08): grammar errors that standard Brazilian Portuguese grammars treat as
# errors in any formal text, detectable with high confidence from a few words around them.
# Each rule has controls in evals/v09/diagnose (clitic "os viu", invariable "os ônibus", numerals,
# "haviam chegado", "fazem dois trabalhos", "à mulher", "à vista"). In informal text they are
# suggestions; in literary text they are the author's choice.
_PLURAL_DETERMINERS = frozenset(
    "dos das nas aos às pelos pelas esses essas estes estas aqueles aquelas seus suas meus minhas nossos nossas "
    "teus tuas vários várias muitos muitas alguns algumas poucos poucas diversos diversas certos certas "
    "outros outras todos todas quaisquer tais".split())
_SENTENCE_START_ONLY = frozenset({"os", "as"})        # elsewhere they may be clitic pronouns ("ele os viu")
_CLITIC_ATTRACTORS = frozenset(
    "eu tu ele ela nós vós eles elas você vocês que não nunca jamais já se quem também só ainda sempre ninguém "
    "alguém tudo isso isto aquilo me te lhe nos vos lhes onde quando como porque".split())
_VERB_ENDING = re.compile(r"(?:ou|eu|iu|aram|eram|iram|ava|avam|ia|iam|ará|erá|irá|arão|erão|irão|ei|amos|emos|imos)$")
_PREP_BEFORE_ARTICLE = frozenset("de em para com por sobre entre sem até após contra perante todos todas".split())
_NOT_A_NOUN = frozenset(
    "que quais quanto quantos quantas qual cujo cuja mesmo mesma demais seguinte próprio própria um uma dois duas três "
    "quatro cinco seis sete oito nove dez onze doze treze catorze quatorze quinze dezesseis dezessete dezoito dezenove "
    "vinte trinta quarenta cinquenta sessenta setenta oitenta noventa cem cento duzentos duzentas mil milhão milhões "
    "e ou nem mas de a o em por para com sem se não já ainda mais menos muito pouco bem mal quem onde quando como "
    "dele dela deles delas nele nela isso isto aquilo outro outra tal".split())
_NUMBER_WORDS = re.compile(r"\d")
_ANGLICISM_END = re.compile(r"(?:ware|ing|er|ion|ment|ness|ity|ow|ay|ey|ck|sh|th)$")
_FAZER_TIME = re.compile(
    r"\b(fazem|faziam|fizeram|farão)\s+((?:\d+|um|uma|dois|duas|três|quatro|cinco|seis|sete|oito|nove|dez|vinte|"
    r"trinta|alguns|algumas|muitos|muitas|vários|várias|poucos|poucas|uns|umas)\s+(?:anos?|meses|mês|dias?|semanas?|"
    r"horas?|minutos?|décadas?|séculos?))\b", re.I)
_HAVER_EXIST = re.compile(
    r"\b(houveram|haviam|haverão|haveriam|hajam)\s+((?:\d+|dois|duas|três|quatro|cinco|seis|sete|oito|nove|dez|"
    r"muitos|muitas|vários|várias|poucos|poucas|alguns|algumas|diversos|diversas|inúmeros|inúmeras|tantos|tantas)\b)",
    re.I)
# v0.9 CP8 dogfood: "houveram/haverão/hajam" are existential before any noun phrase, not only before a
# quantifier ("Houveram atrasos"); the exceptions are "houveram de/por bem" and the auxiliary + participle.
_HAVER_ALWAYS = re.compile(r"\b(houveram|haverão|hajam)\s+(?!de\b|por\b)([^\W\d_]+)", re.I)
_PARTICIPLE = re.compile(r"(?:ado|ada|ados|adas|ido|ida|idos|idas|ito|ita|eito|osto|erto)$", re.I)
_HAVER_FIX = {"houveram": "houve", "haviam": "havia", "haverão": "haverá", "haveriam": "haveria", "hajam": "haja"}
_FAZER_FIX = {"fazem": "faz", "faziam": "fazia", "fizeram": "fez", "farão": "fará"}
_CRASE = re.compile(r"\bà\s+(partir\b|pé\b|cavalo\b|prazo\b|ele\b|eles\b|você\b|vocês\b|"
                    r"[^\W\d_]+(?:ar|er|ir)\b)", re.I)
_CRASE_FEMININE_ER = frozenset({"mulher", "colher"})   # feminine nouns ending like an infinitive


def _grammar(text: str, informal: bool, artistic: bool) -> list[dict]:
    from .text import sentences
    out = []

    def add(kind, start, end, found, message, fix=None):
        if artistic:
            out.append(_d("literary_license", kind, "info", "medium", start, end, found,
                          message + " (literary text: may be the author's choice)", "none", "preserve"))
        elif informal:
            out.append(_d("possible_contextual_error", kind, "info", "medium", start, end, found,
                          message + " (informal register: a person decides)", "form only", "suggest"))
        else:
            out.append(_d("formal_error", kind, "minor", "high", start, end, found, message, "form only",
                          "auto_fix" if fix else "suggest", **({"fix": fix} if fix else {})))

    for s in sentences(text):
        if s.kind != "prose":
            continue
        tokens = list(re.finditer(r"[^\W\d_]+(?:-[^\W\d_]+)*|\d+", s.text))
        for k in range(len(tokens) - 1):
            det, noun = tokens[k].group(0), tokens[k + 1].group(0)
            low = det.lower()
            if low in _SENTENCE_START_ONLY:
                # "os"/"as" are also clitic pronouns: before a verb ("eu as levei", "a diretora as
                # recebeu") or after a word that attracts the pronoun ("ele", "que", "não").
                previous = tokens[k - 1].group(0).lower() if k else None
                verb_next = _VERB_ENDING.search(tokens[k + 1].group(0).lower())
                if k and previous not in _PREP_BEFORE_ARTICLE and (previous in _CLITIC_ATTRACTORS or verb_next):
                    continue
            elif low not in _PLURAL_DETERMINERS:
                continue
            word = noun.lower()
            if (not noun.isalpha() or noun[:1].isupper() or len(word) < 3 or word in _NOT_A_NOUN
                    or word.endswith(("s", "x", "z")) or _NUMBER_WORDS.search(word) or _ANGLICISM_END.search(word)
                    or s.text[tokens[k].end():tokens[k + 1].start()].strip()):
                continue
            start, end = s.start + tokens[k].start(), s.start + tokens[k + 1].end()
            add("plural_agreement", start, end, text[start:end],
                f"'{det} {noun}': plural determiner with a singular word (concordância nominal)")
        for m in _FAZER_TIME.finditer(s.text):
            verb = m.group(1)
            fix = _FAZER_FIX[verb.lower()]
            fix = fix.capitalize() if verb[:1].isupper() else fix
            add("impersonal_fazer", s.start + m.start(1), s.start + m.end(1), verb,
                f"'{verb} {m.group(2)}': 'fazer' indicating elapsed time is impersonal (singular)", fix)
        seen_haver = set()
        for m in list(_HAVER_EXIST.finditer(s.text)) + [m for m in _HAVER_ALWAYS.finditer(s.text)
                                                         if not _PARTICIPLE.search(m.group(2))]:
            if m.start(1) in seen_haver:
                continue
            seen_haver.add(m.start(1))
            verb = m.group(1)
            fix = _HAVER_FIX[verb.lower()]
            fix = fix.capitalize() if verb[:1].isupper() else fix
            add("existential_haver", s.start + m.start(1), s.start + m.end(1), verb,
                f"'{verb} {m.group(2)}': 'haver' meaning 'existir' is impersonal (singular)", fix)
        for m in _CRASE.finditer(s.text):
            target = m.group(1).lower()
            if target in _CRASE_FEMININE_ER:
                continue
            grave = m.group(0)[0]
            add("crase", s.start + m.start(), s.start + m.start() + 1, grave,
                f"'{grave} {m.group(1)}': no crase before a masculine word, a pronoun or a verb",
                "A" if grave == "À" else "a")
    return out


def _tense_mix(text: str, artistic: bool) -> list[dict]:
    """Adjacent narrative sentences switching between preterite and present
    may be a slip or a historical present: always an unresolved ambiguity."""
    from .morph import tense_profile
    from .text import sentences
    out = []
    labels = []
    for s in sentences(text):
        tenses = {next(iter(v)) for v in tense_profile(s.text, prefer_indicative=True).values() if len(v) == 1}
        labels.append((s, tenses))
    for (a, ta), (b, tb) in zip(labels, labels[1:]):
        if ta == {"pret_perf"} and tb == {"pres_ind"} and not artistic:
            out.append(_d("unresolved_ambiguity", "tense_switch", "info", "low", b.start, b.end, b.text,
                          "narration switches from preterite to present: a slip or a historical present",
                          "time of events", "suggest"))
    return out


def _grounding(text: str, facts: list[str] | None, context: dict | None) -> dict:
    """Values of the text against authorised sources. A value whose context
    words match a source value of the same type with another key is a
    mismatch; a value absent from every source is no_evidence (never false)."""
    if not facts:
        return {"status": "not_requested", "diagnostics": []}
    genre = ((context or {}).get("genre") or {}).get("value")
    if genre == "literary":
        return {"status": "skipped_fiction", "diagnostics": []}
    from .spans import HARD_TYPES, extract
    source_spans = [s for f in facts for s in extract(f) if s.type in HARD_TYPES]
    keys = {s.key for s in source_spans}
    out = []
    for span in extract(text):
        if span.type not in HARD_TYPES or span.key in keys:
            continue
        rivals = [s for s in source_spans if s.type == span.type and set(s.anchors) & set(span.anchors)]
        if rivals:
            out.append(_d("source_mismatch", f"{span.type}_differs", "major", "medium", span.start, span.end,
                          span.text, f"the source gives {rivals[0].text} in the same context", "facts", "suggest",
                          source_value=rivals[0].text))
        else:
            out.append(_d("no_evidence", f"{span.type}_not_in_sources", "info", "high", span.start, span.end,
                          span.text, "not found in the authorised sources (absence is not falsity)", "none",
                          "suggest"))
    return {"status": "checked", "diagnostics": out}


def proofread(text: str, diagnosis: dict, mode: str | None) -> dict:
    """Apply the fixes the mode authorises (formal, high confidence, auto_fix).
    Everything else stays as a suggestion. Returns the text and what changed."""
    policy = mode_policy(mode)
    if "formal_error" not in policy["authorized"]:
        return {"text": text, "applied": [], "mode": policy["mode"], "reason": "mode does not authorise edits"}
    fixes = [d for d in diagnosis["diagnostics"] if d["class"] == "formal_error" and d["action"] == "auto_fix"
             and d["confidence"] == "high" and "fix" in d]
    out, last, applied = [], 0, []
    for d in sorted(fixes, key=lambda d: d["start"]):
        if d["start"] < last:
            continue
        out.append(text[last:d["start"]] + d["fix"])
        last = d["end"]
        applied.append({"type": d["type"], "before": d["text"], "after": d["fix"], "start": d["start"]})
    out.append(text[last:])
    return {"text": "".join(out), "applied": applied, "mode": policy["mode"]}
