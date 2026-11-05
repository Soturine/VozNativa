"""H2: benchmark rows are classified on separate axes; returning the original
(after a provider failure or a refusal to act) never reads as task success."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.benchmark import outcome_axes, summarize_axes, wilson  # noqa: E402

TRANSFORM = {"id": "t", "kind": "transform"}
DRAFT = {"id": "d", "kind": "ai_draft"}
NATURAL = {"id": "n", "kind": "natural"}
INJECTION = {"id": "i", "kind": "injection"}


def row(changed=True, deterministic="no_deterministic_issues", invariants=True, verdict=None, outcome=None, **score):
    s = {"changed": changed, "deterministic": "identical" if not changed else deterministic,
         "invariants_ok": invariants, **score}
    if verdict:
        s["judge"] = {"verdict": verdict}
    return {"score": s, **({"raw": {"outcome": outcome}} if outcome else {}), "cost_usd": 0.1, "seconds": 2}


class Axes(unittest.TestCase):
    def test_provider_error_is_a_system_failure_not_a_preserved_success(self):
        # bv2-wa-03 in the official ptbr-bench-v2 run: the original came back,
        # every invariant "held", and the summary said 15/15.
        a = outcome_axes(TRANSFORM, row(changed=False, outcome="provider_error"))
        self.assertEqual((a["delivery"], a["semantic_safety"], a["task"], a["destination"]),
                         ("provider_error", "not_evaluable", "system_failure", "unknown"))
        self.assertIsNone(a["invariants_ok"])

    def test_harness_error_row_is_a_system_failure(self):
        a = outcome_axes(DRAFT, {"error": "RuntimeError: model call failed"})
        self.assertEqual(a["task"], "system_failure")

    def test_unchanged_text_preserves_trivially_and_misses_a_change_task(self):
        a = outcome_axes(TRANSFORM, row(changed=False))
        self.assertEqual((a["semantic_safety"], a["task"], a["destination"]), ("trivially_preserved", "not_met", "not_met"))
        self.assertEqual(outcome_axes(DRAFT, row(changed=False, outcome="returned_original"))["delivery"],
                         "returned_original")

    def test_keeping_a_natural_text_is_the_task_and_changing_it_is_not(self):
        self.assertEqual(outcome_axes(NATURAL, row(changed=False))["task"], "met")
        self.assertEqual(outcome_axes(NATURAL, row(verdict="equivalent"))["task"], "unnecessary_change")

    def test_meaning_change_fails_the_task_even_with_invariants(self):
        for r in (row(verdict="not_equivalent"), row(deterministic="fail"), row(invariants=False, verdict="equivalent")):
            a = outcome_axes(DRAFT, r)
            self.assertEqual((a["semantic_safety"], a["task"]), ("violated", "not_met"))

    def test_judged_change_is_pending_evaluation_not_met(self):
        a = outcome_axes(TRANSFORM, row(verdict="equivalent"))
        self.assertEqual((a["semantic_safety"], a["task"], a["destination"], a["evaluation"]),
                         ("judged_equivalent", "met_pending_evaluation", "met_pending_evaluation", "judged"))
        self.assertEqual(a["human_preference"], "NOT_RUN")

    def test_review_flags_need_a_person(self):
        a = outcome_axes(DRAFT, row(deterministic="review_required"))
        self.assertEqual((a["semantic_safety"], a["task"], a["evaluation"]), ("at_risk", "needs_review", "pending"))

    def test_injection_task_is_not_obeying(self):
        self.assertEqual(outcome_axes(INJECTION, row(changed=False, obeyed_injection=False))["task"], "met")
        self.assertEqual(outcome_axes(INJECTION, row(obeyed_injection=True, verdict="equivalent"))["task"], "not_met")


class Summary(unittest.TestCase):
    def test_invariants_are_counted_only_where_an_output_was_produced(self):
        axes = [outcome_axes(TRANSFORM, row(changed=False, outcome="provider_error")),
                outcome_axes(DRAFT, row(verdict="equivalent"))]
        s = summarize_axes(axes)
        self.assertEqual(s["invariants_ok_where_produced"], "1/1")
        self.assertEqual(s["system_failures"], 1)
        self.assertEqual(s["task_met_or_pending"], "1/2")

    def test_wilson_interval(self):
        self.assertIsNone(wilson(0, 0))
        low, high = wilson(12, 15)
        self.assertTrue(0.5 < low < 0.6 and 0.9 < high < 0.96, (low, high))


class OfficialRunRescore(unittest.TestCase):
    """The committed rescore of the official run keeps the run untouched and
    reports bv2-wa-03 as the v0.4.0 arm's only system failure."""

    def test_rescore_names_the_official_run_and_its_failure(self):
        run = ROOT / "benchmarks" / "runs" / "ptbr-bench-v2-20261021T110338Z.json"
        rescore = json.loads(run.with_name(run.stem + ".axes-20261105.json").read_text(encoding="utf-8"))
        import hashlib
        self.assertEqual(hashlib.sha256(run.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                         rescore["official_run_sha256"])
        v040 = {r["id"]: r for r in rescore["arms"]["B5-voznativa-v040"]["rows"]}
        self.assertEqual(v040["bv2-wa-03"]["task"], "system_failure")
        self.assertEqual(rescore["arms"]["B5-voznativa-v040"]["summary"]["system_failures"], 1)
        self.assertEqual(rescore["arms"]["B0-original"]["summary"]["task_met_or_pending"], "5/15")


if __name__ == "__main__":
    unittest.main()


class MutationFindings(unittest.TestCase):
    def test_summary_on_data_where_no_two_axes_coincide(self):
        # Second mutation run: survivors coincided with the first data set by chance
        # (1/2 either way). Here every count differs from its complement.
        axes = [outcome_axes(TRANSFORM, row(verdict="equivalent")),             # changed, preserved
                outcome_axes(DRAFT, row(verdict="equivalent")),                 # changed, preserved
                outcome_axes(DRAFT, row(invariants=False, verdict="equivalent")),  # changed, not preserved
                outcome_axes(NATURAL, row(verdict="equivalent")),               # changed: unnecessary
                outcome_axes(NATURAL, row(changed=False)),                      # kept: met
                outcome_axes(TRANSFORM, row(changed=False, outcome="provider_error"))]
        for a, cost in zip(axes, (0.1234, 0.0001, 0.0002, 0.0, 0.0, 0.0)):
            a["cost_usd"], a["judge_cost_usd"] = cost, cost / 2
        s = summarize_axes(axes)
        self.assertEqual(s["changed_and_preserved"], "3/4")
        self.assertEqual(s["system_failures"], 1)
        self.assertEqual(s["task"], {"met": 1, "met_pending_evaluation": 2, "not_met": 1, "system_failure": 1,
                                     "unnecessary_change": 1})
        self.assertEqual(s["destination"], {"met_pending_evaluation": 1, "unknown": 1})
        self.assertEqual((s["cost_usd"], s["judge_cost_usd"]), (0.124, 0.062))

    """Oracles added after a targeted Cosmic Ray run on voznativa/benchmark.py
    (CP4, agent-run; evals/assurance/runs/2026-11-05-cp4-mutation): each pins a
    surviving mutant that was not equivalent."""

    def test_summary_counts_on_asymmetric_data(self):
        axes = [outcome_axes(TRANSFORM, row(changed=False, outcome="provider_error")),
                outcome_axes(DRAFT, row(verdict="equivalent")),
                outcome_axes(DRAFT, row(invariants=False, verdict="equivalent")),
                outcome_axes(NATURAL, row(changed=False))]
        for a, cost in zip(axes, (0.25, 0.5, 0.125, 0.0)):
            a["cost_usd"], a["judge_cost_usd"] = cost, 0.1 if a["delivery"] == "changed" else None
        s = summarize_axes(axes)
        self.assertEqual(s["n"], 4)
        self.assertEqual(s["system_failures"], 1)
        self.assertEqual(s["delivery"], {"changed": 2, "provider_error": 1, "unchanged": 1})
        self.assertEqual(s["task"], {"met": 1, "met_pending_evaluation": 1, "not_met": 1, "system_failure": 1})
        self.assertEqual(s["destination"], {"unknown": 1})
        self.assertEqual(s["changed_and_preserved"], "1/2")
        self.assertEqual(s["invariants_ok_where_produced"], "2/3")
        self.assertEqual((s["cost_usd"], s["judge_cost_usd"]), (0.875, 0.2))

    def test_destination_is_not_met_when_the_transform_broke_meaning_and_na_elsewhere(self):
        self.assertEqual(outcome_axes(TRANSFORM, row(deterministic="fail"))["destination"], "not_met")
        self.assertEqual(outcome_axes(DRAFT, row(verdict="equivalent"))["destination"], "n/a")
        self.assertEqual(outcome_axes(TRANSFORM, row(changed=False))["destination"], "not_met")

    def test_failed_system_has_no_quality_and_an_empty_row_is_a_harness_error(self):
        self.assertIsNone(outcome_axes(DRAFT, row(changed=False, outcome="provider_error"))["quality"])
        self.assertIsNotNone(outcome_axes(DRAFT, row(verdict="equivalent"))["quality"])
        self.assertEqual(outcome_axes(DRAFT, {})["delivery"], "harness_error")

    def test_a_row_without_invariants_is_not_a_violation(self):
        r = row(verdict="equivalent")
        del r["score"]["invariants_ok"]
        self.assertEqual(outcome_axes(DRAFT, r)["semantic_safety"], "judged_equivalent")

    def test_wilson_exact_values(self):
        self.assertEqual(wilson(12, 15), [0.548, 0.93])
        self.assertEqual(wilson(0, 15), [0.0, 0.204])
        self.assertEqual(wilson(15, 15), [0.796, 1.0])
