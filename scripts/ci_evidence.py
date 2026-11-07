#!/usr/bin/env python3
"""CI evidence bound to the code that ran, without a self-reference cycle.

The v0.6 gate trusted ``evals/qualification/external.json``: a hand-editable
record said "run N succeeded on SHA X". Two defects:

1. the record is the only proof (anyone can type ``"conclusion": "success"``);
2. committing the record after a green run creates a new HEAD that no run
   ever saw, so the gate can never be PASS on the commit that holds the proof.

Contract (v0.7.0):

* **The record is an index, not proof.** PASS needs a *live, read-only*
  GitHub Actions query (``gh api``) that returns the run, its head SHA, its
  workflow file, ``status=completed``, ``conclusion=success`` and every job of
  the declared matrix with ``conclusion=success``. If the query cannot be
  made, the result is INCONCLUSIVE, never PASS.
* **Code equivalence is checked by git, not asserted.** A run on SHA ``R``
  qualifies HEAD ``H`` when ``R == H``, or when ``R`` is an ancestor of ``H``
  and every path changed between them is an evidence path
  (``EVIDENCE_PATHS``). Anything else (a code change, a divergent branch) is
  NOT_RUN for HEAD.
* **The expected matrix comes from the workflow file** at ``R``, so a run
  with fewer jobs than declared is INCONCLUSIVE.

Pure functions take ``git`` and ``fetch`` callables, so every scenario
(tampering, wrong SHA, incomplete matrix, cancelled/neutral, query down,
divergent branch) is tested offline in ``evals/test_ci_evidence.py``.
"""
from __future__ import annotations

import itertools
import json
import re
import subprocess
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ".github/workflows/ci.yml"
# Paths a commit may change after a CI run without changing what the run tested.
EVIDENCE_PATHS = ("evals/qualification/external.json", "evals/assurance/runs/", "docs/V07_EXECUTION_STATE.md",
                  "docs/V07_RELEASE_QUALIFICATION.md")
# Under a directory prefix only non-executable records count as evidence
# (v0.7.0.dev1, H07-NEW-02): a harness such as replay_survivors.py, a
# conftest.py or a pyproject.toml placed in a run folder is code, so changing it
# after the run must invalidate the run, not ride on it.
EVIDENCE_SUFFIXES = (".json", ".jsonl", ".md", ".txt")
# Events a qualifying run may come from (maintainer policy: manual dispatch only).
ALLOWED_EVENTS = ("workflow_dispatch",)
NOT_PASS_CONCLUSIONS = {"cancelled": "INCONCLUSIVE", "neutral": "INCONCLUSIVE", "skipped": "INCONCLUSIVE",
                        "stale": "INCONCLUSIVE", "action_required": "INCONCLUSIVE", "failure": "FAIL",
                        "timed_out": "FAIL", "startup_failure": "FAIL"}

Git = Callable[[list[str]], tuple[int, str]]
Fetch = Callable[[str], dict]


class Unavailable(RuntimeError):
    """The live query could not be made (no gh, no auth, no network, API error)."""


def real_git(argv: list[str]) -> tuple[int, str]:
    done = subprocess.run(["git", *argv], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", stdin=subprocess.DEVNULL)
    return done.returncode, (done.stdout or "").strip()


def repo_slug(git: Git = real_git) -> str | None:
    code, url = git(["remote", "get-url", "origin"])
    m = re.search(r"github\.com[:/]([^/]+/[^/.\s]+?)(?:\.git)?$", url) if code == 0 else None
    return m.group(1) if m else None


def gh_fetch(slug: str) -> Fetch:
    """Read-only GitHub API through the gh CLI (uses the user's existing login)."""
    def fetch(path: str) -> dict:
        try:
            done = subprocess.run(["gh", "api", f"repos/{slug}/{path}"], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=60, stdin=subprocess.DEVNULL)
        except (FileNotFoundError, subprocess.TimeoutExpired) as error:
            raise Unavailable(f"gh not usable: {error}") from error
        if done.returncode != 0:
            raise Unavailable(f"gh api {path} exited {done.returncode}: {(done.stderr or '').strip()[:200]}")
        try:
            return json.loads(done.stdout)
        except json.JSONDecodeError as error:
            raise Unavailable(f"gh api {path} returned non-JSON") from error
    return fetch


def is_evidence_path(path: str) -> bool:
    if path in EVIDENCE_PATHS:
        return True
    name = path.rsplit("/", 1)[-1]
    return (any(p.endswith("/") and path.startswith(p) for p in EVIDENCE_PATHS)
            and name.lower().endswith(EVIDENCE_SUFFIXES) and ".." not in path.split("/"))


def code_equivalence(run_sha: str, head: str, git: Git = real_git) -> dict:
    """Whether a run on ``run_sha`` tested the code at ``head``."""
    if not run_sha or not head:
        return {"equivalent": False, "reason": "missing revision"}
    if run_sha == head:
        return {"equivalent": True, "relation": "same"}
    code, _ = git(["merge-base", "--is-ancestor", run_sha, head])
    if code != 0:
        return {"equivalent": False, "relation": "not_ancestor",
                "reason": f"{run_sha[:12]} is not an ancestor of {head[:12]} (divergent branch or unknown commit)"}
    # --no-renames: a move lists both the old and the new path, so moving code
    # into an evidence folder still shows the code path that disappeared.
    code, names = git(["diff", "--name-only", run_sha, head, "--no-renames"])
    if code != 0:
        return {"equivalent": False, "relation": "diff_failed", "reason": "git diff failed"}
    changed = [p for p in names.splitlines() if p.strip()]
    code_paths = [p for p in changed if not is_evidence_path(p)]
    if code_paths:
        return {"equivalent": False, "relation": "code_changed", "changed_code_paths": code_paths[:20],
                "reason": f"{len(code_paths)} non-evidence path(s) changed after the run"}
    return {"equivalent": True, "relation": "evidence_only", "changed_evidence_paths": changed}


def expected_job_names(workflow_text: str) -> list[str]:
    """Names GitHub gives the jobs the workflow declares: ``<job id>`` or
    ``<job id> (<value>, <value>)`` with the matrix values in axis order (the
    format of run #124). A job with its own ``name:`` or an ``include``/
    ``exclude`` matrix is refused: this check would have to guess its names."""
    doc = yaml.safe_load(workflow_text) or {}
    names = []
    for job_id, job in (doc.get("jobs") or {}).items():
        job = job or {}
        if "name" in job:
            raise ValueError(f"job {job_id}: a custom job name is not supported by this check")
        matrix = (job.get("strategy") or {}).get("matrix") or {}
        if any(k in matrix for k in ("include", "exclude")):
            raise ValueError(f"job {job_id}: include/exclude matrices are not supported by this check")
        axes = [v for v in matrix.values() if isinstance(v, list)]
        if not axes:
            names.append(str(job_id))
            continue
        names.extend(f"{job_id} ({', '.join(str(v) for v in combo)})" for combo in itertools.product(*axes))
    return names


def expected_jobs(workflow_text: str) -> int:
    """How many jobs the workflow declares (the product of each job's matrix axes)."""
    return len(expected_job_names(workflow_text))


def workflow_events(workflow_text: str) -> list[str]:
    """Trigger names of the workflow. PyYAML reads the bare key ``on`` as True."""
    doc = yaml.safe_load(workflow_text) or {}
    on = doc.get("on", doc.get(True))
    if isinstance(on, str):
        return [on]
    if isinstance(on, list):
        return [str(x) for x in on]
    return sorted(str(k) for k in (on or {}))


def judge_run(run: dict, jobs: list[dict], expected: int, run_sha: str, workflow: str = WORKFLOW,
              expected_names: list[str] | None = None, declared_events: list[str] | None = None) -> dict:
    """Classify one live run. Pure.

    ``expected_names``: job names the workflow at ``run_sha`` declares; when
    given, the run must have exactly these jobs (no missing, extra or
    duplicated name hiding a missing combination). ``declared_events``: the
    workflow's triggers at ``run_sha``; the run's event must be one of them
    and allowed by policy (``ALLOWED_EVENTS``)."""
    base = {"run_id": run.get("id"), "run_number": run.get("run_number"), "url": run.get("html_url"),
            "event": run.get("event"), "head_sha": run.get("head_sha"), "conclusion": run.get("conclusion"),
            "jobs": f"{sum(j.get('conclusion') == 'success' for j in jobs)}/{expected}"}
    if run.get("head_sha") != run_sha:
        return dict(base, status="FAIL", reason=f"the live run is on {str(run.get('head_sha'))[:12]}, not on the "
                                                f"recorded {run_sha[:12]}: the record misattributes it")
    if run.get("path") and run.get("path") != workflow:
        return dict(base, status="INCONCLUSIVE", reason=f"run of {run.get('path')}, not {workflow}")
    event = run.get("event")
    if event not in ALLOWED_EVENTS or (declared_events is not None and event not in declared_events):
        return dict(base, status="INCONCLUSIVE",
                    reason=f"run event {event!r}; a qualifying run must be one of {list(ALLOWED_EVENTS)} "
                           f"declared by the workflow ({declared_events})")
    if run.get("status") != "completed":
        return dict(base, status="INCONCLUSIVE", reason=f"run status is {run.get('status')}")
    conclusion = run.get("conclusion")
    if conclusion != "success":
        return dict(base, status=NOT_PASS_CONCLUSIONS.get(conclusion, "INCONCLUSIVE"),
                    reason=f"run conclusion is {conclusion}")
    bad = [j.get("name") for j in jobs if j.get("conclusion") != "success"]
    if bad:
        return dict(base, status="FAIL", reason=f"jobs not successful: {bad}")
    if len(jobs) < expected:
        return dict(base, status="INCONCLUSIVE", reason=f"{len(jobs)} job(s) ran; the workflow declares {expected}")
    if expected_names is not None:
        ran = sorted(str(j.get("name")) for j in jobs)
        if ran != sorted(expected_names):
            missing = sorted(set(expected_names) - set(ran))
            extra = sorted({n for n in ran if ran.count(n) > expected_names.count(n)})
            return dict(base, status="INCONCLUSIVE",
                        reason=f"job matrix differs from the workflow: missing {missing}, unexpected or "
                               f"duplicated {extra}")
    return dict(base, status="PASS")


def verify(head: str, candidate_shas: list[str], git: Git, fetch: Fetch | None) -> dict:
    """PASS only for a live-verified successful run on a code-equivalent SHA.

    ``candidate_shas``: HEAD plus SHAs named by the local record (an index).
    Runs are looked up live by SHA; the record's own claims are never used."""
    if fetch is None:
        return {"status": "INCONCLUSIVE", "reason": "live GitHub query unavailable; a local record alone is not proof"}
    tried, failures = [], []
    for sha in dict.fromkeys([head, *candidate_shas]):
        eq = code_equivalence(sha, head, git)
        if not eq["equivalent"]:
            tried.append({"sha": sha[:12], **eq})
            continue
        try:
            listing = fetch(f"actions/runs?head_sha={sha}&per_page=50")
        except Unavailable as error:
            return {"status": "INCONCLUSIVE", "reason": f"live query failed: {error}", "equivalence": eq}
        code, wf_text = git(["show", f"{sha}:{WORKFLOW}"])
        if code != 0:
            return {"status": "INCONCLUSIVE", "reason": f"{WORKFLOW} not readable at {sha[:12]}"}
        try:
            names = expected_job_names(wf_text)
        except ValueError as error:
            return {"status": "INCONCLUSIVE", "reason": f"job matrix of {WORKFLOW} at {sha[:12]}: {error}"}
        events = workflow_events(wf_text)
        runs = [r for r in listing.get("workflow_runs") or [] if r.get("path", WORKFLOW) == WORKFLOW]
        for run in sorted(runs, key=lambda r: r.get("run_number") or 0, reverse=True):
            try:
                jobs = fetch(f"actions/runs/{run['id']}/jobs?per_page=100").get("jobs") or []
            except Unavailable as error:
                return {"status": "INCONCLUSIVE", "reason": f"live jobs query failed: {error}"}
            verdict = judge_run(run, jobs, len(names), sha, expected_names=names, declared_events=events)
            if verdict["status"] == "PASS":
                return dict(verdict, equivalence=eq, verified="live")
            failures.append(verdict)
        tried.append({"sha": sha[:12], **eq, "live_runs": len(runs)})
    if failures:
        worst = next((f for f in failures if f["status"] == "FAIL"), failures[0])
        return dict(worst, status="FAIL" if worst["status"] == "FAIL" else "INCONCLUSIVE", tried=tried,
                    other_runs=len(failures) - 1)
    return {"status": "NOT_RUN", "reason": "no live CI run on this revision or a code-equivalent one", "tried": tried}


def verify_record_claims(record_runs: list[dict], fetch: Fetch) -> list[dict]:
    """Tamper check of the index: every recorded run must exist live with the
    recorded head SHA and conclusion."""
    out = []
    for r in record_runs:
        if "id" not in r:
            out.append({"run": r.get("run"), "status": "INCONCLUSIVE", "reason": "record has no run id"})
            continue
        try:
            live = fetch(f"actions/runs/{r['id']}")
        except Unavailable as error:
            out.append({"run": r.get("run"), "status": "INCONCLUSIVE", "reason": str(error)})
            continue
        mismatches = [k for k in ("head_sha", "conclusion") if r.get(k) is not None and live.get(k) != r.get(k)]
        out.append({"run": r.get("run"), "status": "FAIL" if mismatches else "PASS",
                    **({"mismatch": {k: {"recorded": r.get(k), "live": live.get(k)} for k in mismatches}}
                       if mismatches else {})})
    return out


if __name__ == "__main__":
    import sys
    head = real_git(["rev-parse", "HEAD"])[1]
    slug = repo_slug()
    entry = json.loads((ROOT / "evals" / "qualification" / "external.json").read_text(encoding="utf-8"))["ci"]
    fetch = gh_fetch(slug) if slug else None
    result = verify(head, [r.get("head_sha", "") for r in entry.get("runs", [])], real_git, fetch)
    if fetch is not None and "--check-record" in sys.argv:
        result["record_check"] = verify_record_claims(entry.get("runs", []), fetch)
    print(json.dumps(result, ensure_ascii=False, indent=2))
