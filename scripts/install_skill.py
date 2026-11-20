#!/usr/bin/env python3
"""Install the same standalone VozNativa Skill in a project's agent host."""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST_DIRS = {"codex": ".agents", "claude": ".claude", "gemini": ".gemini"}
SKILL_PARTS = (
    "SKILL.md", "LICENSE", "agents", "assets", "references", "voznativa",
    "scripts/_bootstrap.py", "scripts/voznativa_cli.py", "docs/engineering/TRACEABILITY.md",
)


def install_skill(source: Path, project: Path, host: str, skills_dir: Path | None = None) -> Path:
    parent = skills_dir if skills_dir is not None else project / HOST_DIRS[host] / "skills"
    dest = parent / "voznativa"
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f"a Skill já existe em {dest}; escolha outro projeto ou diretório")
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".voznativa-install-", dir=parent) as scratch:
        staged = Path(scratch) / "voznativa"
        for part in SKILL_PARTS:
            src, target = source / part, staged / part
            target.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, target, ignore=shutil.ignore_patterns("__pycache__", "_bundled", "*.pyc"))
            else:
                shutil.copy2(src, target)
        staged.rename(dest)
    return dest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--host", choices=HOST_DIRS, default="codex")
    parser.add_argument("--skills-dir", type=Path, help="directory used by another host that reads SKILL.md")
    args = parser.parse_args(argv)
    try:
        path = install_skill(ROOT, args.project.resolve(strict=True), args.host, args.skills_dir)
    except OSError as error:
        parser.exit(1, f"instalação VozNativa: {error}\n")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
