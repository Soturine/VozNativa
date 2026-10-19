"""Locate the VozNativa home (the checkout that holds ``references/``).

The skill always runs from a checkout. A non-editable ``pip install`` ships
only the package, so reference-dependent commands need ``VOZNATIVA_HOME``
pointing at a checkout.
"""
from __future__ import annotations

import os
from pathlib import Path


class HomeNotFound(ValueError):
    pass


def home() -> Path:
    env = os.environ.get("VOZNATIVA_HOME")
    candidates = [Path(env)] if env else []
    candidates.append(Path(__file__).resolve().parent.parent)
    for root in candidates:
        if (root / "references" / "index.yml").is_file():
            return root
    raise HomeNotFound("references/ not found: run from a VozNativa checkout or set VOZNATIVA_HOME "
                       "to its directory (a non-editable pip install ships only the Python package)")


def references_dir() -> Path:
    return home() / "references"
