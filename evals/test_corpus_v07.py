"""v0.7.0 CP3: text rights apart from annotation licences, and the cross-genre evaluators."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.corpus import policy  # noqa: E402
from voznativa.corpus.connectors import CorpusRecord  # noqa: E402
from voznativa.corpus.evaluate import router_eval, slang_eval, windows  # noqa: E402
from voznativa.corpus.processing import provenance  # noqa: E402
from voznativa.corpus.registry import get_source, validate_source  # noqa: E402


def entry(**lic):
    return {"id": "fx", "status": "EVALUATION_INTEGRATED", "access": {"type": "open_download"},
            "license": dict({"code": "CC-BY-SA-4.0", "per_document": False, "evidence": "fixture"}, **lic),
            "privacy": {"personal_data": False}}


class TextRights(unittest.TestCase):
    def test_unclear_text_rights_block_disclosure_but_not_local_use(self):
        e = entry(text_rights="unclear", text_rights_note="annotations only")
        for op in ("PROCESS_LOCAL", "DERIVE_FEATURES", "EXPORT_STATISTICS"):
            self.assertEqual(policy.decide(e, op).state, "ALLOWED", op)
        for op in policy.TEXT_DISCLOSURE:
            self.assertNotEqual(policy.decide(e, op, destination="CC-BY-SA-4.0").state, "ALLOWED", op)
        d = policy.decide(e, "EXPORT_SAMPLES", destination="CC-BY-SA-4.0")   # ALLOWED by the licence alone
        self.assertEqual(d.state, "UNKNOWN")
        self.assertIn("annotations", d.reasons[0])

    def test_a_stronger_licence_decision_is_not_weakened(self):
        e = entry(text_rights="unclear", text_rights_note="annotations only")
        self.assertEqual(policy.decide(e, "EXPORT_SAMPLES").state, "DENIED")   # share-alike into the MIT repo
        self.assertEqual(policy.decide(e, "TRAIN_MODEL").state, "REQUIRES_PERMISSION")

    def test_control_same_licence_without_the_flag_allows_share_alike_export(self):
        self.assertEqual(policy.decide(entry(), "EXPORT_SAMPLES", destination="CC-BY-SA-4.0").state, "ALLOWED")

    def test_registry_requires_a_note_and_a_known_value(self):
        base = dict(get_source("ud-portuguese-gsd"))
        bad = dict(base, license=dict(base["license"], text_rights="maybe"))
        self.assertTrue(any("text_rights" in p for p in validate_source(bad)))
        no_note = dict(base, license={k: v for k, v in base["license"].items() if k != "text_rights_note"})
        self.assertTrue(any("text_rights_note" in p for p in validate_source(no_note)))

    def test_news_tweet_and_web_sources_are_marked(self):
        for sid in ("ud-portuguese-bosque", "ud-portuguese-gsd", "ud-portuguese-pud", "ud-portuguese-dantestocks"):
            self.assertEqual(get_source(sid)["license"].get("text_rights"), "unclear", sid)
            self.assertNotEqual(policy.decide(get_source(sid), "SEND_TO_EXTERNAL_MODEL").state, "ALLOWED", sid)


class CrossGenreEvaluators(unittest.TestCase):
    def recs(self, texts, group_by="record"):
        e = {"id": "fx", "processing": {"group_by": group_by}}
        return provenance(e, [CorpusRecord("fx", "a", f"r{i}", t, {"doc_id": "D"}) for i, t in enumerate(texts)])

    def test_windows_stay_inside_groups_and_under_the_limit(self):
        recs = self.recs(["palavra " * 60, "palavra " * 60, "palavra " * 60], group_by="doc_id")
        units = windows(recs, max_words=130)
        self.assertEqual([u["words"] for u in units], [120, 60])
        separate = windows(self.recs(["a b c", "d e f"]), max_words=130)
        self.assertEqual(len(separate), 2, "records of different groups are never joined")

    def test_router_eval_separates_abstention_from_confident_errors(self):
        units = [{"text": "vc viu?? kkk blz, pq tbm nn sei", "words": 8},
                 {"text": "Texto curto.", "words": 2}]
        r = router_eval(units, {"literary"})
        self.assertEqual(r["confident_wrong"]["k"], 1)
        self.assertEqual(r["confident_wrong_by_genre"], {"whatsapp": 1})
        self.assertEqual(r["abstention"]["k"], 1)

    def test_slang_eval_counts_forms(self):
        r = slang_eval([{"text": "o rolê foi bom", "words": 4}, {"text": "relatório técnico", "words": 2}])
        self.assertEqual(r["units_with_slang"]["k"], 1)
        self.assertEqual(r["by_form"], {"role": 1})


if __name__ == "__main__":
    unittest.main()
