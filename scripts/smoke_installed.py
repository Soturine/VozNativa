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


def _exit_code(*args: str) -> int:
    return subprocess.run([sys.executable, "-m", "voznativa", *args], capture_output=True).returncode


def _registry_ok() -> bool:
    from voznativa.corpus.registry import load_registry
    return len(load_registry()) >= 25


def _long_form_ok() -> bool:
    from voznativa.document import build_plan, reassemble
    doc = "# T\n\nUm parágrafo.\n\n```\ncodigo\n```\n\n| a | b |\n|---|---|\n"
    plan = build_plan(doc)
    return reassemble(doc, plan) == doc and {"code", "table"} <= {k for u in plan["units"]
                                                                  if u["action"] == "protect" for k in u["kinds"]}


def _morph_ok() -> bool:
    from voznativa.morph import tense_profile
    return tense_profile("Ana terminará o trabalho.") == {"terminar": {"fut_pres"}}


def _license_ok() -> bool:
    from importlib import metadata
    dist = metadata.distribution("voznativa")
    files = [str(f) for f in (dist.files or [])]
    return dist.metadata.get("License-Expression") == "MIT" and any(f.endswith("LICENSE") for f in files)


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
        # finally: a failing check must not leave the temp dir as the current
        # directory; on Windows its cleanup then raised PermissionError and hid
        # the real error (seen in CP5).
        try:
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
                # v0.5.0: the evidence packs are package data; abstention needs no pack.
                "regional-packs": bool(run("regional", "packs")["packs"]),
                "regional-abstains": run("regional", "check", "t.txt")["status"] == "abstain",
                # v0.6.0: the installed distribution declares the MIT licence and ships its file.
                "license-metadata": _license_ok(),
                # v0.6.0: the corpus registry ships as package data and validates.
                "corpus-registry": _registry_ok(),
                # v0.6.0: corpus CLI, slang lexicon and community packs from the wheel, outside the checkout.
                "corpus-list": len(run("corpus", "list")["sources"]) >= 30,
                "corpus-validate": run("corpus", "validate")["valid"] is True,
                "corpus-unknown-source-exit-64": _exit_code("corpus", "info", "nope") == 64,
                "corpus-catalogued-refused-exit-77": _exit_code("corpus", "sample", "obras") == 77,
                "epoch-and-community": run("contract", "t.txt", "--epoch", "current", "--community", "tech",
                                           "--slang-strength", "0.5")["slang_strength"]["effective"] == 0.0,
                # v0.7.0: contract v3, the new commands and the long-form path from the wheel.
                "version-0.7": voznativa.__version__.startswith("0.7."),
                "route-v3": run("route", "t.txt")["schema_version"] == 3,
                "diagnose": run("diagnose", "t.txt")["kind"] == "voznativa.diagnosis",
                "mode-review": run("rewrite", "t.txt", "--mode", "REVIEW")["outcome"] == "no_change",
                "integrity-clean-exit-0": _exit_code("integrity", "t.txt") == 0,
                # v0.8.0 CP3: first use from the wheel, without a model or a key.
                "doctor": run("doctor", "--json")["status"] in {"OK", "WARN"},
                "demo": [c["status"] for c in run("demo", "--json")["comparisons"]]
                        == ["no_deterministic_issues", "fail", "review_required"],
                "missing-file-exit-64": _exit_code("compare", "nao-existe.txt", "t.txt") == 64,
                "long-form-plan": _long_form_ok(),
                "provenance": run("rewrite", "t.txt", "--candidate", "c.txt", "--force")["provenance"]["kind"]
                == "voznativa.provenance",
                "corpus-registry-v07": len(run("corpus", "list")["sources"]) >= 38,
                "morph": _morph_ok(),
            }
        finally:
            os.chdir(start)  # Windows cannot delete the current directory
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps(checks, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
