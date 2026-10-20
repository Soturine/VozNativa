"""Privacy of recorded runs (v0.3.0 M6.2)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RedactedIntegrationReports(unittest.TestCase):
    def test_redact_keeps_no_text_or_raw_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            model = tmp / "model.py"
            model.write_text("import sys\nsys.stdin.read()\nprint('<final>O prazo SEGREDO-42 é sexta.</final>')\n",
                             encoding="utf-8")
            cases = tmp / "cases.jsonl"
            cases.write_text(json.dumps({"id": "p1", "genre": "corporate",
                                         "text": "É importante destacar que o prazo SEGREDO-42 é sexta."}) + "\n",
                             encoding="utf-8")
            label = "privacy-unit-test"
            done = subprocess.run([sys.executable, str(ROOT / "scripts" / "llm_integration.py"), "--cases", str(cases),
                                   "--cmd", json.dumps([sys.executable, str(model)]), "--model-label", label,
                                   "--attempts", "1", "--redact"], capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(done.returncode, 0, done.stderr)
            reports = sorted((ROOT / "evals" / "integration").glob(f"*{label}*"))
            try:
                self.assertTrue(reports)
                content = reports[-1].read_text(encoding="utf-8")
                self.assertNotIn("SEGREDO-42", content)
                self.assertTrue(json.loads(content)["redacted"])
            finally:
                for report in reports:
                    report.unlink()


if __name__ == "__main__":
    unittest.main()
