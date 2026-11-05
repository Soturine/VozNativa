"""Long texts (v0.6.0 M9): a cross-paragraph dependency map, segmentation
that never cuts a dependency it can see, and a conservative policy for
literary prose and verse.

* ``blocks``: the text split into paragraphs with their kind (heading, separator,
  prose, dialogue, verse, list, code, quote) and character offsets.
* ``dependency_map``: for each paragraph, the earlier paragraphs it leans
  on and why: an opening that points back ("Isso", "Por isso", "Ela"), a
  backward reference ("como dito acima"), a dialogue turn, a list or verse
  continuation, a defined term or an acronym introduced earlier, a forward
  reference made by the previous paragraph ("a seguir").
* ``segment``: paragraphs grouped into segments of at most ``max_words``,
  cut only where no dependency crosses. A chain longer than the limit is cut
  at its weakest link and the cut is reported (``forced_cuts``), never
  hidden. Joining the segments gives back the exact text. Each segment
  carries the names and terms introduced before it (``carry``) so a writer
  working on one segment keeps them consistent.
* ``literary_policy``: verse is not rewritten without an explicit request;
  literary prose is edited only locally (no paragraph or document rewrite).

Deterministic and conservative: a surface heuristic sees openings, names
and markers, not meaning. A dependency it misses is a cut it cannot
prevent; the evaluation reports how often cuts land on visible ones.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .text import fold

# Case-sensitive on purpose: with re.I the all-capitals branch matched any
# short line ("O ANTT pediu os anexos a seguir:" became a heading; CP10 test).
_HEADING = re.compile(r"^(?:#{1,6}\s|(?i:cap[ií]tulo)\b|[IVXLC]{1,7}\.?\s*$|\d{1,3}\.?\s*$|"
                      r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 ,.;—-]{3,80}$)")
_DIALOGUE = re.compile(r"^\s*(?:—|–|--|-\s)")
_SEPARATOR = re.compile(r"^\s*(?:[*•·~=_-]\s*){3,}$")
_LIST = re.compile(r"^\s*(?:[-*•]\s|\d{1,3}[.)]\s)")
_QUOTE = re.compile(r"^\s*>")
# Openings that lean on what came before (folded, so accents do not matter).
_BACK_OPENINGS = re.compile(
    r"^(?:isso|isto|esse|essa|esses|essas|este|esta|estes|estas|aquilo|tal|tais|ele|ela|eles|elas|"
    r"por isso|portanto|assim|alem disso|contudo|no entanto|entretanto|todavia|mas|e|tambem|dai|entao|"
    r"nesse caso|neste caso|com isso|apesar disso|ainda assim|por fim|enfim|depois|em seguida|"
    r"o mesmo|a mesma|o qual|a qual|outro|outra)\b")
_BACK_REFERENCES = re.compile(r"\b(?:como (?:dito|vimos|mencionado|ja disse|disse)|acima|anteriormente|"
                              r"ja mencionad[oa]s?|o referido|a referida|supracitad[oa])\b")
_FORWARD = re.compile(r"(?:a seguir|abaixo|adiante|como veremos|seguinte(?:s)?)\s*[:.]?\s*$|:\s*$")
_ACRONYM_DEF = re.compile(r"\(([A-Z]{2,8})\)")
_ACRONYM = re.compile(r"\b([A-Z]{2,8})\b")
# A name only where a capital cannot be a sentence or paragraph start: after a
# lower-case letter, a digit or a comma/semicolon/colon and one space.
_NAME = re.compile(r"(?<=[a-záéíóúâêôãõçà0-9,;:] )([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõçà]{2,}"
                   r"(?:\s+(?:de |da |do |dos |das )?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõçà]{2,})*)")
VERSE_LINE_WORDS = 12


@dataclass
class Block:
    index: int
    start: int
    end: int
    text: str
    kind: str
    words: int
    depends_on: list = field(default_factory=list)   # [(earlier index, reason)]
    introduces: set = field(default_factory=set)      # names and acronyms first seen here

    def as_dict(self) -> dict:
        return {"index": self.index, "kind": self.kind, "words": self.words, "start": self.start, "end": self.end,
                "depends_on": [{"paragraph": i, "reason": r} for i, r in self.depends_on],
                "introduces": sorted(self.introduces)}


def _kind(text: str) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    first = lines[0].strip() if lines else ""
    if first.startswith("```"):
        return "code"
    if lines and all(_SEPARATOR.match(ln) for ln in lines):
        return "separator"
    if _QUOTE.match(first):
        return "quote"
    if _LIST.match(first):
        return "list"
    if _DIALOGUE.match(first):
        return "dialogue"
    if _is_verse(lines):
        return "verse"
    if len(lines) == 1 and len(first.split()) <= 8 and not first.endswith((".", "!", "?", ",", ";")) \
            and _HEADING.match(first):
        return "heading"
    return "prose"


def _is_verse(lines: list[str]) -> bool:
    """Short lines that start with a capital (classic verse), or very short
    lines without final punctuation (free verse). Hard-wrapped prose (lines
    filled to ~70 characters, continuing in lower case) is not verse: on
    Project Gutenberg editions the first rule read a third of each novel as
    verse (CP10)."""
    if len(lines) < 2:
        return False
    body = [ln.strip() for ln in lines]
    lengths = sorted(len(ln) for ln in body[:-1])
    median = lengths[len(lengths) // 2]
    upper = sum(ln[:1].isupper() or ln[:1] in "«\"“'(¡¿" for ln in body) / len(body)
    unpunctuated = sum(not ln.endswith((".", "!", "?", ":", ";")) for ln in body) / len(body)
    if all(len(ln.split()) <= VERSE_LINE_WORDS for ln in body) and upper >= 0.7 and median <= 60:
        return True
    return median <= 40 and unpunctuated >= 0.4 and upper < 0.7 and len(body) >= 3


def blocks(text: str) -> list[Block]:
    """Paragraphs (blank-line separated; a fenced code block is one paragraph)."""
    out, i = [], 0
    pattern = re.compile(r"```.*?(?:```|\Z)|(?:(?!\n[ \t]*\n).)+", re.S)
    for m in pattern.finditer(text):
        chunk = m.group(0)
        if not chunk.strip():
            continue
        out.append(Block(i, m.start(), m.end(), chunk, _kind(chunk), len(chunk.split())))
        i += 1
    return out


def dependency_map(text: str) -> list[Block]:
    out = blocks(text)
    seen_names: dict[str, int] = {}
    seen_acronyms: dict[str, int] = {}
    for b in out:
        prev = out[b.index - 1] if b.index else None
        # strip() first: every block after the first starts with the newline the
        # block pattern keeps, and lstrip of quote marks alone left the opening
        # empty, so no opening ever matched (found by the CP10 tests).
        opening = fold(b.text.strip().lstrip("—–-\"“'«( \t").split("\n", 1)[0])[:60]
        if prev is not None and prev.kind not in ("heading", "separator"):
            if b.kind == "dialogue" and prev.kind == "dialogue":
                b.depends_on.append((prev.index, "dialogue_turn"))
            elif b.kind in ("list", "verse") and prev.kind == b.kind:
                b.depends_on.append((prev.index, f"{b.kind}_continuation"))
            elif b.kind in ("prose", "dialogue") and _BACK_OPENINGS.match(opening):
                b.depends_on.append((prev.index, "opening_points_back"))
            if _FORWARD.search(fold(prev.text.rstrip())) and b.kind != "heading":
                b.depends_on.append((prev.index, "previous_announces_this"))
        if b.kind in ("prose", "dialogue", "list", "quote") and _BACK_REFERENCES.search(fold(b.text)) \
                and prev is not None:
            b.depends_on.append((prev.index, "backward_reference"))
        for acr in _ACRONYM_DEF.findall(b.text):
            seen_acronyms.setdefault(acr, b.index)
        for acr in set(_ACRONYM.findall(b.text)):
            first = seen_acronyms.get(acr)
            if first is not None and first < b.index:
                b.depends_on.append((first, f"acronym:{acr}"))
        for name in set(_NAME.findall(b.text)):
            first = seen_names.setdefault(name, b.index)
            if first == b.index:
                b.introduces.add(name)
        b.introduces |= {a for a, i in seen_acronyms.items() if i == b.index}
        b.depends_on = sorted(set(b.depends_on))
    return out


def _cut_cost(b: Block) -> int:
    """How much a cut just before ``b`` breaks: 0 = safe."""
    adjacent = [r for i, r in b.depends_on if i == b.index - 1]
    if not adjacent:
        return 0
    weights = {"dialogue_turn": 1, "verse_continuation": 2, "list_continuation": 3, "backward_reference": 3,
               "opening_points_back": 4, "previous_announces_this": 5}
    return max(weights.get(r.split(":")[0], 2) for r in adjacent)


def segment(text: str, max_words: int = 900) -> dict:
    """Segments of at most ``max_words`` cut at safe boundaries. A dependency
    on a paragraph further back (a name, an acronym) never forces a cut: it
    travels in ``carry``. Only adjacent dependencies decide where to cut."""
    if max_words < 50:
        raise ValueError("max_words must be at least 50")
    bs = dependency_map(text)
    segments, forced, current, words = [], [], [], 0

    def close():
        if current:
            segments.append(list(current))
            current.clear()

    for b in bs:
        if current and words + b.words > max_words:
            if _cut_cost(b) == 0 or b.kind in ("heading", "separator"):
                close()
                words = 0
            else:
                # Walk back to the last safe boundary inside the current segment.
                safe = next((k for k in range(len(current) - 1, 0, -1) if _cut_cost(current[k]) == 0
                             or current[k].kind in ("heading", "separator")), None)
                if safe is not None:
                    head, tail = current[:safe], current[safe:]
                    current[:] = head
                    close()
                    current.extend(tail)
                    words = sum(x.words for x in tail)
                elif words + b.words > 2 * max_words:
                    # One chain longer than twice the limit: cut at its weakest link, and say so.
                    weakest = min(range(1, len(current) + 1),
                                  key=lambda k: (_cut_cost(current[k]) if k < len(current) else _cut_cost(b), -k))
                    if weakest == len(current):
                        forced.append({"before_paragraph": b.index, "breaks": [r for _, r in b.depends_on]})
                        close()
                        words = 0
                    else:
                        head, tail = current[:weakest], current[weakest:]
                        forced.append({"before_paragraph": tail[0].index, "breaks": [r for _, r in tail[0].depends_on]})
                        current[:] = head
                        close()
                        current.extend(tail)
                        words = sum(x.words for x in tail)
        current.append(b)
        words += b.words
    close()
    out, introduced = [], {}
    for n, seg in enumerate(segments):
        start = 0 if n == 0 else seg[0].start
        end = len(text) if n == len(segments) - 1 else segments[n + 1][0].start
        used = set().union(*(set(_NAME.findall(x.text)) | set(_ACRONYM.findall(x.text)) for x in seg))
        carry = sorted(t for t in used if t in introduced)
        out.append({"index": n, "paragraphs": [x.index for x in seg], "start": start, "end": end,
                    "words": sum(x.words for x in seg), "carry": carry[:40]})
        for x in seg:
            for t in x.introduces:
                introduced.setdefault(t, x.index)
    assert "".join(text[s["start"]:s["end"]] for s in out) == text, "segmentation must be lossless"
    return {"kind": "voznativa.longform_segmentation", "max_words": max_words, "paragraphs": len(bs),
            "segments": out, "forced_cuts": forced,
            "oversize": [s["index"] for s in out if s["words"] > max_words]}


def boundary_report(text: str, max_words: int = 900) -> dict:
    """Counts for evaluation: boundaries cut, and how many fell on a visible
    adjacent dependency (should be only the reported forced cuts)."""
    seg = segment(text, max_words)
    bs = {b.index: b for b in dependency_map(text)}
    cuts = [s["paragraphs"][0] for s in seg["segments"][1:]]
    on_dependency = [c for c in cuts if _cut_cost(bs[c]) > 0]
    return {"paragraphs": seg["paragraphs"], "segments": len(seg["segments"]), "cuts": len(cuts),
            "cuts_on_dependency": len(on_dependency), "forced_cuts": len(seg["forced_cuts"]),
            "unreported": len(set(on_dependency) - {f["before_paragraph"] for f in seg["forced_cuts"]}),
            "oversize_segments": len(seg["oversize"]),
            "dependencies": sum(len(b.depends_on) for b in bs.values())}


# --- literary policy ------------------------------------------------------------------

def verse_share(text: str) -> float:
    bs = [b for b in blocks(text) if b.kind not in ("heading", "separator")]
    total = sum(b.words for b in bs) or 1
    return round(sum(b.words for b in bs if b.kind == "verse") / total, 3)


def literary_policy(text: str, genre: str, explicit: bool = False) -> dict:
    """How far a rewrite may go. Verse (>= 50% of the words) is not
    rewritten without an explicit request; literary prose gets local edits
    only. Other genres are unconstrained by this policy."""
    share = verse_share(text)
    if share >= 0.5:
        return {"policy": "verse", "verse_share": share, "max_scope": None if not explicit else "local",
                "reason": "verse: line breaks, rhythm and repetition are the form; no rewrite without an "
                          "explicit request, and then local edits only"}
    if genre == "literary":
        return {"policy": "literary_prose", "verse_share": share, "max_scope": "local",
                "reason": "literary prose: repetition, long periods and marked order may be the author's "
                          "choice; edits stay local (no paragraph or document rewrite)"}
    return {"policy": "default", "verse_share": share, "max_scope": "document", "reason": None}
