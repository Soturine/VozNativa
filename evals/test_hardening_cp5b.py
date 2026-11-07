"""v0.7.0.dev1 CP5B: closing audit findings H07-NEW-01..03 (and DISC-052).

* H07-NEW-01: a serialised document plan is data, not authority. Editing a
  plan's ``action``/``kinds``/``blocks``/offsets (even with the hashes
  recomputed) must not let ``reassemble`` replace a protected block.
* H07-NEW-02: only non-executable records under ``evals/assurance/runs/``
  count as post-CI evidence; code moved or renamed into that folder does not.
* H07-NEW-03: a qualifying CI run must come from ``workflow_dispatch`` and
  carry exactly the jobs the workflow declares (by name, not by count).
* VN07-DISC-052: a whitespace-only document is returned as is instead of
  crashing the planner.

Each tampering test failed (accepted the tampered plan / run) on d8aa669;
see docs/V07_DISCOVERY_REGISTER.md for the before/after record.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import engine  # noqa: E402
from voznativa.document import build_plan, reassemble, sha256, validate_plan  # noqa: E402
from voznativa.providers import StaticProvider  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ci = _load("ci_evidence")

DOC = ("# Relatório\n\nO time entregou a versão 2.1 em 14/11/2025.\n\n"
       "```\nrm -rf build/\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
       "---\n\n> Citação de Ana Souza, preservada.\n\nOutro parágrafo comum.\n")
POEM = "Quando a noite desce sobre o rio\nE o vento esquece o nome das ruas,\nGuardo no peito um silêncio frio\n"


def roundtrip(plan):
    return json.loads(json.dumps(plan))


def unit_of(plan, kind):
    return next(u for u in plan["units"] if u["kinds"] == [kind])


class PlanIsDataNotAuthority(unittest.TestCase):
    """H07-NEW-01."""

    def assert_refused(self, plan, replacements, text=DOC):
        self.assertTrue(validate_plan(plan, text), "validate_plan accepted a tampered plan")
        with self.assertRaises(ValueError):
            reassemble(text, plan, replacements)

    def test_flipping_action_does_not_unprotect(self):
        for kind in ("code", "table", "separator", "quote"):
            with self.subTest(kind=kind):
                plan = roundtrip(build_plan(DOC))
                u = unit_of(plan, kind)
                self.assertEqual(u["action"], "protect")
                u["action"] = "rewrite"
                self.assert_refused(plan, {u["index"]: "texto benigno"})

    def test_flipping_action_and_kinds_does_not_unprotect(self):
        for kind in ("code", "table", "quote"):
            with self.subTest(kind=kind):
                plan = roundtrip(build_plan(DOC))
                u = unit_of(plan, kind)
                u.update(action="rewrite", kinds=["prose"])
                self.assert_refused(plan, {u["index"]: "texto benigno"})

    def test_merging_a_protected_unit_into_a_rewritable_one_with_fresh_hashes(self):
        plan = roundtrip(build_plan(DOC))
        units = plan["units"]
        first, code = units[0], unit_of(plan, "code")
        self.assertEqual(code["index"], first["index"] + 1)
        first.update(end=code["end"], core_end=code["core_end"], blocks=first["blocks"] + code["blocks"],
                     kinds=first["kinds"] + code["kinds"])
        first["sha256"] = sha256(DOC[first["core_start"]:first["core_end"]])
        units.remove(code)
        for n, u in enumerate(units):
            u["index"] = n
        self.assert_refused(plan, {0: "# Relatório\n\nTudo novo."})

    def test_shifting_core_offsets_with_a_recomputed_hash(self):
        plan = roundtrip(build_plan(DOC))
        u = plan["units"][0]
        u["core_start"] += 2
        u["sha256"] = sha256(DOC[u["core_start"]:u["core_end"]])
        self.assert_refused(plan, {0: "x"})

    def test_duplicate_reordered_or_missing_units(self):
        dup = roundtrip(build_plan(DOC))
        dup["units"][1]["index"] = 0
        self.assert_refused(dup, {0: "# Outro"})
        swapped = roundtrip(build_plan(DOC))
        swapped["units"][0]["blocks"], swapped["units"][1]["blocks"] = (swapped["units"][1]["blocks"],
                                                                        swapped["units"][0]["blocks"])
        self.assertTrue(validate_plan(swapped, DOC))
        missing = roundtrip(build_plan(DOC))
        del missing["units"][-1]["kinds"]
        self.assertTrue(validate_plan(missing, DOC))
        truncated = roundtrip(build_plan(DOC))
        truncated["units"] = []
        self.assertTrue(validate_plan(truncated, DOC))

    def test_plan_of_another_text_is_refused(self):
        self.assert_refused(build_plan(DOC), {}, text=DOC + "Mais uma linha.\n")

    def test_verse_flag_must_match_the_declared_policy(self):
        plan = roundtrip(build_plan(POEM))
        self.assertEqual({u["action"] for u in plan["units"]}, {"protect"})
        plan["verse_explicit"] = True               # policy.protected_kinds still lists verse
        self.assert_refused(plan, {}, text=POEM)
        plan = roundtrip(build_plan(POEM))
        plan["verse_explicit"] = "yes"
        self.assertIn("verse_explicit must be a boolean", validate_plan(plan, POEM))

    def test_verse_explicit_never_unprotects_code_or_quotes(self):
        text = POEM + "\n```\nx = 1\n```\n\n> dito por alguém\n"
        plan = roundtrip(build_plan(text, verse_explicit=True))
        # v0.8 (V08-GAP-01): the caller grants verse; the plan's field alone no longer does.
        self.assertEqual(validate_plan(plan, text, verse_explicit=True), [])
        actions = {k: u["action"] for u in plan["units"] for k in u["kinds"]}
        self.assertEqual(actions, {"verse": "rewrite", "code": "protect", "quote": "protect"})
        unit_of(plan, "code")["action"] = "rewrite"
        self.assertTrue(validate_plan(plan, text, verse_explicit=True))
        with self.assertRaises(ValueError):
            reassemble(text, plan, {unit_of(plan, "code")["index"]: "y = 2"}, verse_explicit=True)

    def test_unknown_or_non_text_replacements_are_refused(self):
        plan = build_plan(DOC)
        with self.assertRaises(ValueError):
            reassemble(DOC, plan, {99: "x"})
        with self.assertRaises(ValueError):
            reassemble(DOC, plan, {"0": "x"})
        with self.assertRaises(ValueError):
            reassemble(DOC, plan, {0: 42})

    # Controls: valid plans keep working.

    def test_valid_plans_survive_json_roundtrip(self):
        for text in (DOC, DOC.replace("\n", "\r\n"), POEM, "Só uma frase.", "```\nsó código\n```"):
            with self.subTest(text=text[:20]):
                plan = roundtrip(build_plan(text))
                self.assertEqual(validate_plan(plan, text), [])
                self.assertEqual(reassemble(text, plan), text)

    def test_rewritable_units_are_still_replaced(self):
        plan = roundtrip(build_plan(DOC))
        last = plan["units"][-1]
        self.assertEqual(last["action"], "rewrite")
        out = reassemble(DOC, plan, {last["index"]: "Um parágrafo diferente."})
        self.assertTrue(out.endswith("Um parágrafo diferente.\n"))
        self.assertIn("rm -rf build/", out)

    def test_whitespace_only_document_is_returned_unchanged(self):
        # VN07-DISC-052: build_plan raised AssertionError and rewrite_document crashed.
        for text in ("", "   ", "\n\n", " \r\n\t\r\n"):
            with self.subTest(text=repr(text)):
                plan = build_plan(text)
                self.assertEqual((plan["units"], reassemble(text, plan)), ([], text))
                result = engine.rewrite_document(text, {"task": "edit"}, StaticProvider(["nunca usado"]))
                self.assertEqual((result["outcome"], result["text"]), ("no_change", text))


def fake_git(diff_output, run_sha="a" * 40, head="b" * 40, calls=None):
    def git(argv):
        if calls is not None:
            calls.append(argv)
        if argv[:2] == ["merge-base", "--is-ancestor"]:
            return (0 if argv[2:4] == [run_sha, head] else 1), ""
        if argv[0] == "diff":
            return 0, diff_output
        return 1, ""
    return git


class EvidencePathsAreRecordsOnly(unittest.TestCase):
    """H07-NEW-02."""

    def test_executable_or_config_files_in_run_folders_are_code(self):
        for path in ("evals/assurance/runs/2026-11-06-h07-cp5/replay_survivors.py",
                     "evals/assurance/runs/x/cr_select.py", "evals/assurance/runs/x/conftest.py",
                     "evals/assurance/runs/x/pyproject.toml", "evals/assurance/runs/x/setup.cfg",
                     "evals/assurance/runs/x/run.sh", "evals/assurance/runs/x/sitecustomize.pth",
                     "evals/assurance/runs/../../voznativa/engine.json"):
            self.assertFalse(ci.is_evidence_path(path), path)

    def test_records_in_run_folders_and_state_docs_are_evidence(self):
        for path in ("evals/qualification/external.json", "evals/assurance/runs/x/MANIFEST.json",
                     "evals/assurance/runs/x/MUTATION.md", "evals/assurance/runs/x/log.txt",
                     "evals/assurance/runs/x/cases.jsonl", "docs/V07_EXECUTION_STATE.md",
                     "docs/V07_RELEASE_QUALIFICATION.md"):
            self.assertTrue(ci.is_evidence_path(path), path)

    def test_editing_a_harness_after_the_run_invalidates_it(self):
        eq = ci.code_equivalence("a" * 40, "b" * 40, fake_git(
            "evals/qualification/external.json\nevals/assurance/runs/x/replay_survivors.py"))
        self.assertEqual(eq["relation"], "code_changed")
        self.assertEqual(eq["changed_code_paths"], ["evals/assurance/runs/x/replay_survivors.py"])

    def test_diff_is_asked_without_rename_detection(self):
        calls = []
        ci.code_equivalence("a" * 40, "b" * 40, fake_git("", calls=calls))
        self.assertIn("--no-renames", next(c for c in calls if c[0] == "diff"))

    @unittest.skipUnless(shutil.which("git"), "git not available")
    def test_real_git_move_add_remove_into_the_evidence_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            def git(argv):
                done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                                       "-c", "commit.gpgsign=false", *argv], cwd=tmp, capture_output=True,
                                      text=True, stdin=subprocess.DEVNULL)
                return done.returncode, done.stdout.strip()

            def commit(message):
                self.assertEqual(git(["add", "-A"])[0], 0)
                self.assertEqual(git(["commit", "-q", "-m", message])[0], 0)
                return git(["rev-parse", "HEAD"])[1]

            root = Path(tmp)
            git(["init", "-q"])
            (root / "voznativa").mkdir()
            (root / "voznativa" / "engine.py").write_text("x = 1\n" * 50, encoding="utf-8")
            (root / "evals" / "assurance" / "runs" / "r").mkdir(parents=True)
            (root / "evals" / "assurance" / "runs" / "r" / "MANIFEST.json").write_text("{}", encoding="utf-8")
            run_sha = commit("run")

            (root / "evals" / "assurance" / "runs" / "r" / "MANIFEST.json").write_text('{"a": 1}', encoding="utf-8")
            (root / "evals" / "assurance" / "runs" / "r" / "NOTES.md").write_text("ok", encoding="utf-8")
            evidence = commit("evidence")
            self.assertEqual(ci.code_equivalence(run_sha, evidence, git)["relation"], "evidence_only")

            (root / "voznativa" / "engine.py").rename(root / "evals" / "assurance" / "runs" / "r" / "engine.py")
            moved = commit("move code into the run folder")
            eq = ci.code_equivalence(run_sha, moved, git)
            self.assertEqual(eq["relation"], "code_changed")
            self.assertIn("voznativa/engine.py", eq["changed_code_paths"])

            (root / "evals" / "assurance" / "runs" / "r" / "engine.py").rename(
                root / "evals" / "assurance" / "runs" / "r" / "engine.json")
            disguised = commit("rename it to look like a record")
            eq = ci.code_equivalence(run_sha, disguised, git)
            self.assertEqual(eq["relation"], "code_changed")
            self.assertIn("voznativa/engine.py", eq["changed_code_paths"])


WORKFLOW_TEXT = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
RUN124_JOBS = ["test (ubuntu-latest, 3.12)", "test (ubuntu-latest, 3.13)", "package (ubuntu-latest)",
               "test (windows-latest, 3.13)", "test (ubuntu-latest, 3.11)", "package (windows-latest)",
               "test (windows-latest, 3.11)", "test (windows-latest, 3.12)"]   # gh api, run 42260943492


def run(event="workflow_dispatch"):
    return {"id": 1, "run_number": 1, "head_sha": "a" * 40, "path": ci.WORKFLOW, "event": event,
            "status": "completed", "conclusion": "success"}


def judged(names, event="workflow_dispatch", workflow=WORKFLOW_TEXT):
    expected = ci.expected_job_names(workflow)
    return ci.judge_run(run(event), [{"name": n, "conclusion": "success"} for n in names], len(expected),
                        "a" * 40, expected_names=expected, declared_events=ci.workflow_events(workflow))


class ManualRunAndExactMatrix(unittest.TestCase):
    """H07-NEW-03."""

    def test_names_come_from_the_versioned_workflow(self):
        self.assertEqual(sorted(ci.expected_job_names(WORKFLOW_TEXT)), sorted(RUN124_JOBS))
        self.assertEqual(ci.workflow_events(WORKFLOW_TEXT), ["workflow_dispatch"])

    def test_the_real_run124_job_list_passes(self):
        self.assertEqual(judged(RUN124_JOBS)["status"], "PASS")

    def test_a_push_run_is_not_qualifying_even_if_declared(self):
        self.assertEqual(judged(RUN124_JOBS, event="push")["status"], "INCONCLUSIVE")
        with_push = WORKFLOW_TEXT.replace("on:\n  workflow_dispatch:", "on:\n  push:\n  workflow_dispatch:")
        self.assertIn("push", ci.workflow_events(with_push))
        self.assertEqual(judged(RUN124_JOBS, event="push", workflow=with_push)["status"], "INCONCLUSIVE")
        for event in ("pull_request", "schedule", None):
            self.assertEqual(judged(RUN124_JOBS, event=event)["status"], "INCONCLUSIVE", event)

    def test_eight_successful_jobs_with_a_duplicate_are_not_the_matrix(self):
        names = RUN124_JOBS[:-1] + [RUN124_JOBS[0]]
        verdict = judged(names)
        self.assertEqual(verdict["status"], "INCONCLUSIVE")
        self.assertIn("test (windows-latest, 3.12)", verdict["reason"])

    def test_a_substituted_combination_is_not_the_matrix(self):
        names = [n.replace("windows-latest, 3.13", "windows-latest, 3.10") for n in RUN124_JOBS]
        self.assertEqual(judged(names)["status"], "INCONCLUSIVE")

    def test_extra_unexpected_job_is_not_hidden(self):
        self.assertEqual(judged(RUN124_JOBS + ["lint"])["status"], "INCONCLUSIVE")

    def test_unsupported_matrix_shapes_make_verify_inconclusive(self):
        custom = WORKFLOW_TEXT.replace("  test:\n", "  test:\n    name: Tests\n", 1)
        with self.assertRaises(ValueError):
            ci.expected_job_names(custom)

        def git(argv):
            return (0, custom) if argv[0] == "show" else (1, "")

        def fetch(path):
            return {"workflow_runs": [run()]} if path.startswith("actions/runs?") else {"jobs": []}
        verdict = ci.verify("a" * 40, [], git, fetch)
        self.assertEqual(verdict["status"], "INCONCLUSIVE")
        self.assertIn("custom job name", verdict["reason"])


if __name__ == "__main__":
    unittest.main()
