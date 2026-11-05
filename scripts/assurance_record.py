#!/usr/bin/env python3
"""Record the raw output of an assurance tool run under evals/assurance/runs/.

Each entry is a file the tool wrote, the exact command and its exit code.
The published copy is sanitized: the user's home, the temporary directory
and the project root become ``<HOME>``, ``<TMP>`` and ``<PROJECT>``, so no
user name or machine path is committed. The manifest keeps the sha256 of
the raw bytes (not published) and of the sanitized copy (published).

    python scripts/assurance_record.py --run 2026-11-05-cp0-baseline \
        --tool assertiva=0.10.1 --tool derivanta-engine=0.1.0 \
        --entry "assertiva-static.json|0|assertiva audit . --output json|/tmp/out.json"

Sanitizing changes bytes; it never changes a finding, a count or a status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "evals" / "assurance" / "runs"


def _variants(path: str) -> list[str]:
    """Spellings of one directory as tools print it: native, forward slashes,
    JSON-escaped backslashes, MSYS (/c/...) and the 8.3 short name on Windows."""
    out = set()
    candidates = {path, os.path.realpath(path)}
    if os.name == "nt":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(1024)
            for p in list(candidates):
                if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024):
                    candidates.add(buf.value)
                if ctypes.windll.kernel32.GetLongPathNameW(p, buf, 1024):
                    candidates.add(buf.value)
        except (AttributeError, OSError):
            pass
    for p in candidates:
        p = p.rstrip("\\/")
        if not p:
            continue
        fwd = p.replace("\\", "/")
        out |= {p, fwd, p.replace("\\", "\\\\")}
        if re.match(r"^[A-Za-z]:/", fwd):
            out.add(f"/{fwd[0].lower()}{fwd[2:]}")
    return sorted(out, key=len, reverse=True)


def sanitizer(project: Path) -> list[tuple[re.Pattern, str]]:
    # Order matters: the most specific directory first (the project and the
    # temp dir usually live under the home directory).
    pairs = [(str(project), "<PROJECT>"), (tempfile.gettempdir(), "<TMP>"), (str(Path.home()), "<HOME>")]
    rules = []
    for path, label in pairs:
        for variant in _variants(path):
            rules.append((re.compile(re.escape(variant), re.IGNORECASE), label))
    return rules


def sanitize(text: str, rules) -> str:
    for pattern, label in rules:
        text = pattern.sub(label, text)
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="run directory name, e.g. 2026-11-05-cp0-baseline")
    parser.add_argument("--tool", action="append", default=[], help="name=version")
    parser.add_argument("--entry", action="append", default=[],
                        help="published-name|exit-code|command|source-path")
    parser.add_argument("--note", action="append", default=[])
    args = parser.parse_args(argv)

    out_dir = RUNS / args.run
    out_dir.mkdir(parents=True, exist_ok=True)
    rules = sanitizer(ROOT)
    manifest_path = out_dir / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "kind": "voznativa.assurance_run", "schema_version": 1, "run": args.run, "entries": []}
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    manifest.update({
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "revision": head, "dirty_paths": sorted(line[3:] for line in dirty.splitlines()),
        "environment": {"python": platform.python_version(), "platform": platform.platform(terse=True)},
    })
    tools = dict(manifest.get("tools", {}))
    tools.update(dict(t.split("=", 1) for t in args.tool))
    manifest["tools"] = tools
    manifest["notes"] = list(dict.fromkeys(manifest.get("notes", []) + args.note))
    entries = {e["file"]: e for e in manifest["entries"]}
    for spec in args.entry:
        name, code, command, source = spec.split("|", 3)
        raw = Path(source).read_bytes()
        clean = sanitize(raw.decode("utf-8"), rules)
        (out_dir / name).write_text(clean, encoding="utf-8", newline="\n")
        entries[name] = {"file": name, "command": sanitize(command, rules), "exit_code": int(code),
                         "raw_sha256": hashlib.sha256(raw).hexdigest(),
                         "published_sha256": hashlib.sha256(clean.encode("utf-8")).hexdigest(),
                         "sanitized": clean != raw.decode("utf-8")}
    manifest["entries"] = sorted(entries.values(), key=lambda e: e["file"])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(manifest_path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
