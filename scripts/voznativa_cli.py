#!/usr/bin/env python3
"""Run the voznativa CLI from a skill checkout without installing the package.

    python <skill-dir>/scripts/voznativa_cli.py compare original.txt candidata.txt

compare, ledger, judge-prompt, analyze and ground need only the standard
library; route, refs, contract, profile and rewrite also need PyYAML.
"""
import sys

import _bootstrap  # noqa: F401

if sys.version_info < (3, 11):
    raise SystemExit("voznativa requires Python 3.11 or newer")

from voznativa.cli import main  # noqa: E402

raise SystemExit(main())
