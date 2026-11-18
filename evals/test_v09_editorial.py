"""v0.9 CP3 (V09-GAP-09): editorial consistency across the units of a long document.

Synthetic fixtures (irrigation and farm records), written for this test. The
real case that motivated the rule is recorded only as counts in
docs/releases/v0.9/EDITORIAL.md.

* ``convergence`` flags openers the rewrite added across units; the author's
  own repeated openers, openers added by one unit only, and article openings
  left by a cut formula are not flagged;
* the long-form engine reports ``style_convergence`` and the outcome is at
  least ``needs_review``; nothing is reverted for style;
* ``EditorialMemory`` tells the next units which openers earlier units
  already added and which spelling of a variable term the document uses; a
  writer that follows the note produces less convergence than one that
  ignores it, with the same gates;
* the memory state holds labels, counts and spellings, never sentences.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import engine  # noqa: E402
from voznativa.document import Limits  # noqa: E402
from voznativa.editorial import EditorialMemory, convergence, openings  # noqa: E402
from voznativa.router import route  # noqa: E402

FENCE = re.compile(r"<<<TEXTO#(\w+)\n(.*)\nTEXTO#\1>>>", re.S)
FORMULA = "É importante destacar que a "
NOUNS = ("técnica", "rotina", "medida", "escala", "prática")

# Five units at segment_words=14; each paragraph has one formula the planner flags.
DOC = "\n\n".join(
    f"É importante destacar que a {noun} garante a umidade do canteiro {n} durante a estiagem de março."
    for n, noun in enumerate(NOUNS, 1)) + "\n"


class Writer:
    """Writer stub: replaces the formula by the demonstrative opener ("Essa técnica garante ..."),
    the convergence seen in the second v0.8.1 dogfood. ``obey`` makes it follow the editorial
    memory note instead (plain article opener)."""
    id = "writer-stub"

    def __init__(self, obey: bool):
        self.obey, self.prompts = obey, []

    def generate(self, prompt, n=1):
        self.prompts.append(prompt)
        body = FENCE.search(prompt).group(2)
        avoid = self.obey and "verbo de efeito" in prompt.split("MEMÓRIA EDITORIAL", 1)[-1] \
            if "MEMÓRIA EDITORIAL" in prompt else False
        out = body.replace(FORMULA, "A " if avoid else "Essa ")
        return [f"<final>{out}</final>"] * n


def run(obey: bool, doc: str = DOC):
    writer = Writer(obey)
    result = engine.rewrite_document(doc, route(doc, genre="technical"), writer, limits=Limits(segment_words=14),
                                     force=True)
    return result, writer


class Convergence(unittest.TestCase):

    def test_openers_added_across_units_are_flagged(self):
        original = "Texto. " * 2 + "\n\n".join(f"A {n} garante o canteiro." for n in NOUNS)
        final = "Texto. " * 2 + "\n\n".join(f"Essa {n} garante o canteiro." for n in NOUNS)
        pairs = [(f"A {n} garante o canteiro.", f"Essa {n} garante o canteiro.") for n in NOUNS]
        flags = convergence(original, final, pairs)
        self.assertEqual([(f["opening"], f["original"], f["final"], f["units_adding"]) for f in flags],
                         [("demonstrative_effect", 0, 5, 5)])

    def test_the_authors_own_openers_are_not_flagged(self):
        text = "\n\n".join(f"Essa {n} garante o canteiro." for n in NOUNS)
        self.assertEqual(convergence(text, text, [(text, text)]), [])
        # the rewrite adds two more to an author who already used five: below twice the original
        more = text + "\n\nEssa poda garante luz.\n\nEssa adubação garante nutrientes."
        self.assertEqual(convergence(text, more), [])

    def test_openers_added_by_a_single_unit_are_not_flagged(self):
        src = "A técnica garante água. A rotina garante luz. A medida garante sombra."
        cand = "Essa técnica garante água. Essa rotina garante luz. Essa medida garante sombra."
        self.assertEqual(convergence(src, cand, [(src, cand)]), [])
        self.assertEqual(len(convergence(src, cand)), 1, "without unit information the count alone decides")

    def test_article_openings_left_by_cut_formulas_are_not_openers(self):
        original = " ".join(f"É importante destacar que o lote {n} chegou." for n in range(6))
        final = " ".join(f"O lote {n} chegou." for n in range(6))
        self.assertEqual(openings(final), {})
        self.assertEqual(convergence(original, final), [])

    def test_effect_verbs_are_verb_forms_only(self):
        self.assertEqual(openings("Essa representação mostra o fluxo. Essa demonstração é curta."),
                         {"demonstrative": 2})
        self.assertEqual(openings("Isso contribui para a colheita. Essa poda favoreceu a floração."),
                         {"demonstrative_effect": 2})


class LongFormEngine(unittest.TestCase):

    def test_convergence_without_memory_effect_is_a_signal(self):
        result, _ = run(obey=False)
        kinds = [g["kind"] for g in result["guards"]["introduced"]]
        self.assertIn("style_convergence", kinds)
        self.assertEqual(result["outcome"], "needs_review")
        self.assertEqual(openings(result["text"])["demonstrative_effect"], 5)
        self.assertEqual(result["reverted_units"], [], "style is a signal, not a reason to revert")

    def test_a_writer_that_follows_the_memory_converges_less(self):
        ignored, w_ignored = run(obey=False)
        followed, w_followed = run(obey=True)
        self.assertEqual(openings(followed["text"])["demonstrative_effect"], 2)  # units 1-2 before the note
        self.assertNotIn("style_convergence", [g["kind"] for g in followed["guards"]["introduced"]])
        notes = ["MEMÓRIA EDITORIAL" in p for p in w_followed.prompts]
        self.assertEqual(notes, [False, False, True, True, True])
        self.assertEqual(followed["editorial_memory"]["avoid"], ["demonstrative_effect"])
        self.assertEqual(ignored["editorial_memory"]["openers_added"], {"demonstrative_effect": 5})

    def test_memory_carries_the_documents_spelling_of_a_variable_term(self):
        doc = ("É importante destacar que o backend da estação registra a umidade a cada hora.\n\n"
               "É importante destacar que o backend envia o resumo diário para a cooperativa.\n")
        _, writer = run(obey=False, doc=doc)
        self.assertTrue(writer.prompts)
        self.assertTrue(all("use exatamente esta forma): backend." in p for p in writer.prompts))

    def test_memory_state_holds_no_sentence(self):
        memory = EditorialMemory.for_document("O backend registra a umidade.")
        memory.record("A técnica garante água.", "Essa técnica garante água.")
        state = memory.state()
        self.assertEqual(state["schema_version"], 1)
        self.assertNotIn("técnica", str(state))
        self.assertNotIn("umidade", str(state))
        self.assertEqual(state["spellings"], {"backend": "backend"})


if __name__ == "__main__":
    unittest.main()
