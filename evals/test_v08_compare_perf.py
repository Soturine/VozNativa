"""v0.8 CP7 (V08-GAP-12): compare on long documents, same answers, and the
document time limit also covers the global validation.

* ``compare._align`` uses an inverted index; ``_align_reference`` is the
  full scan it must agree with.
* ``compare._whole_word_matches`` replaces one regex scan of the whole text
  per entity name; it must return exactly what ``re.finditer`` returns,
  including for characters whose case-insensitive matching is irregular.
* ``rewrite_document`` returns the original when ``timeout_s`` runs out
  during the global validation (each revert runs compare again).

Curves before/after: docs/releases/v0.8/PERFORMANCE.md."""
import json
import random
import re
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import engine, ledger  # noqa: E402
from voznativa.compare import _align, _align_reference, _whole_word_matches, compare  # noqa: E402
from voznativa.document import Limits  # noqa: E402
from voznativa.router import route  # noqa: E402

WORDS = "não nn o a de deploy contrato Ana Bruno pode deve R$ 12.000,00 14/11/2025 sim posso vou . , \n".split(" ")
IRREGULAR = ["K", "K", "ß", "ẞ", "ſ", "s", "S", "İ", "ı", "i", "I", "Σ", "σ", "ς", "µ", "μ", "ﬅ", "st",
             "Ω", "Ω", "Ana", "ANA", "José", "JOSÉ", "Ana-Maria", " ", ".", "-", "\n"]


def suite_pairs():
    for path in sorted((ROOT / "evals").rglob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(case, dict) and isinstance(case.get("original"), str) and isinstance(case.get("candidate"), str):
                yield case["original"], case["candidate"]


class AlignmentIndexIsTheFullScan(unittest.TestCase):

    def test_suites_and_random_texts(self):
        rnd = random.Random(20261107)
        pairs = list(suite_pairs())
        pairs += [(" ".join(rnd.choice(WORDS) for _ in range(rnd.randint(1, 40))),
                   " ".join(rnd.choice(WORDS) for _ in range(rnd.randint(1, 40)))) for _ in range(300)]
        self.assertGreater(len(pairs), 500)
        for a, b in pairs:
            src, out = ledger.build(a), ledger.build(b)
            self.assertEqual(_align(src, out), _align_reference(src, out), (a[:60], b[:60]))


class NameMatchesAreTheRegexMatches(unittest.TestCase):

    def test_random_and_irregular_case(self):
        rnd = random.Random(11)
        for _ in range(800):
            text = "".join(rnd.choice(IRREGULAR) + rnd.choice([" ", "", ".", "\n"]) for _ in range(rnd.randint(1, 40)))
            for name in {rnd.choice(IRREGULAR), "".join(rnd.sample(IRREGULAR, 2)), "Ana Souza", "kpi"}:
                if not name.strip():
                    continue
                expected = [m.span() for m in re.finditer(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text, re.I)]
                self.assertEqual(_whole_word_matches(text, name), expected, (name, text))

    def test_ascii_k_takes_the_index(self):
        # Regression: the first version listed an ASCII "K" among the irregular characters,
        # so every text with a capital K fell back to the slow scan (correct but quadratic).
        from voznativa import compare as module
        self.assertIsNotNone(module._word_index("O KPI da Ana subiu."))
        self.assertIsNone(module._word_index("O ſ antigo."))


class GrowthOfCompare(unittest.TestCase):

    @staticmethod
    def name(k):
        letters = ""
        while True:
            k, r = divmod(k, 26)
            letters += "abcdefghijklmnopqrstuvwxyz"[r]
            if not k:
                return "Mar" + letters

    @classmethod
    def document(cls, blocks):
        # One distinct name per block: the old code ran one regex over the whole text per
        # name (names x text) and scored every sentence pair; both grow with the document.
        out = []
        for k in range(blocks):
            out.append(f"No bloco {k}, {cls.name(k)} revisou o contrato e {cls.name(k + 1)} enviou o parecer "
                       f"ao comitê. O prazo não pode passar de {k + 1} dias.")
        return "\n\n".join(out) + "\n"

    @classmethod
    def best_pair(cls, small_blocks=100, large_blocks=800, repeat=3):
        """Minimum CPU time of each size over ``repeat`` interleaved runs (v0.9 CP3, V09-GAP-14).

        v0.8 measured wall time, twice per size, one size after the other: under the
        load of the whole suite (other processes, I/O) the ratio crossed 19 (19.4,
        21.2) while isolated runs gave 12-13 on the same code. Process CPU time is not
        inflated by other processes, interleaving exposes both sizes to the same load
        bursts, and the minimum keeps the least disturbed run. The threshold did not
        change; the regression it guards against (x24 before the fix) still fails it."""
        docs = {n: cls.document(n) for n in (small_blocks, large_blocks)}
        compare(docs[small_blocks], docs[small_blocks] + "\nUma frase nova.\n")  # warm-up
        times = {n: [] for n in docs}
        for _ in range(repeat):
            for n, doc in docs.items():
                started = time.process_time()
                compare(doc, doc + "\nUma frase nova.\n")
                times[n].append(time.process_time() - started)
        return min(times[small_blocks]), min(times[large_blocks])

    def test_eight_times_the_document_stays_well_below_quadratic(self):
        # Measured on this input, 2026-11-07: before the fix (c353058) x24.0 for x8 the blocks,
        # after x12.6 (linear would be x8; residual: spans checked against the whole text).
        # v0.9 CP3: same threshold, CPU time, interleaved repeats (see best_pair).
        small, large = self.best_pair()
        self.assertLess(large / max(small, 1e-3), 19.0, f"small {small:.2f}s CPU, large {large:.2f}s CPU")


class SlowCompare:
    def __init__(self, seconds):
        self.seconds, self.real = seconds, engine.compare

    def __call__(self, *args, **kwargs):
        time.sleep(self.seconds)
        return self.real(*args, **kwargs)


class GlobalValidationTimeLimit(unittest.TestCase):

    def test_out_of_time_returns_the_original(self):
        doc = ("É importante destacar que o relatório será enviado na segunda.\n\n"
               "Vale ressaltar que o orçamento não pode passar de R$ 3.000,00.\n")

        class Cut:
            id = "cut"

            def generate(self, prompt, n=1):
                body = re.search(r"<<<TEXTO#(\w+)\n(.*)\nTEXTO#\1>>>", prompt, re.S).group(2)
                return ["<final>" + body.replace("É importante destacar que o", "O")
                        .replace("Vale ressaltar que o", "O") + "</final>"] * n

        with mock.patch.object(engine, "compare", SlowCompare(0.4)):
            result = engine.rewrite_document(doc, route(doc), Cut(), limits=Limits(segment_words=10, timeout_s=0.3))
        self.assertEqual((result["outcome"], result["text"]), ("returned_original", doc))
        self.assertIn("global validation", result["reason"])
        # CP15: this path and the normal one keep the same plan fields (one owner, engine._PLAN_IN_RECORD).
        self.assertEqual(tuple(result["plan"]), engine._PLAN_IN_RECORD)
        normal = engine.rewrite_document(doc, route(doc), Cut(), limits=Limits(segment_words=10))
        self.assertEqual(tuple(normal["plan"]), engine._PLAN_IN_RECORD)

    def test_with_time_left_the_document_is_validated(self):
        doc = "É importante destacar que o relatório será enviado na segunda.\n"

        class Cut:
            id = "cut"

            def generate(self, prompt, n=1):
                body = re.search(r"<<<TEXTO#(\w+)\n(.*)\nTEXTO#\1>>>", prompt, re.S).group(2)
                return ["<final>" + body.replace("É importante destacar que o", "O") + "</final>"] * n

        result = engine.rewrite_document(doc, route(doc), Cut(), limits=Limits(timeout_s=60))
        self.assertNotEqual(result["outcome"], "returned_original", result.get("reason"))
        self.assertTrue(result["text"].startswith("O relatório"))


if __name__ == "__main__":
    unittest.main()
