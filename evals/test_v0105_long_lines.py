"""v0.10.5 V105-GAP-14: a long document with one article per line and no blank line (the full text of a law, as
published) was a single long-form unit of 12 thousand words. Found by the long-document flow of the fire trial;
the regulation below is invented, in another domain, with the same shape."""
import unittest

from voznativa import document, longform


def regulation(articles: int = 90) -> str:
    lines = ["REGULAMENTO DO CLUBE DE CICLISMO", "CAPÍTULO I", "DAS DISPOSIÇÕES GERAIS"]
    for n in range(1, articles + 1):
        lines.append(f"Art. {n}. O associado que usar a pista no turno {n} deve registrar a bicicleta na portaria, "
                     f"apresentar o cartão de sócio e respeitar o limite de velocidade fixado pela diretoria:")
        lines.append("I - nos dias de semana, até as vinte horas;")
        lines.append("II - nos fins de semana, até as dezoito horas.")
    return "\n".join(lines) + "\n"


class LongLines(unittest.TestCase):
    def test_defect_one_article_per_line_is_segmented(self):
        text = regulation()
        self.assertGreater(len(text.split()), 3000)
        seg = longform.segment(text, 600)
        self.assertGreater(len(seg["segments"]), 4)          # v0.10.0: 1 segment of the whole text
        self.assertEqual(seg["oversize"], [])
        plan = document.build_plan(text)
        self.assertGreater(len(plan["units"]), 4)
        self.assertEqual(document.validate_plan(plan, text), [])
        self.assertEqual(document.reassemble(text, plan), text)

    def test_cuts_fall_on_line_ends_that_close_a_clause(self):
        text = regulation()
        for s in longform.segment(text, 600)["segments"][1:]:
            before = text[:s["start"]].rstrip("\n")
            self.assertRegex(before[-1], r"[.;:]|[A-Z]", before[-80:])

    def test_control_hard_wrapped_prose_is_not_cut_mid_sentence(self):
        sentence = ("o barqueiro contou que a travessia levava a tarde inteira e que ninguém, nem mesmo o velho "
                    "pescador da enseada, sabia dizer quando a maré voltaria a subir")
        words = (sentence + " ") * 40
        wrapped, line = [], []
        for w in words.split():
            line.append(w)
            if len(" ".join(line)) > 60:
                wrapped.append(" ".join(line))
                line = []
        wrapped.append(" ".join(line) + ".")
        text = "\n".join(wrapped)
        self.assertEqual(len(longform.blocks(text, split_over=600)), 1)

    def test_control_a_big_table_keeps_its_protection(self):
        rows = "\n".join(f"| turno {n} | pista {n % 3} | vinte horas e trinta minutos de uso livre |"
                         for n in range(160))
        bs = longform.blocks(rows, split_over=600)
        self.assertEqual([b.kind for b in bs], ["table"])

    def test_control_without_split_over_blocks_are_unchanged(self):
        text = regulation()
        self.assertEqual(len(longform.blocks(text)), 1)


if __name__ == "__main__":
    unittest.main()
