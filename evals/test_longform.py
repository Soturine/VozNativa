"""v0.6.0 long texts: the dependency map sees what a cut would break,
segmentation is lossless and never cuts a visible dependency without saying
so, verse is recognised (and hard-wrapped prose is not verse), and the
literary policy keeps the planner local or out of verse."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import longform as lf  # noqa: E402
from voznativa.patterns import detect  # noqa: E402
from voznativa.planner import plan  # noqa: E402
from voznativa.router import route  # noqa: E402

REPORT = """# Relatório de entregas

A Agência Nacional de Transportes (ANTT) publicou o edital em março.

Isso mudou o cronograma do projeto inteiro, porque a licitação passou a exigir dois lotes.

O ANTT também pediu os anexos a seguir:

- planilha de custos;
- cronograma físico.

Como dito acima, a entrega final fica para junho."""

POEM = """Musa consoladora,
Quando da minha fronte de mancebo
A última ilusão cair, bem como
Folha amarela e seca

Que ao chão atira a viração do outono,
Ah! no teu seio amigo
Acolhe-me, e haverá minha alma aflita,
Em vez de algumas ilusões que teve,
A paz, o último bem."""

WRAPPED = """Uma noite destas, vindo da cidade para o Engenho Novo, encontrei no
trem da Central um rapaz aqui do bairro, que eu conheço de vista e
de chapéu. Cumprimentou-me, sentou-se ao pé de mim, falou da lua e
dos ministros, e acabou recitando-me versos."""

DIALOGUE = "\n\n".join(["-- Você vem amanhã?", "-- Talvez venha, se a chuva deixar.", "-- Venha, a casa é sua.",
                        "Ela sorriu e não disse mais nada."])


class DependencyMap(unittest.TestCase):
    def test_kinds_and_dependencies(self):
        bs = lf.dependency_map(REPORT)
        self.assertEqual([b.kind for b in bs], ["heading", "prose", "prose", "prose", "list", "prose"])
        deps = {b.index: {r for _, r in b.depends_on} for b in bs}
        self.assertIn("opening_points_back", deps[2])            # "Isso mudou..."
        self.assertIn("acronym:ANTT", deps[3])                   # defined in paragraph 1
        self.assertIn("previous_announces_this", deps[4])        # "...os anexos a seguir:"
        self.assertIn("backward_reference", deps[5])             # "Como dito acima"
        self.assertEqual(deps[1], set())

    def test_verse_dialogue_and_wrapped_prose(self):
        self.assertEqual({b.kind for b in lf.blocks(POEM)}, {"verse"})
        self.assertEqual({b.kind for b in lf.blocks(WRAPPED)}, {"prose"})     # hard-wrapped prose is not verse
        kinds = [b.kind for b in lf.blocks(DIALOGUE)]
        self.assertEqual(kinds, ["dialogue", "dialogue", "dialogue", "prose"])
        self.assertEqual(lf.blocks("*   *   *")[0].kind, "separator")
        self.assertGreaterEqual(lf.verse_share(POEM), 0.99)
        self.assertEqual(lf.verse_share(WRAPPED), 0.0)


class Segmentation(unittest.TestCase):
    def long_text(self):
        paras = []
        for chapter in range(6):
            paras.append(f"CAPÍTULO {chapter + 1}")
            for k in range(8):
                opener = "Isso" if k % 3 == 1 else "O narrador"
                paras.append(f"{opener} conta, no parágrafo {k} do capítulo {chapter}, uma lembrança da casa "
                             "velha, do quintal e das tardes de chuva que ninguém mais lembra. " * 3)
        return "\n\n".join(paras)

    def test_lossless_and_cuts_only_at_safe_boundaries(self):
        text = self.long_text()
        for max_words in (200, 400, 900):
            seg = lf.segment(text, max_words)
            self.assertEqual("".join(text[s["start"]:s["end"]] for s in seg["segments"]), text)
            report = lf.boundary_report(text, max_words)
            self.assertEqual(report["unreported"], 0)
            self.assertEqual(report["cuts_on_dependency"], report["forced_cuts"])

    def test_a_chain_longer_than_twice_the_limit_is_cut_and_reported(self):
        chain = "\n\n".join(["O começo da história, com muitos detalhes sobre a casa e o quintal. " * 5]
                            + ["Isso continua a mesma história, sem pausa nenhuma entre os parágrafos. " * 5] * 12)
        seg = lf.segment(chain, 100)
        self.assertTrue(seg["forced_cuts"])
        self.assertEqual("".join(chain[s["start"]:s["end"]] for s in seg["segments"]), chain)

    def test_carry_lists_names_introduced_earlier(self):
        text = "\n\n".join(["Na casa ao lado morava Capitu, filha do vizinho. " * 25,
                            "Naquela manhã chegou Bentinho, cedo como sempre. " * 25,
                            "Depois saíram juntos, Capitu e Bentinho, pela rua de cima. " * 10])
        seg = lf.segment(text, 200)
        self.assertGreaterEqual(len(seg["segments"]), 2)
        self.assertIn("Capitu", seg["segments"][-1]["carry"])

    def test_limit_floor(self):
        with self.assertRaises(ValueError):
            lf.segment("x", 10)


class LiteraryPolicy(unittest.TestCase):
    def test_policies(self):
        self.assertEqual(lf.literary_policy(POEM, "literary")["policy"], "verse")
        self.assertIsNone(lf.literary_policy(POEM, "unknown")["max_scope"])
        self.assertEqual(lf.literary_policy(POEM, "unknown", explicit=True)["max_scope"], "local")
        self.assertEqual(lf.literary_policy(WRAPPED, "literary")["max_scope"], "local")
        self.assertEqual(lf.literary_policy(WRAPPED, "email")["policy"], "default")

    def test_literary_text_keeps_period_spelling_and_characters_forms_of_address(self):
        text = ("-- O senhor não sabe o facto, disse ela. Você ainda não leu a carta?\n\n"
                "-- Li a acção toda, respondeu o tio, e o projecto não me agrada.")
        literary = detect(text, "literary")
        self.assertNotIn("strong", {f["strength"] for f in literary["findings"] if f["id"] == "pt_pt_variant"})
        self.assertNotIn("treatment_mixed", {f["id"] for f in literary["findings"]})
        unknown = detect(text, "unknown")                       # without the genre, the findings stay
        self.assertIn("strong", {f["strength"] for f in unknown["findings"] if f["id"] == "pt_pt_variant"})
        self.assertIn("treatment_mixed", {f["id"] for f in unknown["findings"]})

    def test_literary_notes_never_decide_or_get_acted_on(self):
        # ptbr-bench-v4 bv4-lt-03: three weak PT-PT notes in a short dialogue reached the weak threshold.
        text = ("-- O senhor não sabe o facto, disse ela. Você ainda não leu a carta?\n\n"
                "-- Li a acção toda, respondeu o tio, e o projecto não me agrada nada.")
        report = detect(text, "literary")
        notes = [f for f in report["findings"] if f["id"] == "pt_pt_variant"]
        self.assertEqual(len(notes), 3)
        self.assertTrue(all(f.get("note_only") for f in notes))
        self.assertEqual(report["decision"], "no_change_candidate")
        p = plan(text, route(text, genre="literary"))
        self.assertEqual(p["decision"], "no_change")
        self.assertFalse(any(r["reasons"] for r in p["sentences"]))

    def test_planner_leaves_verse_alone_without_an_explicit_request(self):
        poem = POEM + "\n\nÉ importante ressaltar que, no cenário atual, cabe destacar a relevância do tema."
        p = plan(poem, route(poem))
        self.assertEqual(p["literary"]["policy"], "verse")
        self.assertEqual(p["decision"], "no_change")


if __name__ == "__main__":
    unittest.main()
