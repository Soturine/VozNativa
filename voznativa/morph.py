"""Verb morphology for Brazilian Portuguese (v0.7.0 CP9L): rules, not a model.

What it gives, per token that may be a verb: the form and its offsets, a
probable lemma, every analysis the ending allows (UD features: VerbForm,
Mood, Tense, Person, Number), the analyser id and version, and whether the
analysis is unique. Ambiguity is kept, never resolved by force: "falamos" is
present or preterite; "contrato" after "o" is not analysed at all.

Periphrases are reported as constructions on top of the tokens: progressive
("está terminando"), periphrastic future ("vai terminar"), compound
pluperfect ("tinha terminado"), compound future ("terá terminado"),
passive ("foi aprovado"). They describe aspect and the *morphological*
reference point; the time of the event in the discourse is not inferred
here (a "presente" can narrate the past).

Mapping to UD follows the Portuguese treebanks as annotated, checked on
Bosque, GSD and PetroGold (docs/adr/ADR-0002-linguistic-analysis.md):
futuro do pretérito = Mood=Cnd (no Tense); imperfeito do subjuntivo =
Mood=Sub|Tense=Imp; futuro do subjuntivo = Mood=Sub|Tense=Fut;
mais-que-perfeito simples = Tense=Pqp; pretérito perfeito = Tense=Past.

No third-party data is embedded: endings and the irregular table are
written here from Portuguese grammar; the treebanks are only used to
measure (scripts/morph_eval.py).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

ANALYZER = "voznativa.morph-rules"
VERSION = "1"

# (traditional name, UD features)
TENSES = {
    "pres_ind": ("presente do indicativo", {"VerbForm": "Fin", "Mood": "Ind", "Tense": "Pres"}),
    "pret_perf": ("pretérito perfeito", {"VerbForm": "Fin", "Mood": "Ind", "Tense": "Past"}),
    "pret_imp": ("pretérito imperfeito", {"VerbForm": "Fin", "Mood": "Ind", "Tense": "Imp"}),
    "pret_mqp": ("pretérito mais-que-perfeito", {"VerbForm": "Fin", "Mood": "Ind", "Tense": "Pqp"}),
    "fut_pres": ("futuro do presente", {"VerbForm": "Fin", "Mood": "Ind", "Tense": "Fut"}),
    "fut_pret": ("futuro do pretérito", {"VerbForm": "Fin", "Mood": "Cnd"}),
    "pres_sub": ("presente do subjuntivo", {"VerbForm": "Fin", "Mood": "Sub", "Tense": "Pres"}),
    "imp_sub": ("pretérito imperfeito do subjuntivo", {"VerbForm": "Fin", "Mood": "Sub", "Tense": "Imp"}),
    "fut_sub": ("futuro do subjuntivo", {"VerbForm": "Fin", "Mood": "Sub", "Tense": "Fut"}),
    "inf": ("infinitivo", {"VerbForm": "Inf"}),
    "ger": ("gerúndio", {"VerbForm": "Ger"}),
    "part": ("particípio", {"VerbForm": "Part"}),
}
P = [("1", "Sing"), ("2", "Sing"), ("3", "Sing"), ("1", "Plur"), ("2", "Plur"), ("3", "Plur")]
# Regular endings per conjugation vowel (a = -ar, e = -er, i = -ir), six persons.
# "você" takes the 3rd person; 2nd person forms are listed for completeness.
REGULAR = {
    "a": {"pres_ind": ["o", "as", "a", "amos", "ais", "am"], "pret_perf": ["ei", "aste", "ou", "amos", "astes", "aram"],
          "pret_imp": ["ava", "avas", "ava", "ávamos", "áveis", "avam"],
          "pret_mqp": ["ara", "aras", "ara", "áramos", "áreis", "aram"],
          "fut_pres": ["arei", "arás", "ará", "aremos", "areis", "arão"],
          "fut_pret": ["aria", "arias", "aria", "aríamos", "aríeis", "ariam"],
          "pres_sub": ["e", "es", "e", "emos", "eis", "em"], "imp_sub": ["asse", "asses", "asse", "ássemos", "ásseis", "assem"],
          "fut_sub": ["ar", "ares", "ar", "armos", "ardes", "arem"]},
    "e": {"pres_ind": ["o", "es", "e", "emos", "eis", "em"], "pret_perf": ["i", "este", "eu", "emos", "estes", "eram"],
          "pret_imp": ["ia", "ias", "ia", "íamos", "íeis", "iam"],
          "pret_mqp": ["era", "eras", "era", "êramos", "êreis", "eram"],
          "fut_pres": ["erei", "erás", "erá", "eremos", "ereis", "erão"],
          "fut_pret": ["eria", "erias", "eria", "eríamos", "eríeis", "eriam"],
          "pres_sub": ["a", "as", "a", "amos", "ais", "am"], "imp_sub": ["esse", "esses", "esse", "êssemos", "êsseis", "essem"],
          "fut_sub": ["er", "eres", "er", "ermos", "erdes", "erem"]},
    "i": {"pres_ind": ["o", "es", "e", "imos", "is", "em"], "pret_perf": ["i", "iste", "iu", "imos", "istes", "iram"],
          "pret_imp": ["ia", "ias", "ia", "íamos", "íeis", "iam"],
          "pret_mqp": ["ira", "iras", "ira", "íramos", "íreis", "iram"],
          "fut_pres": ["irei", "irás", "irá", "iremos", "ireis", "irão"],
          "fut_pret": ["iria", "irias", "iria", "iríamos", "iríeis", "iriam"],
          "pres_sub": ["a", "as", "a", "amos", "ais", "am"], "imp_sub": ["isse", "isses", "isse", "íssemos", "ísseis", "issem"],
          "fut_sub": ["ir", "ires", "ir", "irmos", "irdes", "irem"]},
}
NON_FINITE = {"a": {"inf": "ar", "ger": "ando", "part": ["ado", "ada", "ados", "adas"]},
              "e": {"inf": "er", "ger": "endo", "part": ["ido", "ida", "idos", "idas"]},
              "i": {"inf": "ir", "ger": "indo", "part": ["ido", "ida", "idos", "idas"]}}
# Endings too ambiguous with nouns/adjectives to analyse without a verbal context
# ("casa", "contrato", "doce"): only after a subject pronoun, "não" or a clitic.
WEAK_ENDINGS = {"o", "a", "e", "as", "es", "am", "em", "ar", "er", "ir", "ado", "ada", "ados", "adas", "ido",
                "ida", "idos", "idas", "i", "is", "ara", "era", "ira"}

# Irregular forms written from grammar (frequent auxiliaries and verbs).
IRREGULAR = {
    "ser": {"pres_ind": ["sou", "és", "é", "somos", "sois", "são"], "pret_perf": ["fui", "foste", "foi", "fomos", "fostes", "foram"],
            "pret_imp": ["era", "eras", "era", "éramos", "éreis", "eram"], "fut_pres": ["serei", "serás", "será", "seremos", "sereis", "serão"],
            "fut_pret": ["seria", "serias", "seria", "seríamos", "seríeis", "seriam"],
            "pres_sub": ["seja", "sejas", "seja", "sejamos", "sejais", "sejam"],
            "imp_sub": ["fosse", "fosses", "fosse", "fôssemos", "fôsseis", "fossem"],
            "fut_sub": ["for", "fores", "for", "formos", "fordes", "forem"], "inf": ["ser"], "ger": ["sendo"], "part": ["sido"]},
    "estar": {"pres_ind": ["estou", "estás", "está", "estamos", "estais", "estão"],
              "pret_perf": ["estive", "estiveste", "esteve", "estivemos", "estivestes", "estiveram"],
              "pret_imp": ["estava", "estavas", "estava", "estávamos", "estáveis", "estavam"],
              "pres_sub": ["esteja", "estejas", "esteja", "estejamos", "estejais", "estejam"],
              "imp_sub": ["estivesse", "estivesses", "estivesse", "estivéssemos", "estivésseis", "estivessem"],
              "fut_sub": ["estiver", "estiveres", "estiver", "estivermos", "estiverdes", "estiverem"],
              "fut_pres": ["estarei", "estarás", "estará", "estaremos", "estareis", "estarão"],
              "fut_pret": ["estaria", "estarias", "estaria", "estaríamos", "estaríeis", "estariam"],
              "inf": ["estar"], "ger": ["estando"], "part": ["estado"]},
    "ter": {"pres_ind": ["tenho", "tens", "tem", "temos", "tendes", "têm"], "pret_perf": ["tive", "tiveste", "teve", "tivemos", "tivestes", "tiveram"],
            "pret_imp": ["tinha", "tinhas", "tinha", "tínhamos", "tínheis", "tinham"], "fut_pres": ["terei", "terás", "terá", "teremos", "tereis", "terão"],
            "fut_pret": ["teria", "terias", "teria", "teríamos", "teríeis", "teriam"],
            "pres_sub": ["tenha", "tenhas", "tenha", "tenhamos", "tenhais", "tenham"],
            "imp_sub": ["tivesse", "tivesses", "tivesse", "tivéssemos", "tivésseis", "tivessem"],
            "fut_sub": ["tiver", "tiveres", "tiver", "tivermos", "tiverdes", "tiverem"], "inf": ["ter"], "ger": ["tendo"], "part": ["tido"]},
    "haver": {"pres_ind": ["hei", "hás", "há", "havemos", "haveis", "hão"], "pret_perf": ["houve", "houveste", "houve", "houvemos", "houvestes", "houveram"],
              "pret_imp": ["havia", "havias", "havia", "havíamos", "havíeis", "haviam"],
              "fut_pres": ["haverei", "haverás", "haverá", "haveremos", "havereis", "haverão"],
              "fut_pret": ["haveria", "haverias", "haveria", "haveríamos", "haveríeis", "haveriam"],
              "pres_sub": ["haja", "hajas", "haja", "hajamos", "hajais", "hajam"],
              "imp_sub": ["houvesse", "houvesses", "houvesse", "houvéssemos", "houvésseis", "houvessem"],
              "fut_sub": ["houver", "houveres", "houver", "houvermos", "houverdes", "houverem"], "inf": ["haver"], "ger": ["havendo"], "part": ["havido"]},
    "ir": {"pres_ind": ["vou", "vais", "vai", "vamos", "ides", "vão"], "pret_perf": ["fui", "foste", "foi", "fomos", "fostes", "foram"],
           "pret_imp": ["ia", "ias", "ia", "íamos", "íeis", "iam"], "fut_pres": ["irei", "irás", "irá", "iremos", "ireis", "irão"],
           "fut_pret": ["iria", "irias", "iria", "iríamos", "iríeis", "iriam"], "pres_sub": ["vá", "vás", "vá", "vamos", "vades", "vão"],
           "imp_sub": ["fosse", "fosses", "fosse", "fôssemos", "fôsseis", "fossem"], "fut_sub": ["for", "fores", "for", "formos", "fordes", "forem"],
           "inf": ["ir"], "ger": ["indo"], "part": ["ido"]},
    "fazer": {"pres_ind": ["faço", "fazes", "faz", "fazemos", "fazeis", "fazem"], "pret_perf": ["fiz", "fizeste", "fez", "fizemos", "fizestes", "fizeram"],
              "fut_pres": ["farei", "farás", "fará", "faremos", "fareis", "farão"], "fut_pret": ["faria", "farias", "faria", "faríamos", "faríeis", "fariam"],
              "pres_sub": ["faça", "faças", "faça", "façamos", "façais", "façam"],
              "imp_sub": ["fizesse", "fizesses", "fizesse", "fizéssemos", "fizésseis", "fizessem"],
              "fut_sub": ["fizer", "fizeres", "fizer", "fizermos", "fizerdes", "fizerem"], "part": ["feito", "feita", "feitos", "feitas"]},
    "poder": {"pres_ind": ["posso", "podes", "pode", "podemos", "podeis", "podem"], "pret_perf": ["pude", "pudeste", "pôde", "pudemos", "pudestes", "puderam"],
              "pres_sub": ["possa", "possas", "possa", "possamos", "possais", "possam"],
              "imp_sub": ["pudesse", "pudesses", "pudesse", "pudéssemos", "pudésseis", "pudessem"],
              "fut_sub": ["puder", "puderes", "puder", "pudermos", "puderdes", "puderem"]},
    "dizer": {"pres_ind": ["digo", "dizes", "diz", "dizemos", "dizeis", "dizem"], "pret_perf": ["disse", "disseste", "disse", "dissemos", "dissestes", "disseram"],
              "fut_pres": ["direi", "dirás", "dirá", "diremos", "direis", "dirão"], "fut_pret": ["diria", "dirias", "diria", "diríamos", "diríeis", "diriam"],
              "part": ["dito", "dita", "ditos", "ditas"]},
}
AUX_PROGRESSIVE = {"estar"}
AUX_FUTURE = {"ir"}
AUX_COMPOUND = {"ter", "haver"}
AUX_PASSIVE = {"ser", "estar"}
DETERMINERS = set("o a os as um uma uns umas do da dos das no na nos nas ao aos à às pelo pela pelos pelas "
                  "este esta estes estas esse essa esses essas aquele aquela meu minha seu sua nosso nossa "
                  "cujo cuja todo toda".split())
VERBAL_CONTEXT = set("eu tu ele ela nós vós eles elas você vocês a gente não nunca já se me te lhe nos vos lhes "
                     "que quando".split())
ARTICLES = set("o a os as um uma uns umas".split())
# Frequent non-verbs that end like a gerund or a participle.
NON_VERBS = set("quando enquanto comando bando lindo linda segundo segunda fundo mundo tudo nada cada ".split()
                + "lado cuidado obrigado obrigada estado mercado resultado pedido sentido partido conteúdo".split())
_WORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.U)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s.lower())


def _build_irregular() -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for lemma, table in IRREGULAR.items():
        for code, forms in table.items():
            if code in ("inf", "ger", "part"):
                for f in forms:
                    index.setdefault(f, []).append({"lemma": lemma, "tense": code, **TENSES[code][1]})
                continue
            for (person, number), form in zip(P, forms):
                index.setdefault(form, []).append({"lemma": lemma, "tense": code, "Person": person, "Number": number,
                                                   **TENSES[code][1]})
    return index


IRREGULAR_INDEX = _build_irregular()
_ENDINGS = sorted({(e, vowel, code, i) for vowel, table in REGULAR.items() for code, ends in table.items()
                   for i, e in enumerate(ends)}, key=lambda x: -len(x[0]))


def analyse_word(word: str) -> list[dict]:
    """Every analysis the form allows (irregular table first, then regular
    endings with a plausible stem). Empty when nothing fits."""
    w = _nfc(word)
    if w in NON_VERBS:
        return []
    if w in IRREGULAR_INDEX:
        return [dict(a, ending=None, source="irregular") for a in IRREGULAR_INDEX[w]]
    out = []
    for ending, vowel, code, i in _ENDINGS:
        if not w.endswith(ending):
            continue
        stem = w[:-len(ending)]
        if len(stem) < 2 or not re.search(r"[aeiouáéíóúâêôãõ]", stem):
            continue
        # "falaria" is not the imperfect of a verb "falarer": a stem ending in a conjugation
        # vowel + r before an -ia/-ra ending is the future/conditional of that verb.
        if code in ("pret_imp", "pret_mqp", "pres_sub") and re.search(r"[aei]r$", stem):
            continue
        person, number = P[i]
        out.append({"lemma": stem + {"a": "ar", "e": "er", "i": "ir"}[vowel], "tense": code, "Person": person,
                    "Number": number, "ending": ending, "source": "regular", **TENSES[code][1]})
    for vowel, nf in NON_FINITE.items():
        for code, ends in nf.items():
            for ending in ([ends] if isinstance(ends, str) else ends):
                stem = w[:-len(ending)]
                if w.endswith(ending) and len(stem) >= (3 if code == "ger" else 2)                         and re.search(r"[aeiouáéíóúâêôãõ]", stem):
                    out.append({"lemma": stem + {"a": "ar", "e": "er", "i": "ir"}[vowel], "tense": code,
                                "ending": ending, "source": "regular", **TENSES[code][1]})
    # Keep only the longest ending per (tense, person, number): "falaria" is -aria, not -ia.
    best: dict[tuple, dict] = {}
    for a in out:
        key = (a["tense"], a.get("Person"), a.get("Number"), a["lemma"][-2:])
        if key not in best or len(a["ending"]) > len(best[key]["ending"]):
            best[key] = a
    return list(best.values())


@dataclass
class VerbToken:
    form: str
    start: int
    end: int
    analyses: list = field(default_factory=list)

    @property
    def tenses(self) -> set:
        return {a["tense"] for a in self.analyses}

    @property
    def lemmas(self) -> set:
        return {a["lemma"] for a in self.analyses}

    @property
    def unique(self) -> bool:
        return len(self.tenses) == 1

    def as_dict(self) -> dict:
        return {"form": self.form, "start": self.start, "end": self.end, "analyzer": f"{ANALYZER}@{VERSION}",
                "status": "unique" if self.unique else "ambiguous", "lemmas": sorted(self.lemmas),
                "tenses": sorted(self.tenses), "analyses": self.analyses}


def verbs(text: str, prefer_indicative: bool = False) -> list[VerbToken]:
    """Tokens that may be verbs, with every analysis kept. Weak endings
    ("-o", "-a", "-ado"...) count only in a verbal context (after a subject
    pronoun, "não", a clitic or an auxiliary) and never right after a determiner."""
    tokens = [(m.group(0), m.start(), m.end()) for m in _WORD.finditer(text)]

    def sentence_initial(k: int) -> bool:
        return k == 0 or bool(re.search(r"[.!?:;\n]", text[tokens[k - 1][2]:tokens[k][1]]))

    def is_name(k: int) -> bool:
        return tokens[k][0][:1].isupper() and not sentence_initial(k)

    out = []
    for k, (word, start, end) in enumerate(tokens):
        prev = _nfc(tokens[k - 1][0]) if k else ""
        nxt = _nfc(tokens[k + 1][0]) if k + 1 < len(tokens) else ""
        if prev in DETERMINERS or is_name(k):
            continue
        analyses = analyse_word(word)
        if not analyses:
            continue
        strong = [a for a in analyses if a["source"] == "irregular" or a["ending"] not in WEAK_ENDINGS]
        if not strong:
            subject_before = k > 0 and (prev in VERBAL_CONTEXT or prev in IRREGULAR_INDEX or is_name(k - 1))
            object_after = (k + 1 < len(tokens) and nxt in ARTICLES
                            and not re.search(r"[.!?;:,]", text[end:tokens[k + 1][1]]))
            if not (subject_before or object_after):
                continue
            strong = analyses
        tenses = {a["tense"] for a in strong}
        if prefer_indicative and "pres_sub" in tenses and "pres_ind" in tenses:
            # The present subjunctive needs a trigger ("que", "talvez", "embora"...) earlier in the
            # clause; without one, the indicative reading stays. Off by default: measured on UD
            # (morph-2026-11-06-trigger.json) it raises unique analyses by 5-11 points but lowers
            # their accuracy by 0.5-3.4 and nearly doubles verb readings of non-verbs.
            clause = text[max(0, start - 60):start]
            clause = re.split(r"[.!?;:]", clause)[-1]
            if not _SUBJUNCTIVE_TRIGGER.search(clause):
                strong = [a for a in strong if a["tense"] != "pres_sub"]
        out.append(VerbToken(word, start, end, strong))
    return out


_SUBJUNCTIVE_TRIGGER = re.compile(r"\b(?:que|talvez|embora|caso|tomara|oxalá|quiçá|conquanto|contanto)\b", re.I)


def constructions(text: str, prefer_indicative: bool = False) -> list[dict]:
    """Periphrases: auxiliary + non-finite form, with the aspect or time
    reference they encode. Only adjacent pairs (or with one clitic/"não" between)."""
    vs = verbs(text, prefer_indicative)
    out = []
    for a, b in zip(vs, vs[1:]):
        gap = text[a.end:b.start]
        if len(gap.split()) > 1 or re.search(r"[.!?;:]", gap):
            continue
        aux = {x["lemma"] for x in a.analyses if x["source"] == "irregular"}
        b_forms = b.tenses
        kind, need = None, None
        if aux & AUX_PROGRESSIVE and "ger" in b_forms:
            kind, aspect, need = "progressive", "progressive", "ger"
        elif aux & AUX_FUTURE and "inf" in b_forms:
            kind, aspect, need = "periphrastic_future", "prospective", "inf"
        elif aux & AUX_COMPOUND and "part" in b_forms:
            kind, aspect, need = "compound_perfect", "perfect", "part"
        elif aux & AUX_PASSIVE and "part" in b_forms:
            kind, aspect, need = "passive", None, "part"
        if kind:
            lemmas = sorted({x["lemma"] for x in b.analyses if x["tense"] == need})
            aux_tenses = sorted({x["tense"] for x in a.analyses if x["lemma"] in
                                 (AUX_PROGRESSIVE | AUX_FUTURE | AUX_COMPOUND | AUX_PASSIVE)})
            out.append({"construction": kind, "aspect": aspect, "auxiliary": a.form, "main": b.form,
                        "auxiliary_tenses": aux_tenses, "main_lemmas": lemmas,
                        "start": a.start, "end": b.end})
    return out


def tense_profile(text: str, prefer_indicative: bool = False) -> dict[str, set]:
    """Main-verb lemma -> the set of unambiguous tense/construction labels in
    ``text``. Auxiliaries fold into their construction ("tinha terminado" ->
    terminar: compound_perfect@pret_imp)."""
    profile: dict[str, set] = {}
    cons = constructions(text, prefer_indicative)
    covered = set()
    for c in cons:
        for lemma in c["main_lemmas"]:
            # Voice is not tense: "foi aprovado" is compared as the auxiliary's tense.
            label = ("/".join(c["auxiliary_tenses"]) if c["construction"] == "passive"
                     else f"{c['construction']}@{'/'.join(c['auxiliary_tenses'])}")
            profile.setdefault(lemma, set()).add(label)
        covered |= {c["start"], c["end"]}
    for v in verbs(text, prefer_indicative):
        if v.start in covered or v.end in covered or not v.unique:
            continue
        if any(a["source"] == "irregular" and a["lemma"] in AUX_PROGRESSIVE | AUX_FUTURE | AUX_COMPOUND
               for a in v.analyses) and len(v.lemmas) > 1:
            continue
        for lemma in v.lemmas:
            profile.setdefault(lemma, set()).add(next(iter(v.tenses)))
    return profile
