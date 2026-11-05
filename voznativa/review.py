"""Human review that a plain JSON file cannot fake by itself.

A judgment with ``"kind": "human"`` is only *claimed* unless it carries a
valid signature made by ``voznativa review``, which:

* runs only in an interactive terminal (an agent's non-interactive shell
  cannot answer it);
* binds the verdict to the exact texts (sha256 of original and candidate);
* signs the judgment, by default with HMAC-SHA256 and a per-user key kept
  outside the repository (``~/.voznativa/review.key`` or
  ``VOZNATIVA_REVIEW_KEY``), or with the reviewer's own SSH key
  (``--ssh-key``), verified against the public keys in a reviewer registry.

A signature answers four different questions, and ``assess()`` reports them
apart instead of folding them into one "verified":

* integrity: were these exact bytes signed by that key?
* key possession: who can hold the key? The HMAC key is a shared secret on
  this machine: any process running as this OS user (the developer, an
  agent) can read it and sign, and checking it needs the same secret. An SSH
  key is private to the signer; the project keeps only the public key.
* declared identity: ``judge_id``, the SSH principal and the OS user are
  what someone typed or what the machine reports. Nothing here proves who a
  person is.
* independence: whether the reviewer is someone other than the people who
  built what is being judged. A signature can never show it; at most the
  reviewer registry records it as declared, and an HMAC review on the
  developer's machine is never counted as independent.
"""
from __future__ import annotations

import getpass
import hashlib
import hmac
import json
import os
import platform
import secrets
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

SIGNATURE_ALG = "HMAC-SHA256"
SSH_ALG = "ssh-sig"
SSH_NAMESPACE = "voznativa-review"
RELATIONSHIPS = {"independent", "collaborator", "developer"}


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
    # Created with mode 0600 in one step (H6): writing first and chmod-ing after
    # left the secret readable by other users of the machine in between. O_EXCL
    # also refuses to follow a planted file or link in place of a new key.
    # Windows ignores POSIX modes; there the file stays in the user profile.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as handle:
        handle.write(key.hex())
    return key


def _canonical(judgment: dict) -> bytes:
    body = {k: v for k, v in judgment.items() if k not in {"signature", "authenticity", "assurance"}}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign(judgment: dict, key: bytes) -> dict:
    signed = dict(judgment)
    signed["signature"] = {
        "alg": SIGNATURE_ALG,
        "key_id": hashlib.sha256(key).hexdigest()[:12],
        "value": hmac.new(key, _canonical(judgment), hashlib.sha256).hexdigest(),
    }
    return signed


# --- SSH signatures (ssh-keygen -Y, OpenSSH >= 8.1; no Python dependency) -------

def _ssh_keygen() -> str:
    found = shutil.which("ssh-keygen")
    if not found:
        raise ValueError("ssh-keygen (OpenSSH 8.1+) is needed for SSH-signed reviews")
    return found


def sign_ssh(judgment: dict, key_file: str | Path, principal: str, timeout: float = 120.0) -> dict:
    """Sign with the reviewer's own SSH private key. The principal is part of
    the signed body, so it cannot be swapped afterwards."""
    if not principal:
        raise ValueError("an SSH-signed review needs a principal (the name in allowed_signers)")
    body = dict(judgment, signer={"principal": principal, "method": SSH_ALG})
    with tempfile.TemporaryDirectory(prefix="voznativa-sign-") as tmp:
        data = Path(tmp) / "judgment.json"
        data.write_bytes(_canonical(body))
        # Fresh paths only: ssh-keygen asks before overwriting a .sig and would hang.
        done = subprocess.run([_ssh_keygen(), "-Y", "sign", "-f", str(key_file), "-n", SSH_NAMESPACE, str(data)],
                              stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, check=False)
        sig = data.with_name(data.name + ".sig")
        if done.returncode != 0 or not sig.is_file():
            raise ValueError("ssh-keygen could not sign: " + done.stderr.decode("utf-8", "replace").strip()[:300])
        value = sig.read_text(encoding="ascii")
    body["signature"] = {"alg": SSH_ALG, "namespace": SSH_NAMESPACE, "principal": principal, "value": value}
    return body


def registry_dir() -> Path | None:
    """Reviewer registry: ``allowed_signers`` (OpenSSH public keys) and
    ``registry.json`` (declared identity and relationship to the project)."""
    env = os.environ.get("VOZNATIVA_REVIEWERS")
    if env:
        return Path(env)
    from .paths import candidates
    for root in candidates():
        if (root / "evals" / "reviewers" / "allowed_signers").is_file():
            return root / "evals" / "reviewers"
    return None


def load_registry(directory: Path | None = None) -> dict:
    directory = directory or registry_dir()
    if directory is None or not (directory / "registry.json").is_file():
        return {}
    data = json.loads((directory / "registry.json").read_text(encoding="utf-8"))
    return data.get("reviewers", {})


def registry_problems(directory: Path | None = None) -> list[str]:
    """Entries that cannot be read as declared: an unknown ``relationship``
    (only RELATIONSHIPS are understood) or no declared name. ``assess`` already
    treats an unknown value as ``not_established``; this makes the typo visible
    instead of silently downgrading a reviewer."""
    problems = []
    for principal, entry in sorted(load_registry(directory).items()):
        relationship = entry.get("relationship")
        if relationship not in RELATIONSHIPS:
            problems.append(f"{principal}: relationship {relationship!r} is not one of {sorted(RELATIONSHIPS)}")
        if not entry.get("declared_name"):
            problems.append(f"{principal}: no declared_name")
    return problems


def _verify_ssh(judgment: dict, directory: Path | None) -> str:
    signature = judgment["signature"]
    allowed = directory / "allowed_signers" if directory else None
    if allowed is None or not allowed.is_file():
        return "no_registry"
    principal = signature.get("principal") or ""
    if principal != (judgment.get("signer") or {}).get("principal"):
        return "invalid"
    if not any(line.split()[:1] == [principal] for line in allowed.read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.startswith("#")):
        return "unknown_signer"
    try:
        keygen = _ssh_keygen()
    except ValueError:
        return "no_verifier"
    with tempfile.TemporaryDirectory(prefix="voznativa-verify-") as tmp:
        sig = Path(tmp) / "judgment.sig"
        sig.write_text(signature.get("value", ""), encoding="ascii")
        done = subprocess.run([keygen, "-Y", "verify", "-f", str(allowed), "-I", principal, "-n", SSH_NAMESPACE,
                               "-s", str(sig)], input=_canonical(judgment), capture_output=True, timeout=60,
                              check=False)
    return "verified" if done.returncode == 0 else "invalid"


def verify(judgment: dict, registry: Path | None = None) -> str:
    """'verified', 'unsigned', 'invalid', and why a signature could not be
    checked here: 'no_local_key', 'other_key' (HMAC from another machine or
    user), 'no_registry', 'unknown_signer' or 'no_verifier' (SSH)."""
    signature = judgment.get("signature")
    if not signature:
        return "unsigned"
    if signature.get("alg") == SSH_ALG:
        return _verify_ssh(judgment, registry or registry_dir())
    key = _load_key()
    if key is None:
        return "no_local_key"
    if signature.get("key_id") != hashlib.sha256(key).hexdigest()[:12]:
        return "other_key"
    expected = hmac.new(key, _canonical(judgment), hashlib.sha256).hexdigest()
    return "verified" if hmac.compare_digest(expected, signature.get("value", "")) else "invalid"


def signer_key(judgment: dict) -> str | None:
    """A stable id of the key that signed (HMAC key id or SSH principal)."""
    signature = judgment.get("signature") or {}
    if signature.get("alg") == SSH_ALG:
        return "ssh:" + str(signature.get("principal"))
    return "hmac:" + str(signature.get("key_id")) if signature.get("key_id") else None


def assess(judgment: dict, registry: Path | None = None) -> dict:
    """Integrity, key possession, declared identity and independence, apart."""
    status = verify(judgment, registry)
    integrity = {"verified": "valid", "invalid": "invalid", "unsigned": "unsigned"}.get(status, "unverifiable")
    signature = judgment.get("signature") or {}
    attestation = judgment.get("attestation") or {}
    identity = {"judge_id": judgment.get("judge_id"), "os_user": attestation.get("os_user"),
                "host": attestation.get("host"), "verified": False,
                "note": "declared by the reviewer or reported by the machine; never proof of who signed"}
    if signature.get("alg") == SSH_ALG:
        principal = signature.get("principal")
        entry = load_registry(registry).get(principal, {}) if integrity == "valid" else {}
        identity.update(principal=principal, registry_name=entry.get("declared_name"))
        possession = ("private SSH key of the registered principal; the project holds only its public key"
                      if integrity == "valid" else "SSH key not checked against the registry here")
        relationship = entry.get("relationship")
        independence = ("declared" if relationship == "independent" else
                        "none" if relationship == "developer" else "not_established")
        independence_basis = (f"reviewer registry: relationship={relationship}" if relationship else
                              "no relationship recorded for this principal")
    else:
        possession = ("shared HMAC secret of this machine's OS user: anyone or any process with access to "
                      f"{key_path()} could have signed" if integrity == "valid" else
                      "HMAC key not available here" if status in {"no_local_key", "other_key"} else None)
        independence = "not_established"
        independence_basis = ("a local HMAC key cannot tell the developer, an agent and another person apart"
                              if signature else "unsigned")
    return {"integrity": integrity, "check": status, "method": signature.get("alg"), "key": signer_key(judgment),
            "key_possession": possession, "declared_identity": identity,
            "independence": independence, "independence_basis": independence_basis}


VERDICTS = {"e": "equivalent", "n": "not_equivalent", "u": "uncertain"}


def interactive_review(original: str, candidate: str, report: dict, reviewer: str,
                       ask: Callable[[str], str] = input, show: Callable[[str], None] = print,
                       ssh_key: str | None = None, principal: str | None = None) -> dict:
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
    if ssh_key:
        return sign_ssh(judgment, ssh_key, principal or reviewer)
    return sign(judgment, _load_key(create=True))
