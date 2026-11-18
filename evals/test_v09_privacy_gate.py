"""v0.9 CP0: the pre-push privacy gate catches a planted leak and passes a clean range.

Everything here is synthetic (a fictional gardening diary): a throwaway git
repository receives a clean commit and then commits that leak a five-word
sequence of a "private" document, a distinctive identifier, a sensitive term,
a credential-shaped string, a personal path and a personal e-mail address.
"""
import contextlib
import importlib.util
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "privacy_gate.py"

PRIVATE = ("Diário da horta comunitária. As mudas de manjericão roxo foram transplantadas para o canteiro "
           "norte depois da chuva forte de quinta. O lote HORTA_NORTE_7781 recebeu adubo de minhoca.")


def _load():
    spec = importlib.util.spec_from_file_location("privacy_gate_v09", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@unittest.skipUnless(SCRIPT.is_file() and shutil.which("git"), "needs the checkout's scripts/ and git")
class PrivacyGate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo, self.outside = self.tmp / "repo", self.tmp / "outside"
        self.repo.mkdir()
        self.outside.mkdir()
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.name", "Test")
        _git(self.repo, "config", "user.email", "1+test@users.noreply.github.com")
        (self.repo / "README.md").write_text("Projeto de exemplo sobre jardinagem.\n", encoding="utf-8")
        _git(self.repo, "add", ".")
        _git(self.repo, "commit", "-q", "-m", "base")
        self.private = self.outside / "diario.txt"
        self.private.write_text(PRIVATE, encoding="utf-8")
        self.terms = self.outside / "terms.txt"
        self.terms.write_text("# termos\nCanteiro Secreto\n", encoding="utf-8")
        self.gate = _load()
        self.gate.ROOT = self.repo

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _commit(self, name, text, message="change"):
        (self.repo / name).write_text(text, encoding="utf-8")
        _git(self.repo, "add", name)
        _git(self.repo, "commit", "-q", "-m", message)

    def _run(self, *extra):
        argv = ["--base", "HEAD~1", "--private", str(self.private), "--terms-file", str(self.terms), *extra]
        with contextlib.redirect_stdout(io.StringIO()):
            return self.gate.main(argv)

    def _report(self, *extra):
        out = self.outside / "report.json"
        code = self._run("--out", str(out), *extra)
        import json
        return code, json.loads(out.read_text(encoding="utf-8"))

    def test_clean_range_passes(self):
        self._commit("notas.md", "Regar as plantas pela manhã evita fungos nas folhas.\n")
        code, report = self._report()
        self.assertEqual(code, 0)
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["commits"], 1)

    def test_five_word_fragment_in_a_fixture_is_caught(self):
        self._commit("fixture.txt", "caso = 'mudas de manjericão roxo foram transplantadas'\n")
        code, report = self._report()
        self.assertEqual(code, 1)
        self.assertIn("private_5grams", report["findings"])

    def test_a_leak_removed_by_a_later_unpublished_commit_is_still_caught(self):
        self._commit("fixture.txt", "caso = 'mudas de manjericão roxo foram transplantadas'\n")
        self._commit("fixture.txt", "caso = 'texto sintético neutro'\n")
        argv = ["--base", "HEAD~2", "--private", str(self.private)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.gate.main(argv), 1)

    def test_fragment_only_in_the_commit_message_is_caught(self):
        self._commit("ok.md", "texto neutro\n", message="fix: depois da chuva forte de quinta")
        code, report = self._report()
        self.assertEqual(code, 1)
        self.assertIn("private_5grams", report["findings"])

    def test_distinctive_identifier_is_caught_without_being_echoed(self):
        self._commit("data.json", '{"lote": "HORTA_NORTE_7781"}\n')
        code, report = self._report()
        self.assertEqual(code, 1)
        self.assertEqual(report["findings"]["private_tokens"][0]["count"], 1)
        self.assertNotIn("HORTA_NORTE_7781", str(report["findings"]))

    def test_sensitive_term_credential_path_and_email_are_caught(self):
        # Built at run time so this source file itself carries no credential-, path- or
        # address-shaped string (the gate audits the repository's own commits).
        key = "sk" + "-" + "abcdefghijklmnopqrstu"
        path = "C:" + "\\" + "Users" + "\\" + "jardineira" + "\\projeto\\x.py"
        mail = "jardineira" + "@" + "exemplo.com.br"
        self._commit("leak.md", f"Ver o canteiro secreto.\nchave {key}\n{path}\ncontato: {mail}\n")
        code, report = self._report()
        self.assertEqual(code, 1)
        for key in ("sensitive_terms", "credentials", "personal_paths", "emails"):
            self.assertIn(key, report["findings"], key)

    def test_noreply_identity_and_placeholder_paths_are_not_findings(self):
        self._commit("doc.md", "Autor: 1+test@users.noreply.github.com\nC:\\Users\\<user>\\x e /home/runner/w\n")
        self.assertEqual(self._run(), 0)

    def test_a_private_input_inside_the_repository_is_refused(self):
        inside = self.repo / "privado.txt"
        inside.write_text(PRIVATE, encoding="utf-8")
        self._commit("ok.md", "texto neutro\n")
        self.assertEqual(self.gate.main(["--base", "HEAD~1", "--private", str(inside)]), 2)


if __name__ == "__main__":
    unittest.main()
