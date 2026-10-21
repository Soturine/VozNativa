#!/usr/bin/env python3
"""Smoke-test an installed voznativa outside any checkout.

Run from a directory that is NOT the repository, with the package installed
from a wheel (not editable). Every reference-dependent command must work
from the bundled copy, and stdlib-only commands must work too.

    python smoke_installed.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TEXT = "Prezados, informamos que o deploy não deve ser feito antes das 18h, porque o banco estará em manutenção."


def run(*args: str) -> dict | str:
    done = subprocess.run([sys.executable, "-m", "voznativa", *args], capture_output=True)
    out = done.stdout.decode("utf-8")
    if done.returncode not in (0, 1, 2, 3):
        raise SystemExit(f"voznativa {' '.join(args)} exited {done.returncode}: {done.stderr.decode('utf-8')}")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def main() -> int:
    os.environ.pop("VOZNATIVA_HOME", None)
    import voznativa
    from voznativa.paths import home
    package = Path(voznativa.__file__).resolve().parent
    if (package.parent / "references").exists():
        raise SystemExit(f"not an isolated install: {package.parent} has references/")
    print("package:", package, "| home:", home())
    start = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        Path("t.txt").write_text(TEXT, encoding="utf-8")
        Path("c.txt").write_text(TEXT.replace("não deve", "deve"), encoding="utf-8")
        Path("s1.txt").write_text("vc viu o deploy? nn subiu ainda kkk " * 20, encoding="utf-8")
        checks = {
            "compare": run("compare", "t.txt", "c.txt")["status"] == "fail",
            "ledger": run("ledger", "t.txt")["kind"] == "voznativa.semantic_ledger",
            "route": run("route", "t.txt")["kind"] == "voznativa.context_contract",
            "refs": bool(run("refs", "t.txt")["selected"]),
            "contract": run("contract", "t.txt", "--compact")["regional_strength"] == 0.0,
            "profile": run("profile", "s1.txt")["kind"] == "voznativa.voice_profile",
            "rewrite-prompt": "LEDGER" in run("rewrite-prompt", "t.txt", "--inline-refs"),
            "judge-prompt": "BINDING" in run("judge-prompt", "t.txt", "c.txt"),
            # v0.4.0: rewrite crashed on every call in v0.3.0 and nothing ran the command.
            "rewrite": run("rewrite", "t.txt", "--candidate", "c.txt", "--force")["outcome"] == "returned_original",
            "plan": run("plan", "t.txt")["kind"] == "voznativa.rewrite_plan",
            "patterns": run("patterns", "t.txt")["kind"] == "voznativa.pattern_report",
        }
        os.chdir(start)  # Windows cannot delete the current directory
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps(checks, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
