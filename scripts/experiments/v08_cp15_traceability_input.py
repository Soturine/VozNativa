"""v0.8 CP15: the v0.8 traceability table as a Derivanta Engine traceability input.

Reads docs/releases/v0.8/TRACEABILITY.md (column "Teste") and writes a
`derivanta-engine/traceability-input` 0.1 file. Each backticked token of the
column becomes links:

* `evals/x.py::Class` or a bare `Class` (resolved by searching evals/): one
  link per test method of the class, `evals/x.py::Class::test_y`, so the
  Engine checks each name in the syntax tree;
* `evals/x.py` alone, or any other file (`scripts/...`, `SKILL.md`): a file
  link, which the Engine only checks for presence.

A token that resolves to nothing is kept verbatim, so the Engine reports it
instead of the converter hiding it. Nothing is executed; a link is a
declaration, not a test run.

    python -B scripts/experiments/v08_cp15_traceability_input.py --out <file.json>
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "docs" / "releases" / "v0.8" / "TRACEABILITY.md"
TOKEN = re.compile(r"`([^`]+)`")
IDENT = re.compile(r"^[A-Z][A-Za-z0-9_]*$")


def _classes() -> dict[str, list[tuple[str, list[str]]]]:
    """Test classes under evals/: name -> [(path, [test methods])]."""
    found: dict[str, list[tuple[str, list[str]]]] = {}
    for path in sorted((ROOT / "evals").glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test")]
                found.setdefault(node.name, []).append((path.relative_to(ROOT).as_posix(), methods))
    return found


def _links(cell: str, classes) -> list[str]:
    links: list[str] = []
    current_file = None
    tokens = TOKEN.findall(cell)
    # "evals/x.py (`A`, `B`)" names classes of the file before them
    for token in tokens:
        token = token.strip()
        if "::" in token:
            path, _, cls = token.partition("::")
            cls = cls.split("::")[0]
            match = [m for p, m in classes.get(cls, []) if p == path]
            links += [f"{path}::{cls}::{m}" for m in match[0]] if match and match[0] else [token]
            current_file = path
        elif re.fullmatch(r"test_\w+", token) and (ROOT / "evals" / f"{token}.py").is_file():
            current_file = f"evals/{token}.py"     # a bare test module name
            links.append(current_file)
        elif token.endswith("/") and (ROOT / token).is_dir():
            # the Engine checks files, and refuses a trailing "/": a folder stands for its Markdown records
            links += sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / token).glob("*.md")) or [token]
        elif token.endswith(".py") or "/" in token or token.endswith(".md"):
            current_file = token if token.endswith(".py") else None
            links.append(token)
        elif IDENT.match(token):
            options = classes.get(token, [])
            if current_file:
                options = [o for o in options if o[0] == current_file] or options
            if len(options) == 1 and options[0][1]:
                path, methods = options[0]
                links += [f"{path}::{token}::{m}" for m in methods]
            else:
                links.append(token)       # unresolved or ambiguous: the Engine reports it
    # a file followed by its classes: the class links already cover it
    covered = {link.split("::")[0] for link in links if "::" in link}
    return [link for link in dict.fromkeys(links) if not (link in covered)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    classes = _classes()
    requirements = []
    for line in TABLE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| V08-"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rid, statement, test = cells[0], cells[1], cells[3]
        requirements.append({"id": rid, "statement": statement,
                             "source": f"docs/releases/v0.8/TRACEABILITY.md ({rid})",
                             "verified_by": _links(test, classes)})
    out = {"schema_version": "0.1", "kind": "derivanta-engine/traceability-input", "requirements": requirements}
    args.out.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(requirements)} requirements, {sum(len(r['verified_by']) for r in requirements)} links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
