"""v0.7.0 CP12: character integrity audit, cleaning and provenance.

Integrity is about characters; nothing here detects, removes or certifies the
absence of a statistical watermark, and nothing hides AI involvement."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import integrity  # noqa: E402

HIDDEN = "Texto normal\U000E0049\U000E0047\U000E004E com tags."           # Unicode tag characters
BIDI = "O valor é ‮00,01 R$‬ no recibo."                         # right-to-left override in Latin text
ZW = "pala​vra"
EMOJI_ZWJ = "família \U0001F468‍\U0001F469‍\U0001F467 feliz"
NBSP = "Custa R$ 10,00."
HOMOGLYPH = "Acesse o pаinel agora"                                        # Cyrillic 'а' inside a Latin word
ARABIC = "Olá ‏مرحبا‏ amigo"


def kinds(text):
    return {(f["kind"], f["assessment"]) for f in integrity.audit(text)["findings"]}


class Audit(unittest.TestCase):
    def test_suspicious_classes(self):
        self.assertIn(("tag_character", "suspicious"), kinds(HIDDEN))
        self.assertIn(("bidi_control", "suspicious"), kinds(BIDI))
        self.assertIn(("zero_width", "suspicious"), kinds(ZW))
        self.assertIn(("mixed_script_word", "suspicious"), kinds(HOMOGLYPH))
        self.assertIn(("control_character", "suspicious"), kinds("a\x07b"))

    def test_legitimate_characters_are_not_suspicious(self):
        for text in (EMOJI_ZWJ, NBSP, ARABIC, "﻿início do arquivo", "Texto comum, sem nada."):
            self.assertEqual(integrity.audit(text)["suspicious"], 0, repr(text))

    def test_scope_never_mentions_a_clean_watermark(self):
        dump = json.dumps(integrity.audit(HIDDEN)) + json.dumps(integrity.clean(HIDDEN))
        self.assertNotIn("watermark_free", dump)
        self.assertIn("watermark", integrity.audit(HIDDEN)["scope"] + integrity.clean(HIDDEN)["note"])


class Clean(unittest.TestCase):
    def test_removes_only_named_classes(self):
        out = integrity.clean(HIDDEN + BIDI + ZW + EMOJI_ZWJ + NBSP)
        self.assertNotIn("\U000E0049", out["text"])
        self.assertNotIn("‮", out["text"])
        self.assertNotIn("​", out["text"])
        self.assertIn("\U0001F468‍\U0001F469", out["text"], "emoji joiner kept")
        self.assertIn(" ", out["text"], "no-break space kept")
        self.assertTrue(out["removed"])

    def test_policy_subset_and_unknown_policy(self):
        out = integrity.clean(HIDDEN + ZW, ("tags",))
        self.assertIn("​", out["text"])
        with self.assertRaises(ValueError):
            integrity.clean("x", ("watermark",))

    def test_rtl_text_keeps_its_marks(self):
        self.assertEqual(integrity.clean(ARABIC)["text"], ARABIC)


class Provenance(unittest.TestCase):
    def test_record_has_hashes_not_text(self):
        rec = integrity.provenance_record("original secreto", "versão nova", tool_version="0.7.0.dev0",
                                          operation="rewrite", provider="command", model=None)
        dump = json.dumps(rec, ensure_ascii=False)
        self.assertNotIn("secreto", dump)
        self.assertTrue(rec["ai_assisted"])
        self.assertTrue(rec["disclosure_note"])
        self.assertFalse(rec["retains_text"])
        supplied = integrity.provenance_record("a", "b", tool_version="x", operation="rewrite", provider="static")
        self.assertIsNone(supplied["ai_assisted"], "a candidate file's origin is unknown, not 'AI'")
        unchanged = integrity.provenance_record("a", "a", tool_version="x", operation="rewrite", provider=None)
        self.assertFalse(unchanged["ai_assisted"])
        self.assertIsNone(unchanged["disclosure_note"])

    def test_cli_audit_exit_codes_and_rewrite_provenance(self):
        env = dict(__import__("os").environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            bad, good = Path(tmp) / "bad.txt", Path(tmp) / "good.txt"
            bad.write_text(HIDDEN, encoding="utf-8")
            good.write_text(NBSP, encoding="utf-8")
            run = lambda *a: subprocess.run([sys.executable, "-m", "voznativa", *a], cwd=tmp,  # noqa: E731
                                            capture_output=True, env=env)
            self.assertEqual(run("integrity", str(bad)).returncode, 2)
            self.assertEqual(run("integrity", str(good)).returncode, 0)
            done = run("rewrite", str(good), "--mode", "REVIEW")
            self.assertEqual(done.returncode, 0)
            plain = Path(tmp) / "plain.txt"
            plain.write_text("O relatório foi entregue ontem.", encoding="utf-8")
            cand = Path(tmp) / "c.txt"
            cand.write_text("NO_CHANGE", encoding="utf-8")
            done = run("rewrite", str(plain), "--candidate", str(cand), "--force")
            report = json.loads(done.stdout.decode("utf-8"))
            self.assertEqual(report["provenance"]["kind"], "voznativa.provenance")
            self.assertEqual(report["provenance"]["input_sha256"], integrity.sha256("O relatório foi entregue ontem."))


if __name__ == "__main__":
    unittest.main()
