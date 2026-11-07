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
from bisect import bisect_left
from collections import Counter

from . import ledger as ledger_mod
from . import spans as spans_mod
from . import signals
from .spans import HARD_TYPES
from .text import STOPWORDS, canonical, contains_word, content_stems, fold, normalize_surface, stem, words

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
    "Lost actions are found only when the source verb leaves no stem behind and the candidate keeps "
    "only light verbs (predicate_missing); a different content verb is reported, not judged (predicate_replaced).",
    "No deterministic result proves semantic equivalence; only identity does.",
]


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _issue(code: str, severity: str, message: str, **extra) -> dict:
    return {"code": code, "severity": severity, "message": message, **extra}


def compare(original: str, candidate: str, protect: list[str] | tuple = ()) -> dict:
    original, candidate = canonical(original), canonical(candidate)
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
    issues += _crossing_issues(src, out, alignment)
    issues += _order_issues(src, out, alignment)
    issues += _tense_issues(src, out, alignment)
    issues += _predicate_issues(src, out, alignment)
    issues += _event_issues(src, out, alignment)
    issues += _polarity_issues(src, out, alignment)
    issues += _attribution_issues(src, out)
    issues += _coverage_issues(src, out)
    issues += _length_issues(original, candidate)
    issues += _structure_issues(src, out)
    issues += _regional_referent_issues(original, candidate)

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


_WORD_RUN = re.compile(r"\w+")
# Characters whose IGNORECASE matching is not plain lower(): the non-ASCII members of
# CPython's re._casefix._EXTRA_CASES (ſ, ı, µ, Greek and Cyrillic variants, ligatures...)
# and İ, whose lower() is two characters. With any of them in the name or the text the
# word index could miss a match, so the full scan is used. ASCII i and s are in that
# table only through ı/İ and ſ, which are listed here.
_SPECIAL_CASE = re.compile(
    "[µİıſͅΐΰβεθικμπρς"
    "σφϐϑϕϖϰϱϵвдостъѣ"
    "ᲀᲁᲂᲃᲄᲅᲆᲇᲈṡẛιΐΰꙋ"
    "ﬅﬆ]")


def _whole_word_matches(text: str, name: str) -> list[tuple[int, int]]:
    """``(start, end)`` of every ``(?<!\\w)name(?!\\w)`` match, case-insensitive:
    the same list as ``re.finditer`` over the whole text (v0.8, V08-GAP-12).
    Candidates come from an index of the text's words (the name's first word
    must be a whole word there) and each one is confirmed by the same pattern
    at that position, so nothing is guessed; names or texts the index cannot
    handle exactly fall back to the full scan."""
    pattern = re.compile(r"(?<!\w)" + re.escape(name) + r"(?!\w)", re.IGNORECASE)
    first = _WORD_RUN.match(name)
    index = _word_index(text)
    if first is None or first.start() != 0 or _SPECIAL_CASE.search(name) or index is None:
        return [m.span() for m in pattern.finditer(text)]
    out = []
    for pos in index.get(first.group(0).lower(), ()):
        m = pattern.match(text, pos)
        if m:
            out.append(m.span())
    return out


_INDEX_CACHE: dict[int, tuple[str, dict | None]] = {}


def _word_index(text: str) -> dict[str, list[int]] | None:
    """Start of every word run, by lowercased word (one entry per text, reused
    while ``compare`` looks up many names in the same text). ``None`` when the
    text has a character whose case-insensitive matching the index cannot
    reproduce; callers then scan."""
    cached = _INDEX_CACHE.get(id(text))
    if cached is not None and cached[0] is text:
        return cached[1]
    index: dict[str, list[int]] | None = None
    if not _SPECIAL_CASE.search(text):
        index = {}
        for m in _WORD_RUN.finditer(text):
            index.setdefault(m.group(0).lower(), []).append(m.start())
    if len(_INDEX_CACHE) > 8:
        _INDEX_CACHE.clear()
    _INDEX_CACHE[id(text)] = (text, index)
    return index


def _entity_anchors(led, entity_texts: dict[str, str]) -> dict[str, set]:
    """Anchors of each source entity wherever it occurs (by whole word), so a
    name moved to sentence start, where extraction skips it, is still found."""
    table: dict[str, set] = {}
    for key, text in entity_texts.items():
        for start, end in _whole_word_matches(led.text, text):
            table.setdefault(key, set()).update(spans_mod._anchors(led.text, start, end))
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
    hits = sorted((start, end, name.casefold()) for name in names for start, end in _whole_word_matches(text, name))
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


# Words around which an exchange of content changes who does what or what
# comes first. Most are stopwords, so they are added back to the sequence.
_PIVOT_WORDS = frozenset({"antes", "depois", "apos", "entao", "primeiro", "ate", "desde"})
_VOICE_MARK = re.compile(r"\b(?:pel[oa]s?|por)\b|\b(?:foi|foram|é|são|será|serão)\s+\w+(?:d[oa]s?)\b", re.I)


def _ordered_units(text: str) -> list[str]:
    units = []
    for word in words(text):
        folded = fold(word)
        if folded in _PIVOT_WORDS:
            units.append(folded)
        elif folded not in _STOP_FOLDED and len(word) > 2:
            units.append(stem(word))
    return units


def _project(units: list[str], shared: Counter) -> list[str]:
    left, out = Counter(shared), []
    for unit in units:
        if left[unit] > 0:
            out.append(unit)
            left[unit] -= 1
    return out


def _crossing_issues(src, out, alignment) -> list[dict]:
    """Same words, exchanged across a pivot: "o cliente processou a empresa" ->
    "a empresa processou o cliente", "teste antes de publicar" -> "publique antes
    de testar". The named-entity role check misses common nouns and actions;
    this catches an exchange when the aligned sentences use exactly the same
    content words and some move left-to-right across a word that occurs once
    while others move right-to-left. Fronting a clause moves words one way only
    ("antes de virar X, trabalhei" keeps every word on its side of "antes"), and
    a change of voice ("foi processada pelo") is left to the role check."""
    issues = []
    for i, j, _ in alignment:
        if j is None:
            continue
        a_text, b_text = src.entries[i].sentence.text, out.entries[j].sentence.text
        a, b = _ordered_units(a_text), _ordered_units(b_text)
        # Project both onto the words they share: a rewrite that also drops a
        # formula ("vale ressaltar que") and swaps the roles must still be seen
        # (false green found by the v0.5.0 demo). Each unit keeps at most the
        # count both sentences have.
        shared = Counter(a) & Counter(b)
        a, b = _project(a, shared), _project(b, shared)
        if a == b or len(a) < 3:
            continue
        if bool(_VOICE_MARK.search(a_text)) != bool(_VOICE_MARK.search(b_text)):
            continue
        counts = Counter(a)
        for pivot in (u for u in a if counts[u] == 1):
            ia, ib = a.index(pivot), b.index(pivot)
            left_a, right_a, left_b, right_b = set(a[:ia]), set(a[ia + 1:]), set(b[:ib]), set(b[ib + 1:])
            to_right, to_left = left_a & right_b, right_a & left_b
            if to_right and to_left:
                issues.append(_issue("role_or_order_swapped", "major",
                                     f"the same words traded sides around '{pivot}': who does what, or what comes "
                                     "first, may have changed",
                                     location={"source_sentence": a_text, "candidate_sentence": b_text},
                                     pivot=pivot, moved=sorted(to_right | to_left)))
                break
    return issues


def _regional_referent_issues(original: str, candidate: str) -> list[dict]:
    """A regional variant replaced by another form that a Regional Evidence Pack
    records as a different referent in its scope ("macaxeira" -> "mandioca" in the
    North, where "mandioca" is mostly the wild, inedible root). Major: a person
    decides, since the swap is harmless in other regions."""
    from .regional import referent_swaps
    return [_issue("regional_referent_changed", "major",
                   f"'{s['from']}' became '{s['to']}': {s['risk']} (pack {s['pack']})",
                   text=s["from"], replacement=s["to"], pack=s["pack"]) for s in referent_swaps(original, candidate)]


def _align(src, out) -> list[tuple[int, int | None, float]]:
    """Best candidate sentence for each source sentence by content-stem
    Jaccard. Ties (v0.8, V08-GAP-13) go to the candidate sentence nearest
    the source sentence's relative position. Before, the first of the tied
    sentences won: "O orçamento não pode passar..." and "O orçamento pode
    passar..." have the same stems, so in a long document quoting both, the
    negated one aligned to the other and its negation looked moved (a false
    critical). A higher similarity always wins; only ties are decided
    differently. Preferring an identical surface text instead was tried and
    rejected: an unchanged copy elsewhere then took the alignment and hid a
    negation removed from the other copy (test_v08_alignment).

    Indexed (v0.8, V08-GAP-12): a similarity is above zero only when the
    stem sets (or, for short sentences, the token sets) intersect, so only
    those candidates are scored, in ascending order like the full scan; the
    hard-value fallback looks values up instead of rescanning both texts.
    ``_align_reference`` keeps the full scan; a test checks they agree."""
    pairs = []
    n_src, n_out = len(src.entries), len(out.entries)
    scale = (n_out - 1) / (n_src - 1) if n_src > 1 else 0.0
    stem_index: dict[str, list[int]] = {}
    token_index: dict[str, list[int]] = {}
    out_stems, out_tokens = [], []
    for j, cand in enumerate(out.entries):
        stems_j, tokens_j = set(cand.stems), set(cand.tokens)
        out_stems.append(stems_j)
        out_tokens.append(tokens_j)
        for s in stems_j:
            stem_index.setdefault(s, []).append(j)
        for t in tokens_j:
            token_index.setdefault(t, []).append(j)
    out_hard = [{s.key for s in cand.spans if s.type in HARD_TYPES} for cand in out.entries]
    src_hard = [{s.key for s in entry.spans if s.type in HARD_TYPES} for entry in src.entries]
    hard_out_index: dict[str, set[int]] = {}
    hard_src_index: dict[str, set[int]] = {}
    for j, keys in enumerate(out_hard):
        for k in keys:
            hard_out_index.setdefault(k, set()).add(j)
    for k_, keys in enumerate(src_hard):
        for k in keys:
            hard_src_index.setdefault(k, set()).add(k_)
    # Exact-match buckets: Jaccard never exceeds 1.0, so when some candidate has the
    # same stem set (or, for a short pair, the same token set) the best similarity is
    # 1.0 and only those candidates can win; the nearest one does, as in the full scan.
    same_stems: dict[frozenset, list[int]] = {}
    same_tokens: dict[frozenset, list[int]] = {}          # every candidate
    same_tokens_short: dict[frozenset, list[int]] = {}    # candidates with fewer than 2 stems
    for j in range(n_out):                                # ascending: every bucket is sorted
        if out_stems[j]:
            same_stems.setdefault(frozenset(out_stems[j]), []).append(j)
        if out_tokens[j]:
            same_tokens.setdefault(frozenset(out_tokens[j]), []).append(j)
            if len(out.entries[j].stems) < 2:
                same_tokens_short.setdefault(frozenset(out_tokens[j]), []).append(j)

    def nearest(bucket: list[int], expected: float) -> int | None:
        """Lowest index among those nearest to ``expected`` in a sorted bucket."""
        if not bucket:
            return None
        k = bisect_left(bucket, expected)
        options = [bucket[x] for x in (k - 1, k) if 0 <= x < len(bucket)]
        return min(options, key=lambda j: (abs(j - expected), j))

    for i, entry in enumerate(src.entries):
        a = set(entry.stems)
        tokens_i = set(entry.tokens)
        best, best_sim, best_key = None, 0.0, None
        expected = i * scale
        perfect = []
        if a:
            perfect.append(nearest(same_stems.get(frozenset(a), []), expected))
        if tokens_i:
            buckets = same_tokens if len(a) < 2 else same_tokens_short
            perfect.append(nearest(buckets.get(frozenset(tokens_i), []), expected))
        if not tokens_i and n_src == n_out and i < n_out and not out_tokens[i] \
                and (len(a) < 2 or len(out.entries[i].stems) < 2):
            perfect.append(i)
        perfect = [j for j in perfect if j is not None]
        if perfect:
            j = min(perfect, key=lambda j: (abs(j - expected), j))     # ties: the lowest index
            pairs.append((i, j, 1.0))
            continue
        candidates = {j for s in a for j in stem_index.get(s, ())}
        short_source = len(a) < 2
        for t in tokens_i:
            for j in token_index.get(t, ()):
                if short_source or len(out.entries[j].stems) < 2:
                    candidates.add(j)
        if not tokens_i and n_src == n_out and i < n_out and not out_tokens[i] \
                and (short_source or len(out.entries[i].stems) < 2):
            candidates.add(i)
        for j in sorted(candidates):
            cand = out.entries[j]
            sim = _jaccard(a, out_stems[j])
            if len(a) < 2 or len(cand.stems) < 2:
                sim = max(sim, _jaccard(tokens_i, out_tokens[j]))
                if not tokens_i and not out_tokens[j] and i == j and n_src == n_out:
                    sim = 1.0
            if sim <= 0.0:
                continue
            key = (sim, -abs(j - expected))
            if best_key is None or key > best_key:
                best, best_sim, best_key = j, sim, key
        if best_sim < ALIGN_MIN_SIMILARITY:
            mine = src_hard[i]
            if mine:
                sharing = sorted({j for k in mine for j in hard_out_index.get(k, ())})
                owners = sorted({k_ for k in mine for k_ in hard_src_index.get(k, ())})
                if len(sharing) == 1 and owners == [i]:      # unambiguous: one sentence on each side
                    best, best_sim = sharing[0], ALIGN_MIN_SIMILARITY
        pairs.append((i, best, round(best_sim, 3)))
    return pairs


def _align_reference(src, out) -> list[tuple[int, int | None, float]]:
    """The full O(n*m) scan that ``_align`` must agree with (kept for tests)."""
    pairs = []
    n_out = len(out.entries)
    scale = (n_out - 1) / (len(src.entries) - 1) if len(src.entries) > 1 else 0.0
    for i, entry in enumerate(src.entries):
        a = set(entry.stems)
        best, best_sim, best_key = None, 0.0, None
        expected = i * scale
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
            if sim <= 0.0:
                continue
            key = (sim, -abs(j - expected))
            if best_key is None or key > best_key:
                best, best_sim, best_key = j, sim, key
        # v0.7.0: a rewrite that rephrases a sentence but keeps its hard protected
        # values (money, dates, versions...) is still that sentence. Without this, a
        # negation dropped from "Vale ressaltar que o orçamento não pode ultrapassar
        # R$ 12.000,00" -> "O orçamento pode passar de R$ 12.000,00" was not localized
        # and came out as review_required instead of fail.
        if best_sim < ALIGN_MIN_SIMILARITY:
            mine = {s.key for s in entry.spans if s.type in HARD_TYPES}
            if mine:
                sharing = [j for j, cand in enumerate(out.entries)
                           if mine & {s.key for s in cand.spans if s.type in HARD_TYPES}]
                owners = [k for k, other in enumerate(src.entries)
                          if mine & {s.key for s in other.spans if s.type in HARD_TYPES}]
                if len(sharing) == 1 and owners == [i]:      # unambiguous: one sentence on each side
                    best, best_sim = sharing[0], ALIGN_MIN_SIMILARITY
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
    issues += _moved_signal_issues(src, out, alignment, before, after)
    return issues


def _moved_signal_issues(src, out, alignment, before, after) -> list[dict]:
    """A marker removed from one aligned sentence and added to another keeps
    the document's total unchanged ("A não contratou... O contrato prevê"):
    v0.7.0 CP9 found it passing as no_deterministic_issues."""
    issues = []
    rules = signals.severity_rules()
    for label in sorted(set(before) & set(after)):
        if before[label] != after[label]:
            continue        # a net change is reported above
        category = label.split(".")[0]
        if category in rules["informational"] or label in rules["informational"]:
            continue
        lost, gained = [], []
        for i, j, sim in alignment:
            if j is None or sim < ALIGN_MIN_SIMILARITY:
                continue
            delta = _bucket(out.entries[j].signal_counts()).get(label, 0) - \
                _bucket(src.entries[i].signal_counts()).get(label, 0)
            (lost if delta < 0 else gained if delta > 0 else []).append((i, j))
        if lost and gained:
            critical = category in rules["critical_when_localized"]
            issues.append(_issue(f"{category}_moved", "critical" if critical else "major",
                                 f"{label} marker moved between sentences (same total, different claims)",
                                 label=label, removed_from=src.entries[lost[0][0]].sentence.text,
                                 added_to=out.entries[gained[0][1]].sentence.text))
    return issues


# "vai depositar" and "depositará" name the same time; "ia depositar" and "depositaria" too
# (v0.7.0.dev1, VN07-DISC-041). Aspect-bearing constructions (progressive, compound
# perfect) keep their own label.
_SAME_TIME = {"periphrastic_future@pres_ind": "fut_pres", "periphrastic_future@pret_imp": "fut_pret"}
_NON_FINITE = {"inf", "ger", "part"}


def _time_reference(label: str) -> str | None:
    """A comparable time label, or None when the form carries no tense of its
    own (an infinitive, gerund or participle left over by the analysis)."""
    if label.split("@")[0] in _NON_FINITE:
        return None
    return _SAME_TIME.get(label, label)


def _tense_issues(src, out, alignment) -> list[dict]:
    """Tense, mood or periphrasis of the same verb changed between aligned
    sentences ("contratou" -> "contratará", "terminou" -> "está terminando").
    A review signal from rule-based morphology (voznativa.morph, measured in
    evals/linguistics/runs/): only when both sides are unambiguous; never
    critical, never a proof of equivalence when absent (v0.7.0 CP9L)."""
    from .morph import TENSES, tense_profile
    issues = []
    for i, j, sim in alignment:
        if j is None or sim < ALIGN_MIN_SIMILARITY:
            continue
        before = tense_profile(src.entries[i].sentence.text)
        after = tense_profile(out.entries[j].sentence.text)
        for lemma in sorted(set(before) & set(after)):
            a, b = before[lemma], after[lemma]
            if len(a) == 1 and len(b) == 1 and _time_reference(next(iter(a))) != _time_reference(next(iter(b))) \
                    and None not in (_time_reference(next(iter(a))), _time_reference(next(iter(b)))):
                def name(label):
                    base = label.split("@")[0]
                    return TENSES[base][0] if base in TENSES else label
                issues.append(_issue("tense_changed", "major",
                                     f"verb '{lemma}': {name(next(iter(a)))} -> {name(next(iter(b)))}",
                                     lemma=lemma, before=sorted(a), after=sorted(b),
                                     source_sentence=src.entries[i].sentence.text,
                                     analyzer="voznativa.morph-rules@1"))
    return issues


# Verbs that carry no event of their own here: copulas, auxiliaries, support verbs
# ("fazer a revisão") and modals (modality has its own signal). A source action that
# survives only as one of these ("será enviado" -> "vai até") has lost its predicate.
LIGHT_VERBS = frozenset("ser estar ir ter haver ficar fazer dar vir poder dever precisar querer conseguir".split())
PREDICATE_MIN_STEM = 4


def _event_anchors(text: str) -> dict[str, set]:
    """Content-verb anchors of a sentence: stem -> lemmas. Only confident
    analyses (voznativa.morph): the main verb of an auxiliary construction, or
    a token whose analyses agree on one tense and one stem. Light verbs,
    stopwords ("para" read as "parar") and short stems are left out: the check
    abstains instead of guessing."""
    from .morph import WEAK_ENDINGS, constructions, verbs
    anchors: dict[str, set] = {}
    covered = set()

    def add(lemmas):
        content = {lemma for lemma in lemmas if lemma not in LIGHT_VERBS}
        stems = {lemma[:-2] for lemma in content}
        if len(stems) == 1 and len(next(iter(stems))) >= PREDICATE_MIN_STEM and content == set(lemmas):
            anchors.setdefault(fold(next(iter(stems))), set()).update(content)

    for c in constructions(text):
        add(c["main_lemmas"])
        covered |= {c["start"], c["end"]}
    for v in verbs(text):
        # Tense ambiguity ("cancelaram": perfect or pluperfect) says nothing about whether
        # the token is this verb; one shared stem is what `add` requires.
        if v.start in covered or v.end in covered or fold(v.form) in _STOP_FOLDED:
            continue
        # A weak ending ("-o", "-e", "-a") accepted only from context reads "durante" as
        # "durantar" and "prazo" as "prazar": not an anchor.
        if all(a["source"] == "regular" and a["ending"] in WEAK_ENDINGS for a in v.analyses):
            continue
        add(v.lemmas)
    return anchors


def _predicate_issues(src, out, alignment) -> list[dict]:
    """The source sentence's action has no counterpart in its aligned candidate
    sentence (v0.7.0.dev1, H07-006). Preserved when the verb's stem is still
    there in any form ("enviado" -> "envio", "foi enviado pela") or the same
    lemma is. Otherwise:

    * the candidate has only light verbs or none ("vai até", "fica para",
      "é em março"): ``predicate_missing`` (major: a person decides);
    * the candidate has another content verb ("enviado" -> "encaminhado",
      "assinou" -> "recebeu"): ``predicate_replaced`` (info). A synonym and a
      different event look the same to rules; the judge decides.

    Never critical, and never evidence of equivalence when absent."""
    issues = []
    for i, j, sim in alignment:
        if j is None or sim < ALIGN_MIN_SIMILARITY:
            continue
        source_text = src.entries[i].sentence.text
        before = _event_anchors(source_text)
        if not before:
            continue
        # The aligned sentence and its neighbours: a rewrite may split or merge sentences.
        near = [out.entries[k].sentence.text for k in (j - 1, j, j + 1) if 0 <= k < len(out.entries)]
        near_words = {fold(w) for text in near for w in words(text)}
        after = _event_anchors(out.entries[j].sentence.text)
        after_lemmas = {lemma for text in near for lemmas in _event_anchors(text).values() for lemma in lemmas}
        for stem_, lemmas in sorted(before.items()):
            if any(w.startswith(stem_) for w in near_words) or lemmas & after_lemmas:
                continue
            lemma = sorted(lemmas)[0]
            common = {"lemma": lemma, "source_sentence": source_text,
                      "candidate_sentence": out.entries[j].sentence.text, "analyzer": "voznativa.morph-rules@1"}
            if after:
                issues.append(_issue("predicate_replaced", "info",
                                     f"verb '{lemma}' became {sorted(l for ls in after.values() for l in ls)}: "
                                     "same action or another event? needs judgment",
                                     candidate_verbs=sorted(l for ls in after.values() for l in ls), **common))
            else:
                issues.append(_issue("predicate_missing", "major",
                                     f"the action '{lemma}' has no counterpart in the candidate sentence "
                                     "(only a light verb or none): an action or commitment may be lost",
                                     **common))
    return issues


def _same_word(a: str, b: str) -> bool:
    """Same head word, allowing an inflection ("fornecedor"/"fornecedores")."""
    if a == b:
        return True
    shorter, longer = sorted((a, b), key=len)
    return len(shorter) >= 5 and longer.startswith(shorter[:-1]) and len(longer) - len(shorter) <= 2


def _event_issues(src, out, alignment) -> list[dict]:
    """Who received what, and whether the event turned into its converse
    (v0.8 CP6, V08-GAP-04), from ``voznativa.events`` frames:

    * ``recipient_dropped`` / ``recipient_changed`` (major): a transfer verb's
      recipient ("ao cliente", "para a diretoria") is nowhere in the aligned
      candidate sentence or its neighbours (moving it, or a passive that keeps
      it, is fine);
    * ``agent_recipient_swapped`` (major): the same transfer with giver and
      receiver exchanged;
    * ``event_converted`` (major): the verb became its converse (comprou ->
      vendeu, enviou -> recebeu) with the same subject; a converse with the
      roles swapped ("A comprou de B" -> "B vendeu para A") is not flagged.

    Major, never critical: frames come from rules and abstain on anything
    unclear; a person or a judge decides. Absence of these issues proves
    nothing."""
    from .events import converse, frames
    issues = []
    for i, j, sim in alignment:
        if j is None or sim < ALIGN_MIN_SIMILARITY:
            continue
        source = src.entries[i].sentence.text
        near = [out.entries[k].sentence.text for k in (j - 1, j, j + 1) if 0 <= k < len(out.entries)]
        near_words = {fold(w) for text in near for w in words(text)}
        out_frames = [f for text in near for f in frames(text)]
        for f in frames(source):
            loc = {"source_sentence": source, "candidate_sentence": out.entries[j].sentence.text}
            same_verb = [g for g in out_frames if g.stem == f.stem]
            if f.recipient and f.agent and any(g.agent and g.recipient and _same_word(g.agent, f.recipient)
                                               and _same_word(g.recipient, f.agent) for g in same_verb):
                issues.append(_issue("agent_recipient_swapped", "major",
                                     f"'{f.agent}' gave and '{f.recipient}' received '{f.verb}'; the candidate "
                                     "swaps giver and receiver", verb=f.verb, location=loc))
                continue
            if f.recipient and not any(_same_word(f.recipient, w) for w in near_words):
                other = next((g.recipient for g in same_verb if g.recipient), None)
                code, why = (("recipient_changed", f"now '{other}'") if other else
                             ("recipient_dropped", "it is no longer said who receives it"))
                issues.append(_issue(code, "major", f"recipient '{f.recipient}' of '{f.verb}' is gone: {why}",
                                     verb=f.verb, recipient=f.recipient, location=loc))
            if f.agent and not any(w.startswith(f.stem) for w in near_words):
                for g in out_frames:
                    if g.agent and not g.passive and converse(f.stem, g.stem) and _same_word(g.agent, f.agent):
                        issues.append(_issue("event_converted", "major",
                                             f"'{f.verb}' became its converse '{g.verb}' with the same subject "
                                             f"'{f.agent}': the direction of the event changed", verb=f.verb,
                                             candidate_verb=g.verb, location=loc))
                        break
    return issues


def _order_issues(src, out, alignment) -> list[dict]:
    """A sentence that leans on the previous one ("Por isso...", "Ele...")
    now sits elsewhere: its antecedent changed (v0.7.0 CP9)."""
    from .longform import _BACK_OPENINGS
    image = {i: j for i, j, sim in alignment if j is not None and sim >= ALIGN_MIN_SIMILARITY}
    issues = []
    for i, j in sorted(image.items()):
        if i == 0 or (i - 1) not in image:
            continue
        opening = fold(src.entries[i].sentence.text.strip().lstrip("—–-\"“'«( \t"))[:60]
        if not _BACK_OPENINGS.match(opening):
            continue
        antecedent = image[i - 1]
        between = [k for k, v in image.items() if k not in (i, i - 1) and antecedent < v < j]
        if antecedent >= j or between:
            issues.append(_issue("dependent_sentence_moved", "major",
                                 "a sentence that refers back to the previous one no longer follows it: "
                                 "what it refers to may have changed",
                                 sentence=src.entries[i].sentence.text))
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
        if len(stems) >= 2 and not stems & src_stems:
            # v0.7.0 CP9: a short sentence made only of new content ("Ele assinou o termo.")
            # stayed under both thresholds above.
            issues.append(_issue("possible_addition", "major",
                                 "candidate sentence has no content word of the source; check for an added claim",
                                 sentence=entry.sentence.text, novelty=1.0, new_words=sorted(new)))
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
    * An LLM judgment with ``generator_relation == "same_agent"`` (the agent
      judging its own candidate, v0.8 V08-GAP-16) is a dependent
      self-assessment: an ``equivalent`` is recorded as ``agent_assessment``
      and accepts nothing; the report still requires an independent judgment.
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
    self_assessed = kind == "llm" and judgment.get("generator_relation") == "same_agent"
    if self_assessed and verdict == "equivalent":
        merged["agent_assessment"] = {
            "verdict": verdict, "judge_id": judgment.get("judge_id"), "generator_relation": "same_agent",
            "evidence": "AGENT_OBSERVED",
            "note": "the agent that wrote the candidate judged it: a dependent self-assessment, not an "
                    "independent judgment; nothing is accepted on it"}
        merged["safe_to_auto_accept"] = False
        merged["requires"] = sorted(set(report.get("requires") or []) | {"independent_judgment"})
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
        if kind == "human":
            # Accepted on a valid signature; what the signature does NOT show
            # (who the person is, whether they are independent) travels with it.
            merged["human_review"] = {"authenticity": "verified", "assurance": judgment.get("assurance")}
        judged = "grounded" if judgment.get("mode") == "grounding" else "equivalent"
        merged.update(status=f"accepted_by_{kind}",
                      semantic_equivalence=f"judged_{judged}_by_{kind}",
                      safe_to_auto_accept=True, requires=[])
    return merged
