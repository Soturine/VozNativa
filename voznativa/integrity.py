"""Text integrity audit and provenance record (v0.7.0 CP12).

Integrity is about *characters*: zero-width and format characters, bidi
controls, Unicode tag characters (a known channel for hidden instructions),
control characters, unusual spaces, soft hyphens and mixed-script words
(homoglyphs). Each finding says whether it is likely legitimate (a no-break
space in "R$ 10", a joiner inside an emoji sequence, right-to-left text) or
suspicious, and ``clean`` removes only what a policy names.

What this module is NOT:

* a statistical watermark detector or remover. Generative watermarks are
  distributions over word choices, verifiable only with the method and key of
  whoever embedded them; removing invisible characters neither finds nor
  removes them. No function here returns or implies ``watermark_free``.
* a way to hide AI involvement. ``provenance_record`` states which tool and
  provider touched the text, with hashes, so a person can disclose it (EU AI
  Act Art. 50 §4 asks deployers publishing AI-generated public-interest text
  to disclose it unless it underwent human review or editorial control).
"""
from __future__ import annotations

import hashlib
import unicodedata
from datetime import datetime, timezone

SCHEMA_VERSION = 1
ZERO_WIDTH = {0x200B: "ZERO WIDTH SPACE", 0x200C: "ZERO WIDTH NON-JOINER", 0x200D: "ZERO WIDTH JOINER",
              0x2060: "WORD JOINER", 0xFEFF: "ZERO WIDTH NO-BREAK SPACE / BOM"}
BIDI = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A)) | {0x200E, 0x200F, 0x061C}
TAGS = range(0xE0000, 0xE0080)
VARIATION = set(range(0xFE00, 0xFE10)) | set(range(0xE0100, 0xE01F0))
RTL_SCRIPTS = ("ARABIC", "HEBREW", "SYRIAC", "THAANA", "NKO")
CLEAN_POLICIES = ("tags", "bidi_unbalanced", "zero_width_outside_emoji", "controls", "soft_hyphen")


def _script(ch: str) -> str | None:
    if not ch.isalpha():
        return None
    name = unicodedata.name(ch, "")
    for script in ("LATIN", "CYRILLIC", "GREEK"):
        if name.startswith(script):
            return script
    return "OTHER"


def _is_emoji(ch: str) -> bool:
    cp = ord(ch)
    return 0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF


def audit(text: str) -> dict:
    """Every non-ordinary character, classified; no change to the text."""
    findings = []
    has_rtl = any(unicodedata.name(c, "").startswith(RTL_SCRIPTS) for c in text if c.isalpha())

    def add(i, kind, assessment, note):
        ch = text[i]
        findings.append({"offset": i, "codepoint": f"U+{ord(ch):04X}", "name": unicodedata.name(ch, "<unnamed>"),
                         "category": unicodedata.category(ch), "kind": kind, "assessment": assessment, "note": note})

    for i, ch in enumerate(text):
        cp = ord(ch)
        if cp in TAGS:
            add(i, "tag_character", "suspicious", "invisible tag characters can carry hidden text or instructions")
        elif cp in BIDI:
            add(i, "bidi_control", "legitimate_possible" if has_rtl else "suspicious",
                "direction control; in text without right-to-left script it can reorder what a reader sees")
        elif cp in ZERO_WIDTH:
            emoji_join = cp == 0x200D and 0 < i < len(text) - 1 and _is_emoji(text[i - 1]) and _is_emoji(text[i + 1])
            bom = cp == 0xFEFF and i == 0
            add(i, "zero_width", "legitimate_possible" if emoji_join or bom else "suspicious",
                "joins an emoji sequence" if emoji_join else "byte order mark at the start" if bom
                else "invisible; changes matching, counting and copy-paste")
        elif cp in VARIATION:
            add(i, "variation_selector", "legitimate_possible", "selects a glyph variant (emoji or CJK)")
        elif cp == 0x00AD:
            add(i, "soft_hyphen", "legitimate_possible", "invisible hyphenation hint; breaks search")
        elif unicodedata.category(ch) == "Cc" and ch not in "\t\n\r":
            add(i, "control_character", "suspicious", "control character inside text")
        elif unicodedata.category(ch) == "Zs" and ch != " ":
            add(i, "unusual_space", "legitimate_possible",
                "no-break or typographic space (often intentional: 'R$ 10', '10 %')")
        elif unicodedata.category(ch) == "Cf":
            add(i, "format_character", "suspicious", "other invisible format character")

    words = []
    start = None
    for i, ch in enumerate(text + " "):
        if ch.isalpha():
            start = i if start is None else start
        elif start is not None:
            words.append((start, i))
            start = None
    for a, b in words:
        scripts = {_script(c) for c in text[a:b]} - {None}
        if "LATIN" in scripts and scripts & {"CYRILLIC", "GREEK"}:
            findings.append({"offset": a, "end": b, "kind": "mixed_script_word", "assessment": "suspicious",
                             "text": text[a:b], "scripts": sorted(scripts),
                             "note": "Latin word with Cyrillic/Greek letters: possible homoglyph"})
    counts: dict[str, int] = {}
    for f in findings:
        counts[f["kind"]] = counts.get(f["kind"], 0) + 1
    return {"kind": "voznativa.integrity_audit", "schema_version": SCHEMA_VERSION, "characters": len(text),
            "findings": findings, "counts": counts,
            "suspicious": sum(f["assessment"] == "suspicious" for f in findings),
            "scope": "character-level integrity only; says nothing about statistical watermarks or authorship"}


def clean(text: str, policies: tuple[str, ...] = ("tags", "bidi_unbalanced", "zero_width_outside_emoji",
                                                   "controls")) -> dict:
    """Remove only the classes named. NBSP, variation selectors, emoji joiners
    and RTL text are kept. The result says what was removed, by code point."""
    unknown = set(policies) - set(CLEAN_POLICIES)
    if unknown:
        raise ValueError(f"unknown policies {sorted(unknown)}; choose from {CLEAN_POLICIES}")
    report = audit(text)
    drop = set()
    for f in report["findings"]:
        if "codepoint" not in f:
            continue
        kind = f["kind"]
        if (kind == "tag_character" and "tags" in policies) or \
                (kind == "bidi_control" and f["assessment"] == "suspicious" and "bidi_unbalanced" in policies) or \
                (kind == "zero_width" and f["assessment"] == "suspicious" and "zero_width_outside_emoji" in policies) or \
                (kind == "control_character" and "controls" in policies) or \
                (kind == "soft_hyphen" and "soft_hyphen" in policies):
            drop.add(f["offset"])
    out = "".join(ch for i, ch in enumerate(text) if i not in drop)
    removed: dict[str, int] = {}
    for i in drop:
        key = f"U+{ord(text[i]):04X}"
        removed[key] = removed.get(key, 0) + 1
    return {"text": out, "removed": removed, "policies": list(policies),
            "note": "integrity cleaning; not watermark removal and not a change of provenance"}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def provenance_record(original: str, final: str, *, tool_version: str, operation: str, provider: str | None,
                      model: str | None = None, declared_origin: str = "unknown", human_review: str = "not_recorded",
                      outcome: str | None = None) -> dict:
    """What touched the text, without the text: hashes, the tool, the provider
    and model when one was called, the declared origin of the input and
    whether a person reviewed the result. Meant for disclosure, never to hide it."""
    ai_assisted = provider not in (None, "", "none")
    return {
        "kind": "voznativa.provenance", "schema_version": SCHEMA_VERSION,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_sha256": sha256(original), "output_sha256": sha256(final), "changed": original != final,
        "tool": {"name": "voznativa", "version": tool_version, "operation": operation, "outcome": outcome},
        "provider": provider, "model": model, "ai_assisted": ai_assisted,
        "declared_origin": declared_origin, "human_review": human_review,
        "disclosure_note": ("text edited with an AI model through VozNativa; disclose it where the law or the venue "
                            "asks (e.g. EU AI Act Art. 50 §4 for public-interest publications without human "
                            "editorial control)") if ai_assisted and original != final else None,
        "retains_text": False,
    }
