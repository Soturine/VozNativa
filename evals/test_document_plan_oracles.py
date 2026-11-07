"""v0.7.0.dev1 CP5B (backlog B-M3): boundary oracles for ``document.py``.

Round D of the CP5 mutation sample (evals/assurance/runs/2026-11-06-h07-cp5)
left survivors at the segment cut (``segment_words`` boundary, back-off to a
safe cut, forced cut), at the core/edge offsets, at the field-by-field refusal
of a plan and at the protected-unit check after a JSON round trip. Each test
names the lines (of c909f1d) whose survivors it is meant to kill; the replay
is recorded in evals/assurance/runs/2026-11-07-h07-cp5b/.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import longform  # noqa: E402
from voznativa.document import (SCHEMA_VERSION, Limits, PlanLimitExceeded, build_plan, reassemble,  # noqa: E402
                                structure_of, unit_text, validate_plan)


def para(n: int, tag: str) -> str:
    """A prose paragraph of exactly ``n`` words that depends on nothing."""
    return " ".join([f"Registro{tag}"] + ["dado"] * (n - 2) + ["fim."])


def linked(n: int, tag: str) -> str:
    """A paragraph of ``n`` words whose opening points back (cut cost > 0)."""
    return " ".join(["Portanto", f"registro{tag}"] + ["dado"] * (n - 3) + ["fim."])


def blocks_of(plan):
    return [u["blocks"] for u in plan["units"]]


class SegmentCut(unittest.TestCase):
    """c909f1d lines 87-96."""

    def test_fixture_cut_costs(self):
        bs = longform.dependency_map("\n\n".join([para(4, "a"), linked(4, "b")]))
        self.assertEqual([b.kind for b in bs], ["prose", "prose"])
        self.assertEqual([longform._cut_cost(b) for b in bs], [0, 4])

    def test_a_unit_may_reach_exactly_segment_words(self):
        text = "\n\n".join([para(5, "a"), para(5, "b"), para(5, "c")])
        self.assertEqual(blocks_of(build_plan(text, limits=Limits(segment_words=10))), [[0, 1], [2]])

    def test_the_limit_adds_word_counts(self):
        # 6 + 5 = 11 > 10 must cut (6 | 5 = 7 would not: line 87).
        text = "\n\n".join([para(6, "a"), para(5, "b")])
        self.assertEqual(blocks_of(build_plan(text, limits=Limits(segment_words=10))), [[0], [1]])

    def test_the_back_off_starts_at_the_last_block_of_the_unit(self):
        # Three safe blocks, then a linked one: the cut moves back by one block only (line 90).
        text = "\n\n".join([para(3, "a"), para(3, "b"), para(3, "c"), linked(3, "d")])
        self.assertEqual(blocks_of(build_plan(text, limits=Limits(segment_words=10))), [[0, 1], [2, 3]])

    def test_blocks_below_the_limit_stay_together(self):
        text = "\n\n".join([para(3, "a"), para(3, "b"), para(3, "c")])
        self.assertEqual(blocks_of(build_plan(text, limits=Limits(segment_words=10))), [[0, 1, 2]])

    def test_the_cut_backs_off_to_the_last_safe_boundary(self):
        text = "\n\n".join([para(4, "a"), para(4, "b"), linked(4, "c"), para(4, "d")])
        plan = build_plan(text, limits=Limits(segment_words=10))
        self.assertEqual(blocks_of(plan), [[0], [1, 2], [3]])
        self.assertEqual(plan["forced_cuts"], [])

    def test_a_chain_without_safe_cut_is_forced_past_twice_the_limit(self):
        text = "\n\n".join([para(4, "a")] + [linked(3, str(i)) for i in range(4)])
        plan = build_plan(text, limits=Limits(segment_words=5))
        # 4+3 and 4+3+3 = 10 do not exceed 2 * 5; the third linked block (13 > 10) is forced.
        self.assertEqual(blocks_of(plan), [[0, 1, 2], [3, 4]])
        self.assertEqual([c["before_block"] for c in plan["forced_cuts"]], [3])
        self.assertTrue(plan["forced_cuts"][0]["breaks"])

    def test_max_units_counts_rewritable_units_only(self):
        text = "\n\n".join(["```\na\n```", para(4, "a"), "```\nb\n```", "```\nc\n```"])
        plan = build_plan(text, limits=Limits(max_units=1))
        self.assertEqual(sum(u["action"] == "protect" for u in plan["units"]), 3)
        with self.assertRaises(PlanLimitExceeded):
            build_plan("\n\n```\nx\n```\n\n".join([para(4, "a"), para(4, "b")]), limits=Limits(max_units=1))


class CoreAndEdges(unittest.TestCase):
    """c909f1d lines 116-123 and 134."""

    # Odd runs of trailing blanks (3 and 1): trimming two at a time would eat a visible character (line 123).
    TEXT = "\n\n  " + para(4, "a") + "  \t\n\n```\nx = 1\n```\n\n" + para(5, "b") + " 14/11/2025.\t\n\n\n"

    def test_first_and_last_units_reach_the_text_edges(self):
        plan = build_plan(self.TEXT)
        self.assertEqual((plan["units"][0]["start"], plan["units"][-1]["end"]), (0, len(self.TEXT)))

    def test_core_drops_surrounding_blank_lines_and_trailing_spaces(self):
        plan = build_plan(self.TEXT)
        first, last = plan["units"][0], plan["units"][-1]
        self.assertEqual(unit_text(self.TEXT, first), "  " + para(4, "a"))
        self.assertEqual(unit_text(self.TEXT, last), para(5, "b") + " 14/11/2025.")

    def test_replacing_cores_keeps_every_edge_byte(self):
        plan = build_plan(self.TEXT)
        out = reassemble(self.TEXT, plan, {0: "NOVO", plan["units"][-1]["index"]: "FIM"})
        self.assertEqual(out, "\n\nNOVO  \t\n\n```\nx = 1\n```\n\nFIM\t\n\n\n")

    def test_values_belong_to_the_unit_that_holds_them(self):
        plan = build_plan(self.TEXT)
        self.assertEqual(plan["units"][0]["values"], [])
        self.assertTrue(plan["units"][-1]["values"])


class FieldByFieldRefusal(unittest.TestCase):
    """c909f1d lines 162-168 and 190."""

    TEXT = para(4, "a") + "\n\n```\nx\n```\n\n" + para(4, "b") + "\n"

    def plan(self):
        return json.loads(json.dumps(build_plan(self.TEXT)))

    def test_schema_version_is_part_of_the_contract(self):
        self.assertEqual((SCHEMA_VERSION, build_plan(self.TEXT)["schema_version"]), (1, 1))
        for version in (0, 2, "1", None):
            plan = self.plan()
            plan["schema_version"] = version
            self.assertTrue(validate_plan(plan, self.TEXT), version)

    def test_kind_and_document_hash_are_checked(self):
        plan = self.plan()
        plan["kind"] = "voznativa.other"
        self.assertTrue(validate_plan(plan, self.TEXT))
        plan = self.plan()
        plan["sha256"] = "0" * 64
        self.assertTrue(validate_plan(plan, self.TEXT))

    def test_a_unit_that_overlaps_the_previous_one_is_refused(self):
        plan = self.plan()
        plan["units"][1]["start"] -= 1
        self.assertTrue(validate_plan(plan, self.TEXT))

    def test_protected_unit_of_a_json_plan_cannot_be_replaced(self):
        # Strings from json.loads are not interned: an `is` comparison would let this through.
        plan = self.plan()
        code = next(u for u in plan["units"] if u["kinds"] == ["code"])
        with self.assertRaises(ValueError):
            reassemble(self.TEXT, plan, {code["index"]: "y"})


class SmallContracts(unittest.TestCase):
    """c909f1d lines 143 and 204."""

    def test_structure_ignores_separators(self):
        self.assertEqual(structure_of(para(3, "a") + "\n\n---\n\n" + para(3, "b")), ["prose", "prose"])
        # Kinds that sort after "separator" are kept too (line 204: != is not <).
        table = "| a | b |\n|---|---|\n| 1 | 2 |"
        verse = "Quando a noite desce sobre o rio\nE o vento esquece o nome das ruas,\nGuardo no peito um silêncio frio"
        self.assertEqual(structure_of(table + "\n\n---\n\n" + verse), ["table", "verse"])

    def test_context_keeps_values_and_protections(self):
        ctx = {"task": {"value": "edit"}, "genre": "news", "register": {"value": None}, "protections": ["X"]}
        self.assertEqual(build_plan(para(4, "a"), ctx)["context"],
                         {"task": "edit", "genre": "news", "register": None, "protections": ["X"]})
        self.assertEqual(build_plan(para(4, "a"), {"task": None})["context"]["task"], None)


if __name__ == "__main__":
    unittest.main()
