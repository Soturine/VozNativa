"""v0.7.0 CP1: CI evidence and the checkpoint harness cannot produce a false PASS.

Scenarios required by the plan: evidence tampering, run on the wrong SHA,
incomplete matrix, neutral/cancelled run, live query unavailable, divergent
branch, evidence-only commits after a green run (no self-reference cycle),
a failed first pipeline stage, and a push the remote did not receive.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ci = _load("ci_evidence")
checkpoint = _load("checkpoint")
qualify = _load("qualify")

WORKFLOW = """
name: CI
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12", "3.13"]
    steps: []
  package:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    steps: []
"""
RUN_SHA = "a" * 40
HEAD_EVIDENCE = "b" * 40      # descendant of RUN_SHA, only evidence changed
HEAD_CODE = "c" * 40          # descendant, code changed
DIVERGENT = "d" * 40          # not a descendant


def fake_git(argv):
    if argv[:2] == ["merge-base", "--is-ancestor"]:
        return (0 if argv[2] == RUN_SHA and argv[3] in (HEAD_EVIDENCE, HEAD_CODE) else 1), ""
    if argv[0] == "diff":
        if argv[3] == HEAD_EVIDENCE:
            return 0, "evals/qualification/external.json\nevals/assurance/runs/x/MANIFEST.json"
        return 0, "voznativa/engine.py\nevals/qualification/external.json"
    if argv[0] == "show":
        return 0, WORKFLOW
    return 1, ""


def jobs(n=8, conclusion="success"):
    return [{"name": f"job{i}", "conclusion": conclusion} for i in range(n)]


def fake_fetch(runs, job_list=None, down=False):
    def fetch(path):
        if down:
            raise ci.Unavailable("network down")
        if path.startswith("actions/runs?head_sha="):
            sha = path.split("=")[1].split("&")[0]
            return {"workflow_runs": [r for r in runs if r["head_sha"] == sha]}
        if path.endswith("/jobs?per_page=100"):
            return {"jobs": job_list if job_list is not None else jobs()}
        run_id = int(path.rsplit("/", 1)[1])
        return next(r for r in runs if r["id"] == run_id)
    return fetch


def run(sha=RUN_SHA, conclusion="success", status="completed", **over):
    return dict({"id": 7, "run_number": 130, "head_sha": sha, "path": ci.WORKFLOW, "event": "workflow_dispatch",
                 "status": status, "conclusion": conclusion, "html_url": "https://example.invalid/run/7"}, **over)


class LiveCiEvidence(unittest.TestCase):
    def test_expected_jobs_come_from_the_workflow_matrix(self):
        self.assertEqual(ci.expected_jobs(WORKFLOW), 8)
        real = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertEqual(ci.expected_jobs(real), 8)

    def test_live_success_on_head_is_pass(self):
        r = ci.verify(RUN_SHA, [], fake_git, fake_fetch([run()]))
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["verified"], "live")

    def test_evidence_only_commit_after_the_run_is_still_pass(self):
        # The cycle of v0.6: committing the record made a new HEAD no run saw.
        r = ci.verify(HEAD_EVIDENCE, [RUN_SHA], fake_git, fake_fetch([run()]))
        self.assertEqual((r["status"], r["equivalence"]["relation"]), ("PASS", "evidence_only"))

    def test_a_code_change_after_the_run_is_not_run(self):
        r = ci.verify(HEAD_CODE, [RUN_SHA], fake_git, fake_fetch([run()]))
        self.assertEqual(r["status"], "NOT_RUN")
        self.assertIn("voznativa/engine.py", json.dumps(r))

    def test_divergent_branch_is_not_run(self):
        r = ci.verify(DIVERGENT, [RUN_SHA], fake_git, fake_fetch([run()]))
        self.assertEqual(r["status"], "NOT_RUN")

    def test_query_unavailable_is_inconclusive_never_pass(self):
        self.assertEqual(ci.verify(RUN_SHA, [], fake_git, fake_fetch([run()], down=True))["status"], "INCONCLUSIVE")
        self.assertEqual(ci.verify(RUN_SHA, [], fake_git, None)["status"], "INCONCLUSIVE")

    def test_cancelled_and_neutral_runs_are_not_pass(self):
        for conclusion in ("cancelled", "neutral", "skipped"):
            r = ci.verify(RUN_SHA, [], fake_git, fake_fetch([run(conclusion=conclusion)]))
            self.assertEqual(r["status"], "INCONCLUSIVE", conclusion)

    def test_failed_run_is_fail(self):
        self.assertEqual(ci.verify(RUN_SHA, [], fake_git, fake_fetch([run(conclusion="failure")]))["status"], "FAIL")

    def test_incomplete_matrix_is_inconclusive(self):
        r = ci.verify(RUN_SHA, [], fake_git, fake_fetch([run()], job_list=jobs(5)))
        self.assertEqual(r["status"], "INCONCLUSIVE")
        self.assertIn("declares 8", r["reason"])

    def test_a_failed_job_inside_a_success_run_is_fail(self):
        r = ci.verify(RUN_SHA, [], fake_git, fake_fetch([run()], job_list=jobs(7) + jobs(1, "failure")))
        self.assertEqual(r["status"], "FAIL")

    def test_in_progress_run_is_inconclusive(self):
        r = ci.verify(RUN_SHA, [], fake_git, fake_fetch([run(status="in_progress", conclusion=None)]))
        self.assertEqual(r["status"], "INCONCLUSIVE")

    def test_run_of_another_workflow_is_ignored(self):
        r = ci.verify(RUN_SHA, [], fake_git, fake_fetch([run(path=".github/workflows/other.yml")]))
        self.assertEqual(r["status"], "NOT_RUN")

    def test_tampered_record_is_caught(self):
        # The record claims success on RUN_SHA; GitHub says failure on another SHA.
        record = [{"run": 130, "id": 7, "head_sha": RUN_SHA, "conclusion": "success"}]
        live = [run(sha=DIVERGENT, conclusion="failure")]
        checked = ci.verify_record_claims(record, fake_fetch(live))
        self.assertEqual(checked[0]["status"], "FAIL")
        self.assertEqual(set(checked[0]["mismatch"]), {"head_sha", "conclusion"})
        # And the verdict for RUN_SHA never uses the record's claim.
        self.assertEqual(ci.verify(RUN_SHA, [RUN_SHA], fake_git, fake_fetch(live))["status"], "NOT_RUN")

    def test_judge_rejects_a_run_whose_sha_differs_from_the_one_asked(self):
        self.assertEqual(ci.judge_run(run(sha=DIVERGENT), jobs(), 8, RUN_SHA)["status"], "FAIL")

    def test_evidence_paths_are_narrow(self):
        self.assertTrue(ci.is_evidence_path("evals/assurance/runs/2026/x.json"))
        for code in ("voznativa/engine.py", "scripts/qualify.py", "evals/test_x.py", ".github/workflows/ci.yml",
                     "evals/qualification/expectations.json"):
            self.assertFalse(ci.is_evidence_path(code), code)


class WorkflowTriggerAudit(unittest.TestCase):
    def test_bare_on_key_is_read(self):
        self.assertEqual(qualify.workflow_triggers("on:\n  workflow_dispatch:\njobs: {}\n"), ["workflow_dispatch"])

    def test_automatic_triggers_are_listed(self):
        text = "on:\n  push:\n    branches: [main]\n  workflow_dispatch:\n  schedule:\n    - cron: '0 0 * * *'\n"
        self.assertEqual(qualify.workflow_triggers(text), ["push", "schedule", "workflow_dispatch"])
        self.assertEqual(qualify.workflow_triggers("on: [push, pull_request]\n"), ["push", "pull_request"])

    def test_repository_workflows_are_dispatch_only(self):
        self.assertEqual(qualify.gate_workflow_triggers(None)["status"], "PASS")


PY = sys.executable


class CheckpointHarness(unittest.TestCase):
    def test_failing_first_stage_fails_the_checkpoint(self):
        # Negative control for `cmd | tail`: the first stage fails, a later one succeeds.
        report = checkpoint.run_steps([[PY, "-c", "import sys; sys.exit(3)"], [PY, "-c", "print('ok')"]])
        self.assertEqual((report["status"], report["exit_code"]), ("FAIL", 3))
        self.assertEqual(len(report["steps"]), 1)
        self.assertEqual(len(report["not_run"]), 1)

    def test_pipeline_with_tail_hides_the_failure(self):
        # Documents the defect the harness removes: a shell pipeline reports tail's code.
        if sys.platform == "win32":
            self.skipTest("POSIX shell pipeline semantics")
        done = subprocess.run(["sh", "-c", f'"{PY}" -c "import sys; sys.exit(3)" | tail -1'])
        self.assertEqual(done.returncode, 0)
        done = subprocess.run(["bash", "-c", f'set -o pipefail; "{PY}" -c "import sys; sys.exit(3)" | tail -1'])
        self.assertEqual(done.returncode, 3)

    def test_success_records_hashes_and_revision(self):
        report = checkpoint.run_steps([[PY, "-c", "print('hello')"]])
        self.assertEqual(report["status"], "PASS")
        step = report["steps"][0]
        self.assertEqual(step["exit_code"], 0)
        self.assertEqual(len(step["stdout_sha256"]), 64)
        self.assertIn("sha", report["revision"])

    def test_missing_program_and_timeout_are_failures(self):
        self.assertEqual(checkpoint.run_steps([["no-such-program-vn07"]])["status"], "FAIL")
        report = checkpoint.run_steps([[PY, "-c", "import time; time.sleep(5)"]], timeout=0.5)
        self.assertEqual((report["status"], report["steps"][0]["error"]), ("FAIL", "timeout"))

    def test_push_is_verified_against_the_remote_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            bare, work = tmp / "remote.git", tmp / "work"

            def g(*argv, cwd=work):
                subprocess.run(["git", *argv], cwd=cwd, check=True, capture_output=True)

            subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
            subprocess.run(["git", "init", "-q", "-b", "dev", str(work)], check=True)
            g("config", "user.name", "t")
            g("config", "user.email", "t@example.invalid")
            (work / "f.txt").write_text("x", encoding="utf-8")
            g("add", "f.txt")
            g("commit", "-q", "-m", "x")
            g("remote", "add", "origin", str(bare))
            ok = checkpoint.verify_push("dev", cwd=work)
            self.assertEqual((ok["status"], ok["local_sha"]), ("PASS", ok["remote_sha"]))
            # A push the remote rejects (non-fast-forward) is a failure, not a green tail.
            other = tmp / "other"
            subprocess.run(["git", "clone", "-q", "-b", "dev", str(bare), str(other)], check=True)
            g("config", "user.name", "t", cwd=other)
            g("config", "user.email", "t@example.invalid", cwd=other)
            (other / "g.txt").write_text("y", encoding="utf-8")
            g("add", "g.txt", cwd=other)
            g("commit", "-q", "-m", "y", cwd=other)
            g("push", "-q", "origin", "dev", cwd=other)
            (work / "h.txt").write_text("z", encoding="utf-8")
            g("add", "h.txt")
            g("commit", "-q", "-m", "z")
            rejected = checkpoint.verify_push("dev", cwd=work)
            self.assertEqual((rejected["status"], rejected["exit_code"]), ("FAIL", 1))


if __name__ == "__main__":
    unittest.main()
