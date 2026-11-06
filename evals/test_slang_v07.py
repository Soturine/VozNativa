"""v0.7.0 CP6 (G3 and slang out of its time): sense by occurrence context.

evals/slang/cases-v07.jsonl was written and hashed before the code change
(first run: 17/18 under a list comparison; the one difference was two hits
of the same entry, "mano" and "mana", not a sense error; the cases ask for
the set of entry ids)."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import temporal  # noqa: E402
from voznativa.ptbr import variant_markers  # noqa: E402

CASES_PATH = ROOT / "evals" / "slang" / "cases-v07.jsonl"
CASES_SHA256 = "07fafef0a2456daa31945072df2a7ae777c22dbd488b9b4a9f900c5327284dc8"
CASES = [json.loads(x) for x in CASES_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]
# Second sample (sentences new, written before the hyphen/coordination/"cara" fix; the error
# classes were seen in corpus windows, so this sample tests transfer, not blind discovery).
CASES_B_PATH = ROOT / "evals" / "slang" / "cases-v07b.jsonl"
CASES_B_SHA256 = "b6401329ee8b99b336c9bcad62c1549173f0c32b0908678df4587841bb5f77c1"
CASES_B = [json.loads(x) for x in CASES_B_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]


def ids(hits, sense):
    return sorted({h["id"] for h in hits if h["sense"] == sense})


class HeldOutSample(unittest.TestCase):
    def test_frozen(self):
        self.assertEqual(hashlib.sha256(CASES_PATH.read_bytes()).hexdigest(), CASES_SHA256)
        self.assertEqual(hashlib.sha256(CASES_B_PATH.read_bytes()).hexdigest(), CASES_B_SHA256)

    def test_cases(self):
        for c in CASES + CASES_B:
            with self.subTest(case=c["id"]):
                hits = temporal.observe(c["text"])
                self.assertEqual(ids(hits, "slang"), sorted(set(c["slang"])))
                if "ambiguous" in c:
                    self.assertEqual(ids(hits, "ambiguous"), sorted(set(c["ambiguous"])))
                self.assertEqual(ids(hits, "other_sense"), [], "context-decided other senses are dropped")
                if "other" in c:
                    self.assertEqual(ids(hits, "other_sense_likely"), sorted(set(c["other"])))

    def test_negative_control_v06_pattern_misses_the_slang_use(self):
        # The v0.6 pattern refused any following word: "de boa no telão" was lost (G3).
        import re
        v06 = re.compile(r"\b(?:de|na) boa(?!\s*[a-záàâãéêíóôõúüç])", re.I)
        self.assertIsNone(v06.search("o jogo roda tudo de boa no telão novo."))


class ConsumersCountTheSlangSenseOnly(unittest.TestCase):
    NOVEL = ("Naquelle anno o mano de Luiza voltou da côrte, e ella o esperava no caes. "
             "O mano trazia cartas, e a mana chorou ao vel-o.")

    def test_stuffing_and_author_slang_ignore_old_senses(self):
        from voznativa.engine import _temporal_and_community_issues
        from voznativa.router import route
        ctx = route(self.NOVEL)
        rewrite = self.NOVEL.replace("O mano trazia", "Ele trazia")
        codes = {i["code"] for i in _temporal_and_community_issues(self.NOVEL, rewrite, ctx)}
        self.assertNotIn("author_slang_removed", codes)
        self.assertNotIn("slang_stuffing", codes)

    def test_control_real_slang_removed_is_still_reported(self):
        from voznativa.engine import _temporal_and_community_issues
        from voznativa.router import route
        chat = "vlw mano, o rolê foi top demais kkk"
        ctx = route(chat)
        codes = {i["code"] for i in _temporal_and_community_issues(chat, "obrigado, o passeio foi ótimo", ctx)}
        self.assertIn("author_slang_removed", codes)

    def test_introducing_an_ambiguous_form_is_still_caught(self):
        # The introduction guard stays conservative: any lexicon form the source lacked.
        added = temporal.introduced_terms("O diretor saiu da reunião.", "O diretor saiu irado da reunião.")
        self.assertEqual([a["id"] for a in added], ["irado"])

    def test_profile_does_not_learn_old_senses_as_habits(self):
        from voznativa.profile import build
        def slang_habits(texts):
            dump = json.dumps(build([{"text": t} for t in texts]), ensure_ascii=False)
            return [h for h in dump.split('"') if h.startswith("slang.")]
        self.assertEqual(slang_habits([self.NOVEL] * 3), [])
        self.assertIn("slang.mano", slang_habits(["vlw mano, valeu demais kkk"] * 3), "control: real slang is a habit")


class FalseFriendNeedsCorroboration(unittest.TestCase):
    def test_propina_alone_is_brazilian(self):
        found = variant_markers("O delator disse que pagou propina para liberar a obra.")
        self.assertTrue(found and all(m.get("uncorroborated") for m in found))
        from voznativa.ptbr import findings
        notes = [f for f in findings("O delator disse que pagou propina.", "journalistic")
                 if f["family"] == "variante PT-PT"]
        self.assertTrue(notes and all(f.get("note_only") for f in notes))

    def test_control_propina_next_to_another_marker_counts(self):
        found = {m["text"].lower(): m for m in variant_markers("A propina da universidade subiu e a equipa protestou.")}
        self.assertIn("propina", found)
        self.assertNotIn("uncorroborated", found["propina"])


if __name__ == "__main__":
    unittest.main()
