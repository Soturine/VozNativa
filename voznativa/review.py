"""Human review that a plain JSON file cannot fake by itself.

A judgment with ``"kind": "human"`` is only *claimed* unless it carries a
valid signature made by ``voznativa review``, which:

* runs only in an interactive terminal (an agent's non-interactive shell
  cannot answer it);
* binds the verdict to the exact texts (sha256 of original and candidate);
* signs the judgment with HMAC-SHA256 using a per-user key kept outside the
  repository (``~/.voznativa/review.key`` or ``VOZNATIVA_REVIEW_KEY``).

What this proves: the holder of that key, on a machine that has it, approved
these exact texts. It does not prove who the person is, and a process that
reads the key file can forge a signature; on a machine without the key the
signature cannot be checked and the review stays "claimed".
"""
from __future__ import annotations

import getpass
import hashlib
import hmac
import json
import os
import platform
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

SIGNATURE_ALG = "HMAC-SHA256"


def content_hash(text: str) -> str:
    """sha256 of the text with LF line endings (stable across Windows/Linux)."""
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def key_path() -> Path:
    env = os.environ.get("VOZNATIVA_REVIEW_KEY")
    return Path(env) if env else Path.home() / ".voznativa" / "review.key"


def _load_key(create: bool = False) -> bytes | None:
    path = key_path()
    if path.is_file():
        return bytes.fromhex(path.read_text(encoding="ascii").strip())
    if not create:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(32)
    path.write_text(key.hex(), encoding="ascii")
    try:
        os.chmod(path, 0o600)
    except OSError:  # Windows ignores POSIX modes; the file stays in the user profile
        pass
    return key


def _canonical(judgment: dict) -> bytes:
    body = {k: v for k, v in judgment.items() if k not in {"signature", "authenticity"}}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign(judgment: dict, key: bytes) -> dict:
    signed = dict(judgment)
    signed["signature"] = {
        "alg": SIGNATURE_ALG,
        "key_id": hashlib.sha256(key).hexdigest()[:12],
        "value": hmac.new(key, _canonical(judgment), hashlib.sha256).hexdigest(),
    }
    return signed


def verify(judgment: dict) -> str:
    """'verified', 'unsigned', 'no_local_key', 'other_key' or 'invalid'."""
    signature = judgment.get("signature")
    if not signature:
        return "unsigned"
    key = _load_key()
    if key is None:
        return "no_local_key"
    if signature.get("key_id") != hashlib.sha256(key).hexdigest()[:12]:
        return "other_key"
    expected = hmac.new(key, _canonical(judgment), hashlib.sha256).hexdigest()
    return "verified" if hmac.compare_digest(expected, signature.get("value", "")) else "invalid"


VERDICTS = {"e": "equivalent", "n": "not_equivalent", "u": "uncertain"}


def interactive_review(original: str, candidate: str, report: dict, reviewer: str,
                       ask: Callable[[str], str] = input, show: Callable[[str], None] = print) -> dict:
    """Ask a person for a verdict and return a signed, text-bound judgment."""
    show("=== ORIGINAL ===\n" + original + "\n=== CANDIDATA ===\n" + candidate)
    show(f"Gate determinístico: {report['status']}")
    for issue in report["issues"]:
        show(f"  [{issue['severity']}] {issue['code']}: {issue['message']}")
    answer = ""
    while answer not in VERDICTS:
        answer = ask("A candidata diz o mesmo que o original? [e]quivalente / [n]ão / [u] incerto: ").strip().lower()[:1]
    statement = ""
    while len(statement) < 10:
        statement = ask("Em uma frase, o que você verificou (mín. 10 caracteres): ").strip()
    judgment = {
        "kind": "human",
        "judge_id": reviewer,
        "verdict": VERDICTS[answer],
        "statement": statement,
        "claims": [],
        "added_claims": [],
        "original_sha256": content_hash(original),
        "candidate_sha256": content_hash(candidate),
        "attestation": {"method": "interactive_tty", "os_user": getpass.getuser(), "host": platform.node()},
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return sign(judgment, _load_key(create=True))
