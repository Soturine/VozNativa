"""v0.6.0 known gaps, reproducible (BACKLOG). Each test states the desired
behaviour and is marked expectedFailure: it documents the gap today and
fails the suite ("unexpected success") the day the gap is closed, so the
backlog entry cannot go stale silently. Priorities and reasons are in
docs/ROADMAP.md (v0.6 backlog) and evals/corpus/LONGFORM_v0.6.md.

G1 (P1) router: hard-wrapped literature with "--" dialogue is read as
   whatsapp (259/804 Gutenberg segments, CP10). The lowercase-line cue fires
   on every wrapped line and the literary cue only knows the em dash. Fixing
   it needs line unwrapping before inference and a rerun of the frozen router
   suite; P1 because a wrong genre removes the literary protections.
G2 (P2) dedup: a chapter contained in the full novel is not clustered with
   it (Jaccard is symmetric and small for a 1:10 containment). The CP10
   long-form split found it by titles; a containment measure is needed
   before any split that mixes editions of the same work is called
   independent.
G3 (P3) slang: the final "de boa" pattern misses "de boa" followed by a
   word ("roda tudo de boa no telão"; ptbr-bench-v4 bv4-sl-03). Recall
   traded for precision on purpose; a better pattern needs a new held-out
   sample, not the frozen case.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import temporal  # noqa: E402
from voznativa.corpus.connectors import CorpusRecord  # noqa: E402
from voznativa.corpus.processing import cluster, provenance  # noqa: E402
from voznativa.router import infer_genre  # noqa: E402

WRAPPED_DIALOGUE = """Quando cheguei a casa, a tarde ia acabando, e a criada veio dizer-me que
minha tia estava na sala, a conversar com o vigario, um homem gordo e
manso, que a visitava todos os sabbados depois da missa.

--Entra, menino, disse ella, ainda com o rosario na mão.

--Boa tarde, minha tia.

--Senta-te ahi, que o senhor vigario tem uma noticia para ti, e é
noticia boa, ou eu me engano muito com as cousas deste mundo."""


class KnownGaps(unittest.TestCase):
    def test_g1_wrapped_literary_dialogue_is_not_whatsapp(self):
        # Closed in v0.7.0 CP5 (inference-only unwrapping, '--' dialogue cue); the
        # full oracle (genre AND protections) is in evals/test_router_v3.py.
        self.assertNotEqual(infer_genre(WRAPPED_DIALOGUE)["value"], "whatsapp")

    def test_g2_a_contained_chapter_clusters_with_its_novel(self):
        # Closed in v0.7.0 CP4 (directional containment); kept as a regression test.
        chapter = " ".join(f"Frase {i} do capítulo sobre a casa velha e o quintal de muitos anos." for i in range(40))
        novel = " ".join(f"Outra parte {i} do romance, com outros fatos e outras pessoas na cidade."
                         for i in range(400)) + " " + chapter
        recs = provenance({"id": "s"}, [CorpusRecord("s", "a", "novel", novel, {}),
                                        CorpusRecord("s", "a", "chapter", chapter, {})])
        cluster(recs)
        self.assertEqual(recs[0].cluster, recs[1].cluster)

    def test_g3_de_boa_followed_by_a_word(self):
        # Closed in v0.7.0 CP6 (sense by the class of the next word); held-out sample in
        # evals/slang/cases-v07.jsonl, tests in evals/test_slang_v07.py.
        self.assertEqual([f["id"] for f in temporal.observe("O jogo roda tudo de boa no telão novo.")], ["de-boa"])


if __name__ == "__main__":
    unittest.main()
