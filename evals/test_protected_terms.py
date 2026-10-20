"""User-protected terms (v0.3.0 M1.8)."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import cli
from voznativa.compare import compare

ORIGINAL = "O Plano Turbo Plus inclui suporte prioritário e vale para a squad Fênix."


class ProtectedTerms(unittest.TestCase):
    def test_lost_protected_term_fails(self):
        # Capitalized names are already protected as entities; the option matters
        # for lower-case terms, which nothing protects by default.
        original = "O modo foco silencia as notificações durante a reunião."
        candidate = "O modo silencia as notificações durante a reunião."
        self.assertNotEqual(compare(original, candidate)["status"], "fail")
        report = compare(original, candidate, protect=["modo foco"])
        self.assertEqual(report["status"], "fail")
        self.assertIn("protected_term", {i.get("type") for i in report["issues"]})

    def test_case_and_position_do_not_matter(self):
        candidate = "Plano Turbo Plus: suporte prioritário, válido para a squad Fênix."
        report = compare(ORIGINAL, candidate, protect=["plano turbo plus"])
        self.assertNotIn("span_missing", {i["code"] for i in report["issues"]})

    def test_whole_word_only(self):
        report = compare("Use o modo Max.", "Use o modo Maxwell.", protect=["Max"])
        self.assertEqual(report["status"], "fail")

    def test_cli_protect_and_protect_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b, terms = Path(tmp, "a.txt"), Path(tmp, "b.txt"), Path(tmp, "terms.txt")
            a.write_text(ORIGINAL, encoding="utf-8")
            b.write_text("O plano inclui suporte prioritário e vale para a squad.", encoding="utf-8")
            terms.write_text("# termos do produto\nPlano Turbo Plus\n", encoding="utf-8")
            for extra in (["--protect", "Plano Turbo Plus"], ["--protect-file", str(terms)]):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    code = cli.main(["compare", str(a), str(b), *extra])
                self.assertEqual(code, 1, extra)
                self.assertEqual(json.loads(buffer.getvalue())["status"], "fail")


if __name__ == "__main__":
    unittest.main()
