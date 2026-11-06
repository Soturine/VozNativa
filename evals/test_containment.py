"""v0.7.0 CP4 (G2): directional containment, historic spelling and multi-key splits.

Synthetic text only: sentences drawn by a seeded generator so no two
documents share wording unless the test puts it there."""
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.corpus.connectors import CorpusRecord  # noqa: E402
from voznativa.corpus.processing import (assign_splits, cluster, containment, leakage, ortho_key,  # noqa: E402
                                         provenance)

NOUNS = ("casa rio janela cidade estrada porta cavalo carta jardim igreja ponte mesa livro campo praia "
         "torre feira loja barco moinho serra vila praça escola fábrica").split()
VERBS = ("abriu fechou viu levou trouxe deixou achou guardou pintou vendeu comprou mostrou perdeu "
         "ganhou limpou").split()
PEOPLE = "Ana Bento Clara Davi Elisa Fábio Gil Helena Ivo Júlia Lauro Marta Nuno Olga".split()
ADJ = "velha nova azul larga estreita quieta antiga clara escura alta baixa".split()


def prose(seed: int, sentences: int) -> str:
    rnd = random.Random(seed)
    out = []
    for _ in range(sentences):
        out.append(f"{rnd.choice(PEOPLE)} {rnd.choice(VERBS)} a {rnd.choice(NOUNS)} {rnd.choice(ADJ)} perto da "
                   f"{rnd.choice(NOUNS)} de {rnd.choice(PEOPLE)} quando {rnd.choice(PEOPLE).lower()} "
                   f"{rnd.choice(VERBS)} o {rnd.choice(NOUNS)}.")
    return " ".join(out)


def records(texts, source="s", group_by="record", meta=None):
    entry = {"id": source, "processing": {"group_by": group_by}}
    return provenance(entry, [CorpusRecord(source, "a", f"{source}-{i}", t, (meta or [{}] * len(texts))[i])
                              for i, t in enumerate(texts)])


class Containment(unittest.TestCase):
    def test_measure_is_directional(self):
        chapter, rest = prose(1, 40), prose(2, 400)
        novel = rest + " " + chapter
        self.assertGreater(containment(chapter, novel), 0.95)
        self.assertLess(containment(novel, chapter), 0.15)

    def test_chapter_clusters_with_its_novel(self):
        chapter = prose(1, 40)
        recs = records([prose(2, 400) + " " + chapter, chapter])
        report = cluster(recs)
        self.assertEqual(recs[0].cluster, recs[1].cluster)
        self.assertEqual(report["containment_links"], 1)

    def test_control_without_containment_the_chapter_is_separate(self):
        # Negative control: the v0.6 behaviour (Jaccard only) is the G2 gap.
        chapter = prose(1, 40)
        recs = records([prose(2, 400) + " " + chapter, chapter])
        cluster(recs, with_containment=False)
        self.assertNotEqual(recs[0].cluster, recs[1].cluster)

    def test_excerpt_republished_by_another_source_is_linked_across_sources(self):
        excerpt = prose(7, 25)
        recs = records([prose(8, 300) + " " + excerpt + " " + prose(9, 100)], source="a") + \
            records([excerpt], source="b")
        report = cluster(recs)
        self.assertEqual(recs[0].cluster, recs[1].cluster)
        self.assertEqual(report["cross_source_containment_links"], 1)

    def test_modernised_edition_meets_the_original(self):
        old = ("Na acção do sabbado, o director da pharmacia escreveu um acto e um facto no escripto que "
               "o collega guardou na gaveta da sala, junto ao projecto do anno anterior. ") * 3
        new = ("Na ação do sábado, o diretor da farmácia escreveu um ato e um fato no escrito que "
               "o colega guardou na gaveta da sala, junto ao projeto do ano anterior. ") * 3
        self.assertEqual(ortho_key("accao"), ortho_key("acao"))
        recs = records([old + prose(3, 30), new + prose(3, 30)])
        cluster(recs)
        self.assertEqual(recs[0].cluster, recs[1].cluster)

    def test_same_topic_different_text_is_not_a_duplicate(self):
        a = ("A prefeitura anunciou obras na ponte velha da cidade; o prazo é de seis meses e o trânsito será "
             "desviado pela estrada do porto durante a reforma. ") + prose(11, 30)
        b = ("Moradores criticaram o desvio do trânsito causado pela reforma da ponte velha, prevista para "
             "durar meio ano segundo a prefeitura. ") + prose(12, 30)
        recs = records([a, b])
        report = cluster(recs)
        self.assertNotEqual(recs[0].cluster, recs[1].cluster)
        self.assertEqual(report["containment_links"], 0)

    def test_a_famous_quotation_does_not_glue_documents(self):
        quote = ("Minha terra tem palmeiras onde canta o sabiá, as aves que aqui gorjeiam não gorjeiam como lá "
                 "e nosso céu tem mais estrelas e nossas várzeas têm mais flores. ")
        texts = [quote + prose(100 + i, 30) for i in range(30)]
        recs = records(texts)
        report = cluster(recs)
        self.assertEqual(report["containment_links"], 0)
        self.assertEqual(len({r.cluster for r in recs}), 30)
        # The quotation as a record of its own: inside ONE document it is real
        # containment (same words; splitting them would leak the text)...
        self.assertEqual(cluster(records([quote, texts[0]]))["containment_links"], 1)
        # ...but when it is quoted by many documents its shingles are common and
        # link nothing.
        self.assertEqual(cluster(records([quote] + texts))["containment_links"], 0)

    def test_a_short_sentence_is_never_called_contained(self):
        sentence = "Ana abriu a porta da casa velha."
        self.assertEqual(cluster(records([sentence, prose(5, 50) + " " + sentence]))["containment_links"], 0)


class MultiKeySplits(unittest.TestCase):
    def test_works_of_one_author_never_cross_a_split(self):
        meta = [{"work": f"w{i}", "author": f"a{i % 3}"} for i in range(30)]
        recs = records([prose(200 + i, 5) for i in range(30)], group_by=["work", "author"], meta=meta)
        cluster(recs)
        splits = assign_splits(recs, {"calibration": 0.5, "evaluation": 0.5})
        by_author = {}
        for r, m in zip(recs, meta):
            by_author.setdefault(m["author"], set()).add(splits[f"{r.source}:{r.record_id}"])
        self.assertTrue(all(len(v) == 1 for v in by_author.values()), by_author)
        self.assertFalse(leakage(recs, splits)["contaminated"])

    def test_leakage_reports_an_author_in_two_splits(self):
        meta = [{"work": "w1", "author": "x"}, {"work": "w2", "author": "x"}]
        recs = records([prose(1, 5), prose(2, 5)], group_by=["work", "author"], meta=meta)
        forced = {f"{recs[0].source}:{recs[0].record_id}": "calibration",
                  f"{recs[1].source}:{recs[1].record_id}": "evaluation"}
        report = leakage(recs, forced)
        self.assertTrue(report["contaminated"])
        self.assertEqual(report["extra_group"], ["s:author=x"])


if __name__ == "__main__":
    unittest.main()
