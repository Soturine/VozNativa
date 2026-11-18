"""v0.10.5 (V105-GAP-08): an explicit POLISH/ADAPT asks for an edit; the model is called.

Fire trial, task T08: "Revise este resumo para clareza e concisão" with --mode POLISH on a well-written abstract
came back as no_change without a single model call (no detector finding, no destination). Defect red on v0.10.0;
controls: without a mode, a text without findings still does not call the model; PRESERVE never does.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from voznativa.cli import main

TEXT = "A comissão aprovou o calendário de vacinação do rebanho para o próximo semestre, com reforço em março."


def run(*extra):
    import contextlib
    import io
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "t.txt"
        src.write_text(TEXT, encoding="utf-8")
        calls = Path(tmp) / "calls.txt"
        stub = Path(tmp) / "stub.py"
        stub.write_text("import sys\nopen(sys.argv[1], 'a').write('x')\nsys.stdin.read()\n"
                        f"print('<final>{TEXT}</final>')\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            try:
                main(["rewrite", str(src), "--cmd", json.dumps([sys.executable, str(stub), str(calls)]),
                      "--provider-env", "minimal", "--attempts", "1", *extra])
            except SystemExit:
                pass
        n = len(calls.read_text()) if calls.exists() else 0
        return n, json.loads(out.getvalue())


class ExplicitMode(unittest.TestCase):
    def test_defect_polish_and_adapt_call_the_model(self):
        for mode in ("POLISH", "ADAPT"):
            calls, result = run("--mode", mode)
            self.assertGreaterEqual(calls, 1, mode)

    def test_control_without_mode_no_findings_no_call(self):
        calls, result = run()
        self.assertEqual(calls, 0)
        self.assertEqual(result["outcome"], "no_change")

    def test_control_preserve_never_calls(self):
        calls, result = run("--mode", "PRESERVE")
        self.assertEqual(calls, 0)


if __name__ == "__main__":
    unittest.main()
