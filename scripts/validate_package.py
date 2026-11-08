#!/usr/bin/env python3
"""Validate the VozNativa package: structure, metadata consistency and data files.

Checks content, not just file presence: SKILL.md frontmatter against the Agent
Skills spec, version consistency, links from SKILL.md, and that every YAML,
JSON and JSONL file parses with the fields its consumers need.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voznativa import __version__  # noqa: E402

REQUIRED = [
    "README.md", "SKILL.md", "ROADMAP.md", "CHANGELOG.md", "pyproject.toml", "agents/openai.yaml",
    "docs/TRACEABILITY.md", "docs/DESIGN_SPEC.md", "docs/COMPETITIVE_BENCHMARK.md",
    "references/VOICE_STACK.md", "voznativa/__init__.py", "voznativa/cli.py", "voznativa/compare.py",
    "voznativa/ledger.py", "voznativa/data/markers_pt_br.json", "evals/semantic/cases.jsonl",
    "benchmarks/cases/smoke.jsonl", ".github/workflows/ci.yml",
]
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_WORD_CAP = 5000
JSONL_FIELDS = {
    "evals/semantic": ("id", "category", "original", "candidate", "expect"),
    "benchmarks/cases": ("id", "text"),
    "evals/patterns": ("id", "genre", "text", "expect"),
    "evals/decision": ("id", "text", "expect"),
    "benchmarks/runs": ("tag", "cost_usd"),  # per-call cost logs of benchmark runs: records, not cases
}
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "build", "dist"}


def files(pattern: str):
    for path in sorted(ROOT.rglob(pattern)):
        if not SKIP_DIRS.intersection(path.relative_to(ROOT).parts) and ".egg-info" not in str(path):
            yield path


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter delimited by ---")
    return yaml.safe_load(match.group(1)) or {}, match.group(2)


def check_skill(errors: list[str]) -> None:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    try:
        meta, body = frontmatter(text)
    except (ValueError, yaml.YAMLError) as error:
        errors.append(f"SKILL.md: {error}")
        return
    name = meta.get("name", "")
    if name != "voznativa" or not SKILL_NAME_RE.match(name) or len(name) > 64:
        errors.append("SKILL.md: name must be 'voznativa' (lowercase, digits, hyphens, <=64 chars)")
    description = meta.get("description", "")
    if not description or len(description) > 1024:
        errors.append("SKILL.md: description must be non-empty and <=1024 chars")
    version = str((meta.get("metadata") or {}).get("version", ""))
    if version != __version__:
        errors.append(f"SKILL.md metadata.version {version!r} != package version {__version__!r}")
    words = len(body.split())
    if words > SKILL_WORD_CAP:
        errors.append(f"SKILL.md body has {words} words; cap is {SKILL_WORD_CAP} (it is read on every use)")
    for link in sorted(set(re.findall(r"`((?:references|docs|scripts|evals|assets|benchmarks|voznativa)/[^`*\s]+)`", body))):
        if not (ROOT / link.rstrip("/")).exists():
            errors.append(f"SKILL.md links to missing path: {link}")


def check_data(errors: list[str]) -> None:
    for path in list(files("*.yml")) + list(files("*.yaml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            errors.append(f"{rel(path)}: invalid YAML: {error}")
    for path in files("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{rel(path)}: invalid JSON: {error}")
    for path in files("*.jsonl"):
        required = next((fields for prefix, fields in JSONL_FIELDS.items() if rel(path).startswith(prefix)), ("id",))
        ids = set()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"{rel(path)}:{number}: invalid JSON: {error}")
                continue
            missing = [f for f in required if f not in row]
            if missing:
                errors.append(f"{rel(path)}:{number}: missing fields {missing}")
            if "id" in required and row.get("id") in ids:
                errors.append(f"{rel(path)}:{number}: duplicate id {row.get('id')}")
            ids.add(row.get("id"))
            expect = row.get("expect")
            if rel(path).startswith("evals/semantic") and not (isinstance(expect, dict) and expect.get("status")):
                errors.append(f"{rel(path)}:{number}: expect.status must list accepted statuses")
            if rel(path).startswith("evals/router") and not (isinstance(expect, list) and expect):
                errors.append(f"{rel(path)}:{number}: expect must list accepted genres")
    index = ROOT / "references" / "index.yml"
    if index.exists():
        for entry in (yaml.safe_load(index.read_text(encoding="utf-8")) or {}).get("entries", []):
            missing = [k for k in ("path", "purpose", "when", "priority") if k not in entry]
            if missing:
                errors.append(f"references/index.yml: entry {entry.get('path')} missing {missing}")
            elif not (ROOT / entry["path"]).exists():
                errors.append(f"references/index.yml points to missing file: {entry['path']}")
    for path in files("voznativa/data/*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "schema_version" not in data or "level" not in data.get("evidence", {}):
            errors.append(f"{rel(path)}: data files need schema_version and evidence.level")


def check_docs(errors: list[str]) -> None:
    trace = (ROOT / "docs" / "TRACEABILITY.md").read_text(encoding="utf-8")
    for must_have in ("Semantic/factual lock", "Voice Drift Guard", "Regional Overfit Guard", "Rewrite engine",
                      "Competitive benchmark protocol"):
        if must_have not in trace:
            errors.append(f"docs/TRACEABILITY.md missing: {must_have}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for forbidden in ("probabilidade de ia:", "ai probability:"):
        if forbidden in readme:
            errors.append("README must not advertise AI-authorship probability")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    first = re.search(r"^## (.+)$", changelog, re.M)
    if not first or not (__version__ in first.group(1) or "Unreleased" in first.group(1)):
        errors.append(f"CHANGELOG.md first entry must be 'Unreleased' or {__version__}")
    skill_meta, _ = frontmatter((ROOT / "SKILL.md").read_text(encoding="utf-8"))
    first_sentence = re.match(r"(.+?\.)(?:\s|$)", skill_meta.get("description", ""))
    for manifest in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        path = ROOT / manifest
        if not path.exists():
            errors.append(f"missing {manifest}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = [data] if manifest.endswith("plugin.json") else data.get("plugins", [])
        for entry in entries:
            if entry.get("name") != "voznativa":
                errors.append(f"{manifest}: name must be voznativa")
            if first_sentence and entry.get("description") != first_sentence.group(1):
                errors.append(f"{manifest}: description must equal the first sentence of SKILL.md description")
        if manifest.endswith("plugin.json"):
            if data.get("version") != __version__:
                errors.append(f"{manifest}: version {data.get('version')!r} != {__version__!r}")
            if data.get("skills") != ["./"]:
                errors.append(f"{manifest}: skills must point at the repository root (['./'])")
    agent = yaml.safe_load((ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")) or {}
    if not (agent.get("interface") or {}).get("display_name"):
        errors.append("agents/openai.yaml: interface.display_name is required")


CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]|\r(?!\n)")
TEXT_SUFFIXES = {".py", ".json", ".jsonl", ".yml", ".yaml", ".md", ".toml"}


def check_text_files(errors: list[str]) -> None:
    """Catch control characters (e.g. a backspace from an unescaped \\b, or a
    bare CR) hidden inside source or data lines."""
    for path in files("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            text = path.read_bytes().decode("utf-8", errors="replace")
            for number, line in enumerate(text.split("\n"), 1):
                if CONTROL_CHARS.search(line.rstrip("\r")):
                    errors.append(f"{rel(path)}:{number}: control character inside the line")
                # v0.7.0.dev1 (H07-016): a heredoc that expanded "\n" split a register row in two.
                if path.suffix == ".md" and line.startswith("|") and not line.rstrip().endswith("|"):
                    errors.append(f"{rel(path)}:{number}: Markdown table row does not end with '|' "
                                  "(a row split across lines?)")


# --- documentation checks (v0.8 CP12) ------------------------------------------------
_MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
_HEADING_LINE = re.compile(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$")
_PERSONAL_PATH = re.compile(r"[A-Za-z]:[\\/]Users[\\/](?!<)[^\\/\s`]+|/home/[a-z][\w.-]*/|/Users/[A-Z][\w.-]*/")
_SECRET = re.compile(r"sk-ant-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}"
                     r"|-----BEGIN [A-Z ]*PRIVATE KEY-----")
_COMMAND = re.compile(r"(?:\bvoznativa|\$VN)[ \t]+([a-z][a-z-]+)")
# Documents whose commands must exist today (history may name commands of its own time).
CURRENT_DOCS = ("README.md", "SKILL.md", "docs/README.md", "docs/guide/")


def slug(heading: str) -> str:
    """GitHub-style anchor of a heading."""
    text = re.sub(r"`", "", heading.strip().lower())
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def markdown_problems(root: Path, paths: list[Path], subcommands: set[str] | None) -> list[str]:
    """Broken relative links and anchors, personal absolute paths, secrets and
    (in current documents) subcommands that do not exist. Pure: the negative
    tests run it on copies with planted defects."""
    problems = []
    anchors: dict[Path, set[str]] = {}

    def anchors_of(path: Path) -> set[str]:
        if path not in anchors:
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            anchors[path] = {slug(h) for h in _HEADING_LINE.findall(re.sub(r"(?s)```.*?```", "", text))}
        return anchors[path]

    for path in paths:
        name = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        prose = re.sub(r"(?s)```.*?```", "", text)
        for target in _MD_LINK.findall(prose):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            target_path, _, fragment = target.partition("#")
            resolved = (path.parent / target_path.replace("%20", " ")).resolve() if target_path else path.resolve()
            if target_path and not resolved.exists():
                problems.append(f"{name}: broken link {target}")
            elif fragment and resolved.suffix == ".md" and fragment not in anchors_of(resolved):
                problems.append(f"{name}: anchor #{fragment} not found in {target_path or name}")
        for m in _PERSONAL_PATH.finditer(text):
            problems.append(f"{name}: personal absolute path {m.group(0)!r}")
        for m in _SECRET.finditer(text):
            problems.append(f"{name}: secret-looking token {m.group(0)[:12]}...")
        if subcommands is not None and any(name == c or name.startswith(c) for c in CURRENT_DOCS if c.endswith("/")
                                           or name == c):
            for command in sorted(set(_COMMAND.findall(prose)) - subcommands):
                problems.append(f"{name}: mentions `voznativa {command}`, which is not a subcommand")
    return problems


def documentation_files(root: Path) -> list[Path]:
    keep = ("README.md", "SKILL.md", "ROADMAP.md", "CHANGELOG.md")
    out = [root / p for p in keep if (root / p).is_file()]
    for folder in ("docs", "examples", "references", "benchmarks"):
        out += [p for p in sorted((root / folder).rglob("*.md")) if not SKIP_DIRS.intersection(p.parts)]
    return out


def check_documentation(errors: list[str]) -> None:
    from voznativa.cli import build_parser
    parser = build_parser()
    action = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
    errors += markdown_problems(ROOT, documentation_files(ROOT), set(action.choices))


def validate() -> list[str]:
    errors = [f"missing required file: {p}" for p in REQUIRED if not (ROOT / p).exists()]
    check_text_files(errors)
    check_documentation(errors)
    check_skill(errors)
    check_data(errors)
    check_docs(errors)
    try:
        from voznativa.corpus.registry import load_registry
        load_registry()
        from voznativa.temporal import load_lexicon
        load_lexicon()
    except ValueError as error:
        errors.append(str(error))
    from voznativa.review import registry_problems
    errors += [f"evals/reviewers/registry.json: {p}" for p in registry_problems(ROOT / "evals" / "reviewers")]
    return errors


def main() -> int:
    errors = validate()
    if errors:
        sys.stderr.write("\n".join(errors) + "\n")
        return 1
    print(f"VozNativa package v{__version__} is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
