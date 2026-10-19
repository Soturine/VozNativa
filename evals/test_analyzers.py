"""Regression tests for the descriptive analyzers (v0.1.0 audit findings)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.analyze import analyze
from voznativa.audit import audit
from voznativa.drift import inspect as drift
from voznativa.region import inspect as region
from voznativa.text import sentences


class Analyzer(unittest.TestCase):
    def test_words_that_only_look_like_gerunds_are_not_counted(self):
        self.assertEqual(analyze("Quando o comando falhou, segundo o log, o mundo parou.")["gerund_count"], 0)
        self.assertEqual(analyze("Estou testando e corrigindo.")["gerund_count"], 2)

    def test_words_that_only_look_like_adverbs_are_not_counted(self):
        self.assertEqual(analyze("A semente e a mente de Clemente.")["mente_count"], 0)
        self.assertEqual(analyze("Ele respondeu rapidamente.")["mente_count"], 1)

    def test_unicode_ellipsis_and_spaced_en_dash(self):
        result = analyze("Hmm… sei lá. Isso – talvez – funcione...")
        self.assertEqual(result["ellipsis_count"], 2)
        self.assertEqual(result["en_dash_spaced_count"], 2)

    def test_abbreviations_do_not_split_sentences(self):
        self.assertEqual(len(sentences("O Dr. Silva chegou às 10h. Tudo certo.")), 2)

    def test_decimals_and_urls_do_not_split_sentences(self):
        self.assertEqual(len(sentences("Custa 3.5 vezes mais. Veja https://x.com/a.b agora.")), 2)

    def test_fenced_code_is_one_unit(self):
        text = "Rode:\n\n```bash\necho a. b. c.\n```\n\nPronto."
        kinds = [s.kind for s in sentences(text)]
        self.assertEqual(kinds, ["prose", "code", "prose"])


class AuditAndGuards(unittest.TestCase):
    def test_mechanicality_does_not_penalize_ordinary_gerunds(self):
        result = audit("Estamos testando o fluxo enquanto corrigimos os bugs.")
        self.assertEqual(result["mechanicality"]["gerundism_count"], 0)
        self.assertEqual(audit("Estaremos realizando a entrega.")["mechanicality"]["gerundism_count"], 1)

    def test_audit_reports_semantic_loss_only_with_original(self):
        self.assertIsNone(audit("O prazo é sexta.")["semantic_loss"])
        loss = audit("O prazo é sexta-feira.", original="O prazo não é sexta-feira.")["semantic_loss"]
        self.assertEqual(loss["status"], "fail")

    def test_region_code_is_case_insensitive(self):
        self.assertFalse(region("uai, sô", "MG")["requested_region_mismatch"])
        self.assertTrue(region("uai, bah", "MG")["requested_region_mismatch"])

    def test_drift_is_length_normalized(self):
        # Same style at two lengths must not look like drift.
        short = "Frase curta, com vírgula. Outra frase curta, igual."
        text = short + "\n\n" + " ".join([short] * 6)
        self.assertFalse(drift(text, size=1)["drift"])

    def test_drift_flags_real_style_change(self):
        formal = "Prezados, informamos que o processo foi concluído conforme o cronograma estabelecido anteriormente."
        chat = "vc viu?? nn deu certo kkk!! pq será?? manda msg!!"
        self.assertTrue(drift(formal + "\n\n" + chat, size=1)["drift"])


if __name__ == "__main__":
    unittest.main()
