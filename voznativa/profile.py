"""Voice Profile v2: observable writing habits from authorized samples.

The profile stores derived statistics, never raw text or topic words (what
someone writes about is not how they write, and topic words leak private
content). Each habit carries its evidence count, how many samples support
it and a confidence that is capped by the number of samples, so one short
message never becomes "a habit".

It does not, and must not, infer identity: age, gender, region, class,
personality or any other attribute.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import datetime, timezone

from . import features
from .text import fold, words

SCHEMA_VERSION = 2
DISCOURSE_OPENERS = {"entao", "olha", "bom", "enfim", "tipo", "na verdade", "sinceramente", "assim", "pois e",
                     "veja", "agora", "ah", "e ai", "pois", "alias", "inclusive", "beleza", "certo", "show"}


def _community_terms() -> set[str]:
    """Every community pack form (v0.6.0 packs, schema 2): the author's use of
    them is a habit to keep, not an anglicism to fix."""
    from .community import all_terms
    return all_terms()


def confidence(support: int, samples: int) -> float:
    """Share of samples showing the habit, damped by sample count.

    1 sample caps at 0.5, 3 samples at 0.75, 9 samples at 0.9.
    """
    if samples <= 0:
        return 0.0
    return round((support / samples) * (samples / (samples + 1)), 3)


def maturity(samples: int, total_words: int, channels: Counter) -> str:
    if samples < 3 or total_words < 150:
        return "explicit_only"
    if any(n >= 6 for n in channels.values()):
        return "channel_profile"
    return "provisional"


def _habit(feature_id: str, value, evidence: int, support: int, samples: int, scope: str) -> dict:
    conf = confidence(support, samples)
    return {"id": feature_id, "value": value, "evidence_count": evidence, "sample_support": support,
            "confidence": conf, "stability": "high" if conf >= 0.75 else "medium" if conf >= 0.5 else "low",
            "scope": scope}


def build(samples: list[dict]) -> dict:
    """``samples``: [{"text": ..., "channel": optional, "date": optional}]."""
    if not samples:
        raise ValueError("at least one authorized sample is required")
    texts = [s["text"] for s in samples]
    n = len(texts)
    channels = Counter(s.get("channel") or "unspecified" for s in samples)
    total_words = sum(len(t.split()) for t in texts)
    community = _community_terms()

    vectors = [features.vector(window) for t in texts for window in (features.windows(t) or [t])]
    style = features.summarize(vectors)

    per_sample_tokens = [Counter(fold(w) for w in words(t)) for t in texts]
    abbreviations, foreign, contractions = Counter(), Counter(), Counter()
    support_abbr, support_foreign, support_contr = Counter(), Counter(), Counter()
    folded_contractions = {fold(c) for c in features.CONTRACTIONS}
    for tokens in per_sample_tokens:
        for token, count in tokens.items():
            if token in features.CHAT_ABBREVIATIONS:
                abbreviations[token] += count
                support_abbr[token] += 1
            if token in community:
                foreign[token] += count
                support_foreign[token] += 1
            if token in folded_contractions:
                contractions[token] += count
                support_contr[token] += 1

    openers = Counter()
    opener_support = Counter()
    for t in texts:
        seen = set()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", t):
            first = fold(" ".join(words(sentence)[:2]))
            one = first.split(" ")[0] if first else ""
            for candidate in (first, one):
                if candidate in DISCOURSE_OPENERS:
                    openers[candidate] += 1
                    seen.add(candidate)
                    break
        for o in seen:
            opener_support[o] += 1

    habits = []
    for token in sorted(abbreviations):
        habits.append(_habit(f"abbreviation.{token}", True, abbreviations[token], support_abbr[token], n, "lexicon"))
    for token in sorted(contractions):
        habits.append(_habit(f"contraction.{token}", True, contractions[token], support_contr[token], n, "lexicon"))
    for token in sorted(foreign):
        habits.append(_habit(f"community_term.{token}", "keep", foreign[token], support_foreign[token], n, "lexicon"))
    # Regional forms of evidence packs the author actually used (closed list,
    # counts only): a form the author writes wins over a pack's regional default.
    from .regional import forms_in, load_packs
    regional, support_regional = Counter(), Counter()
    for t in texts:
        for pack in load_packs():
            for feature in pack["features"]:
                for form in forms_in(t, feature):
                    regional[fold(form)] += len(re.findall(r"(?<!\w)" + re.escape(fold(form)) + r"(?!\w)", fold(t)))
                    support_regional[fold(form)] += 1
    for token in sorted(regional):
        habits.append(_habit(f"regional_form.{token}", "keep", regional[token], support_regional[token], n, "lexicon"))
    # Slang the author writes (temporal lexicon, closed list, counts only): the
    # author's forms are kept whatever their attestation; nothing is inferred
    # about the author's age or generation from them.
    from .temporal import observe_slang
    slang, support_slang = Counter(), Counter()
    for t in texts:
        hits = observe_slang(t)   # v0.7.0: "mano" = irmão is not a slang habit
        slang.update(h["id"] for h in hits)
        support_slang.update({h["id"] for h in hits})
    for sid in sorted(slang):
        habits.append(_habit(f"slang.{sid}", "keep", slang[sid], support_slang[sid], n, "lexicon"))
    for opener in sorted(openers):
        habits.append(_habit(f"opener.{opener}", True, openers[opener], opener_support[opener], n, "discourse"))
    for name in ("em_dash_per_100w", "emoji_per_100w", "exclamation_per_sentence", "semicolon_per_100w",
                 "lowercase_start_ratio", "list_line_ratio", "ellipsis_per_100w"):
        support = sum(1 for t in texts if features.vector(t)[name] > 0)
        habits.append(_habit(f"style.{name}", style[name]["mean"], support, support, n, "style"))

    digest = hashlib.sha256("\n".join(hashlib.sha256(t.encode()).hexdigest() for t in texts).encode()).hexdigest()
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "voznativa.voice_profile",
        "locale": "pt-BR",
        "profile": {"id": digest[:16], "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        "source": {
            "type": "samples", "sample_count": n, "total_words": total_words, "channels": dict(channels),
            "sample_sha256": [hashlib.sha256(t.encode()).hexdigest() for t in texts],
            "date_range": _dates(samples),
        },
        "maturity": maturity(n, total_words, channels),
        "style": style,
        "channels": {ch: features.summarize([features.vector(s["text"]) for s in samples
                                             if (s.get("channel") or "unspecified") == ch])
                     for ch in channels if channels[ch] >= 2},
        "habits": habits,
        # v1-compatible summary (lists only; detail lives in habits)
        "lexicon": {
            "abbreviations": sorted(abbreviations),
            "contractions": sorted(contractions),
            "foreign_terms": sorted(foreign),
            "recurring": [],
            "recurring_policy": "topic words are not stored",
        },
        "inference_policy": {"observations_only": True, "infer_identity": False,
                             "infer_sensitive_attributes": False},
        "privacy": {"retain_raw_samples": False, "stores": "derived statistics and sample hashes only"},
        "limitations": [
            "Thresholds and confidence damping are heuristic and uncalibrated.",
            "Absence of a habit in few samples is not evidence that the author avoids it.",
        ],
    }


def _dates(samples: list[dict]) -> dict:
    dates = sorted(s["date"] for s in samples if s.get("date"))
    return {"from": dates[0] if dates else None, "to": dates[-1] if dates else None}


REQUIRED_KEYS = {"schema_version", "locale", "source", "maturity", "style", "habits", "inference_policy", "privacy"}


def validate(profile: dict) -> list[str]:
    errors = [f"missing key: {k}" for k in sorted(REQUIRED_KEYS - set(profile))]
    if profile.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    policy = profile.get("inference_policy", {})
    if policy.get("infer_identity") is not False or policy.get("infer_sensitive_attributes") is not False:
        errors.append("inference_policy must forbid identity and sensitive-attribute inference")
    if profile.get("privacy", {}).get("retain_raw_samples") is not False:
        errors.append("profiles must not retain raw samples")
    missing_features = set(features.FEATURES) - set(profile.get("style", {}))
    if missing_features:
        errors.append(f"style lacks features: {sorted(missing_features)}")
    for habit in profile.get("habits", []):
        if not 0 <= habit.get("confidence", -1) <= 1:
            errors.append(f"habit {habit.get('id')} has invalid confidence")
    return errors
