#!/usr/bin/env python3
"""Generate docs/guide/CLI.md from the CLI parser itself (v0.8 CP12).

The reference cannot drift from the software: evals/test_v08_guides.py
regenerates it and compares. Run after changing a subcommand:

    python scripts/cli_reference.py --write
"""
from __future__ import annotations

import argparse
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "guide" / "CLI.md"

INTRO = """# Referência da CLI

Gerada de `voznativa --help` e do `--help` de cada subcomando por `scripts/cli_reference.py`; um teste confere que este arquivo está igual ao que o parser produz. Guia de uso: [`QUICKSTART.md`](QUICKSTART.md).

Códigos de saída do `compare` (e do `rewrite` com `--judgment`): 0 `identical` ou aceito, 1 `fail`, 2 revisão (`review_required`, `human_review_claimed`), 3 `no_deterministic_issues` (precisa de juiz). Erro de uso ou de entrada: 64. Recusa da política de dados: 77.

"""


def help_of(parser) -> str:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        parser.print_help()
    return _version_neutral(buffer.getvalue().replace("\r\n", "\n"))


def _version_neutral(text: str) -> str:
    """argparse wraps the usage block and the trailing "..." of a subcommand list differently from
    Python 3.13 on (same content, other line breaks; found by the CP16 Linux 3.13 run). Join both so
    the reference is the same on every supported Python; the help paragraphs wrap alike everywhere."""
    out: list[str] = []
    in_usage = False
    for line in text.split("\n"):
        if line.startswith("usage:"):
            in_usage = True
            out.append(line.rstrip())
            continue
        if in_usage and line.strip():
            out[-1] += " " + line.strip()
            continue
        in_usage = False
        if line.strip() == "..." and out:
            out[-1] = out[-1].rstrip() + " ..."
            continue
        out.append(line)
    return "\n".join(out)


def render() -> str:
    import os
    os.environ["COLUMNS"] = "100"     # argparse wraps to the terminal width: fix it so every machine agrees
    from voznativa.cli import build_parser
    parser = build_parser()
    sub = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
    parts = [INTRO, "## `voznativa`\n\n```text\n", help_of(parser).rstrip() + "\n```\n"]
    for name, child in sorted(sub.choices.items()):
        parts.append(f"\n## `voznativa {name}`\n\n```text\n{help_of(child).rstrip()}\n```\n")
        nested = [a for a in child._actions if a.__class__.__name__ == "_SubParsersAction"]
        for action in nested:
            for nested_name, grandchild in sorted(action.choices.items()):
                parts.append(f"\n### `voznativa {name} {nested_name}`\n\n```text\n{help_of(grandchild).rstrip()}\n```\n")
    return "".join(parts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    text = render()
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(ROOT).as_posix()}")
        return 0
    current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    if current.replace("\r\n", "\n") != text:
        print("docs/guide/CLI.md is out of date: run python scripts/cli_reference.py --write")
        return 1
    print("docs/guide/CLI.md is up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
