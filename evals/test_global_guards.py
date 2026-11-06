"""v0.7.0 CP9: global semantic guards, metamorphic stability and document guards.

The cross-paragraph probes were run before the fixes: negation moved between
sentences, a dependent paragraph moved and a short added sentence all came
out as no_deterministic_issues (false greens). Controls must stay clean."""
import sys
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import engine  # noqa: E402
from voznativa.compare import compare  # noqa: E402
from voznativa.document import Limits  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.planner import plan  # noqa: E402
from voznativa.router import route  # noqa: E402

P1 = "A empresa contratou João em março.\n\n"
P2 = "O contrato não prevê multa se o atraso for menor que 5 dias.\n\n"
P3 = "Por isso, a auditoria deve terminar até 30/06/2025."
SRC = P1 + P2 + P3


def codes(a, b):
    r = compare(a, b)
    return r["status"], {i["code"] for i in r["issues"]}


class CrossParagraph(unittest.TestCase):
    def test_negation_moved_between_sentences_fails(self):
        moved = P1.replace("contratou", "não contratou") + P2.replace("não prevê", "prevê") + P3
        status, found = codes(SRC, moved)
        self.assertEqual(status, "fail")
        self.assertIn("negation_moved", found)

    def test_dependent_paragraph_moved_needs_review(self):
        status, found = codes(SRC, P2 + P1 + P3)
        self.assertEqual(status, "review_required")
        self.assertIn("dependent_sentence_moved", found)

    def test_short_added_sentence_needs_review(self):
        status, found = codes(SRC, SRC + "\n\nEle assinou o termo.")
        self.assertIn("possible_addition", found)
        self.assertNotEqual(status, "no_deterministic_issues")

    def test_rephrased_sentence_keeps_its_value_and_its_negation_is_localized(self):
        # Found while writing the README demo (VN07-DISC-035): the rephrasing lowered
        # lexical similarity, the negation was not localized and only asked for review.
        src = ("É importante destacar que o relatório será enviado até sexta-feira, 14/11/2025. "
               "Vale ressaltar que o orçamento não pode ultrapassar R$ 12.000,00.")
        bad = "O relatório vai até sexta-feira, 14/11/2025. O orçamento pode passar de R$ 12.000,00."
        good = "O relatório vai até sexta-feira, 14/11/2025. O orçamento não pode passar de R$ 12.000,00."
        self.assertEqual(codes(src, bad)[0], "fail")
        self.assertIn("negation_changed", codes(src, bad)[1])
        self.assertNotEqual(codes(src, good)[0], "fail")

    def test_known_detections_still_fire(self):
        self.assertEqual(codes(SRC, P1 + "O contrato não prevê multa.\n\n" + P3)[0], "fail")       # condition
        self.assertEqual(codes(SRC, P1 + P2 + P3.replace("30/06", "30/07"))[0], "fail")             # far value
        self.assertEqual(codes(SRC, P1 + P2 + P3.replace("deve terminar", "terminará"))[0], "fail")  # modality
        self.assertIn("role_or_order_swapped", codes(SRC, "João contratou a empresa em março.\n\n" + P2 + P3)[1])

    def test_controls_stay_clean(self):
        for candidate in (
                P1 + "O contrato não prevê multa. Isso vale se o atraso for menor que 5 dias.\n\n" + P3,  # split
                "Em março, a empresa contratou João.\n\n" + P2 + "Por isso, a auditoria precisa terminar até "
                "30/06/2025.",                                                                         # reword
                "João foi contratado pela empresa em março.\n\n" + P2 + P3):                            # passive
            self.assertEqual(codes(SRC, candidate)[0], "no_deterministic_issues", candidate)


VARIANTS = {
    "crlf": lambda t: t.replace("\n", "\r\n"),
    "nfd": lambda t: unicodedata.normalize("NFD", t),
    "nbsp": lambda t: t.replace(" ", " "),
    "wrap": lambda t: t.replace(", a equipe", ",\na equipe").replace(" antes de", "\nantes de"),
    "tab_blank_line": lambda t: t.replace("\n\n", "\n\t\n"),
    "double_space": lambda t: t.replace(". ", ".  "),
}
META_SRC = ("É importante destacar que o contrato não será renovado antes de 15/03/2025.\n"
            "Caso o cliente pague R$ 1.200,00 até sexta-feira, a equipe poderá entregar 3 relatórios.\n\n"
            "A diretoria aprovou o orçamento, mas o prazo depende da auditoria.")
META_CAND = ("O contrato não será renovado antes de 15/03/2025.\n"
             "Se o cliente pagar R$ 1.200,00 até sexta-feira, a equipe poderá entregar 3 relatórios.\n\n"
             "A diretoria aprovou o orçamento, mas o prazo depende da auditoria.")


class Metamorphic(unittest.TestCase):
    def test_formatting_does_not_change_verdicts(self):
        base_cmp = codes(META_SRC, META_CAND)
        base_plan = plan(META_SRC, route(META_SRC))
        base_pat = sorted(f["id"] for f in detect(META_SRC, "corporate")["findings"])
        for name, f in VARIANTS.items():
            with self.subTest(variant=name):
                self.assertEqual(codes(f(META_SRC), f(META_CAND)), base_cmp)
                self.assertEqual(codes(META_SRC, f(META_CAND)), base_cmp)
                p = plan(f(META_SRC), route(f(META_SRC)))
                self.assertEqual((p["decision"], p["scope"]), (base_plan["decision"], base_plan["scope"]))
                self.assertEqual(sorted(x["id"] for x in detect(f(META_SRC), "corporate")["findings"]), base_pat)

    def test_negative_control_a_semantic_change_is_not_formatting(self):
        self.assertEqual(codes(META_SRC, META_CAND.replace("não será", "será"))[0], "fail")


class DocumentGuards(unittest.TestCase):
    DOC = "\n\n".join(f"É importante destacar que o lote {i} chegou sem atraso ao cliente da filial." for i in range(6))

    def test_slang_introduced_anywhere_in_the_document_needs_review(self):
        class Slangy:
            id = "slangy"

            def generate(self, prompt, n=1):
                import re
                body = re.search(r"<<<TEXTO#(\w+)\n(.*)\nTEXTO#\1>>>", prompt, re.S).group(2)
                return ["<final>" + body.replace("É importante destacar que o", "Mano, o") + "</final>"] * n
        result = engine.rewrite_document(self.DOC, route(self.DOC, genre="corporate"), Slangy(),
                                         limits=Limits(segment_words=50), force=True)
        # The unit gates let the candidate through as review (slang is "major"), so the
        # document changes; the document guard must then see the slang and keep it in review.
        self.assertNotEqual(result["text"], self.DOC)
        self.assertEqual(result["outcome"], "needs_review")
        self.assertEqual({a["id"] for a in result["guards"]["introduced"]}, {"mano"})
        self.assertEqual(result["guards"]["equivalence"].split()[0], "unverified")


if __name__ == "__main__":
    unittest.main()
