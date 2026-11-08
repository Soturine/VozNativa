"""Blind pairwise human review instrument (v0.3.0 M4.4). No human result is
produced here: the tests type answers to check the mechanism only."""
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import cli
from voznativa.blind import build_tasks, review, summarize

RUN = {"rows": [
    {"arm": "B0-original", "id": "c1", "output": "Original um."},
    {"arm": "X", "id": "c1", "output": "Texto do X."},
    {"arm": "Y", "id": "c1", "output": "Texto do Y."},
    {"arm": "B0-original", "id": "c2", "output": "Original dois."},
    {"arm": "X", "id": "c2", "output": "Outro do X."},
    {"arm": "Y", "id": "c2", "output": "Outro do X."},  # identical to X: no task
    {"arm": "Z", "id": "c2", "error": "boom"},
]}


class TempKey:
    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.prev = os.environ.get("VOZNATIVA_REVIEW_KEY")
        os.environ["VOZNATIVA_REVIEW_KEY"] = str(Path(self.tmp.name) / "k")

    def __exit__(self, *exc):
        if self.prev is None:
            os.environ.pop("VOZNATIVA_REVIEW_KEY", None)
        else:
            os.environ["VOZNATIVA_REVIEW_KEY"] = self.prev
        self.tmp.cleanup()


class Tasks(unittest.TestCase):
    def test_pairs_skip_identical_outputs_and_errors(self):
        tasks = build_tasks(RUN, seed=1)["tasks"]
        self.assertEqual({t["case"] for t in tasks}, {"c1", "c2"})
        self.assertFalse(any({t["a"]["arm"], t["b"]["arm"]} == {"X", "Y"} and t["case"] == "c2" for t in tasks))
        self.assertTrue(all(t["original"].startswith("Original") for t in tasks))

    def test_focus_and_seeded_order(self):
        focused = build_tasks(RUN, focus="X", seed=3)["tasks"]
        # CP14 (Assertiva UNCHECKED_ALL lead, confirmed by a negative control): a focus that dropped
        # every pair passed the all() below vacuously.
        self.assertTrue(focused, "the focus keeps the pairs that include X")
        self.assertTrue(all("X" in (t["a"]["arm"], t["b"]["arm"]) for t in focused))
        self.assertEqual(build_tasks(RUN, seed=7), build_tasks(RUN, seed=7))


class ReviewAndSummary(unittest.TestCase):
    def test_only_verified_answers_count(self):
        tasks = build_tasks(RUN, focus="X", seed=2)
        with TempKey():
            typed = iter(["a", "a", "a"] * 10)
            answers = review(tasks, "tester", ask=lambda _: next(typed), show=lambda _: None)
            forged = dict(answers[0], meaning="B")  # edited after signing
            summary = summarize(tasks, answers + [forged])
        self.assertEqual(summary["answers_counted"], len(answers))
        self.assertEqual(summary["answers_rejected"], 1)
        wins = sum(cell["meaning"]["win"] for cell in summary["by_arm"].values())
        self.assertEqual(wins, len(answers))

    def test_summary_without_a_local_key_counts_nothing(self):
        tasks = build_tasks(RUN, seed=2)
        with TempKey():
            typed = iter(["e"] * 30)
            answers = review(tasks, "tester", ask=lambda _: next(typed), show=lambda _: None)
        with TempKey():  # another machine: the signature cannot be verified
            self.assertEqual(summarize(tasks, answers)["answers_counted"], 0)

    def test_cli_refuses_without_a_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp, "t.json")
            tasks.write_text('{"tasks": []}', encoding="utf-8")
            original = sys.stdin
            sys.stdin = io.StringIO("a\n")
            try:
                with redirect_stdout(io.StringIO()):
                    code = cli.main(["blind-review", str(tasks), "--reviewer", "x", "--out", str(Path(tmp, "a.jsonl"))])
            finally:
                sys.stdin = original
            self.assertEqual(code, 64)


if __name__ == "__main__":
    unittest.main()
