"""Entry-point checks for the Skill's HTML delivery and the text it represents."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class EditorialHtml(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.report = str(self.folder / "revisao.html")

    def file(self, name, value):
        path = self.folder / name
        path.write_text(value, encoding="utf-8")
        return str(path)

    def cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, "-m", "voznativa", *args], input=stdin,
                              capture_output=True, encoding="utf-8")

    def html(self):
        return Path(self.report).read_text(encoding="utf-8")

    def test_compare_preserves_gate_and_escapes_literal_text(self):
        before = self.file("antes.txt", "O relatório  não deve sair às 18h.")
        after = self.file("depois.txt", "O relatório não deve sair às 18h.")
        notes = self.file("notas.json", json.dumps([
            {"before": "  ", "after": " ", "reason": '<img src=x onerror="alert(1)">'},
        ]))
        gate = self.cli("compare", before, after)
        saved = self.cli("compare", before, after, "--html-out", self.report, "--editorial-notes", notes)
        self.assertEqual((saved.returncode, saved.stdout), (gate.returncode, gate.stdout))
        html = self.html()
        self.assertIn("Variação de superfície", html)
        self.assertIn("<del>  </del>", html)
        self.assertIn('<a class="jump" href="#mudanca-1">', html)
        self.assertIn("&lt;img src=x", html)
        self.assertNotIn("<img src=x", html)
        existing = self.cli("compare", before, after, "--html-out", self.report)
        self.assertEqual(existing.returncode, 64)
        self.assertEqual(self.html(), html)

    def test_rejected_candidate_marks_original_as_delivered(self):
        before = self.file("antes.txt", "As inscrições encerram às 18h.")
        after = self.file("depois.txt", "As inscrições encerram às 20h.")
        run = self.cli("compare", before, after, "--kept-original", "--html-out", self.report)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"], "fail")
        self.assertIn("Candidata reprovada", self.html())
        self.assertIn("Entrega: original mantido.", self.html())
        self.assertIn('data-side="before"', self.html())

    def test_ground_keeps_request_out_of_before_column(self):
        request = self.file("pedido.txt", "Escreva sobre o plantão. A equipe atende às 18h.")
        candidate = self.file("candidata.txt", "A equipe atende às 18h.")
        run = self.cli("ground", candidate, "--request", request, "--html-out", self.report)
        self.assertEqual(run.returncode, 3, run.stderr)
        self.assertIn("Candidata de criação", self.html())
        self.assertNotIn("Escreva sobre o plantão", self.html())

    def test_rewrite_stdin_and_protected_formal_correction(self):
        text = "Avisamos que fazem dois anos desde a mudança."
        run = self.cli("rewrite", "-", "--mode", "PROOFREAD", "--protect", "fazem dois anos",
                       "--html-out", self.report, stdin=text)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(json.loads(run.stdout)["text"], text)
        self.assertIn("Candidata reprovada", self.html())

    def test_proofread_records_the_applied_correction(self):
        run = self.cli("rewrite", "-", "--mode", "PROOFREAD", "--html-out", self.report,
                       stdin="O relatório foi enviado para o o cliente.")
        self.assertEqual(run.returncode, 3, run.stderr)
        self.assertIn("Correção formal detectada pelo PROOFREAD", self.html())

    def test_no_change_records_the_decision(self):
        path = self.file("original.txt", "A oficina começa amanhã.")
        reason = "O aviso já informa quando a oficina começa."
        run = self.cli("compare", path, path, "--delivery-reason", reason, "--html-out", self.report)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(reason, self.html())
        self.assertIn("Sem alterações", self.html())

    def test_long_unbroken_text_highlights_only_the_local_edit(self):
        from voznativa.editorial_report import render

        prefix = "O trecho anterior continua aqui. " * 400
        suffix = " O trecho seguinte continua aqui." * 400
        html = render(prefix + "Antes" + suffix, prefix + "Depois" + suffix, {"status": "review_required"})
        self.assertIn("<del>Antes</del>", html)
        self.assertIn("<ins>Depois</ins>", html)

    def test_plan_stdin_matches_file_with_explicit_context(self):
        text = "É importante destacar que a reunião começa amanhã."
        path = self.file("fonte.txt", text)
        args = ("--attr", "pedido=deixe mais direto")
        file_result = self.cli("plan", path, *args)
        input_result = self.cli("plan", "-", *args, stdin=text)
        self.assertEqual(input_result.returncode, 0, input_result.stderr)
        self.assertEqual(json.loads(input_result.stdout), json.loads(file_result.stdout))
