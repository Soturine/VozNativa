"""H5: signals.markers was rewritten to try only positions where a phrase can
start. This differential test runs the previous algorithm (kept verbatim
below as the oracle) and the current one on every text the suites and the
benchmarks hold, plus adversarial inputs, and requires identical markers."""
import glob
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import signals  # noqa: E402
from voznativa.signals import (Marker, _clause_initial, _compounds, _negative_concord, _patterns,  # noqa: E402
                               _phrase_matches, _phrases, _TOKEN_RE)
from voznativa.text import fold  # noqa: E402


def reference_markers(text: str) -> list:
    """signals.markers as of 24ba7e2 (scan of every position)."""
    tokens = [(fold(m.group(0)), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]
    folded = [t[0] for t in tokens]
    used = [False] * len(tokens)
    found = []
    for pattern, category, cls in _patterns():
        for m in pattern.finditer(text):
            idx = [i for i, t in enumerate(tokens) if t[1] >= m.start() and t[2] <= m.end()]
            if not idx or any(used[i] for i in idx):
                continue
            for i in idx:
                used[i] = True
            found.append(Marker(category, cls, m.group(0), m.start(), m.end()))
    compounds = _compounds()
    for i, token in enumerate(folded):
        if not used[i] and token in compounds:
            used[i] = True
            for category, cls in compounds[token]:
                found.append(Marker(category, cls, text[tokens[i][1]:tokens[i][2]], tokens[i][1], tokens[i][2]))
    for phrase, category, cls in _phrases():
        n = len(phrase)
        for i in range(len(tokens) - n + 1):
            if any(used[i:i + n]) or not _phrase_matches(phrase, folded[i:i + n]):
                continue
            if phrase == ("se",) and not _clause_initial(folded, i):
                continue
            for j in range(i, i + n):
                used[j] = True
            found.append(Marker(category, cls, text[tokens[i][1]:tokens[i + n - 1][2]],
                                tokens[i][1], tokens[i + n - 1][2]))
    return _negative_concord(sorted(found, key=lambda m: m.start))


def corpus() -> list[str]:
    texts = []
    for path in glob.glob(str(ROOT / "evals" / "**" / "*.jsonl"), recursive=True) + \
            glob.glob(str(ROOT / "benchmarks" / "cases" / "*.jsonl")):
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            case = json.loads(line)
            texts += [v for k, v in case.items() if k in {"original", "candidate", "text"} and isinstance(v, str)]
    for run in glob.glob(str(ROOT / "benchmarks" / "runs" / "*Z.json")):
        texts += [r["output"] for r in json.loads(Path(run).read_text(encoding="utf-8")).get("rows", [])
                  if isinstance(r.get("output"), str)]
    return texts


class MarkersEquivalence(unittest.TestCase):
    def test_same_markers_as_the_reference_on_every_recorded_text(self):
        texts = corpus()
        self.assertGreater(len(texts), 500)
        for text in texts:
            self.assertEqual(signals.markers(text), reference_markers(text), text[:80])

    def test_same_markers_on_adversarial_and_edge_inputs(self):
        for text in ("", "a", "se", "Se não for possível, a não ser que chova, ao menos tente.",
                     "a, " * 300 + "b.", "não " * 200, "aumentou aumento aument", "pelo pela pelos ao à às",
                     "Não afetou nenhum cliente, nem nunca afetará.",
                     # inputs near a phrase's first slot ("na função de", "pela conta de"), absent
                     # from the recorded corpus; a mutant of the position index survived without them.
                     "Ele atua na função de gerente.", "Pagou pela conta de luz.", "Saiu pelo isso mesmo.",
                     "Chegou nas razão de sempre.", "Do jeito nenhum que pediram."):
            self.assertEqual(signals.markers(text), reference_markers(text), text[:40])


if __name__ == "__main__":
    unittest.main()


class FirstSlotContractions(unittest.TestCase):
    """A contraction matches only inside a phrase: "na função de gerente" (in
    the role of) is not "em função de" (because of)."""

    def labels(self, text):
        return [m.label for m in signals.markers(text)]

    def test_contraction_in_the_first_slot_is_not_the_phrase(self):
        self.assertNotIn("causality.causal", self.labels("Ele atua na função de gerente."))
        self.assertNotIn("causality.causal", self.labels("Pagou pela conta de luz."))
        self.assertNotIn("attribution.source", self.labels("Do acordo com a empresa saiu nada."))

    def test_the_phrase_itself_and_inner_contractions_still_match(self):
        self.assertIn("causality.causal", self.labels("Atrasou em função de chuva."))
        self.assertIn("causality.causal", self.labels("Atrasou por conta da chuva."))
        self.assertIn("causality.causal", self.labels("A chuva leva ao atraso."))
