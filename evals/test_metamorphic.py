"""CP7 metamorphic tests of the semantic gate.

Relations that must hold whatever the text says:

1. Surface-equivalent rewrites (same value in another notation) are never
   blocked.
2. A surface transform applied to BOTH texts (NFD accents, no-break spaces,
   CRLF, tabs, zero-width characters, surrounding blank lines) never changes
   the verdict. Before CP7, NFD turned 20 of 216 suite verdicts around, some
   into false greens ("não" decomposed into "na" + "o"), and a no-break space
   hid "fim do mês" from the time spans.
3. Applying a transform to the candidate alone, when it is the original, never
   blocks it.
"""
import glob
import json
import sys
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare  # noqa: E402
from voznativa.engine import rewrite  # noqa: E402
from voznativa.providers import StaticProvider  # noqa: E402
from voznativa.router import route  # noqa: E402

UNSAFE = {"fail", "review_required"}
TRANSFORMS = {
    "nfd": lambda t: unicodedata.normalize("NFD", t),
    "nbsp": lambda t: t.replace(" ", " "),
    "narrow_nbsp": lambda t: t.replace(" ", " "),
    "crlf": lambda t: t.replace("\n", "\r\n"),
    "tabs": lambda t: t.replace(" ", "\t", 2),
    "zero_width": lambda t: t.replace(" ", " ​", 3),
    "wrapped": lambda t: "\n" + t + "\n",
}


def suite_pairs():
    pairs = []
    for path in sorted(glob.glob(str(ROOT / "evals" / "semantic" / "*.jsonl"))):
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                case = json.loads(line)
                pairs.append((f"{Path(path).name}:{case['id']}", case["original"], case["candidate"]))
    return pairs


class SurfaceEquivalence(unittest.TestCase):
    NOTATIONS = [("R$ 1.500,00", "R$1.500,00"), ("às 14h", "às 14:00"), ("às 14h", "às 2 da tarde"),
                 ("dois dias", "2 dias"), ("segunda-feira", "segunda"), ("5%", "5 por cento"),
                 ("10 mil", "10.000"), ("3 de março de 2026", "03/03/2026"), ('"aspas"', "“aspas”"),
                 ("30 minutos", "meia hora")]

    def test_another_notation_of_the_same_value_is_not_blocked(self):
        base = "O pagamento de {} foi confirmado pela Ana."
        for a, b in self.NOTATIONS:
            report = compare(base.format(a), base.format(b))
            self.assertNotIn(report["status"], UNSAFE, f"{a} -> {b}: {[i['code'] for i in report['issues']]}")

    def test_a_different_value_is_still_blocked(self):
        base = "O pagamento de {} foi confirmado pela Ana."
        for a, b in [("às 14h", "às 2 da manhã"), ("R$ 1.500,00", "R$ 1.050,00"), ("15 minutos", "meia hora")]:
            self.assertIn(compare(base.format(a), base.format(b))["status"], UNSAFE, f"{a} -> {b}")


class SharedTransformInvariance(unittest.TestCase):
    def test_a_transform_of_both_texts_never_changes_the_verdict(self):
        pairs = suite_pairs()
        self.assertGreater(len(pairs), 200)
        baseline = {name: compare(a, b)["status"] for name, a, b in pairs}
        for label, transform in TRANSFORMS.items():
            changed = [(name, baseline[name], compare(transform(a), transform(b))["status"])
                       for name, a, b in pairs]
            changed = [c for c in changed if c[1] != c[2]]
            self.assertEqual(changed, [], label)

    def test_a_transformed_copy_of_the_original_is_never_blocked(self):
        for name, original, _ in suite_pairs():
            for label, transform in TRANSFORMS.items():
                self.assertNotIn(compare(original, transform(original))["status"], UNSAFE, f"{label} {name}")


class UserTextIsReturnedAsGiven(unittest.TestCase):
    def test_returned_original_keeps_the_users_bytes(self):
        # Analysis runs on a canonical copy; what the user gets back is untouched.
        text = unicodedata.normalize("NFD", "O deploy não deve ser feito antes das 18h.").replace(" ", " ", 1)
        bad = "<final>O deploy deve ser feito antes das 18h.</final>"
        result = rewrite(text, route(text), StaticProvider([bad] * 3), force=True, attempts=1)
        self.assertEqual(result["outcome"], "returned_original")
        self.assertEqual(result["text"], text)


if __name__ == "__main__":
    unittest.main()
