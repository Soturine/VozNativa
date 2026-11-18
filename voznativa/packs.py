"""Linguistic pack contract (v0.9 CP6, V09-GAP-21).

Every pack (community, regional, and the ones contributors add) passes two
checks: this envelope, common to all kinds, and the kind's own validator
(``community.validate_pack``, ``regional.validate_pack``). The envelope
exists so that a data file can never become code or authority:

* **identity**: ``id`` is lower-case letters, digits and hyphens (2-64) and
  equals the file name; ``kind`` is a known pack kind; ``schema_version`` is
  an integer;
* **safety**: the file is at most ``MAX_BYTES``; YAML is read with
  ``safe_load`` (no tags, no objects); every string is at most
  ``MAX_STRING`` characters; a field named like a regular expression must be
  at most ``MAX_REGEX`` characters and compile; a value that looks like a path
  must stay inside the pack (no absolute path, no ``..``);
* **no authority over the gates**: keys that would change how text is judged
  or run code (``severity``, ``guards``, ``gate``, ``compare``, ``protect``,
  ``unprotect``, ``override``, ``exec``, ``eval``, ``code``, ``python``,
  ``module``, ``import``, ``callable``, ``script``, ``hook``) are refused
  anywhere in the file. A pack can say which forms belong to a context; it
  cannot relax the Semantic Ledger, ``compare`` or any guard;
* **provenance** (required for external packs, reported as missing for
  bundled ones written before v0.9): ``license`` (an SPDX id, or
  ``proprietary-facts-only`` for counts and facts cited from a source),
  ``provenance`` with ``authors`` and ``created``, and evidence sources.

Problems are errors (the pack is refused) or warnings (reported).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ENVELOPE_VERSION = 1
MAX_BYTES = 512 * 1024
MAX_STRING = 2000
MAX_REGEX = 300
KINDS = {"voznativa.community_pack": "community", "voznativa.regional_evidence_pack": "regional"}
FORBIDDEN_KEYS = frozenset({"severity", "guards", "guard", "gate", "gates", "compare", "protect", "unprotect",
                            "override", "overrides", "exec", "eval", "code", "python", "module", "import", "callable",
                            "script", "hook", "hooks", "command"})
_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
_PATH_KEYS = re.compile(r"(?:^|_)(?:path|file|dir)$")
_REGEX_KEYS = re.compile(r"(?:^|_)(?:regex|pattern)$")
LICENSE_OK = re.compile(r"^(?:CC0-1\.0|CC-BY-4\.0|CC-BY-SA-4\.0|MIT|Apache-2\.0|ODbL-1\.0|"
                        r"proprietary-facts-only|[A-Za-z0-9.+-]{2,40})$")


def _walk(node, path=()):
    if isinstance(node, dict):
        for key, value in node.items():
            yield path + (str(key),), key, value
            yield from _walk(value, path + (str(key),))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, path + (str(i),))


def envelope_problems(pack, file_name: str | None = None, external: bool = False) -> tuple[list[str], list[str]]:
    """(errors, warnings) of the common envelope."""
    errors, warnings = [], []
    if not isinstance(pack, dict):
        return ["a pack must be a mapping"], []
    pid = pack.get("id")
    if not isinstance(pid, str) or not _ID.match(pid):
        errors.append(f"id {pid!r} must be 2-64 lower-case letters, digits or hyphens")
    elif file_name is not None and Path(file_name).stem != pid:
        errors.append(f"id {pid!r} must match the file name {Path(file_name).name}")
    if pack.get("kind") not in KINDS:
        errors.append(f"kind {pack.get('kind')!r} is not a pack kind ({sorted(KINDS)})")
    if not isinstance(pack.get("schema_version"), int) or isinstance(pack.get("schema_version"), bool):
        errors.append("schema_version must be an integer")
    for path, key, value in _walk(pack):
        where = "/".join(path)
        if str(key).lower() in FORBIDDEN_KEYS:
            errors.append(f"{where}: '{key}' is refused: a pack cannot change the gates or run code")
        if isinstance(value, str):
            if len(value) > MAX_STRING:
                errors.append(f"{where}: string longer than {MAX_STRING} characters")
            if _REGEX_KEYS.search(str(key)):
                if len(value) > MAX_REGEX:
                    errors.append(f"{where}: regular expression longer than {MAX_REGEX} characters")
                else:
                    try:
                        re.compile(value)
                    except re.error as error:
                        errors.append(f"{where}: invalid regular expression ({error})")
            if _PATH_KEYS.search(str(key)) and (os.path.isabs(value) or ".." in Path(value).parts
                                                or re.match(r"^[A-Za-z]:", value)):
                errors.append(f"{where}: a path must stay inside the pack")
    target = errors if external else warnings      # bundled packs predate the v0.9 envelope
    license_ = pack.get("license")
    if isinstance(license_, dict):          # regional packs describe their terms in a mapping; spdx names it
        license_ = license_.get("spdx")
    if not license_ or not isinstance(license_, str) or not LICENSE_OK.match(license_.strip()):
        target.append("license missing or not an SPDX id (or proprietary-facts-only)")
    prov = pack.get("provenance")
    if not isinstance(prov, dict) or not prov.get("authors") or not prov.get("created"):
        target.append("provenance with authors and created is missing")
    return errors, warnings


def validate_file(path: str | Path, external: bool = True) -> dict:
    """Envelope and kind validation of one pack file."""
    import yaml
    path = Path(path)
    report = {"file": path.name, "id": None, "kind": None, "errors": [], "warnings": []}
    try:
        size = path.stat().st_size
    except OSError as error:
        report["errors"].append(f"cannot read: {error}")
        return report
    if size > MAX_BYTES:
        report["errors"].append(f"file of {size} bytes exceeds {MAX_BYTES}")
        return report
    try:
        pack = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        report["errors"].append(f"not safe YAML: {type(error).__name__}")
        return report
    errors, warnings = envelope_problems(pack, path.name, external)
    report.update(id=(pack or {}).get("id") if isinstance(pack, dict) else None,
                  kind=(pack or {}).get("kind") if isinstance(pack, dict) else None, errors=errors, warnings=warnings)
    if not errors:
        kind = KINDS[pack["kind"]]
        if kind == "community":
            from .community import validate_pack
        else:
            from .regional import validate_pack
        report["errors"] += validate_pack(pack)
    report["status"] = "valid" if not report["errors"] else "invalid"
    return report


def bundled_dirs() -> dict[str, Path]:
    data = Path(__file__).resolve().parent / "data"
    return {"community": data / "community_packs", "regional": data / "regional_packs"}


def external_dir() -> Path | None:
    """User packs: ``$VOZNATIVA_PACKS_DIR`` (community packs as ``*.yml``)."""
    value = os.environ.get("VOZNATIVA_PACKS_DIR")
    return Path(value) if value else None


def inventory() -> dict:
    out = {"kind": "voznativa.pack_inventory", "envelope_version": ENVELOPE_VERSION, "packs": []}
    for kind, directory in bundled_dirs().items():
        for path in sorted(directory.glob("*.yml")):
            out["packs"].append({"source": "bundled", **validate_file(path, external=False)})
    ext = external_dir()
    if ext is not None:
        for path in sorted(ext.glob("*.yml")) if ext.is_dir() else []:
            out["packs"].append({"source": "external", **validate_file(path, external=True)})
        out["external_dir"] = str(ext)
    return out
