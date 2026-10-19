"""Project/Repository Context: use a repository as a source of facts.

``scan()`` indexes what a repository can vouch for: file paths, identifiers
defined in code, commands shown in its docs, and declared package versions.
``ground()`` checks that every protected value in a candidate text (paths,
commands, identifiers, versions, numbers...) is supported by the original,
by user-supplied fact files or by the repository.

Repository text is evidence of facts, never of voice: docs in a repository
usually have several authors.
"""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import spans as spans_mod
from .compare import _report as _base_report

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".tox", ".mypy_cache",
             ".pytest_cache", "target", ".next", ".idea", ".vscode"}
TEXT_SUFFIXES = {".md", ".rst", ".txt", ".py", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
                 ".rb", ".php", ".sh", ".ps1", ".yml", ".yaml", ".toml", ".json", ".cfg", ".ini", ".sql"}
DOC_NAMES = re.compile(r"^(?:readme|changelog|contributing|architecture|design|guide|docs?)", re.I)
MAX_FILES = 2000
VALUE_TYPES = {"number", "money", "percent", "quantity", "date", "time", "weekday", "relative_time", "ordinal"}
MAX_BYTES = 300_000

_DEFINITIONS = [
    re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", re.M),
    re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.M),
    re.compile(r"\b(?:function|class|interface|type|enum)\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*="),
    re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)", re.M),
    re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)", re.M),
    re.compile(r"^([A-Z][A-Z0-9_]{2,})\s*=", re.M),
]
_SHELL_FENCE = re.compile(r"```(?:bash|sh|shell|console|powershell|ps1|cmd|zsh)[ \t]*\n(.*?)```", re.S)
_ANY_FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
_CLI_NAMES = [
    re.compile(r"add_parser\(\s*[\"']([\w-]+)"),
    re.compile(r"add_argument\(\s*[\"'](-{1,2}[\w-]+)"),
    re.compile(r"add_argument\(\s*[\"'][\w-]+[\"']\s*,\s*[\"'](--[\w-]+)"),
    re.compile(r"@\w+\.command\(\s*(?:name\s*=\s*)?[\"']([\w-]+)"),
    re.compile(r"\.option\(\s*[\"'](-{1,2}[\w-]+)"),
]
# Tools the repository cannot vouch for; only project-specific tokens are checked.
EXTERNAL_TOOLS = {"pip", "pip3", "python", "python3", "py", "npm", "npx", "pnpm", "yarn", "node", "git", "gh",
                  "uv", "uvx", "poetry", "make", "docker", "cargo", "go", "curl", "cd", "ls", "cat", "echo"}
_PLACEHOLDER = re.compile(r"^(?:<.*>|\{.*\}|[A-Z][A-Z0-9_]+|.*[./\\].*)$")


@dataclass
class ProjectContext:
    root: Path
    files: set[str] = field(default_factory=set)
    identifiers: set[str] = field(default_factory=set)
    commands: set[str] = field(default_factory=set)
    versions: dict[str, str] = field(default_factory=dict)
    doc_sources: list[str] = field(default_factory=list)
    doc_text: str = ""
    doc_words: set[str] = field(default_factory=set)
    cli_names: set[str] = field(default_factory=set)
    scripts: set[str] = field(default_factory=set)
    truncated: bool = False

    def summary(self) -> dict:
        return {
            "root": str(self.root),
            "files": len(self.files),
            "identifiers": len(self.identifiers),
            "commands": sorted(self.commands)[:50],
            "versions": self.versions,
            "doc_sources": self.doc_sources,
            "truncated": self.truncated,
            "use": "facts only; never voice",
        }


def scan(root: str | Path) -> ProjectContext:
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"repository path is not a directory: {root}")
    ctx = ProjectContext(root=root)
    docs = []
    count = 0
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if SKIP_DIRS.intersection(rel.parts) or not path.is_file():
            continue
        count += 1
        if count > MAX_FILES:
            ctx.truncated = True
            break
        ctx.files.add(rel.as_posix())
        if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > MAX_BYTES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in _DEFINITIONS:
            ctx.identifiers.update(pattern.findall(text))
        for pattern in _CLI_NAMES:
            ctx.cli_names.update(pattern.findall(text))
        if path.suffix.lower() in {".md", ".rst", ".txt"}:
            for block in _SHELL_FENCE.findall(text):
                for line in block.splitlines():
                    line = re.sub(r"^\s*[$>]\s*", "", line).strip()
                    if line and not line.startswith("#"):
                        ctx.commands.add(line)
            for block in _ANY_FENCE.findall(text):  # unlabeled fences: only prompt lines
                for line in block.splitlines():
                    if re.match(r"^\s*\$\s+\S", line):
                        ctx.commands.add(re.sub(r"^\s*\$\s*", "", line).strip())
            if DOC_NAMES.match(path.name) or "docs" in rel.parts or len(rel.parts) == 1:
                ctx.doc_sources.append(str(path))
                docs.append(text)
        _versions(path, text, ctx)
    ctx.doc_text = "\n\n".join(docs)
    ctx.doc_words = set(re.findall(r"[A-Za-z_][\w.-]*", ctx.doc_text))
    return ctx


def _versions(path: Path, text: str, ctx: ProjectContext) -> None:
    try:
        if path.name == "pyproject.toml":
            project = tomllib.loads(text).get("project", {})
            if project.get("name"):
                ctx.versions[project["name"]] = str(project.get("version", "dynamic"))
                ctx.scripts.update(project.get("scripts", {}).keys())
        elif path.name == "package.json":
            data = json.loads(text)
            if data.get("name"):
                ctx.versions[data["name"]] = str(data.get("version", ""))
                bins = data.get("bin") or {}
                ctx.scripts.update(bins.keys() if isinstance(bins, dict) else [data["name"]])
        elif path.name == "__init__.py":
            m = re.search(r"__version__\s*=\s*['\"]([^'\"]+)", text)
            if m:
                ctx.versions[path.parent.name] = m.group(1)
    except (tomllib.TOMLDecodeError, json.JSONDecodeError):
        return


def _supported(span: spans_mod.Span, known_keys: set[str], fact_text: str, project: ProjectContext | None) -> str | None:
    if span.key in known_keys:
        return "source"
    raw = span.text.strip("`").strip()
    if raw and raw in fact_text:
        return "fact_text"
    if project is None or span.type in VALUE_TYPES:
        # Values (numbers, money, dates...) need an explicit source: a "3000"
        # somewhere in a repository proves nothing about this sentence.
        return None
    if span.type == "path":
        candidate = raw.lstrip("./").replace("\\", "/")
        if candidate in project.files or any(f.endswith("/" + candidate) for f in project.files):
            return "repository_file"
    if span.type in {"inline_code", "command", "code_block"}:
        verdict = _command_support(raw, project)
        if verdict:
            return verdict
        if verdict is False:
            return None
    if span.type == "identifier" and (raw.rstrip("()") in project.identifiers or raw in project.cli_names):
        return "repository_code"
    if raw in project.doc_text:
        return "repository_docs"
    if span.type == "version" and raw.lstrip("v") in project.versions.values():
        return "repository_version"
    return None


def _command_support(raw: str, project: ProjectContext) -> str | bool | None:
    """Return a support label, False when the text is a project command that
    uses unknown subcommands/flags, or None when it is not a command at all."""
    if raw in project.commands:
        return "repository_docs_command"
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith("```")]
    if not lines:
        return None
    for line in lines:
        tokens = line.split()
        program = tokens[0].lstrip("$").strip() or (tokens[1] if len(tokens) > 1 else "")
        if program == "python" and tokens[1:3] and tokens[1] == "-m":
            program, tokens = tokens[2], tokens[2:]
        if program in project.scripts:
            unknown = [t for t in tokens[1:] if not _PLACEHOLDER.match(t)
                       and t.split("=")[0] not in project.cli_names]
            if unknown:
                return False
        elif program in EXTERNAL_TOOLS:
            project_tokens = [t for t in tokens[1:] if t in project.scripts or t in project.versions]
            if not project_tokens and not any(t in project.doc_words for t in tokens[1:]):
                return None
        else:
            if line in project.commands or line.rstrip("()") in project.identifiers:
                continue
            return None
    return "repository_cli"


def ground(candidate: str, original: str | None = None, facts: list[str] | None = None,
           project: ProjectContext | None = None) -> dict:
    """Every hard protected value in ``candidate`` must come from somewhere."""
    sources = [t for t in [original or "", *(facts or [])] if t]
    known = {s.key for text in sources for s in spans_mod.extract(text)}
    fact_text = "\n".join(sources)
    issues = []
    supported = []
    for span in spans_mod.extract(candidate):
        origin = _supported(span, known, fact_text, project)
        if origin:
            supported.append({"text": span.text, "type": span.type, "support": origin})
            continue
        if span.type == "entity":
            issues.append({"code": "unsupported_entity", "severity": "major",
                           "message": f"entity '{span.text}' not found in any fact source",
                           "text": span.text, "type": span.type})
        elif span.type in spans_mod.HARD_TYPES:
            issues.append({"code": "unsupported_span", "severity": "critical",
                           "message": f"{span.type} '{span.text}' is not supported by the original, "
                                      "fact files or repository", "text": span.text, "type": span.type})
    if any(i["severity"] == "critical" for i in issues):
        status = "fail"
    elif issues:
        status = "review_required"
    else:
        status = "no_deterministic_issues"
    report = _base_report(status, issues, original or "", candidate)
    report["kind"] = "voznativa.grounding"
    report["supported"] = supported
    report["sources"] = {"original": original is not None, "fact_files": len(facts or []),
                         "repository": str(project.root) if project else None}
    report["limitations"] = [
        "Grounding checks protected values and entities only; unprotected claims need a judge.",
        "A value found in the repository is supported as existing, not as correctly described.",
    ]
    return report
