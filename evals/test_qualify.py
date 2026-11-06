"""The qualification runner's classification is a contract: a skipped or
uncollected suite must never read as PASS, and a new failure in a suite with
known failures must never hide behind them."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("qualify", ROOT / "scripts" / "qualify.py")
qualify = importlib.util.module_from_spec(spec)
sys.modules["qualify"] = qualify
spec.loader.exec_module(qualify)


def outcome(**over):
    base = {"ran": 3, "passed": ["a", "b", "c"], "failed": [], "errors": [], "collection_errors": [],
            "skipped": [], "expected_failures": [], "unexpected_successes": []}
    return dict(base, **over)


class UnittestClassification(unittest.TestCase):
    def test_all_passed_is_pass(self):
        self.assertEqual(qualify.classify_unittest(outcome()), "PASS")

    def test_failure_error_import_error_and_unexpected_success_fail(self):
        for over in ({"failed": [{"id": "t"}]}, {"errors": [{"id": "t"}]},
                     {"collection_errors": ["unittest.loader._FailedTest.test_x"]},
                     {"unexpected_successes": ["t"]}):
            self.assertEqual(qualify.classify_unittest(outcome(**over)), "FAIL", over)

    def test_nothing_collected_is_inconclusive_not_pass(self):
        self.assertEqual(qualify.classify_unittest(outcome(ran=0, passed=[])), "INCONCLUSIVE")

    def test_everything_skipped_is_skipped_not_pass(self):
        skipped = [{"id": i, "reason": "r"} for i in "abc"]
        self.assertEqual(qualify.classify_unittest(outcome(passed=[], skipped=skipped)), "SKIPPED")


class KnownFailures(unittest.TestCase):
    def test_new_failure_fails_even_beside_known_ones(self):
        r = qualify.classify_known({"dc-021", "dc-030"}, {"dc-021", "dc-029"})
        self.assertEqual(r["status"], "FAIL")
        self.assertEqual(r["new_failures"], ["dc-030"])
        self.assertEqual(r["known_failures_now_passing"], ["dc-029"])

    def test_only_known_failures_pass(self):
        self.assertEqual(qualify.classify_known({"dc-021"}, {"dc-021", "dc-029"})["status"], "PASS")


class Verdict(unittest.TestCase):
    R = qualify.Result

    def test_required_failure_wins(self):
        self.assertEqual(qualify.overall([self.R("a", "PASS", True, "local"), self.R("b", "FAIL", True, "local")]),
                         ("FAIL", 1))

    def test_blocked_or_not_run_required_gate_is_incomplete_not_pass(self):
        for status in ("BLOCKED", "NOT_RUN", "SKIPPED", "INCONCLUSIVE"):
            self.assertEqual(qualify.overall([self.R("a", "PASS", True, "local"), self.R("b", status, True, "local")]),
                             ("INCOMPLETE", 3), status)

    def test_optional_gates_do_not_decide(self):
        self.assertEqual(qualify.overall([self.R("a", "PASS", True, "local"), self.R("b", "FAIL", False, "release")]),
                         ("PASS", 0))

    def test_external_evidence_is_never_pass_without_a_run(self):
        import json
        external = json.loads(qualify.EXTERNAL.read_text(encoding="utf-8"))
        for key in ("independent_holdout", "blind_human_review"):
            self.assertIn(external[key]["status"], {"BLOCKED", "NOT_RUN", "WAIVED_BY_OWNER", "PASS"}, key)
            if external[key]["status"] == "PASS":
                self.assertIn("evidence", external[key], f"{key}: PASS needs a recorded run")
        self.assertNotEqual(external["ci"]["status"], "PASS", "CI status is derived per revision, never stored")


class PackageGateTools(unittest.TestCase):
    def test_missing_pip_or_build_is_blocked_not_a_project_failure(self):
        # v0.7.0: `uv venv` makes venvs without pip; the wheel step then failed and read as FAIL.
        real = qualify.importlib.util.find_spec
        for absent in ("pip", "build"):
            qualify.importlib.util.find_spec = lambda name, _a=absent: None if name == _a else real(name)
            try:
                result = qualify.gate_package(None)
            finally:
                qualify.importlib.util.find_spec = real
            self.assertEqual(result["status"], "BLOCKED", absent)
            self.assertIn(absent, result["reason"])


class CiEvidenceBindsToARevision(unittest.TestCase):
    """v0.6.0 CP0: CI evidence is PASS only for the revision a green run tested
    (the v0.5.0 records kept a stale BLOCKED while runs were passing)."""
    ENTRY = {"status": "NOT_RUN", "runs": [
        {"run": 122, "head_sha": "40e19e49993f865119c2d7efb43ec130b3b2b574", "conclusion": "failure"},
        {"run": 123, "head_sha": "40e19e49993f865119c2d7efb43ec130b3b2b574", "conclusion": "success"}]}

    def test_recorded_green_run_of_this_revision_is_not_pass_without_live_check(self):
        # v0.7.0 CP1 (VN07-DISC-001): the record is an index; PASS needs the live query.
        r = qualify.classify_ci(self.ENTRY, "40e19e49993f865119c2d7efb43ec130b3b2b574")
        self.assertEqual((r["status"], r["run"]["run"]), ("INCONCLUSIVE", 123))

    def test_another_revision_is_not_run_even_after_a_green_run(self):
        r = qualify.classify_ci(self.ENTRY, "3c5d2849cb3b0000000000000000000000000000")
        self.assertEqual(r["status"], "NOT_RUN")
        self.assertIn("40e19e49993f", r["reason"])

    def test_a_failed_run_of_this_revision_is_not_pass(self):
        entry = {"status": "NOT_RUN", "runs": [self.ENTRY["runs"][0]]}
        self.assertEqual(qualify.classify_ci(entry, "40e19e49993f865119c2d7efb43ec130b3b2b574")["status"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
