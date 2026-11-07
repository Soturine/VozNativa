"""v0.8 CP2 (V08-GAP-02): spans.extract without quadratic scans, same output.

Two helpers replaced full scans: ``_Occupied`` (a byte map instead of a list
checked in full for every match) and ``_sentence_start`` (a bounded search
instead of ``_SENTENCE_START_RE.search(text[:start])`` for every capitalised
word). The equality tests compare each helper with the exact expression it
replaced, on adversarial and random inputs, at every position. The growth
test fails on the old code (time grew ~6.5x for 2x input).

Before/after output equality over 3,036 texts (82,487 spans, every field) and
the curve are recorded in evals/assurance/runs/2026-11-07-v08-cp2/.
"""
import random
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import spans  # noqa: E402
from voznativa.spans import _SENTENCE_START_RE, _Occupied, _sentence_start, extract  # noqa: E402

ADVERSARIAL = [
    "", "Ana", "\nAna", "\n", "\n\n", " Ana", "1. Ana", "12) Ana", "## Ana", "- Ana", "• Ana", "* Ana", "+ Ana",
    "Fim.   \t Ana", "Fim. Ana", "Fim. Ana", "Fim:　Ana", "Fim!\r\nAna", "Fim?\x0bAna",
    "texto\r\n\r\n  3.  Ana", "x\n" + " " * 300 + "Ana", "x. " + "1 " * 200 + "Ana", "x" + "#" * 300 + " Ana",
    "Linha Ana", "Linha\u0085Ana", "Ok…  Ana", "a)\nb)\n#\n", "9.\n", ".\n", ":", "…\t", "\n-\n",
    "١٢. Ana",   # Arabic-Indic digits are \d too
]


def random_texts(seed: int, count: int) -> list[str]:
    rnd = random.Random(seed)
    alphabet = list(" \t\n\r.!?…:-*+•#)0123456789aAéÉ") + [" ", " ", " ", "\u0085", "\x0b", "Ana", "1.",
                                                         "##", "\r\n", "x"]
    return ["".join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 60))) for _ in range(count)]


class SentenceStartIsTheSameQuestion(unittest.TestCase):

    def assert_same(self, text):
        for start in range(len(text) + 1):
            expected = _SENTENCE_START_RE.search(text[:start]) is not None
            self.assertEqual(_sentence_start(text, start), expected, (text, start))

    def test_adversarial_texts_at_every_position(self):
        for text in ADVERSARIAL:
            with self.subTest(text=text[:20]):
                self.assert_same(text)

    def test_random_texts_at_every_position(self):
        for text in random_texts(20261107, 1500):
            self.assert_same(text)


class OccupiedIsTheSameQuestion(unittest.TestCase):

    def test_random_claims_including_overlapping_ones(self):
        rnd = random.Random(7)
        for _ in range(3000):
            size = rnd.randint(0, 50)
            occupied, reference = _Occupied(size), []
            for _ in range(rnd.randint(0, 25)):
                start = rnd.randint(0, size)
                end = rnd.randint(start, size)
                if rnd.random() < 0.5:   # the old code appended ranges that overlap (numeral + "reais")
                    occupied.add(start, end)
                    reference.append((start, end))
                q_start = rnd.randint(0, size)
                q_end = rnd.randint(q_start, size)
                expected = any(q_start < e and q_end > s for s, e in reference)
                self.assertEqual(occupied.overlaps(q_start, q_end), expected, (reference, q_start, q_end))


class GrowthIsNotQuadratic(unittest.TestCase):
    """Capitalised words far from a sentence start: each one made the old
    code copy and scan the whole prefix."""

    @staticmethod
    def best_of(text, runs=3):
        best = None
        for _ in range(runs):
            started = time.perf_counter()
            extract(text)
            elapsed = time.perf_counter() - started
            best = elapsed if best is None else min(best, elapsed)
        return best

    def test_four_times_the_input_is_not_sixteen_times_the_time(self):
        unit = "o projeto de Ana e de Bruno avança com Caio e Davi "
        small = self.best_of(unit * 600)
        large = self.best_of(unit * 2400)
        # Linear growth gives ~4x; the old code gave well over 16x on this input.
        self.assertLess(large / max(small, 1e-3), 9.0, f"small {small:.3f}s, large {large:.3f}s")

    def test_output_on_the_growth_input_is_unchanged_in_shape(self):
        unit = "o projeto de Ana e de Bruno avança com Caio e Davi "
        found = extract(unit * 50)
        self.assertEqual(len(found), 200)
        self.assertEqual({s.type for s in found}, {"entity"})
        self.assertIs(spans.extract, extract)


class MorphMemoAndOrder(unittest.TestCase):
    """``morph.analyse_word`` is memoised; ``_ENDINGS`` ties are ordered."""

    WORDS = ("APROVADO", "aprovado", "falaria", "enviou", "entregarão", "vai", "pode", "ser", "comando", "xyz")

    def test_callers_cannot_change_what_the_next_caller_gets(self):
        from voznativa import morph
        first = morph.analyse_word("falaria")
        self.assertTrue(first)
        first[0]["lemma"] = "ESTRAGADO"
        first.append({"lemma": "extra"})
        again = morph.analyse_word("falaria")
        self.assertNotIn("ESTRAGADO", {a["lemma"] for a in again})
        self.assertNotIn("extra", {a["lemma"] for a in again})
        self.assertEqual(again, morph._analyse_word("falaria"))

    def test_memo_returns_what_the_analysis_returns(self):
        from voznativa import morph
        for word in self.WORDS:
            with self.subTest(word=word):
                self.assertEqual(morph.analyse_word(word), morph._analyse_word(word))

    def test_order_does_not_depend_on_string_hashing(self):
        # Before v0.8 the order of equal-length endings came from a set, so it changed with PYTHONHASHSEED.
        import json
        import os
        import subprocess
        code = ("import json,sys; sys.path.insert(0, sys.argv[1]); from voznativa import morph; "
                f"print(json.dumps([morph.analyse_word(w) for w in {list(self.WORDS)!r}]))")
        outputs = set()
        for seed in ("1", "2", "3", "4"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            run = subprocess.run([sys.executable, "-B", "-c", code, str(ROOT)], env=env, capture_output=True,
                                 text=True, check=True)
            outputs.add(run.stdout)
        self.assertEqual(len(outputs), 1, "analyse_word order changed with the hash seed")
        self.assertTrue(json.loads(outputs.pop()))


if __name__ == "__main__":
    unittest.main()
