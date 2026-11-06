"""v0.7.0 CP5: Context Contract v3 and the G1 oracle end to end.

The oracle is not "genre != whatsapp": literature must get the literary
protections (local scope in the planner, PT-PT markers as notes), ambiguous
literary/historical text must keep them while abstaining, and real chat must
still route as chat. Cases in evals/router/cases-v07.jsonl were written and
hashed before the first run of this file (frozen; do not edit to pass)."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import planner  # noqa: E402
from voznativa.longform import literary_policy  # noqa: E402
from voznativa.ptbr import findings as ptbr_findings  # noqa: E402
from voznativa.router import (DIMENSIONS, infer_genre, infer_time_of_text, route,  # noqa: E402
                              unwrap_for_inference)

CASES_PATH = ROOT / "evals" / "router" / "cases-v07.jsonl"
CASES_SHA256 = "5a4db241619b3ec8f6297b024771a3c127096f1e0f089f9d8aa7417d7da68eab"
CASES = [json.loads(line) for line in CASES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

G1 = """Quando cheguei a casa, a tarde ia acabando, e a criada veio dizer-me que
minha tia estava na sala, a conversar com o vigario, um homem gordo e
manso, que a visitava todos os sabbados depois da missa.

--Entra, menino, disse ella, ainda com o rosario na mão.

--Boa tarde, minha tia.

--Senta-te ahi, que o senhor vigario tem uma noticia para ti, e é
noticia boa, ou eu me engano muito com as cousas deste mundo."""


def literary_protection(text: str) -> dict:
    ctx = route(text)
    return literary_policy(text, ctx["genre"]["value"],
                           conservative=ctx["protections"]["conservative"])


class FrozenOracleSuite(unittest.TestCase):
    def test_suite_is_frozen(self):
        self.assertEqual(hashlib.sha256(CASES_PATH.read_bytes()).hexdigest(), CASES_SHA256)
        self.assertGreaterEqual(len(CASES), 14)

    def test_every_case(self):
        for case in CASES:
            with self.subTest(case=case["id"]):
                ctx = route(case["text"])
                genre = ctx["genre"]["value"]
                self.assertIn(genre, case["expect"])
                self.assertNotIn(genre, case["never"])
                if case.get("protections") == "literary_or_conservative":
                    self.assertEqual(literary_protection(case["text"])["max_scope"], "local")
                if case.get("structure"):
                    self.assertEqual(ctx["dimensions"]["structure"]["value"], case["structure"])
                if case.get("structure_not"):
                    self.assertNotEqual(ctx["dimensions"]["structure"]["value"], case["structure_not"])


class G1EndToEnd(unittest.TestCase):
    def test_genre_and_protections(self):
        ctx = route(G1)
        self.assertEqual(ctx["genre"]["value"], "literary")
        self.assertEqual(literary_protection(G1)["policy"], "literary_prose")

    def test_planner_keeps_edits_local(self):
        ctx = route(G1)
        self.assertEqual(planner.plan(G1, ctx)["literary"]["max_scope"], "local")

    def test_historic_spelling_is_dated_and_not_pt_pt(self):
        self.assertEqual(infer_time_of_text(G1)["value"], "pre_reform_orthography")
        ctx = route(G1)
        self.assertEqual(ctx["dimensions"]["language_variant"]["value"], "unknown")
        self.assertTrue(ctx["protections"]["historical_spelling_is_not_an_error"])

    def test_the_original_is_never_changed(self):
        before = str(G1)
        route(G1)
        infer_genre(G1)
        self.assertEqual(G1, before)
        unwrapped, info = unwrap_for_inference(G1)
        self.assertGreater(info["joined_line_breaks"], 0)
        self.assertEqual(unwrapped.replace("\n", " ").split(), G1.replace("\n", " ").split(),
                         "unwrapping only replaces line breaks; no word changes")


class AbstentionKeepsProtections(unittest.TestCase):
    AMBIGUOUS = ("Naquella tarde elle voltou cedo para casa, e a mãe, que o esperava\n"
                 "desde o almoço, perguntou pelo anno de escola sem levantar os olhos\n"
                 "do bordado que fazia na janela.")

    def test_unknown_with_historical_evidence_is_conservative(self):
        ctx = route(self.AMBIGUOUS)
        if ctx["genre"]["value"] == "literary":
            self.assertEqual(literary_protection(self.AMBIGUOUS)["max_scope"], "local")
        else:
            self.assertEqual(ctx["genre"]["value"], "unknown")
            self.assertTrue(ctx["protections"]["conservative"])
            self.assertEqual(literary_protection(self.AMBIGUOUS)["policy"], "conservative_unknown")

    def test_control_unknown_without_evidence_is_not_restricted(self):
        text = "Texto curto sem pistas."
        ctx = route(text)
        self.assertEqual(ctx["genre"]["value"], "unknown")
        self.assertFalse(ctx["protections"]["conservative"])
        self.assertEqual(literary_protection(text)["policy"], "default")


class HistoricSpellingIsNotPtPt(unittest.TestCase):
    def test_marker_becomes_a_note_in_pre_reform_text(self):
        old = "Elle disse que o facto se deu no anno passado, na direcção da cidade."
        modern_pt = "O facto é que a equipa vai jogar amanhã; estou a falar a sério."
        old_notes = [f for f in ptbr_findings(old, "unknown") if f["family"] == "variante PT-PT"]
        pt_notes = [f for f in ptbr_findings(modern_pt, "unknown") if f["family"] == "variante PT-PT"]
        self.assertTrue(old_notes and all(f.get("note_only") for f in old_notes))
        self.assertTrue(pt_notes and not all(f.get("note_only") for f in pt_notes),
                        "control: current PT-PT keeps its strong finding")

    def test_modern_chat_typos_are_not_historic(self):
        self.assertEqual(infer_time_of_text("tambem quero, mae falou q vc vai logar no sistema")["value"], "unknown")


class ChatNeedsCorroboration(unittest.TestCase):
    def test_one_cue_family_is_not_chat(self):
        quoted = "O técnico disse: \"tá tudo certo, né, pra mim o time joga bem\". A diretoria não comentou."
        fragments = "Figura 3 mostra o fluxo.\n\nhtm\n\nfluido de perfuração com aditivos."
        for text in (quoted, fragments):
            g = infer_genre(text)
            self.assertNotEqual(g["value"], "whatsapp", text)

    def test_two_cue_families_are_chat(self):
        self.assertEqual(infer_genre("oi\nvc vai hj?\nnao sei ainda kkk")["value"], "whatsapp")


class ContractV3(unittest.TestCase):
    def test_every_dimension_has_value_source_confidence(self):
        ctx = route("Olá, segue o relatório.", channel="email", register="professional-formal", audience="cliente")
        self.assertEqual(ctx["schema_version"], 3)
        self.assertEqual(sorted(ctx["dimensions"]), sorted(DIMENSIONS))
        for name, dim in ctx["dimensions"].items():
            self.assertTrue({"value", "source", "confidence"} <= set(dim), name)
        self.assertEqual(ctx["dimensions"]["channel"]["source"], "explicit")
        self.assertEqual(ctx["dimensions"]["region_of_text"]["source"], "not_inferred")

    def test_v1_fields_are_kept(self):
        ctx = route("vc viu?? kkk")
        for key in ("task", "genre", "channel", "register", "targets", "flags", "constraints", "sources", "policy"):
            self.assertIn(key, ctx)

    def test_source_names_do_not_change_the_decision(self):
        # Generalization rule 1: nothing depends on an author, source or edition name.
        for name in ("Machado de Assis", "Júlia Lopes de Almeida", "Gutenberg", "Fulano"):
            text = G1 + f"\n\n{name}"
            self.assertEqual(route(text)["genre"]["value"], "literary", name)

    def test_line_endings_and_nbsp_are_irrelevant(self):
        base = route(G1)["genre"]["value"]
        self.assertEqual(route(G1.replace("\n", "\r\n"))["genre"]["value"], base)
        self.assertEqual(route(G1.replace(" ", " ", 5))["genre"]["value"], base)

    def test_long_form_blocks_are_the_same_with_crlf(self):
        from voznativa.longform import blocks
        lf = [b.kind for b in blocks(G1)]
        self.assertEqual([b.kind for b in blocks(G1.replace("\n", "\r\n"))], lf)
        self.assertGreater(len(lf), 1)


if __name__ == "__main__":
    unittest.main()
