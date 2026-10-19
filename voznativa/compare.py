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

from collections import Counter

from . import ledger as ledger_mod
from . import signals
from .spans import HARD_TYPES
from .text import contains_word, normalize_surface

SCHEMA_VERSION = 1

# Thresholds are heuristic and uncalibrated; evals pin their behavior.
ALIGN_MIN_SIMILARITY = 0.5
OMISSION_MAX_COVERAGE = 0.4
ADDITION_MIN_NOVELTY = 0.6
MIN_STEMS_FOR_COVERAGE = 3
LENGTH_RATIO_BOUNDS = (0.5, 1.8)

INLINE_ADDITION_MIN_NEW_STEMS = 4

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


def compare(original: str, candidate: str) -> dict:
    if normalize_surface(original) == normalize_surface(candidate):
        return _report("identical", [], original, candidate)

    src = ledger_mod.build(original)
    out = ledger_mod.build(candidate)
    issues: list[dict] = []
    issues += _span_issues(src, out)
    issues += _binding_issues(src, out)
    alignment = _align(src, out)
    issues += _signal_issues(src, out, alignment)
    issues += _coverage_issues(src, out)
    issues += _length_issues(original, candidate)

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


def _binding_issues(src, out) -> list[dict]:
    """Detect values that kept their multiset but moved to other entities."""
    def anchors_by_key(led):
        table: dict[str, set] = {}
        for s in led.spans:
            if s.type in HARD_TYPES and s.anchors:
                table.setdefault(s.key, set()).update(s.anchors)
        return table

    a_src, a_out = anchors_by_key(src), anchors_by_key(out)
    issues = []
    reported = set()
    # A swap is mutual: A now sits where B was AND B now sits where A was.
    # Requiring both directions keeps reordering ("às 10h não vai") from firing.
    for key_a, src_a in a_src.items():
        out_a = a_out.get(key_a)
        if not out_a or src_a & out_a:
            continue
        for key_b, src_b in a_src.items():
            if key_b == key_a or (key_b, key_a) in reported:
                continue
            out_b = a_out.get(key_b)
            if out_b and not (src_b & out_b) and (out_a & src_b) and (out_b & src_a):
                texts = [next(s.text for s in src.spans if s.key == k) for k in (key_a, key_b)]
                reported.add((key_a, key_b))
                issues.append(_issue("binding_changed", "critical",
                                     f"'{texts[0]}' and '{texts[1]}' swapped the words they qualify",
                                     key=key_a, text=texts[0], swapped_with=texts[1]))
    return issues


def _align(src, out) -> list[tuple[int, int | None, float]]:
    pairs = []
    for i, entry in enumerate(src.entries):
        a = set(entry.stems)
        best, best_sim = None, 0.0
        for j, cand in enumerate(out.entries):
            sim = _jaccard(a, set(cand.stems))
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
    * A human ``equivalent`` verdict also resolves ``review_required``.
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
        merged.update(status="fail", semantic_equivalence="violated", safe_to_auto_accept=False, requires=[])
    elif verdict == "uncertain":
        merged.update(status="review_required", safe_to_auto_accept=False, requires=["human_review"])
    elif status == "no_deterministic_issues" or (status == "review_required" and kind == "human"):
        merged.update(status=f"accepted_by_{kind}",
                      semantic_equivalence=f"judged_equivalent_by_{kind}",
                      safe_to_auto_accept=True, requires=[])
    return merged
