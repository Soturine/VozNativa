"""Discourse relations between clauses and sentences (v0.10 CP5).

A rewrite can keep every fact and still change how the facts relate: a
concession ("embora") becomes a cause ("como"), a contrast ("mas") becomes a
consequence ("por isso"), a purpose ("para que") becomes a cause ("porque").
The marker lexicon of ``compare`` saw causal and conditional connectives one
by one; nothing compared the *relation* each connective expresses, so a
concession turned into a cause passed when no causal marker of the lexicon
was involved, and a causal connective swapped for an equivalent one ("porque"
-> "Como ..., ") was flagged as a lost cause.

Relations are counted by family:

* ``counter``: contrast and concession (the second fact holds *despite* the first);
* ``causal``: cause and consequence (one fact *produces* the other);
* ``purpose``: one fact is done *so that* another happens.

Within a family a swap preserves the relation; across opposed families it
changes it. Implicit relations (two sentences side by side) are not read as
anything: adding a causal connective between them is an invented relation.
Connectives with several readings are counted only in the reading the
pattern pins down ("Como" opening a clause that a comma closes, "assim" not
followed by "como", "logo" not followed by a time word); everything else is
left out, which makes the check abstain rather than guess.
"""
from __future__ import annotations

import re
from collections import Counter

RELATIONS = {
    "contrast": r"mas|porém|entretanto|contudo|todavia|no entanto|ainda assim|mesmo assim|só que",
    "concession": r"embora|apesar d[eoa]s?|mesmo que|ainda que|conquanto|se bem que|mesmo com",
    "cause": r"porque|pois|já que|visto que|uma vez que|devido a[o]?s?|devido à|por causa d[eoa]s?|"
             r"graças a[o]?s?|graças à",
    "consequence": r"por isso|portanto|consequentemente|por conseguinte|de modo que|de forma que|"
                   r"assim(?!\s+como|\s+que)|logo(?!\s+(?:após|depois|cedo|mais|em seguida|que|no|na|de))|"
                   r"então(?=\s*,)",
    "purpose": r"para que|a fim de que|a fim de|com o objetivo de|com o intuito de",
}
FAMILY = {"contrast": "counter", "concession": "counter", "cause": "causal", "consequence": "causal",
          "purpose": "purpose"}
OPPOSED = {"counter": {"causal"}, "causal": {"counter", "purpose"}, "purpose": {"causal"}}
_PATTERNS = {rel: re.compile(rf"(?<![\w-])(?:{expr})(?![\w-])", re.I) for rel, expr in RELATIONS.items()}
# "Como o pavilhão alagou, a feira foi adiada": causal when "Como" opens the sentence and a comma
# closes the clause; not "Como sempre," / "Como previsto," / "Como fazer…?".
_COMO_CAUSAL = re.compile(r"(?:^|[.!?;]\s+)Como\s+(?!sempre\b|de costume\b|previsto\b|esperado\b|combinado\b|"
                          r"dito\b|já\s+dito\b|se\b|fazer\b|assim\b)[^,.?!]{3,120},")


def relations(text: str) -> list[dict]:
    """Every explicit relation with its connective and offset."""
    found = []
    for rel, pattern in _PATTERNS.items():
        for m in pattern.finditer(text):
            found.append({"relation": rel, "family": FAMILY[rel], "connective": m.group(0).lower(),
                          "start": m.start()})
    for m in _COMO_CAUSAL.finditer(text):
        start = m.group(0).index("Como") + m.start()
        found.append({"relation": "cause", "family": "causal", "connective": "como", "start": start})
    # "mesmo assim"/"ainda assim" also match "assim" (consequence): keep the longer reading
    spans = sorted(found, key=lambda r: (r["start"], -len(r["connective"])))
    kept, last_end = [], -1
    for r in spans:
        if r["start"] < last_end:
            continue
        kept.append(r)
        last_end = r["start"] + len(r["connective"])
    return kept


def profile(text: str) -> Counter:
    return Counter(r["family"] for r in relations(text))


def issues(original: str, candidate: str) -> list[dict]:
    """Relation-level differences between source and candidate (family counts).

    * ``relation_changed`` (major): a family lost on one side and an opposed family
      gained on the other ("embora" -> "como", "mas" -> "por isso", "para que" -> "porque");
    * ``relation_invented`` (major): a causal relation appears with no causal relation lost
      and no opposed one lost (two juxtaposed facts joined by "porque"/"assim");
    * ``relation_dropped`` (info): a counter relation disappears with nothing in its place
      (the contrast may now be implicit; a person decides).
    """
    before, after = profile(original), profile(candidate)
    out = []
    lost = {f for f in before if after[f] < before[f]}
    gained = {f for f in after if after[f] > before[f]}
    reported = set()
    for family in sorted(lost):
        for other in sorted(gained & OPPOSED.get(family, set())):
            out.append({"code": "relation_changed", "severity": "major",
                        "message": f"a {family} relation became {other} "
                                   f"({_connectives(original, family)} -> {_connectives(candidate, other)})",
                        "before": family, "after": other})
            reported.add(other)
    if "causal" in gained and "causal" not in reported:
        out.append({"code": "relation_invented", "severity": "major",
                    "message": "a causal relation appears that the source did not state "
                               f"({_connectives(candidate, 'causal')}); juxtaposed facts are not a cause",
                    "after": "causal"})
    if "counter" in lost and not (gained & OPPOSED["counter"]):
        out.append({"code": "relation_dropped", "severity": "info",
                    "message": f"the contrast/concession ({_connectives(original, 'counter')}) is no longer marked",
                    "before": "counter"})
    return out


def preserved(original: str, candidate: str, family: str) -> bool:
    """The family appears as many times on both sides (connectives may differ)."""
    before, after = profile(original), profile(candidate)
    return before[family] > 0 and before[family] == after[family]


def _connectives(text: str, family: str) -> str:
    words = sorted({r["connective"] for r in relations(text) if r["family"] == family})
    return ", ".join(f"'{w}'" for w in words) or "none"
