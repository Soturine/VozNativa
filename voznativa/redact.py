"""Redaction for recorded runs and error messages (v0.4.0 M0.6).

Three kinds of sensitive data reach a recorded run:

* user texts (inputs, outputs, raw model answers, previews), replaced by a
  keyed hash and a length;
* credentials in the model command (``--api-key sk-...``, ``-H
  "Authorization: Bearer ..."``, ``TOKEN=...``), masked in argv and ids;
* fragments of either inside free text (provider errors that echo stderr,
  judge errors that quote a claim), scrubbed before anything is written.

Hashes are HMAC-SHA256 with a key that is never written to the report: a
plain sha256 of a short text ("sim", a phone number) can be reversed by
guessing. With the same key (``--redact-key``) two runs can still be
compared; without it the hashes only match texts within one run.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets

MASK = "<redacted>"
SECRET_FLAGS = re.compile(r"^--?(?:api[-_]?key|key|token|access[-_]?token|auth|authorization|password|passwd|"
                          r"secret|client[-_]?secret|bearer|cookie|header|H)$", re.I)
SECRET_ASSIGNMENT = re.compile(r"^((?:--)?[\w.-]*(?:key|token|secret|password|passwd|auth)[\w.-]*=)(.+)$", re.I)
SECRET_VALUES = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),                     # OpenAI / Anthropic style keys
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"),  # GitHub tokens
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                        # AWS access key id
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"),                    # Google API key
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),              # Slack
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)\b(?:api[-_]?key|token|secret|password)\s*[:=]\s*\S+"),
]
_QUOTED = re.compile(r"\"[^\"\n]{4,}\"|'[^'\n]{4,}'|“[^”\n]{4,}”")


def new_key() -> bytes:
    return secrets.token_bytes(32)


def shield(text: str | None, key: bytes) -> dict | None:
    """A keyed hash and the length of ``text``; never the text."""
    if text is None:
        return None
    digest = hmac.new(key, text.replace("\r\n", "\n").encode("utf-8"), hashlib.sha256).hexdigest()
    return {"hmac_sha256": digest, "chars": len(text)}


def scrub_secrets(text: str) -> str:
    for pattern in SECRET_VALUES:
        text = pattern.sub(MASK, text)
    return text


def redact_argv(argv: list[str]) -> list[str]:
    """Mask credential values in a command line: the value after a secret
    flag, ``name=value`` assignments whose name looks secret, header values
    and any token that matches a known key format."""
    out, mask_next = [], False
    for arg in argv:
        if mask_next:
            out.append(MASK)
            mask_next = False
            continue
        if SECRET_FLAGS.match(arg):
            out.append(arg)
            mask_next = True
            continue
        assignment = SECRET_ASSIGNMENT.match(arg)
        if assignment:
            out.append(assignment.group(1) + MASK)
            continue
        out.append(scrub_secrets(arg))
    return out


def scrub_message(message: str | None, texts: list[str] = (), limit: int = 300) -> str | None:
    """Free text safe to record in a redacted run: secrets masked, quoted
    material removed, and any sentence of a known text (input, output, model
    answer) replaced. Cut to ``limit`` characters."""
    if message is None:
        return None
    message = scrub_secrets(message)
    for text in sorted({t for t in texts if t}, key=len, reverse=True):
        for piece in sorted({p.strip() for p in re.split(r"(?<=[.!?\n])\s+", text)}, key=len, reverse=True):
            if len(piece) >= 8:
                message = message.replace(piece, MASK)
    message = _QUOTED.sub(MASK, message)
    return message if len(message) <= limit else message[:limit] + f"... [{len(message) - limit} chars cut]"
