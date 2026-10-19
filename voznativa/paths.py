"""Locate the VozNativa home: the directory that holds ``references/``.

Search order:
1. ``VOZNATIVA_HOME`` (explicit override);
2. the checkout that contains this package (skill and editable installs);
3. the copy bundled into an installed wheel (``voznativa/_bundled``).
"""
from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent


class HomeNotFound(ValueError):
    pass


def candidates() -> list[Path]:
    env = os.environ.get("VOZNATIVA_HOME")
    found = [Path(env)] if env else []
    return found + [PACKAGE_DIR.parent, PACKAGE_DIR / "_bundled"]


def home() -> Path:
    for root in candidates():
        if (root / "references" / "index.yml").is_file():
            return root
    raise HomeNotFound("references/ not found: set VOZNATIVA_HOME to a VozNativa checkout, or reinstall the "
                       "package from a build that bundles references (pip install .)")


def references_dir() -> Path:
    return home() / "references"
