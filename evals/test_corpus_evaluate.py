"""v0.6.0 corpus evaluation: the counts behind the calibration run are right
on records whose answers are known, and nothing derived carries text."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.corpus.connectors import CorpusRecord  # noqa: E402
from voznativa.corpus.evaluate import (by_label, documents, length_bin, pattern_eval, threshold_sweep,  # noqa: E402
                                       variant_documents, variant_eval)
from voznativa.corpus.processing import provenance  # noqa: E402

ENTRY = {"id": "bosque", "processing": {"group_by": "sent_id_prefix",
                                         "variant_by_sent_id_prefix": {"CF": "pt-BR", "CP": "pt-PT"}}}
ROWS = [("CF1-1", "O time ganhou o jogo no domingo e a torcida comemorou na avenida."),
        ("CF1-2", "Você pode pegar o ônibus na esquina da rua de baixo."),
        ("CP1-1", "O comboio chegou atrasado à estação de Lisboa."),
        ("CP1-2", "Estou a fazer o relatório para o gabinete."),
        ("CP2-1", "A reunião foi adiada para a próxima semana.")]


def recs():
    return provenance(ENTRY, [CorpusRecord("bosque", "a", rid, text, {}) for rid, text in ROWS])


class Variant(unittest.TestCase):
    def test_sentence_and_document_confusion(self):
        label = by_label(ENTRY)
        report = variant_eval(recs(), label)
        self.assertEqual((report["pt_pt_sentences"], report["pt_br_sentences"]), (3, 2))
        self.assertEqual(report["false_positive_rate_pt_br"]["k"], 0)
        self.assertGreaterEqual(report["recall_pt_pt"]["k"], 2)        # comboio, estar a + infinitivo
        self.assertEqual(report["recall_pt_pt"]["n"], 3)                # CP2-1 has no PT-PT marker
        docs = variant_documents(recs(), label)
        self.assertEqual((docs["recall_pt_pt"]["k"], docs["recall_pt_pt"]["n"]), (1, 2))
        self.assertEqual(docs["false_positive_rate_pt_br"]["n"], 1)

    def test_unlabelled_records_are_ignored(self):
        report = variant_eval(recs(), lambda r: None)
        self.assertEqual(report["pt_pt_sentences"] + report["pt_br_sentences"], 0)
        self.assertIsNone(report["precision"]["rate"])


class Patterns(unittest.TestCase):
    def test_documents_join_groups_in_order(self):
        docs = documents(recs())
        self.assertEqual(set(docs), {"bosque:CF1", "bosque:CP1", "bosque:CP2"})
        self.assertTrue(docs["bosque:CF1"]["text"].startswith("O time"))

    def test_report_is_aggregate_only(self):
        report = pattern_eval(documents(recs()), "journalistic")
        self.assertEqual(report["documents"], 3)
        dumped = json.dumps(report, ensure_ascii=False)
        for _, text in ROWS:
            self.assertNotIn(text[:25], dumped)
        self.assertEqual(sum(report["weak_findings_histogram"].values()), 3)
        self.assertEqual(sum(b["documents"] for b in report["by_length"].values()), 3)

    def test_threshold_sweep_follows_the_rule(self):
        rows = [(209, 0, 2), (90, 0, 1), (40, 1, 0), (400, 0, 2)]
        sweep = threshold_sweep(rows)
        # dc-029 shape (209 words, 2 weak): edit under /150 and /200, not under /75 or /100
        self.assertEqual(sweep["weak/150"]["k"], 2)   # 209w/2 weak and 40w strong; 400w needs 3 weak
        self.assertEqual(sweep["weak/100"]["k"], 1)
        self.assertEqual(sweep["weak/300"]["k"], 3)
        self.assertEqual(sweep["strong_only"]["k"], 1)

    def test_length_bins(self):
        self.assertEqual([length_bin(w) for w in (1, 49, 50, 209, 300, 5000)],
                         ["0-49", "0-49", "50-149", "150-299", "300+", "300+"])


if __name__ == "__main__":
    unittest.main()
