"""Brazilian Portuguese contextual layer (v0.4.0 M2).

Four questions a PT-BR rewrite has to answer and a word list alone cannot:

* variant: does the text carry European Portuguese choices (lexicon such as
  "telemóvel", "estar a + infinitivo", spellings with a silent consonant)?
  False friends ("propina", "constipação", "rapariga") are flagged as
  meaning-sensitive: the rewrite must check the sense, not swap the word.
* foreign terms: is "deploy" or "feedback" at home in this genre? Domain terms
  are kept (translating "deploy" in a runbook is purism, not naturalness);
  clusters of out-of-domain terms are reported.
* forms of address: does the text mix "você" with "o senhor", or with "teu"
  in a formal register? (Mixing "você" and "te" is ordinary Brazilian usage
  and is not reported in casual registers.)
* written orality: do chat abbreviations or speech forms clash with the
  target register?

Quoted material is skipped: a quote keeps its own variant and register.
Like the pattern detector, this is descriptive and never an authorship score.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from .text import fold, sentences

DATA = Path(__file__).resolve().parent / "data" / "ptbr_contextual.yml"
_QUOTES = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”|«[^»\n]*»")


@lru_cache(maxsize=1)
def data() -> dict:
    raw = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    markers = []
    for kind in ("lexical", "spelling"):
        for m in raw["variant_markers"][kind]:
            markers.append(dict(m, kind=kind, confidence=m.get("confidence", "exclusive"),
                                rx=re.compile(rf"\b(?:{m['pt']})\b", re.I if kind == "lexical" else 0)))
    for m in raw["variant_markers"]["syntax"]:
        markers.append(dict(m, kind="syntax", rx=re.compile(m["pt"], re.I),
                            skip_rx=re.compile(m["skip"], re.I) if m.get("skip") else None))
    raw["_markers"] = markers
    terms = {}
    for domain, mapping in raw["foreign_terms"].items():
        if domain == "genre_domains":
            continue
        for term, pt in mapping.items():
            terms[str(term).lower()] = (domain, str(pt))
    raw["_terms"] = terms
    raw["_terms_rx"] = re.compile(r"(?<![\w-])(" + "|".join(sorted((re.escape(t) for t in terms), key=len, reverse=True))
                                  + r")(?![\w-])", re.I)
    t = raw["treatment"]
    raw["_treatment"] = {k: re.compile(t[k], re.I) for k in ("formal", "voce", "tu")}
    o = raw["orality"]
    raw["_orality"] = {k: re.compile(o[k], re.I) for k in ("chat", "speech")}
    return raw


def _unquoted(text: str) -> str:
    """Blank out quoted material, keeping offsets."""
    return _QUOTES.sub(lambda m: " " * len(m.group(0)), text)


def _sentence_of(offset: int, sents) -> int:
    for s in sents:
        if s.start <= offset < s.end:
            return s.index
    return sents[-1].index if sents else 0


def variant_markers(text: str) -> list[dict]:
    plain = _unquoted(text)
    found = []
    for m in data()["_markers"]:
        for hit in m["rx"].finditer(plain):
            if m.get("skip_rx") and m["skip_rx"].search(hit.group(0)):
                continue
            found.append({"text": hit.group(0), "start": hit.start(), "end": hit.end(), "kind": m["kind"],
                          "pt_br": m["br"], "confidence": m.get("confidence", "exclusive"),
                          **({"meaning_sensitive": m["meaning_sensitive"]} if m.get("meaning_sensitive") else {}),
                          **({"note": m["note"]} if m.get("note") else {})})
    return sorted(found, key=lambda f: f["start"])


def foreign_terms(text: str, genre: str) -> dict:
    d = data()
    home = set(d["foreign_terms"]["genre_domains"].get(genre, d["foreign_terms"]["genre_domains"]["unknown"]))
    in_domain, out_domain = [], []
    for hit in d["_terms_rx"].finditer(_unquoted(text)):
        domain, pt = d["_terms"][hit.group(1).lower()]
        entry = {"text": hit.group(1), "start": hit.start(), "end": hit.end(), "domain": domain, "pt": pt}
        (in_domain if domain in home else out_domain).append(entry)
    return {"in_domain": in_domain, "out_of_domain": out_domain, "genre_domains": sorted(home)}


def treatment(text: str) -> dict:
    plain = _unquoted(text)
    forms = {name: [m.group(0) for m in rx.finditer(plain)] for name, rx in data()["_treatment"].items()}
    used = sorted(name for name, hits in forms.items() if hits)
    return {"forms": used, "examples": {k: v[:3] for k, v in forms.items() if v}}


def orality(text: str) -> dict:
    plain = _unquoted(text)
    return {kind: [m.group(0) for m in rx.finditer(plain)] for kind, rx in data()["_orality"].items()}


def _finding(fid, family, strength, text, start, end, sents, suggestion, **extra) -> dict:
    return {"id": fid, "family": family, "strength": strength, "text": text, "start": start, "end": end,
            "sentence": _sentence_of(start, sents), "suggestion": suggestion, **extra}


def findings(text: str, genre: str = "unknown", channel: str | None = None, register: str | None = None) -> list[dict]:
    """Findings in the pattern-report format, so the detector, the engine and
    the planner treat them like any other editorial finding."""
    d = data()
    sents = sentences(text)
    out = []
    markers = variant_markers(text)
    # Literary text (v0.6.0 CP10): a character's or a period's variant is the
    # text's material. On Machado de Assis (public domain, BR) the strong PT-PT
    # finding fired on pre-1943 Brazilian spelling ("acção", "facto") and on
    # 19th-century usage ("rapariga"), and drove 55% / 16% of segments to
    # `edit` (evals/corpus/LONGFORM_v0.6.md). In literature it is a note that
    # never counts toward an edit (ptbr-bench-v4 bv4-lt-03: three weak notes in
    # a 25-word dialogue still reached the weak threshold).
    literary = genre == "literary"
    # v0.7.0 CP5 (VN07-DISC-011): pre-reform Brazilian spelling ("acção",
    # "facto" next to "elle", "anno") is the time of the text, not PT-PT.
    from .router import infer_time_of_text
    historic = infer_time_of_text(text)["value"] == "pre_reform_orthography"
    literary = literary or historic
    for m in markers:
        exclusive = m["confidence"] == "exclusive" and not literary
        out.append(_finding("pt_pt_variant", "variante PT-PT", "strong" if exclusive else "weak", m["text"],
                            m["start"], m["end"], sents,
                            f"PT-BR: {m['pt_br']}" + (f" (atenção: {m['meaning_sensitive']}; confira o sentido)"
                                                      if m.get("meaning_sensitive") else ""),
                            **({"meaning_sensitive": True} if m.get("meaning_sensitive") else {}),
                            **({"note_only": True} if literary else {})))

    terms = foreign_terms(text, genre if not channel else _channel_genre(channel, genre))
    distinct = {t["text"].lower() for t in terms["out_of_domain"]}
    if distinct:
        strength = "strong" if len(distinct) >= 3 else "weak"
        for t in terms["out_of_domain"]:
            out.append(_finding("anglicism_out_of_domain", "estrangeirismo fora do domínio", strength, t["text"],
                                t["start"], t["end"], sents,
                                f"fora do domínio {t['domain']} prefira '{t['pt']}' se o leitor não usa o termo"))

    casual = (genre in d["orality"]["casual_genres"] or (channel or "") in d["orality"]["casual_genres"]
              or register in d["orality"]["casual_registers"])
    tr = treatment(text)
    plain = _unquoted(text)
    if literary:
        pass  # characters address each other differently; that is dialogue, not inconsistency
    elif "formal" in tr["forms"] and ("voce" in tr["forms"] or "tu" in tr["forms"]):
        hit = data()["_treatment"]["formal"].search(plain)
        out.append(_finding("treatment_mixed", "tratamento", "strong", hit.group(0), hit.start(), hit.end(), sents,
                            "escolha uma forma de tratamento: 'o senhor' ou 'você', e mantenha"))
    elif "voce" in tr["forms"] and "tu" in tr["forms"] and not casual and \
            register in set(d["treatment"]["formal_registers"]) | {"professional-natural"}:
        hit = data()["_treatment"]["tu"].search(plain)
        out.append(_finding("treatment_mixed", "tratamento", "weak", hit.group(0), hit.start(), hit.end(), sents,
                            "em registro profissional, mantenha 'você/seu' em vez de alternar com 'teu/contigo'"))

    if not casual and register:
        for m in data()["_orality"]["chat"].finditer(plain):
            out.append(_finding("orality_in_formal", "oralidade fora do registro", "strong", m.group(0),
                                m.start(), m.end(), sents, "abreviação de chat: escreva a palavra inteira"))
        if register in d["orality"]["formal_registers"]:
            for m in data()["_orality"]["speech"].finditer(plain):
                out.append(_finding("orality_in_formal", "oralidade fora do registro", "weak", m.group(0),
                                    m.start(), m.end(), sents, "forma da fala num registro formal: 'pra' -> 'para'"))
    return out


def _channel_genre(channel: str, genre: str) -> str:
    from .router import data as router_data
    return router_data().get("channel_genre", {}).get(channel.lower(), genre)


def candidate_issues(original: str, candidate: str, genre: str, register_explicit: bool = False) -> list[dict]:
    """What a PT-BR rewrite must not do to the source: introduce European
    Portuguese, translate the domain's own terms, or change the form of
    address nobody asked to change."""
    issues = []
    before = {fold(m["text"]) for m in variant_markers(original)}
    added = sorted({m["text"] for m in variant_markers(candidate) if fold(m["text"]) not in before})
    if added:
        issues.append({"code": "variant_drift", "severity": "major",
                       "message": f"candidate introduces European Portuguese forms: {added}", "examples": added})
    src_terms = {t["text"].lower() for t in foreign_terms(original, genre)["in_domain"]}
    out_low = candidate.lower()
    lost = sorted(t for t in src_terms if not re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", out_low))
    if lost:
        issues.append({"code": "domain_term_translated", "severity": "info",
                       "message": f"domain terms of the source are gone from the candidate: {lost}", "examples": lost})
    if not register_explicit:
        src, out = set(treatment(original)["forms"]), set(treatment(candidate)["forms"])
        if src and out and src != out:
            issues.append({"code": "treatment_changed", "severity": "major",
                           "message": f"form of address changed from {sorted(src)} to {sorted(out)} without a request"})
    return issues
