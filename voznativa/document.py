"""Document contract for long-form rewriting (v0.7.0 CP7).

A versioned, serialisable plan of a whole document, built on ``longform``
(blocks, dependency map, safe cut costs) and ``spans`` (protected values):

* **units**: contiguous, lossless slices of the text. Protected blocks (code,
  tables, separators, quotations, verse without an explicit request) are
  units of their own with action ``protect`` and never reach a model.
  Rewritable blocks are grouped up to ``segment_words`` and cut only where
  no adjacent dependency crosses; a cut that must break one is recorded in
  ``forced_cuts``.
* **core vs. edges**: each unit knows the offsets of its text without the
  surrounding blank lines; ``reassemble`` replaces only cores, so the
  document's whitespace and every untouched byte survive.
* **inventory**: protected values of the whole document (numbers, dates,
  money, versions, quotes, entities) and names/acronyms with the unit that
  introduces them; each unit carries the ones it uses (``carry``).
* **dependencies**: for each unit, the earlier units its blocks lean on.
* **limits**: words, units, provider calls, attempts per unit, seconds.
  Exceeding a limit raises ``PlanLimitExceeded`` (fail closed: the engine
  returns the original instead of a truncated document).

The plan describes; it never edits. ``validate_plan`` checks that a plan
still matches its text (sha256, coverage, order) before anyone uses it.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

from . import longform

SCHEMA_VERSION = 1
KIND = "voznativa.document_plan"
ALWAYS_PROTECTED = ("code", "table", "separator", "quote")


class PlanLimitExceeded(ValueError):
    """The document is larger than the configured limits allow."""


@dataclass(frozen=True)
class Limits:
    max_words: int = 200_000
    max_units: int = 400
    segment_words: int = 600
    attempts_per_unit: int = 3
    max_provider_calls: int = 800
    timeout_s: float = 3600.0

    def as_dict(self) -> dict:
        return asdict(self)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _protected_kind(kind: str, verse_explicit: bool) -> bool:
    return kind in ALWAYS_PROTECTED or (kind == "verse" and not verse_explicit)


def _core(text: str, bs) -> tuple[int, int]:
    """Offsets of the visible text of consecutive blocks ``bs``."""
    core_start, core_end = bs[0].start, bs[-1].end
    # A block keeps the newline it starts with; the core starts at its first visible character.
    while core_start < core_end and text[core_start] in "\r\n":
        core_start += 1
    while core_end > core_start and text[core_end - 1] in " \t\r\n":
        core_end -= 1
    return core_start, core_end


def _expected_protected_kinds(verse_explicit: bool) -> list[str]:
    return list(ALWAYS_PROTECTED) + ([] if verse_explicit else ["verse"])


def build_plan(text: str, context: dict | None = None, limits: Limits = Limits(), verse_explicit: bool = False,
               instruction: str | None = None) -> dict:
    """The plan of ``text``. ``verse_explicit``: the user asked for verse to be
    rewritten (otherwise verse is protected, like the v0.6 literary policy)."""
    words = len(text.split())
    if words > limits.max_words:
        raise PlanLimitExceeded(f"{words} words > max_words {limits.max_words}")
    blocks = longform.dependency_map(text)
    units: list[dict] = []
    forced: list[dict] = []
    current: list = []

    def close(action: str):
        if current:
            units.append({"blocks": list(current), "action": action})
            current.clear()

    for b in blocks:
        if _protected_kind(b.kind, verse_explicit):
            close("rewrite")
            current.append(b)
            close("protect")
            continue
        size = sum(x.words for x in current)
        if current and size + b.words > limits.segment_words:
            safe = longform._cut_cost(b) == 0 or b.kind in ("heading",)
            if not safe:
                back = next((k for k in range(len(current) - 1, 0, -1) if longform._cut_cost(current[k]) == 0), None)
                if back is not None:
                    tail = current[back:]
                    del current[back:]
                    close("rewrite")
                    current.extend(tail)
                elif size + b.words > 2 * limits.segment_words:
                    forced.append({"before_block": b.index, "breaks": [r for _, r in b.depends_on]})
                    close("rewrite")
            else:
                close("rewrite")
        current.append(b)
    close("rewrite")

    rewrite_units = sum(u["action"] == "rewrite" for u in units)
    if rewrite_units > limits.max_units:
        raise PlanLimitExceeded(f"{rewrite_units} rewritable units > max_units {limits.max_units}")

    from .spans import extract
    inventory = [{"type": s.type, "text": s.text, "key": s.key, "start": s.start, "end": s.end}
                 for s in extract(text)]
    introduced: dict[str, int] = {}
    block_unit: dict[int, int] = {}
    out_units = []
    for n, u in enumerate(units):
        bs = u["blocks"]
        start = 0 if n == 0 else bs[0].start
        end = len(text) if n == len(units) - 1 else units[n + 1]["blocks"][0].start
        core_start, core_end = _core(text, bs)
        for b in bs:
            block_unit[b.index] = n
        used = set().union(*(set(longform._NAME.findall(b.text)) | set(longform._ACRONYM.findall(b.text))
                             for b in bs))
        deps = sorted({block_unit[i] for b in bs for i, _ in b.depends_on if block_unit.get(i, n) != n})
        out_units.append({
            "index": n, "action": u["action"], "kinds": [b.kind for b in bs], "blocks": [b.index for b in bs],
            "start": start, "end": end, "core_start": core_start, "core_end": core_end,
            "words": sum(b.words for b in bs), "sha256": sha256(text[core_start:core_end]),
            "carry": sorted(t for t in used if t in introduced)[:40], "depends_on_units": deps,
            "values": sorted({i["key"] for i in inventory if core_start <= i["start"] < core_end})[:80],
        })
        for b in bs:
            for t in b.introduces:
                introduced.setdefault(t, n)
    plan = {
        "kind": KIND, "schema_version": SCHEMA_VERSION, "sha256": sha256(text), "words": words,
        "limits": limits.as_dict(), "verse_explicit": verse_explicit,
        "instruction": instruction,
        "context": ({k: (context.get(k) or {}).get("value") if isinstance(context.get(k), dict) else context.get(k)
                     for k in ("task", "genre", "register")} | {"protections": context.get("protections")})
        if context else None,
        "units": out_units, "forced_cuts": forced,
        "inventory": {"values": [{k: i[k] for k in ("type", "text", "key")} for i in inventory],
                      "introduced": {t: u for t, u in sorted(introduced.items())}},
        "policy": {"protected_kinds": _expected_protected_kinds(verse_explicit),
                   "unit_failure": "keep the unit's original text",
                   "global_failure": "revert changed units until the document passes, else return the original"},
    }
    problems = validate_plan(plan, text)
    if problems:   # a bug in the planner, never the user's fault: fail closed
        raise AssertionError(f"inconsistent document plan: {problems}")
    return plan


def validate_plan(plan: dict, text: str) -> list[str]:
    """Problems that make a plan unusable for ``text`` (empty = usable).

    A serialised plan is data, not authority (v0.7.0.dev1, H07-NEW-01): which
    units may be rewritten is derived again from ``text`` and the protection
    policy, so editing ``action``, ``kinds``, ``blocks`` or the core offsets of
    a plan cannot unprotect a code block, table, separator or quotation.
    ``verse_explicit`` is the caller's authorisation to rewrite verse (the same
    one ``build_plan`` takes), so it is checked for consistency, not overruled."""
    problems = []
    if plan.get("kind") != KIND or plan.get("schema_version") != SCHEMA_VERSION:
        problems.append("unsupported plan kind or schema_version")
    if plan.get("sha256") != sha256(text):
        problems.append("the plan was built for another text (sha256 differs)")
    verse_explicit = plan.get("verse_explicit", False)
    if not isinstance(verse_explicit, bool):
        problems.append("verse_explicit must be a boolean")
        verse_explicit = False
    if (plan.get("policy") or {}).get("protected_kinds") != _expected_protected_kinds(verse_explicit):
        problems.append("policy.protected_kinds does not match the protection policy")
    units = plan.get("units", [])
    if not isinstance(units, list) or not all(isinstance(u, dict) for u in units):
        return problems + ["units must be a list of objects"]
    required = ("index", "action", "kinds", "blocks", "start", "end", "core_start", "core_end", "sha256")
    missing = [n for n, u in enumerate(units) if any(k not in u for k in required)]
    if missing:
        return problems + [f"unit(s) {missing[:10]} miss required fields"]
    derived = longform.blocks(text)
    position, next_block = 0, 0
    for n, u in enumerate(units):
        if u["index"] != n:
            problems.append(f"unit at position {n} has index {u['index']!r}")
        if u["start"] != position:
            problems.append(f"unit {u['index']} starts at {u['start']}, expected {position}")
        if not (u["start"] <= u["core_start"] <= u["core_end"] <= u["end"]):
            problems.append(f"unit {u['index']} core outside the unit")
        elif sha256(text[u["core_start"]:u["core_end"]]) != u["sha256"]:
            problems.append(f"unit {u['index']} core sha256 differs")
        position = u["end"]
        expected_blocks = list(range(next_block, next_block + len(u["blocks"]) if isinstance(u["blocks"], list) else 0))
        if not expected_blocks or u["blocks"] != expected_blocks or expected_blocks[-1] >= len(derived):
            problems.append(f"unit {u['index']} blocks {u['blocks']!r} are not the next blocks of the text")
            continue
        next_block = expected_blocks[-1] + 1
        bs = derived[expected_blocks[0]:next_block]
        if u["kinds"] != [b.kind for b in bs]:
            problems.append(f"unit {u['index']} kinds {u['kinds']!r} differ from the text's {[b.kind for b in bs]}")
        if (u["core_start"], u["core_end"]) != _core(text, bs):
            problems.append(f"unit {u['index']} core offsets do not match its blocks")
        protected = [b.kind for b in bs if _protected_kind(b.kind, verse_explicit)]
        expected_action = "protect" if protected else "rewrite"
        if protected and len(bs) > 1:
            problems.append(f"unit {u['index']} mixes protected blocks {protected} with other blocks")
        if u["action"] != expected_action:
            problems.append(f"unit {u['index']} action {u['action']!r}; the policy requires {expected_action!r}")
    # A text without blocks (empty or only whitespace) has no units; reassemble returns it as is.
    if units and position != len(text):
        problems.append(f"units end at {position}, text has {len(text)} characters")
    if next_block != len(derived):
        problems.append(f"units cover {next_block} of the text's {len(derived)} blocks")
    return problems


def reassemble(text: str, plan: dict, replacements: dict[int, str] | None = None) -> str:
    """The document with unit cores replaced. Protected units cannot be
    replaced; without replacements the result is byte-identical to ``text``."""
    problems = validate_plan(plan, text)
    if problems:
        raise ValueError(f"plan does not match the text: {problems}")
    replacements = replacements or {}
    known = {u["index"] for u in plan["units"]}
    unknown = [k for k in replacements if k not in known]
    if unknown:
        raise ValueError(f"replacements for unknown unit(s) {unknown[:10]}")
    if any(v is not None and not isinstance(v, str) for v in replacements.values()):
        raise ValueError("a replacement must be text")
    if not plan["units"]:
        return text
    out = []
    for u in plan["units"]:
        new = replacements.get(u["index"])
        if new is not None and u["action"] == "protect":
            raise ValueError(f"unit {u['index']} is protected ({u['kinds']}) and cannot be replaced")
        core = text[u["core_start"]:u["core_end"]] if new is None else new
        out.append(text[u["start"]:u["core_start"]] + core + text[u["core_end"]:u["end"]])
    return "".join(out)


def unit_text(text: str, unit: dict) -> str:
    return text[unit["core_start"]:unit["core_end"]]


def structure_of(text: str) -> list[str]:
    """Block kinds in order: a rewrite of a unit must keep them (a list stays
    a list, dialogue turns stay turns)."""
    return [b.kind for b in longform.blocks(text) if b.kind != "separator"]
