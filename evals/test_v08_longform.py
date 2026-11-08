"""v0.8 CP7: long documents end to end after the GAP-13 and GAP-12 fixes.

* A clean rewrite of a document that quotes "pode" / "não pode" twins in
  different units must be kept: before CP7a the global validation saw a
  false negation_moved and reverted every unit (returned_original).
* One document with every block kind: which units reach the model with and
  without the verse authorisation, and byte equality of everything protected.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import engine  # noqa: E402
from voznativa.document import Limits, build_plan  # noqa: E402
from voznativa.router import route  # noqa: E402

FENCE = re.compile(r"<<<TEXTO#(\w+)\n(.*)\nTEXTO#\1>>>", re.S)
FORMULAS = ("É importante destacar que ", "Vale ressaltar que ")


class Cleaner:
    """Removes the two formulas from whatever unit it receives; records the units."""
    id = "cleaner-stub"

    def __init__(self):
        self.units = []

    def generate(self, prompt, n=1):
        body = FENCE.search(prompt).group(2)
        self.units.append(body)
        out = body
        for formula in FORMULAS:
            out = re.sub(re.escape(formula) + r"(\w)", lambda m: m.group(1).upper(), out)
        return [f"<final>{out}</final>"] * n


# Two pairs of twins in opposite orders (positive first, then negative first), each in
# different units: the shape that made the old alignment report a false negation_moved.
TWINS = ("# Notas da reunião\n\n"
         "É importante destacar que o relatório será enviado na segunda-feira para a diretoria.\n\n"
         "O orçamento pode passar de R$ 12.000,00.\n\n"
         "O deploy não deve ser feito antes das 18h.\n\n"
         "## Exemplos citados\n\n"
         "Vale ressaltar que a ata será publicada na terça-feira.\n\n"
         "O orçamento não pode passar de R$ 12.000,00.\n\n"
         "O deploy deve ser feito antes das 18h.\n")


class TwinsAcrossUnits(unittest.TestCase):

    def test_a_clean_rewrite_is_not_reverted(self):
        stub = Cleaner()
        result = engine.rewrite_document(TWINS, route(TWINS), stub, limits=Limits(segment_words=12))
        self.assertGreater(len(build_plan(TWINS, limits=Limits(segment_words=12))["units"]), 2)
        self.assertEqual(result["reverted_units"], [], result.get("global_report"))
        self.assertNotEqual(result["outcome"], "returned_original", result.get("reason"))
        self.assertNotIn("É importante destacar", result["text"])
        self.assertIn("O orçamento não pode passar de R$ 12.000,00.", result["text"])
        self.assertIn("O deploy não deve ser feito antes das 18h.", result["text"])
        # Edits were kept, so the whole document was validated: the report must exist (no conditional check).
        self.assertIsNotNone(result["global_report"])
        self.assertNotEqual(result["global_report"]["status"], "fail")


MIXED = ("# Relatório anual\n\n"
         "É importante destacar que a equipe entregou a versão 2.1 em 14/11/2025.\n\n"
         "- primeira entrega no prazo\n- segunda entrega com atraso\n\n"
         "— Vamos revisar amanhã? — perguntou Ana.\n— Vamos — respondeu Bruno.\n\n"
         "Rosa que não se abre\nguarda o seu perfume\nno silêncio da manhã\n\n"
         "```\ndeploy --env prod\n```\n\n"
         "| item | valor |\n|---|---|\n| servidor | R$ 900,00 |\n\n"
         "> Nada muda sem o comitê, disse a diretora.\n\n"
         "---\n\n"
         "Vale ressaltar que o orçamento não pode passar de R$ 12.000,00.\n")
PROTECTED = ("```\ndeploy --env prod\n```", "| item | valor |\n|---|---|\n| servidor | R$ 900,00 |",
             "> Nada muda sem o comitê, disse a diretora.", "\n---\n")
VERSE = "Rosa que não se abre\nguarda o seu perfume\nno silêncio da manhã"


class MixedDocument(unittest.TestCase):

    def run_doc(self, text, verse_explicit):
        # force: every rewritable unit goes to the model, so "never sent" means "never eligible"
        # (without force the planner rightly skips units with nothing to edit, verse included).
        stub = Cleaner()
        result = engine.rewrite_document(text, route(text), stub, limits=Limits(segment_words=15),
                                         verse_explicit=verse_explicit, force=True)
        return result, stub

    def test_protected_blocks_never_reach_the_model_and_keep_their_bytes(self):
        for text in (MIXED, MIXED.replace("\n", "\r\n")):
            for grant in (False, True):
                with self.subTest(crlf="\r\n" in text, verse=grant):
                    result, stub = self.run_doc(text, grant)
                    sent = "\n".join(stub.units).replace("\r\n", "\n")
                    for block in PROTECTED:
                        self.assertNotIn(block.strip(), sent)
                        self.assertIn(block.replace("\n", "\r\n") if "\r\n" in text else block, result["text"])
                    self.assertEqual(VERSE in sent, grant, "verse reaches the model only when authorised")
                    self.assertNotIn("É importante destacar", result["text"])
                    self.assertIn("R$ 12.000,00", result["text"])

    def test_without_a_change_the_document_is_byte_identical(self):
        class Echo:
            id = "echo"

            def generate(self, prompt, n=1):
                return ["<final>" + FENCE.search(prompt).group(2) + "</final>"] * n

        for text in (MIXED, MIXED.replace("\n", "\r\n")):
            result = engine.rewrite_document(text, route(text), Echo(), limits=Limits(segment_words=15), force=True)
            self.assertEqual(result["text"], text)


if __name__ == "__main__":
    unittest.main()
