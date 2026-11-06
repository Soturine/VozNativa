#!/usr/bin/env python3
"""Single local qualification runner for VozNativa.

Runs every local gate in its own process, keeps each exit code, and
classifies each gate as one of:

  PASS             ran and met its criterion
  FAIL             ran and did not meet its criterion (a test failed, a suite regressed)
  BLOCKED          could not run: infrastructure missing (a tool, the network, the platform's
                   capability, an external service such as GitHub Actions)
  NOT_RUN          deliberately not run here (wrong OS, needs people, outside --scope)
  SKIPPED          ran, but its tests were skipped (never counted as passed)
  INCONCLUSIVE     ran, but the result cannot decide the criterion (no test collected, timeout)
  WAIVED_BY_OWNER  the maintainer waived it in evals/qualification/external.json

No shell pipelines: every command is an argv list; output is decoded as
UTF-8 and the report is written as UTF-8 JSON, so PowerShell 5.1 code pages
cannot corrupt it.

    python scripts/qualify.py                       # local gates
    python scripts/qualify.py --scope release       # also the external gates (CI, people)
    python scripts/qualify.py --only unittest,semantic:dev --out report.json

Exit code: 0 every required gate PASS or WAIVED_BY_OWNER; 1 a required gate
FAIL; 3 no failure, but a required gate BLOCKED, NOT_RUN, SKIPPED or
INCONCLUSIVE (qualification incomplete); 2 usage error.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
EXPECTATIONS = ROOT / "evals" / "qualification" / "expectations.json"
EXTERNAL = ROOT / "evals" / "qualification" / "external.json"

STATES = ("PASS", "FAIL", "BLOCKED", "NOT_RUN", "SKIPPED", "INCONCLUSIVE", "WAIVED_BY_OWNER")
EXIT_PASS, EXIT_FAIL, EXIT_USAGE, EXIT_INCOMPLETE = 0, 1, 2, 3
TIMEOUT_S = 1800


def child_env() -> dict:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    env.pop("VOZNATIVA_HOME", None)
    return env


def run(argv: list[str], cwd: Path = ROOT, timeout: float = TIMEOUT_S, env: dict | None = None) -> dict:
    """Run one command; never raises for the command's own failure."""
    started = time.monotonic()
    try:
        done = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout, env=env or child_env(),
                              stdin=subprocess.DEVNULL)
    except FileNotFoundError as error:
        return {"argv": argv, "exit_code": None, "error": f"not found: {error}", "seconds": 0.0,
                "stdout": "", "stderr": ""}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "exit_code": None, "timeout": True, "seconds": round(time.monotonic() - started, 2),
                "stdout": (error.stdout or b"").decode("utf-8", "replace"),
                "stderr": (error.stderr or b"").decode("utf-8", "replace")}
    return {"argv": argv, "exit_code": done.returncode, "seconds": round(time.monotonic() - started, 2),
            "stdout": done.stdout.decode("utf-8", "replace"), "stderr": done.stderr.decode("utf-8", "replace")}


def _tail(text: str, lines: int = 12) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


@dataclass
class Gate:
    id: str
    run: Callable[[argparse.Namespace], dict]
    required: bool = True
    scope: str = "local"          # local gates run by default; release gates only with --scope release
    description: str = ""


@dataclass
class Result:
    id: str
    status: str
    required: bool
    scope: str
    detail: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"id": self.id, "status": self.status, "required": self.required, "scope": self.scope, **self.detail}


# --- unittest: run in a child process with a result class that keeps every outcome ---------

class _Collect(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed: list[str] = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed.append(test.id())


def unittest_child(out: Path, start: str, pattern: str) -> int:
    """Executed as ``qualify.py --unittest-child OUT``: discovery and run in this
    process, every outcome written to OUT as UTF-8 JSON."""
    sys.path.insert(0, str(ROOT))
    loader = unittest.TestLoader()
    # Same discovery as CI (`-m unittest discover -s evals`): evals/ is its own top level.
    suite = loader.discover(start, pattern=pattern)
    with open(os.devnull, "w", encoding="utf-8") as sink:
        result = unittest.TextTestRunner(stream=sink, resultclass=_Collect, verbosity=0).run(suite)

    def ident(test) -> str:
        return test.id()

    collection = [ident(t) for t, _ in result.errors if t.id().startswith("unittest.loader._FailedTest")]
    data = {
        "ran": result.testsRun,
        "passed": result.passed,
        "failed": [{"id": ident(t), "trace": _tail(tb, 8)} for t, tb in result.failures],
        "errors": [{"id": ident(t), "trace": _tail(tb, 8)} for t, tb in result.errors
                   if not t.id().startswith("unittest.loader._FailedTest")],
        "collection_errors": collection,
        "skipped": [{"id": ident(t), "reason": reason} for t, reason in result.skipped],
        "expected_failures": [ident(t) for t, _ in result.expectedFailures],
        "unexpected_successes": [ident(t) for t in result.unexpectedSuccesses],
    }
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


def classify_unittest(data: dict) -> str:
    """Pure classification, tested in evals/test_qualify.py."""
    if data["failed"] or data["errors"] or data["collection_errors"] or data["unexpected_successes"]:
        return "FAIL"
    if data["ran"] == 0:
        return "INCONCLUSIVE"
    executed = data["ran"] - len(data["skipped"])
    if executed == 0:
        return "SKIPPED"
    return "PASS"


def gate_unittest(args) -> dict:
    with tempfile.TemporaryDirectory(prefix="vn-qualify-") as tmp:
        out = Path(tmp) / "unittest.json"
        proc = run([sys.executable, str(Path(__file__).resolve()), "--unittest-child", str(out)])
        if proc.get("timeout"):
            return {"status": "INCONCLUSIVE", "reason": "timeout", "command": proc["argv"]}
        if not out.exists():
            return {"status": "FAIL", "reason": "the test process crashed before reporting",
                    "exit_code": proc["exit_code"], "stderr": _tail(proc["stderr"])}
        data = json.loads(out.read_text(encoding="utf-8"))
    status = classify_unittest(data)
    return {"status": status, "exit_code": proc["exit_code"], "seconds": proc["seconds"],
            "counts": {"ran": data["ran"], "passed": len(data["passed"]), "failed": len(data["failed"]),
                       "errors": len(data["errors"]), "collection_errors": len(data["collection_errors"]),
                       "skipped": len(data["skipped"]), "expected_failures": len(data["expected_failures"]),
                       "unexpected_successes": len(data["unexpected_successes"])},
            "failed": data["failed"], "errors": data["errors"], "collection_errors": data["collection_errors"],
            "skipped": data["skipped"], "unexpected_successes": data["unexpected_successes"]}


# --- in-process data gates (no model, deterministic) ----------------------------------------

def _expectations() -> dict:
    return json.loads(EXPECTATIONS.read_text(encoding="utf-8"))


def classify_known(failing: set[str], known: set[str]) -> dict:
    """A suite with recorded known failures: a new failure is a regression
    (FAIL); a known failure that now passes is reported, never hidden."""
    new = sorted(failing - known)
    return {"status": "FAIL" if new else "PASS", "new_failures": new,
            "known_failures_still_failing": sorted(failing & known),
            "known_failures_now_passing": sorted(known - failing)}


def _sub_python(code: str) -> dict:
    """Evaluate in a child interpreter so a crash or import error is a gate
    result, and the gate imports this checkout's package."""
    proc = run([sys.executable, "-c", f"import sys; sys.path.insert(0, {str(ROOT)!r}); {code}"])
    if proc["exit_code"] != 0:
        return {"error": True, "exit_code": proc["exit_code"], "stderr": _tail(proc["stderr"])}
    return json.loads(proc["stdout"])


def gate_semantic_dev(args) -> dict:
    code = ("import json; from pathlib import Path; from voznativa.evals import run; "
            "r = run(Path('evals/semantic/cases.jsonl')); "
            "print(json.dumps({'cases': r['cases'], 'passed': r['passed'], 'failures': [f['id'] for f in r['failures']]}))")
    data = _sub_python(code)
    if data.get("error"):
        return {"status": "FAIL", **data}
    if data["cases"] == 0:
        return {"status": "INCONCLUSIVE", "reason": "no case loaded", **data}
    return {"status": "PASS" if data["passed"] == data["cases"] else "FAIL", **data}


def _holdout_reports() -> dict:
    code = ("import json; from pathlib import Path; from voznativa.evals import run\n"
            "out = {}\n"
            "for p in sorted(Path('evals/semantic').glob('*.jsonl')):\n"
            "    r = run(p)\n"
            "    out[p.name] = {'role': r['provenance'].get('role'), 'frozen': bool(r['provenance'].get('frozen')),"
            " 'sha256_matches': r['provenance'].get('sha256_matches'), 'cases': r['cases'], 'passed': r['passed'],"
            " 'failures': {f['id']: f['failure_kind'] for f in r['failures']}}\n"
            "print(json.dumps(out))")
    return _sub_python(code)


def gate_holdout_safety(args) -> dict:
    """No missed detection on any held-out suite and every holdout intact.
    Classification divergences (blocked under another issue code) are not
    safety failures; they are reported by the strict gate."""
    data = _holdout_reports()
    if data.get("error"):
        return {"status": "FAIL", **data}
    holdouts = {k: v for k, v in data.items() if v["role"] != "dev"}
    problems = []
    for name, r in holdouts.items():
        if not r["frozen"] or r["sha256_matches"] is not True:
            problems.append(f"{name}: not frozen or sha256 mismatch")
        unsafe = {i: k for i, k in r["failures"].items() if k != "classification_divergence"}
        if unsafe:
            problems.append(f"{name}: {unsafe}")
    if not holdouts or not sum(r["cases"] for r in holdouts.values()):
        return {"status": "INCONCLUSIVE", "reason": "no holdout case loaded"}
    return {"status": "FAIL" if problems else "PASS", "problems": problems,
            "suites": {k: f"{v['passed']}/{v['cases']}" for k, v in holdouts.items()}}


def gate_holdout_strict(args) -> dict:
    data = _holdout_reports()
    if data.get("error"):
        return {"status": "FAIL", **data}
    known = {f"{suite}:{case}" for suite, cases in _expectations()["semantic_strict_known"].items() for case in cases}
    failing = {f"{name}:{case}" for name, r in data.items() if r["role"] != "dev" for case in r["failures"]}
    return {**classify_known(failing, known),
            "note": "strict = status and issue codes as written; known items are frozen cases whose recorded "
                    "first run already diverged (see evals/qualification/expectations.json)"}


def gate_decisions(args) -> dict:
    code = ("import json; from pathlib import Path; from voznativa.evals import run_decisions; "
            "r = run_decisions(Path('evals/decision/cases.jsonl')); "
            "print(json.dumps({'cases': r['cases'], 'passed': r['passed'], "
            "'failures': {f['id']: f['failure_kind'] for f in r['failures']}}))")
    data = _sub_python(code)
    if data.get("error"):
        return {"status": "FAIL", **data}
    result = classify_known(set(data["failures"]), set(_expectations()["decision_known"]))
    return {**result, "passed": f"{data['passed']}/{data['cases']}", "failures": data["failures"]}


def gate_router(args) -> dict:
    code = ("import json; from voznativa.router import infer_genre\n"
            "cases = [json.loads(l) for l in open('evals/router/cases.jsonl', encoding='utf-8') if l.strip()]\n"
            "print(json.dumps({'cases': len(cases), 'failures': [c['id'] for c in cases "
            "if infer_genre(c['text'])['value'] not in c['expect']]}))")
    data = _sub_python(code)
    if data.get("error"):
        return {"status": "FAIL", **data}
    result = classify_known(set(data["failures"]), set(_expectations()["router_known"]))
    return {**result, "passed": f"{data['cases'] - len(data['failures'])}/{data['cases']}"}


def gate_validator(args) -> dict:
    proc = run([sys.executable, "scripts/validate_package.py"])
    return {"status": "PASS" if proc["exit_code"] == 0 else "FAIL", "exit_code": proc["exit_code"],
            "output": _tail(proc["stdout"] + proc["stderr"], 20)}


# --- CLI contract: exit codes are an interface (gate scripts read them) ---------------------

CLI_CASES = [
    # (label, argv after `-m voznativa`, files, expected exit code)
    ("compare identical -> 0", ["compare", "{a}", "{a}"], {"a": "vc viu o deploy? nn subiu ainda kkk"}, 0),
    ("compare negation removed -> 1 fail", ["compare", "{a}", "{b}"],
     {"a": "O deploy não deve ser feito antes das 18h.", "b": "O deploy deve ser feito antes das 18h."}, 1),
    ("compare added claim -> 2 review", ["compare", "{a}", "{b}"],
     {"a": "Lançamos o recurso de exportação para CSV.",
      "b": "Lançamos o recurso de exportação para CSV. Os clientes adoraram e o engajamento disparou desde então."}, 2),
    ("compare clean rewrite -> 3 needs judgment", ["compare", "{a}", "{b}"],
     {"a": "Não recomendamos usar a versão 2.3.0 em produção.",
      "b": "Não recomendamos a versão 2.3.0 para produção."}, 3),
    ("unknown flag -> 64 usage, never a gate status", ["compare", "--no-such-flag", "{a}", "{a}"], {"a": "x"}, 64),
    ("missing file -> 64", ["compare", "{missing}", "{missing}"], {}, 64),
    ("plan runs without a model -> 0", ["plan", "{a}"], {"a": "É importante destacar que o deploy será na sexta."}, 0),
    ("--help -> 0", ["--help"], {}, 0),
]


def gate_cli(args) -> dict:
    rows, ok = [], True
    with tempfile.TemporaryDirectory(prefix="vn-cli-") as tmp:
        paths = {"missing": str(Path(tmp) / "does-not-exist.txt")}
        for label, argv, files, expected in CLI_CASES:
            for key, text in files.items():
                path = Path(tmp) / f"{key}.txt"
                path.write_text(text, encoding="utf-8")
                paths[key] = str(path)
            proc = run([sys.executable, "-m", "voznativa", *[a.format(**paths) for a in argv]], cwd=Path(tmp),
                       env=dict(child_env(), PYTHONPATH=str(ROOT)))
            passed = proc["exit_code"] == expected
            ok &= passed
            rows.append({"case": label, "expected": expected, "exit_code": proc["exit_code"], "passed": passed})
    return {"status": "PASS" if ok else "FAIL", "cases": rows}


# --- package: sdist -> wheel -> clean venv -> smoke outside the checkout (the CI `package` job) ---

NETWORK_HINTS = ("connection", "network", "temporary failure", "name resolution", "could not fetch",
                 "no matching distribution", "proxy", "ssl")


def gate_package(args) -> dict:
    missing = [m for m in ("build", "pip") if importlib.util.find_spec(m) is None]
    if missing:
        # v0.7.0: a venv made without pip (e.g. `uv venv`) failed the wheel step and was
        # reported as a FAIL of the project; it is a missing tool, like 'build'.
        return {"status": "BLOCKED", "reason": f"missing in this interpreter: {missing} "
                                               "(install them in the venv that runs qualify; `uv venv --seed` adds pip)"}
    steps = []
    with tempfile.TemporaryDirectory(prefix="vn-pkg-") as tmp:
        tmp = Path(tmp)
        src = tmp / "src"
        tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True).stdout.decode().split("\0")
        for rel in filter(None, tracked):
            if (ROOT / rel).is_file():
                (src / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, src / rel)
        for name, argv, cwd in (
            ("sdist", [sys.executable, "-m", "build", "--sdist", "--outdir", str(tmp / "dist"), str(src)], tmp),
        ):
            proc = run(argv, cwd=cwd)
            steps.append({"step": name, "exit_code": proc["exit_code"], "seconds": proc["seconds"]})
            if proc["exit_code"] != 0:
                return _package_failure(steps, proc)
        sdist = next((tmp / "dist").glob("*.tar.gz"))
        import tarfile
        with tarfile.open(sdist) as archive:
            archive.extractall(tmp / "sdist", filter="data")
        unpacked = next((tmp / "sdist").iterdir())
        proc = run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(tmp / "dist"), str(unpacked)])
        steps.append({"step": "wheel from sdist", "exit_code": proc["exit_code"], "seconds": proc["seconds"]})
        if proc["exit_code"] != 0:
            return _package_failure(steps, proc)
        proc = run([sys.executable, "-m", "venv", str(tmp / "venv")])
        steps.append({"step": "venv", "exit_code": proc["exit_code"]})
        if proc["exit_code"] != 0:
            return {"status": "BLOCKED", "reason": "venv creation failed", "steps": steps, "stderr": _tail(proc["stderr"])}
        vpy = tmp / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        wheel = next((tmp / "dist").glob("*.whl"))
        proc = run([str(vpy), "-m", "pip", "install", "--disable-pip-version-check", str(wheel)])
        steps.append({"step": "install wheel (+ declared deps)", "exit_code": proc["exit_code"], "seconds": proc["seconds"]})
        if proc["exit_code"] != 0:
            return _package_failure(steps, proc)
        smoke = tmp / "smoke.py"
        shutil.copy2(ROOT / "scripts" / "smoke_installed.py", smoke)
        proc = run([str(vpy), "-I", str(smoke)], cwd=tmp)
        steps.append({"step": "smoke outside the checkout", "exit_code": proc["exit_code"], "seconds": proc["seconds"]})
        status = "PASS" if proc["exit_code"] == 0 else "FAIL"
        return {"status": status, "wheel": wheel.name, "steps": steps,
                **({} if status == "PASS" else {"output": _tail(proc["stdout"] + proc["stderr"], 20)})}


def _package_failure(steps: list, proc: dict) -> dict:
    text = (proc["stdout"] + proc["stderr"]).lower()
    blocked = any(h in text for h in NETWORK_HINTS)
    return {"status": "BLOCKED" if blocked else "FAIL",
            "reason": "package index or network unavailable" if blocked else "packaging step failed",
            "steps": steps, "output": _tail(proc["stdout"] + proc["stderr"], 20)}


def gate_pty(args) -> dict:
    if os.name == "nt":
        return {"status": "NOT_RUN", "reason": "needs a POSIX pseudo-terminal; runs on Linux/macOS"}
    proc = run([sys.executable, "scripts/pty_review_check.py"], env=dict(child_env(), PYTHONPATH=str(ROOT)))
    return {"status": "PASS" if proc["exit_code"] == 0 else "FAIL", "exit_code": proc["exit_code"],
            "output": _tail(proc["stdout"] + proc["stderr"])}


def classify_ci(entry: dict, revision: str) -> dict:
    """Offline view of the local record. Since v0.7.0 a record is an index,
    never proof: a recorded green run of this exact revision is INCONCLUSIVE
    until a live query confirms it (scripts/ci_evidence.py); any other
    revision is NOT_RUN (a nearby green run proves nothing about it)."""
    for run in entry.get("runs", []):
        if run.get("conclusion") == "success" and revision and run.get("head_sha", "").startswith(revision[:12]) \
                and revision.startswith(run.get("head_sha", "")[:12]):
            return {"status": "INCONCLUSIVE", "run": run,
                    "reason": "recorded only; PASS needs the live GitHub Actions query (scripts/ci_evidence.py)"}
    last = next((r for r in reversed(entry.get("runs", [])) if r.get("conclusion") == "success"), None)
    return {"status": entry.get("status", "NOT_RUN") if entry.get("status") != "PASS" else "NOT_RUN",
            "reason": "no recorded CI run for this revision" + (f"; last green run #{last['run']} was on "
                                                                 f"{last['head_sha'][:12]}" if last else ""),
            "policy": entry.get("policy")}


def _ci_evidence():
    spec = importlib.util.spec_from_file_location("ci_evidence", ROOT / "scripts" / "ci_evidence.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gate_ci(args) -> dict:
    entry = json.loads(EXTERNAL.read_text(encoding="utf-8"))["ci"]
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty:
        return {"status": "NOT_RUN", "reason": "working tree has changes: no CI run can prove it"}
    ci = _ci_evidence()
    slug = ci.repo_slug()
    fetch = ci.gh_fetch(slug) if slug and not getattr(args, "offline", False) else None
    result = ci.verify(revision, [r.get("head_sha", "") for r in entry.get("runs", [])], ci.real_git, fetch)
    if result["status"] == "INCONCLUSIVE" and fetch is None:
        result["offline_record"] = classify_ci(entry, revision)
    return dict(result, source="live GitHub Actions query (gh api); record is an index only")


def workflow_triggers(text: str) -> list[str]:
    """Trigger names of one workflow. PyYAML reads the bare key ``on`` as True."""
    import yaml
    doc = yaml.safe_load(text) or {}
    on = doc.get("on", doc.get(True))
    if isinstance(on, str):
        return [on]
    if isinstance(on, list):
        return [str(x) for x in on]
    return sorted(str(k) for k in (on or {}))


def gate_workflow_triggers(args) -> dict:
    """Maintainer cost policy: every workflow runs only by workflow_dispatch."""
    files = sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
    if not files:
        return {"status": "INCONCLUSIVE", "reason": "no workflow file found"}
    found = {f.name: workflow_triggers(f.read_text(encoding="utf-8")) for f in files}
    bad = {name: t for name, t in found.items() if t != ["workflow_dispatch"]}
    return {"status": "FAIL" if bad else "PASS", "workflows": found,
            **({"reason": f"automatic triggers present: {bad}"} if bad else {})}


def gate_external(key: str) -> Callable:
    def gate(args) -> dict:
        data = json.loads(EXTERNAL.read_text(encoding="utf-8"))[key]
        if data["status"] not in STATES:
            return {"status": "INCONCLUSIVE", "reason": f"unknown status {data['status']!r} in {EXTERNAL.name}"}
        return dict(data, source=EXTERNAL.relative_to(ROOT).as_posix())
    return gate


GATES = [
    Gate("validator", gate_validator, description="package layout, data, docs commands"),
    Gate("unittest", gate_unittest, description="python -m unittest discovery of evals/test_*.py"),
    Gate("semantic:dev", gate_semantic_dev, description="dev semantic suite passes completely"),
    Gate("semantic:holdouts:safety", gate_holdout_safety, description="no missed detection; holdouts frozen and intact"),
    Gate("semantic:holdouts:strict", gate_holdout_strict, description="exact status and codes; known divergences listed"),
    Gate("decision:regression", gate_decisions, description="engine decision suite; no new failure"),
    Gate("router:regression", gate_router, description="genre router suite; no new failure"),
    Gate("cli:exit-codes", gate_cli, description="CLI exit codes are the documented gate interface"),
    Gate("package:sdist-wheel-smoke", gate_package, description="sdist -> wheel -> clean venv -> smoke (CI package job)"),
    Gate("review:pty", gate_pty, description="interactive signed review through a real pseudo-terminal"),
    Gate("ci:workflow-triggers", gate_workflow_triggers,
         description="every workflow is workflow_dispatch only (no automatic Actions minutes)"),
    Gate("ci:github-actions", gate_ci, scope="release", description="declared CI matrix ran green on this exact revision"),
    Gate("holdout:independent", gate_external("independent_holdout"), scope="release",
         description="semantic holdout written by someone other than the developer"),
    Gate("review:blind-human", gate_external("blind_human_review"), scope="release",
         description="blind pairwise review by real reviewers"),
]


def overall(results: list[Result]) -> tuple[str, int]:
    required = [r for r in results if r.required]
    if any(r.status == "FAIL" for r in required):
        return "FAIL", EXIT_FAIL
    if all(r.status in {"PASS", "WAIVED_BY_OWNER"} for r in required):
        return "PASS", EXIT_PASS
    return "INCOMPLETE", EXIT_INCOMPLETE


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scope", choices=("local", "release"), default="local")
    parser.add_argument("--only", help="comma-separated gate ids")
    parser.add_argument("--out", help="write the JSON report here (UTF-8)")
    parser.add_argument("--offline", action="store_true",
                        help="never query GitHub; ci:github-actions is then INCONCLUSIVE at best")
    parser.add_argument("--unittest-child", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.unittest_child:
        return unittest_child(Path(args.unittest_child), str(ROOT / "evals"), "test_*.py")

    wanted = set(args.only.split(",")) if args.only else None
    unknown = (wanted or set()) - {g.id for g in GATES}
    if unknown:
        parser.error(f"unknown gate(s): {sorted(unknown)}")
    results = []
    for gate in GATES:
        if wanted is not None and gate.id not in wanted:
            continue
        if gate.scope == "release" and args.scope != "release" and wanted is None:
            results.append(Result(gate.id, "NOT_RUN", False, gate.scope, {"reason": "release-scope gate; use --scope release"}))
            continue
        started = time.monotonic()
        try:
            detail = gate.run(args)
        except Exception as error:  # a crash of the gate itself is a failure of the qualification, not hidden
            detail = {"status": "FAIL", "reason": f"gate crashed: {type(error).__name__}: {error}"}
        detail.setdefault("seconds", round(time.monotonic() - started, 2))
        status = detail.pop("status")
        required = gate.required and (gate.scope == "local" or args.scope == "release")
        results.append(Result(gate.id, status, required, gate.scope, {"description": gate.description, **detail}))
        print(f"{status:16s} {gate.id}", flush=True)

    verdict, code = overall(results)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    sys.path.insert(0, str(ROOT))
    from voznativa import __version__
    report = {"kind": "voznativa.qualification", "schema_version": 1,
              "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "version": __version__, "revision": head, "dirty": bool(dirty), "scope": args.scope,
              "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                              "platform": platform.platform(terse=True), "executable_is_venv": sys.prefix != sys.base_prefix},
              "verdict": verdict, "exit_code": code,
              "counts": {s: sum(r.status == s for r in results) for s in STATES},
              "gates": [r.as_dict() for r in results]}
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"verdict: {verdict} (exit {code}); revision {head[:12]}{' dirty' if dirty else ''}")
    return code


if __name__ == "__main__":
    sys.exit(main())
