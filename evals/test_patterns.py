"""Editorial pattern detector (v0.3.0 M2.1)."""
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import cli
from voznativa.benchmark import load_cases
from voznativa.patterns import detect

CASES = [json.loads(line) for line in (ROOT / "evals" / "patterns" / "cases.jsonl").read_text(encoding="utf-8").splitlines()
         if line.strip()]


class PatternSuite(unittest.TestCase):
    def test_genre_aware_suite(self):
        for case in CASES:
            report = detect(case["text"], case["genre"])
            ids = {f["id"] for f in report["findings"]}
            expect = case["expect"]
            if "decision" in expect:
                self.assertEqual(report["decision"], expect["decision"], case["id"])
            for pid in expect.get("present", []):
                self.assertIn(pid, ids, case["id"])
            for pid in expect.get("absent", []):
                self.assertNotIn(pid, ids, case["id"])

    def test_separates_ai_style_drafts_from_natural_texts(self):
        # Written by the developer, so this is a sanity check, not independent evidence.
        drafts = load_cases(ROOT / "benchmarks" / "cases" / "ptbr-ai-drafts-v1.jsonl")
        self.assertTrue(all(detect(c["text"], c["genre"])["decision"] == "edit" for c in drafts))
        natural = [c for c in load_cases(ROOT / "benchmarks" / "cases" / "ptbr-v1.jsonl") if c["id"] != "bm-email-001"]
        self.assertTrue(all(detect(c["text"], c["genre"])["decision"] == "no_change_candidate" for c in natural))

    def test_exempt_genre_keeps_the_construction(self):
        text = "O locatário deverá efetuar o pagamento da multa contratual."
        self.assertIn("support_verb", {f["id"] for f in detect(text, "corporate")["findings"]})
        self.assertNotIn("support_verb", {f["id"] for f in detect(text, "legal")["findings"]})

    def test_report_is_not_an_authorship_score(self):
        report = detect("É importante destacar que o prazo foi mantido.", "corporate")
        self.assertIn("not an authorship score", report["note"])
        self.assertNotIn("ai", {k.lower() for k in report["summary"]})

    def test_cli(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "t.txt")
            path.write_text("Estaremos realizando a manutenção no domingo.", encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = cli.main(["patterns", str(path), "--genre", "corporate"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(buffer.getvalue())["decision"], "edit")


if __name__ == "__main__":
    unittest.main()
