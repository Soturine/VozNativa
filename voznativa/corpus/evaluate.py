"""Corpus-backed evaluation of VozNativa's instruments (v0.6.0 M5).

Measures existing detectors on human-written text from prepared sources,
per split, so a threshold calibrated on ``calibration`` is confirmed on
``evaluation``. Outputs are aggregate counts and rates (EXPORT_STATISTICS),
never text.

* ``variant``: the PT-PT marker detector on sentences labelled PT-BR or
  PT-PT by the source itself (UD Bosque: CF = Brazil, CP = Portugal).
* ``patterns``: editorial findings and the edit decision on natural texts.
  These texts were written by people and published; a high edit rate means
  the detector would make VozNativa change text that did not need it.
* ``threshold``: how often the weak-finding rule (``max(2, ceil(words/k))``)
  asks for an edit, for several k, without changing the rule.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

from ..patterns import detect
from ..ptbr import variant_markers

WEAK_DIVISORS = (75, 100, 150, 200, 300)
LENGTH_BINS = ((0, 50), (50, 150), (150, 300), (300, 10 ** 9))   # dc-029 has 209 words


def length_bin(words: int) -> str:
    lo, hi = next(b for b in LENGTH_BINS if b[0] <= words < b[1])
    return f"{lo}+" if hi == 10 ** 9 else f"{lo}-{hi - 1}"


def documents(records, joiner: str = " ") -> dict[str, dict]:
    """Records of one group joined in order (a news document), or one record
    per document when every group has one record."""
    docs: dict[str, dict] = {}
    for r in records:
        doc = docs.setdefault(r.group, {"group": r.group, "texts": [], "ids": [], "meta": r.meta})
        doc["texts"].append(r.text)
        doc["ids"].append(r.record_id)
    for doc in docs.values():
        doc["text"] = joiner.join(doc.pop("texts"))
    return docs


def variant_eval(records, label_of) -> dict:
    """Confusion counts of 'has a PT-PT marker' against the source label."""
    counts = Counter()
    by_marker = Counter()
    hits_pt = Counter()
    for r in records:
        label = label_of(r)
        if label not in {"pt-BR", "pt-PT"}:
            continue
        found = variant_markers(r.text)
        flagged = bool(found)
        counts[(label, flagged)] += 1
        if flagged and label == "pt-BR":
            by_marker.update(m["text"].lower() for m in found)
        if flagged and label == "pt-PT":
            hits_pt.update(m["kind"] for m in found)
    tp, fn = counts[("pt-PT", True)], counts[("pt-PT", False)]
    fp, tn = counts[("pt-BR", True)], counts[("pt-BR", False)]
    return {"pt_pt_sentences": tp + fn, "pt_br_sentences": fp + tn, "recall_pt_pt": _rate(tp, tp + fn),
            "false_positive_rate_pt_br": _rate(fp, fp + tn), "precision": _rate(tp, tp + fp),
            "false_positive_markers": dict(by_marker.most_common(15)),
            "true_positive_marker_kinds": dict(hits_pt.most_common())}


def variant_documents(records, label_of) -> dict:
    """Same question per document (all sentences of a news item together):
    the unit VozNativa actually receives."""
    docs: dict[str, list] = defaultdict(list)
    labels: dict[str, str] = {}
    for r in records:
        label = label_of(r)
        if label in {"pt-BR", "pt-PT"}:
            docs[r.group].append(r.text)
            labels[r.group] = label
    counts = Counter((labels[g], bool(variant_markers(" ".join(t)))) for g, t in docs.items())
    tp, fn = counts[("pt-PT", True)], counts[("pt-PT", False)]
    fp, tn = counts[("pt-BR", True)], counts[("pt-BR", False)]
    return {"recall_pt_pt": _rate(tp, tp + fn), "false_positive_rate_pt_br": _rate(fp, fp + tn),
            "precision": _rate(tp, tp + fp)}


def pattern_eval(docs: dict[str, dict], genre: str, channel: str | None = None) -> dict:
    per_pattern = Counter()
    docs_with = Counter()
    decisions = Counter()
    drivers = Counter()             # what made an edited document 'edit'
    weak_hist = Counter()
    bins: dict[str, list] = defaultdict(list)
    words_total, rows = 0, []
    for doc in docs.values():
        report = detect(doc["text"], genre, channel)
        words = max(1, len(doc["text"].split()))
        words_total += words
        decisions[report["decision"]] += 1
        ids = Counter(f["id"] for f in report["findings"])
        per_pattern.update(ids)
        docs_with.update(set(ids))
        strong, weak = report["summary"]["strong"], report["summary"]["weak"]
        weak_hist[min(weak, 4)] += 1
        if report["decision"] == "edit":
            strong_ids = {f["id"] for f in report["findings"] if f["strength"] == "strong"}
            drivers.update(sorted(strong_ids) or ["weak_accumulation"])
        rows.append((words, strong, weak))
        bins[length_bin(words)].append((words, strong, weak))
    n = len(docs)
    return {"documents": n, "words": words_total,
            "edit_rate": _rate(decisions["edit"], n),
            "edit_drivers": dict(drivers.most_common()),
            "weak_findings_histogram": {("4+" if k == 4 else str(k)): v for k, v in sorted(weak_hist.items())},
            "by_length": {b: {"documents": len(r), "threshold": threshold_sweep(r)} for b, r in sorted(bins.items())},
            "findings_per_1000_words": round(1000 * sum(per_pattern.values()) / max(1, words_total), 3),
            "documents_with_pattern": {k: {"documents": v, "rate": _rate(v, n),
                                           "per_1000_words": round(1000 * per_pattern[k] / max(1, words_total), 3)}
                                       for k, v in docs_with.most_common()},
            "threshold": threshold_sweep(rows)}


def threshold_sweep(rows: list[tuple[int, int, int]]) -> dict:
    """Edit rate under max(2, ceil(words/k)) weak findings (or any strong one)."""
    out = {}
    for k in WEAK_DIVISORS:
        edits = sum(1 for words, strong, weak in rows if strong >= 1 or weak >= max(2, math.ceil(words / k)))
        out[f"weak/{k}"] = _rate(edits, len(rows))
    out["strong_only"] = _rate(sum(1 for _, strong, _ in rows if strong >= 1), len(rows))
    return out


def _rate(a: int, b: int) -> dict:
    """A proportion with its 95% Wilson interval (n stated)."""
    from ..benchmark import wilson
    return {"k": a, "n": b, "rate": round(a / b, 4) if b else None, "wilson95": wilson(a, b)}


def split_records(records, splits: dict[str, str], name: str):
    return [r for r in records if splits.get(f"{r.source}:{r.record_id}") == name]


def by_label(entry: dict):
    prefixes = ((entry.get("processing") or {}).get("variant_by_sent_id_prefix")) or {}

    def label(record):
        return next((v for k, v in prefixes.items() if record.record_id.startswith(k)), None)
    return label
