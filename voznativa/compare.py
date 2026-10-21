"""Compare a candidate rewrite against its source through the Semantic Ledger.

Verdict policy (conservative by design):

* ``identical``: same text after whitespace/quote normalization. The only
  case where equivalence is proven deterministically.
* ``fail``: a deterministic check found a violation (protected value lost,
  changed, swapped or added; a negation/modality flip in an aligned sentence).
* ``review_required``: a heuristic found a change that may alter meaning.
* ``no_deterministic_issues``: nothing was found, which is *not* proof of
  equivalence. ``semantic_equivalence`` stays ``"unverified"`` until a judge
  (LLM or human) records a verdict through :func:`apply_judgment`.
"""
from __future__ import annotations

import re
from collections import Counter

from . import ledger as ledger_mod
from . import spans as spans_mod
from . import signals
from .spans import HARD_TYPES
from .text import STOPWORDS, contains_word, content_stems, fold, normalize_surface, stem

_STOP_FOLDED = frozenset(fold(w) for w in STOPWORDS)

SCHEMA_VERSION = 1

# Thresholds are heuristic and uncalibrated; evals pin their behavior.
ALIGN_MIN_SIMILARITY = 0.5
OMISSION_MAX_COVERAGE = 0.4
ADDITION_MIN_NOVELTY = 0.6
MIN_STEMS_FOR_COVERAGE = 3
LENGTH_RATIO_BOUNDS = (0.5, 1.8)

INLINE_ADDITION_MIN_NEW_STEMS = 4
CLAUSE_MIN_NEW_STEMS = 2
CLAUSE_MIN_NOVELTY = 0.66

LIMITATIONS = [
    "Marker counts cannot see lexical antonyms (aumentou/diminuiu) or morphological negation (impossível).",
    "Sentence alignment uses crude stem overlap; heavy restructuring produces review flags, not proof.",
    "Entity detection relies on capitalization and misses lower-case names.",
    "No deterministic result proves semantic equivalence; only identity does.",
]


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _issue(code: str, severity: str, message: str, **extra) -> dict:
    return {"code": code, "severity": severity, "message": message, **extra}


def compare(original: str, candidate: str, protect: list[str] | tuple = ()) -> dict:
    if normalize_surface(original) == normalize_surface(candidate):
        return _report("identical", [], original, candidate)

    src = ledger_mod.build(original, protect)
    out = ledger_mod.build(candidate, protect)
    issues: list[dict] = []
    issues += _span_issues(src, out)
    issues += _binding_issues(src, out)
    alignment = _align(src, out)
    issues += _signal_issues(src, out, alignment)
    issues += _causal_direction_issues(src, out, alignment)
    issues += _polarity_issues(src, out, alignment)
    issues += _attribution_issues(src, out)
    issues += _coverage_issues(src, out)
    issues += _length_issues(original, candidate)
    issues += _structure_issues(src, out)

    if any(i["severity"] == "critical" for i in issues):
        status = "fail"
    elif any(i["severity"] == "major" for i in issues):
        status = "review_required"
    else:
        status = "no_deterministic_issues"
    return _report(status, issues, original, candidate, src=src, out=out)


def _report(status, issues, original, candidate, src=None, out=None) -> dict:
    equivalence = {"identical": "identical", "fail": "violated"}.get(status, "unverified")
    requires = []
    if status == "review_required":
        requires = ["human_review"]
    elif status == "no_deterministic_issues":
        requires = ["semantic_judgment"]
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "voznativa.comparison",
        "status": status,
        "semantic_equivalence": equivalence,
        "safe_to_auto_accept": status == "identical",
        "requires": requires,
        "issues": issues,
        "summary": {
            "critical": sum(i["severity"] == "critical" for i in issues),
            "major": sum(i["severity"] == "major" for i in issues),
            "info": sum(i["severity"] == "info" for i in issues),
            "protected_in_original": len(src.spans) if src else None,
            "words_original": len(original.split()),
            "words_candidate": len(candidate.split()),
        },
        "evidence": {"deterministic": True, "judgments": []},
        "limitations": LIMITATIONS,
    }


def _span_issues(src, out) -> list[dict]:
    issues = []
    before = Counter(s.key for s in src.spans)
    after = Counter(s.key for s in out.spans)
    sample = {s.key: s for s in src.spans}
    sample_out = {s.key: s for s in out.spans}

    for key, expected in before.items():
        span = sample[key]
        actual = after.get(key, 0)
        if span.type == "entity":
            # Entities are checked by presence: rewrites legitimately drop repeats
            # and move names to sentence start, where extraction skips them.
            if not contains_word(out.text, span.text):
                issues.append(_issue("span_missing", "critical", f"entity lost: {span.text}",
                                     type="entity", text=span.text, expected_count=expected, actual_count=0))
            continue
        if actual < expected:
            issues.append(_issue(
                "span_missing", "critical",
                f"{span.type} '{span.text}' expected {expected}x, found {actual}x",
                type=span.type, text=span.text, key=key, expected_count=expected, actual_count=actual))

    for key, count in after.items():
        span = sample_out[key]
        if span.type == "entity":
            if not contains_word(src.text, span.text):
                issues.append(_issue("span_added", "major", f"entity not in source: {span.text}",
                                     type="entity", text=span.text))
            continue
        if key not in before:
            severity = "critical" if span.type in HARD_TYPES else "major"
            issues.append(_issue("span_added", severity, f"{span.type} '{span.text}' is not in the source",
                                 type=span.type, text=span.text, key=key, actual_count=count))
        elif count > before[key]:
            issues.append(_issue("span_repeated", "major",
                                 f"{span.type} '{span.text}' appears {count}x, source has {before[key]}x",
                                 type=span.type, text=span.text, key=key))
    return issues


def _mutual_swaps(a_src: dict, a_out: dict) -> list[tuple[str, str]]:
    """Keys A and B such that A now sits where B was AND B where A was.
    Requiring both directions keeps plain reordering from firing."""
    swaps, seen = [], set()
    for key_a, src_a in a_src.items():
        out_a = a_out.get(key_a)
        if not out_a or src_a & out_a:
            continue
        for key_b, src_b in a_src.items():
            if key_b == key_a or (key_b, key_a) in seen:
                continue
            out_b = a_out.get(key_b)
            if out_b and not (src_b & out_b) and (out_a & src_b) and (out_b & src_a):
                seen.add((key_a, key_b))
                swaps.append((key_a, key_b))
    return swaps


def _entity_anchors(led, entity_texts: dict[str, str]) -> dict[str, set]:
    """Anchors of each source entity wherever it occurs (by whole word), so a
    name moved to sentence start, where extraction skips it, is still found."""
    table: dict[str, set] = {}
    for key, text in entity_texts.items():
        for m in re.finditer(r"(?<!\w)" + re.escape(text) + r"(?!\w)", led.text, re.IGNORECASE):
            table.setdefault(key, set()).update(spans_mod._anchors(led.text, m.start(), m.end()))
    return table


def _binding_issues(src, out) -> list[dict]:
    """Detect values and entities that kept their presence but swapped the
    words they attach to: "17 casos e 71 erros" -> "71 casos e 17 erros",
    "a Ana revisa e o Bruno assina" -> "o Bruno revisa e a Ana assina"."""
    def anchors_by_key(led):
        table: dict[str, set] = {}
        for s in led.spans:
            if s.type in HARD_TYPES and s.anchors:
                table.setdefault(s.key, set()).update(s.anchors)
        return table

    issues = []
    for key_a, key_b in _mutual_swaps(anchors_by_key(src), anchors_by_key(out)):
        texts = [next(s.text for s in src.spans if s.key == k) for k in (key_a, key_b)]
        issues.append(_issue("binding_changed", "critical",
                             f"'{texts[0]}' and '{texts[1]}' swapped the words they qualify",
                             key=key_a, text=texts[0], swapped_with=texts[1]))

    entities = {s.key: s.text for s in src.spans if s.type == "entity"}
    if len(entities) >= 2:
        names = list(entities.values())
        role_issues, preserved = _role_issues(src, out, names)
        issues += role_issues
        for key_a, key_b in _mutual_swaps(_entity_anchors(src, entities), _entity_anchors(out, entities)):
            pair = frozenset({entities[key_a].casefold(), entities[key_b].casefold()})
            if pair in preserved:
                continue  # active <-> passive rewrite that keeps who did what to whom
            issues.append(_issue("entity_binding_changed", "critical",
                                 f"'{entities[key_a]}' and '{entities[key_b]}' swapped roles "
                                 "(each now attaches to the other's words)",
                                 text=entities[key_a], swapped_with=entities[key_b]))
    return issues


_PASSIVE = re.compile(
    r"^\s*(?:foi|foram|é|são|será|serão|era|eram|seria|seriam|seja|sejam|fosse|fossem|"
    r"tinha sido|tinham sido|tem sido|têm sido|está sendo|estava sendo)\s+(\w+)\s+(?:\w+\s+){0,2}?"
    r"(?:por|pelo|pela|pelos|pelas)\s*$", re.I)
_ACTIVE = re.compile(r"^\s*(?:\w+\s+){0,2}?(\w+)\s+(?:o|a|os|as|ao|à|aos|às)?\s*$", re.I)
_LINKERS = re.compile(r"[,;:]|\s(?:e|ou|mas|que)\s", re.I)


def _role_triples(text: str, names: list[str]) -> set[tuple[str, str, str]]:
    """(agent, verb stem, patient) between two named entities in one clause.
    Passive: "A XP foi adquirida pelo Itaú" -> (itaú, adqui, xp).
    Active: "O Itaú adquiriu a XP" -> (itaú, adqui, xp). Coordinated or
    longer stretches are skipped rather than guessed."""
    hits = sorted((m.start(), m.end(), name.casefold()) for name in names
                  for m in re.finditer(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text, re.IGNORECASE))
    triples = set()
    for (s1, e1, a), (s2, e2, b) in zip(hits, hits[1:]):
        between = text[e1:s2]
        if a == b or _LINKERS.search(between) or len(between.split()) > 6:
            continue
        passive = _PASSIVE.match(between)
        if passive:
            triples.add((b, stem(passive.group(1)), a))
            continue
        active = _ACTIVE.match(between)
        if active and fold(active.group(1)) not in _STOP_FOLDED:
            triples.add((a, stem(active.group(1)), b))
    return triples


def _role_issues(src, out, names: list[str]) -> tuple[list[dict], set]:
    issues, preserved = [], set()
    out_triples = _role_triples(out.text, names)
    for agent, verb, patient in _role_triples(src.text, names):
        pair = frozenset({agent, patient})
        if (agent, verb, patient) in out_triples:
            preserved.add(pair)
        elif (patient, verb, agent) in out_triples:
            issues.append(_issue("role_reversed", "critical",
                                 f"'{agent}' and '{patient}' swapped agent and patient of the same action",
                                 text=agent, swapped_with=patient, verb=verb))
    return issues, preserved


def _align(src, out) -> list[tuple[int, int | None, float]]:
    pairs = []
    for i, entry in enumerate(src.entries):
        a = set(entry.stems)
        best, best_sim = None, 0.0
        for j, cand in enumerate(out.entries):
            sim = _jaccard(a, set(cand.stems))
            if len(a) < 2 or len(cand.stems) < 2:
                # Short sentences ("Não vou." -> "Vou.") have no content stems;
                # compare every non-marker word instead.
                sim = max(sim, _jaccard(set(entry.tokens), set(cand.tokens)))
                if (not entry.tokens and not cand.tokens and i == j
                        and len(src.entries) == len(out.entries)):
                    # Both sentences are made only of markers ("nn posso" -> "posso");
                    # with the same sentence count, position is the best alignment.
                    sim = 1.0
            if sim > best_sim:
                best, best_sim = j, sim
        pairs.append((i, best, round(best_sim, 3)))
    return pairs


def _bucket(counts: Counter) -> Counter:
    """Collapse category-level categories (negation) into one bucket so that
    "não é possível" and "é impossível" count as the same negation."""
    merged = Counter()
    level = signals.category_level()
    for label, n in counts.items():
        category = label.split(".")[0]
        merged[category if category in level else label] += n
    return merged


def _signal_issues(src, out, alignment) -> list[dict]:
    issues = []
    before, after = _bucket(src.signal_counts()), _bucket(out.signal_counts())
    for label in sorted(set(before) | set(after)):
        delta = after.get(label, 0) - before.get(label, 0)
        if delta == 0:
            continue
        category = label.split(".")[0]
        located = None
        for i, j, sim in alignment:
            if j is None or sim < ALIGN_MIN_SIMILARITY:
                continue
            s_count = _bucket(src.entries[i].signal_counts()).get(label, 0)
            c_count = _bucket(out.entries[j].signal_counts()).get(label, 0)
            if (c_count - s_count) * delta > 0:
                located = {"source_sentence": src.entries[i].sentence.text,
                           "candidate_sentence": out.entries[j].sentence.text, "similarity": sim}
                break
        rules = signals.severity_rules()
        if category in rules["informational"] or label in rules["informational"]:
            severity = "info"
        elif located and category in rules["critical_when_localized"] and not (
                delta > 0 and label in rules["review_only_on_addition"]):
            severity = "critical"
        else:
            severity = "major"
        direction = "added" if delta > 0 else "removed"
        issues.append(_issue(
            f"{category}_changed", severity,
            f"{label} marker {direction} ({before.get(label, 0)} -> {after.get(label, 0)})",
            label=label, before=before.get(label, 0), after=after.get(label, 0),
            location=located,
            examples=_marker_examples(src if delta < 0 else out, label)))
    return issues


def _cause_effect(entry) -> tuple[set, set] | None:
    causal = [m for m in entry.markers if m.label == "causality.causal"]
    if len(causal) != 1:  # zero or several connectors: direction is ambiguous
        return None
    m = causal[0]
    before = set(content_stems(entry.sentence.text[:m.start]))
    after = set(content_stems(entry.sentence.text[m.end:]))
    return (after, before) if signals.causal_orientation(m.phrase) == "backward" else (before, after)


def _causal_relations(led) -> list[tuple[set, set, str]]:
    """(cause stems, effect stems, sentence) for every causal link the text
    states: inside one sentence ("X porque Y") and across adjacent sentences
    when a forward connector opens the second one ("X. Por isso, Y.")."""
    relations = []
    for k, entry in enumerate(led.entries):
        causal = [m for m in entry.markers if m.label == "causality.causal"]
        opener = causal[0] if causal and not entry.sentence.text[:causal[0].start].strip(" \"'(") else None
        if opener and k > 0 and len(causal) == 1 and signals.causal_orientation(opener.phrase) == "forward" \
                and led.entries[k - 1].sentence.paragraph == entry.sentence.paragraph:
            relations.append((set(led.entries[k - 1].stems), set(content_stems(entry.sentence.text[opener.end:])),
                              led.entries[k - 1].sentence.text + " " + entry.sentence.text))
            continue
        pair = _cause_effect(entry)
        if pair and pair[0] and pair[1]:
            relations.append((pair[0], pair[1], entry.sentence.text))
    return relations


def _causal_direction_issues(src, out, alignment=None) -> list[dict]:
    """A stated cause and effect that traded places, inside a sentence
    ("a falha causou a queda" -> "a queda causou a falha") or across
    sentences ("X. Por isso, Y." -> "Y. Por isso, X.")."""
    issues = []
    candidates = _causal_relations(out)
    for o_cause, o_effect, o_text in _causal_relations(src):
        best = max(candidates, key=lambda r: _jaccard(o_cause | o_effect, r[0] | r[1]), default=None)
        if not best or _jaccard(o_cause | o_effect, best[0] | best[1]) < 0.4:
            continue
        c_cause, c_effect, c_text = best
        crossed = _jaccard(c_cause, o_effect), _jaccard(c_effect, o_cause)
        kept = _jaccard(c_cause, o_cause), _jaccard(c_effect, o_effect)
        if min(crossed) >= 0.3 and crossed[0] > kept[0] and crossed[1] > kept[1]:
            issues.append(_issue("causal_direction_reversed", "critical", "cause and effect traded places",
                                 location={"source_sentence": o_text, "candidate_sentence": c_text}))
    return issues


def _polarity_issues(src, out, alignment) -> list[dict]:
    """A polarity class replaced by its antonym in an aligned sentence
    ("aumentou" -> "diminuiu", "aprovado" -> "recusado")."""
    issues = []
    for i, j, sim in alignment:
        if j is None or sim < ALIGN_MIN_SIMILARITY:
            continue
        before, after = src.entries[i].signal_counts(), out.entries[j].signal_counts()
        for x, y in signals.polarity_antonyms():
            lx, ly = f"polarity.{x}", f"polarity.{y}"
            for lost, gained in ((lx, ly), (ly, lx)):
                if after.get(lost, 0) < before.get(lost, 0) and after.get(gained, 0) > before.get(gained, 0):
                    issues.append(_issue("polarity_flipped", "critical",
                                         f"{lost} replaced by its antonym {gained}",
                                         location={"source_sentence": src.entries[i].sentence.text,
                                                   "candidate_sentence": out.entries[j].sentence.text}))
    return issues


PREPOSED_SOURCE = {"segundo", "de acordo com", "conforme"}


def _attributions(led, entity_texts: list[str]) -> dict[str, set]:
    """Map each source entity to the content it introduces, clause by clause:
    'A Ana disse que X' (source before the verb), 'Segundo o IBGE, X' and
    'X, segundo o IBGE' (preposed/postposed source)."""
    table: dict[str, set] = {}
    for entry in led.entries:
        text = entry.sentence.text
        bounds = [0] + [m.end() for m in re.finditer(r";", text)] + [len(text) + 1]
        for k in range(len(bounds) - 1):
            lo, hi = bounds[k], bounds[k + 1] - 1
            clause = text[lo:hi]
            marks = [m for m in entry.markers if m.category == "attribution" and lo <= m.start < hi]
            if len(marks) != 1:
                continue
            m = marks[0]
            m_start, m_end = m.start - lo, m.end - lo
            found = []
            for name in entity_texts:
                for hit in re.finditer(r"(?<!\w)" + re.escape(name) + r"(?!\w)", clause, re.IGNORECASE):
                    found.append((hit.start(), hit.end(), name))
            if fold(m.phrase) in {fold(p) for p in PREPOSED_SOURCE}:
                after = [f for f in found if f[0] >= m_end]
                if not after:
                    continue
                start, end, name = min(after)
                claim = clause[end:] if m_start <= 2 else clause[:m_start]
            else:
                before = [f for f in found if f[1] <= m_start]
                if not before:
                    continue
                start, end, name = max(before)
                claim = clause[m_end:]
            table.setdefault(name.casefold(), set()).update(content_stems(claim))
    return table


def _attribution_issues(src, out) -> list[dict]:
    """Two sources that traded the claims they are credited with."""
    names = sorted({s.text for s in src.spans if s.type == "entity"})
    if len(names) < 2:
        return []
    a_src, a_out = _attributions(src, names), _attributions(out, names)
    issues, seen = [], set()
    for a in a_src:
        for b in a_src:
            if a >= b or a not in a_out or b not in a_out:
                continue
            crossed = _jaccard(a_out[a], a_src[b]), _jaccard(a_out[b], a_src[a])
            kept = _jaccard(a_out[a], a_src[a]), _jaccard(a_out[b], a_src[b])
            if min(crossed) >= 0.3 and crossed[0] > kept[0] and crossed[1] > kept[1] and (a, b) not in seen:
                seen.add((a, b))
                issues.append(_issue("attribution_swapped", "critical",
                                     f"claims attributed to '{a}' and '{b}' were exchanged", text=a, swapped_with=b))
    return issues


def _marker_examples(led, label) -> list[str]:
    return [m.phrase for e in led.entries for m in e.markers
            if m.label == label or m.category == label][:3]


def _coverage_issues(src, out) -> list[dict]:
    issues = []
    out_stems, src_stems = out.stems(), src.stems()
    for entry in src.entries:
        stems = set(entry.stems)
        if len(stems) < MIN_STEMS_FOR_COVERAGE:
            continue
        coverage = len(stems & out_stems) / len(stems)
        if coverage < OMISSION_MAX_COVERAGE:
            issues.append(_issue("possible_omission", "major",
                                 "most content words of a source sentence are absent",
                                 sentence=entry.sentence.text, coverage=round(coverage, 3)))
    for entry in out.entries:
        stems = set(entry.stems)
        new = stems - src_stems
        if not stems:
            continue
        novelty = len(new) / len(stems)
        if (len(stems) > MIN_STEMS_FOR_COVERAGE and novelty >= ADDITION_MIN_NOVELTY) \
                or len(new) >= INLINE_ADDITION_MIN_NEW_STEMS:
            issues.append(_issue("possible_addition", "major",
                                 "candidate sentence introduces content words absent from the source; "
                                 "check for added claims",
                                 sentence=entry.sentence.text, novelty=round(novelty, 3),
                                 new_words=sorted(new)))
            continue
        clause = _novel_clause(entry, src_stems)
        if clause:
            issues.append(_issue("possible_addition", "major",
                                 "a clause of the candidate is mostly new content; check for an inserted claim",
                                 sentence=entry.sentence.text, clause=clause[0], new_words=clause[1]))
    return issues


_CLAUSE_SPLIT = re.compile(r"[,;:()\[\]]|\s[—–-]\s")


def _novel_clause(entry, src_stems: set) -> tuple[str, list[str]] | None:
    """An inserted clause ("..., onde liderei a migração, ...") can hide inside
    a sentence whose overall novelty is low. Look at each clause: at least
    CLAUSE_MIN_NEW_STEMS new content stems making up most of the clause."""
    pieces = [p for p in _CLAUSE_SPLIT.split(entry.content) if p.strip()]
    if len(pieces) < 2:  # a single clause is the whole sentence, already checked above
        return None
    for piece in pieces:
        stems = set(content_stems(piece))
        new = stems - src_stems
        if len(new) >= CLAUSE_MIN_NEW_STEMS and len(new) / len(stems) >= CLAUSE_MIN_NOVELTY:
            return piece.strip(), sorted(new)
    return None


def _structure_issues(src, out) -> list[dict]:
    """Markdown structure: list items, headings and code blocks are part of a
    document's contract (navigation, steps); paragraph merges are routine."""
    def counts(led):
        kinds = Counter(e.sentence.kind for e in led.entries)
        return {"list_item": kinds["list_item"], "heading": kinds["heading"], "code": kinds["code"],
                "paragraph": len({e.sentence.paragraph for e in led.entries if e.sentence.kind == "prose"})}
    before, after = counts(src), counts(out)
    issues = []
    for kind in ("list_item", "heading", "code"):
        if before[kind] != after[kind]:
            issues.append(_issue("structure_changed", "major", f"{kind} count {before[kind]} -> {after[kind]}",
                                 element=kind, before=before[kind], after=after[kind]))
    if before["paragraph"] != after["paragraph"]:
        issues.append(_issue("paragraphs_changed", "info",
                             f"paragraph count {before['paragraph']} -> {after['paragraph']}"))
    return issues


def _length_issues(original: str, candidate: str) -> list[dict]:
    a, b = len(original.split()), len(candidate.split())
    if a < 8:
        return []
    ratio = b / a
    low, high = LENGTH_RATIO_BOUNDS
    if ratio < low or ratio > high:
        return [_issue("length_ratio", "major", f"length ratio {ratio:.2f} outside {low}-{high}",
                       ratio=round(ratio, 3))]
    return []


# --- Judgments -----------------------------------------------------------------

JUDGE_KINDS = {"llm", "human"}
JUDGE_VERDICTS = {"equivalent", "not_equivalent", "uncertain"}


def apply_judgment(report: dict, judgment: dict) -> dict:
    """Merge an external semantic judgment into a comparison report.

    * Deterministic ``fail`` is never overridden.
    * An LLM ``equivalent`` verdict only upgrades ``no_deterministic_issues``.
    * A human ``equivalent`` verdict also resolves ``review_required``, but only
      when its signature verified (``authenticity == "verified"``); otherwise
      the result is ``human_review_claimed`` and nothing is accepted.
    * ``not_equivalent`` from anyone downgrades to ``fail``; ``uncertain`` to review.
    """
    kind = judgment.get("kind")
    verdict = judgment.get("verdict")
    if kind not in JUDGE_KINDS or verdict not in JUDGE_VERDICTS:
        raise ValueError(f"judgment needs kind in {sorted(JUDGE_KINDS)} and verdict in {sorted(JUDGE_VERDICTS)}")
    merged = dict(report)
    merged["evidence"] = {**report["evidence"], "judgments": report["evidence"]["judgments"] + [judgment]}
    status = report["status"]
    if status in {"fail", "identical"}:
        return merged
    if verdict == "not_equivalent":
        # Rejections are accepted from any source: they can only make the result safer.
        merged.update(status="fail", semantic_equivalence="violated", safe_to_auto_accept=False, requires=[])
    elif kind == "human" and judgment.get("authenticity") != "verified":
        merged.update(status="human_review_claimed", safe_to_auto_accept=False,
                      requires=["verified_human_review"],
                      human_review={"authenticity": judgment.get("authenticity", "unsigned"),
                                    "note": "a JSON file alone does not prove a human review; "
                                            "run `voznativa review` in an interactive terminal"})
    elif verdict == "uncertain":
        merged.update(status="review_required", safe_to_auto_accept=False, requires=["human_review"])
    elif status == "no_deterministic_issues" or (status == "review_required" and kind == "human"):
        judged = "grounded" if judgment.get("mode") == "grounding" else "equivalent"
        merged.update(status=f"accepted_by_{kind}",
                      semantic_equivalence=f"judged_{judged}_by_{kind}",
                      safe_to_auto_accept=True, requires=[])
    return merged
