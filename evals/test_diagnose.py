"""v0.7.0 CP9D: original-error awareness and editorial modes.

The original is evidence of intent, not proof of correctness; a diagnosis
is never applied unless the mode authorises it and it is formal."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.diagnose import diagnose, mode_policy, proofread  # noqa: E402
from voznativa.router import route  # noqa: E402


def classes(text, **kw):
    return {(d["class"], d["type"]) for d in diagnose(text, route(text), **kw)["diagnostics"]}


class ErrorClasses(unittest.TestCase):
    def test_formal_error_in_prose(self):
        found = classes("O relatório foi enviado para o o cliente ontem.")
        self.assertIn(("formal_error", "repeated_word"), found)

    def test_reduplication_that_is_portuguese_is_not_an_error(self):
        self.assertEqual(classes("Ele chegou bem bem cedo e saiu logo logo depois."), set())

    def test_repetition_in_verse_is_literary_license(self):
        poem = "Sozinho, sozinho no cais\nE a noite, a noite que não volta mais\nO mar, o mar que não para\n"
        verse = "Canto canto a mesma canção\nE a onda onda volta ao chão\nNo cais cais da solidão\n"
        found = classes(verse)
        self.assertTrue(found)
        self.assertTrue(all(c == "literary_license" for c, _ in found), found)
        self.assertNotIn("formal_error", {c for c, _ in classes(poem)})

    def test_internal_contradictions(self):
        found = classes("A reunião será na segunda-feira, 12/11/2026, às 10h.")   # 12/11/2026 is a Thursday
        self.assertIn(("internal_contradiction", "weekday_date_mismatch"), found)
        found = classes("A Agência Nacional de Águas (ANA) abriu o edital. Depois, a Associação Nacional "
                        "dos Advogados (ANA) contestou.")
        self.assertIn(("internal_contradiction", "acronym_redefined"), found)

    def test_historical_spelling_is_a_legitimate_choice(self):
        found = classes("Elle voltou no anno passado e trouxe a pharmacia para a cidade.")
        self.assertIn(("legitimate_choice", "historical_spelling"), found)
        self.assertNotIn("formal_error", {c for c, _ in found})

    def test_tense_switch_is_an_ambiguity_not_an_error(self):
        found = classes("Ana abriu a porta. Ana entra na sala e acende a luz.")
        self.assertIn(("unresolved_ambiguity", "tense_switch"), found)


class Grounding(unittest.TestCase):
    def test_mismatch_vs_no_evidence(self):
        text = "O contrato custa R$ 1.500,00 e vence em 30/06/2025."
        report = diagnose(text, route(text, genre="corporate"), facts=["O contrato custa R$ 1.200,00."])
        kinds = {d["class"]: d for d in report["diagnostics"]}
        self.assertEqual(kinds["source_mismatch"]["source_value"], "R$ 1.200,00")
        self.assertEqual(kinds["no_evidence"]["severity"], "info", "absence of evidence is not falsity")

    def test_fiction_is_not_checked_against_facts(self):
        text = "Em 1890, o barão pagou 300 contos pela fazenda."
        report = diagnose(text, route(text, genre="literary"), facts=["O barão nunca comprou fazenda alguma."])
        self.assertEqual(report["grounding"], "skipped_fiction")


class Modes(unittest.TestCase):
    TEXT = "O relatório foi enviado para o o cliente, que não aprovou o orçamento."

    def test_preserve_and_review_authorise_nothing(self):
        for mode in ("PRESERVE", "REVIEW"):
            d = diagnose(self.TEXT, route(self.TEXT))
            self.assertEqual(proofread(self.TEXT, d, mode)["text"], self.TEXT)

    def test_proofread_applies_only_formal_fixes(self):
        d = diagnose(self.TEXT, route(self.TEXT))
        out = proofread(self.TEXT, d, "PROOFREAD")
        self.assertEqual(out["text"], "O relatório foi enviado para o cliente, que não aprovou o orçamento.")
        self.assertEqual(len(out["applied"]), 1)

    def test_facts_are_never_automatic(self):
        for mode in ("PROOFREAD", "POLISH", "ADAPT"):
            self.assertIn("facts", mode_policy(mode)["never_automatic"])
        with self.assertRaises(ValueError):
            mode_policy("WHATEVER")

    def test_cli_modes_without_a_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.txt"
            path.write_text(self.TEXT, encoding="utf-8")
            env = dict(__import__("os").environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8")

            def run(*args):
                done = subprocess.run([sys.executable, "-m", "voznativa", *args], cwd=tmp, capture_output=True, env=env)
                return done.returncode, json.loads(done.stdout.decode("utf-8"))
            code, review = run("rewrite", str(path), "--mode", "REVIEW")
            self.assertEqual((code, review["outcome"], review["text"]), (0, "no_change", self.TEXT))
            self.assertTrue(review["diagnosis"]["diagnostics"])
            code, fixed = run("rewrite", str(path), "--mode", "PROOFREAD")
            self.assertNotIn("o o cliente", fixed["text"])
            self.assertIn(fixed["outcome"], {"needs_judgment", "needs_review"})
            code, diag = run("diagnose", str(path), "--mode", "PRESERVE")
            self.assertEqual((code, diag["kind"], diag["mode"]["rewrite"]), (0, "voznativa.diagnosis", False))


if __name__ == "__main__":
    unittest.main()
