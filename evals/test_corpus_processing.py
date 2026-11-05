"""v0.6.0 processing: originals are preserved, duplicates (exact, near,
cross-corpus, original vs normalized) and groups never cross a split, and
the leakage check catches contamination planted on purpose."""
import sys
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.corpus.connectors import CorpusRecord  # noqa: E402
from voznativa.corpus.processing import (assign_splits, cluster, diff_manifests, group_key, jaccard,  # noqa: E402
                                         leakage, provenance, segments)

ESSAY = ("A prefeitura anunciou que a nova linha de ônibus começa a operar em março, ligando o centro aos bairros "
         "da zona norte, com intervalos de quinze minutos nos horários de pico e de meia hora no restante do dia.")


def records(source, rows, **meta):
    return [CorpusRecord(source, "a", rid, text, dict(meta, **m)) for rid, text, m in rows]


def entry(source, group_by="record"):
    return {"id": source, "processing": {"group_by": group_by}}


class Provenance(unittest.TestCase):
    def test_original_is_kept_and_normalised_copy_is_separate(self):
        nfd = unicodedata.normalize("NFD", "Não há ônibus hoje.")
        (rec,) = provenance(entry("s"), records("s", [("1", nfd, {})]))
        self.assertNotEqual(rec.original_sha256, rec.normalized_sha256)
        self.assertEqual(rec.text, "Não há ônibus hoje.")
        self.assertNotIn("text", rec.as_manifest())  # manifests carry hashes, never text
        self.assertEqual([s["index"] for s in segments(rec)], [0])

    def test_group_keys(self):
        rec = CorpusRecord("bosque", "a", "CF876-3", "x", {})
        self.assertEqual(group_key({"id": "bosque", "processing": {"group_by": "sent_id_prefix"}}, rec), "bosque:CF876")
        rev = CorpusRecord("b2w", "a", "row-9", "x", {"reviewer_id": "abc"})
        self.assertEqual(group_key({"id": "b2w", "processing": {"group_by": "reviewer_id"}}, rev),
                         "b2w:reviewer_id=abc")
        self.assertEqual(group_key({"id": "b2w"}, rev), "b2w:row-9")


class Deduplication(unittest.TestCase):
    def test_exact_near_and_cross_source_duplicates_are_clustered(self):
        edited = ESSAY.replace("quinze minutos", "15 minutos").replace("anunciou", "informou")
        recs = provenance(entry("folha"), records("folha", [("1", ESSAY, {}), ("2", "Outro texto sem relação.", {})]))
        recs += provenance(entry("mirror"), records("mirror", [("1", ESSAY + " ", {}), ("2", edited, {})]))
        self.assertGreaterEqual(jaccard(ESSAY, edited), 0.5)
        report = cluster(recs, threshold=0.5)
        clusters = {r.source + r.record_id: r.cluster for r in recs}
        self.assertEqual(clusters["folha1"], clusters["mirror1"])        # exact after normalisation
        self.assertEqual(clusters["folha1"], clusters["mirror2"])        # near duplicate (republished, edited)
        self.assertNotEqual(clusters["folha1"], clusters["folha2"])
        self.assertEqual((report["exact_duplicates"], report["cross_source_clusters"]), (1, 1))

    def test_unrelated_texts_stay_apart(self):
        recs = provenance(entry("s"), records("s", [(str(i), f"Frase número {i} sobre um assunto {i * 7} diferente "
                                                                 f"do resto da coleção {i * 13}.", {}) for i in range(40)]))
        self.assertEqual(cluster(recs)["clusters"], 40)


class Splits(unittest.TestCase):
    def build(self):
        rows = [(f"CF{d}-{s}", f"Documento {d}, frase {s}: " + ESSAY.replace("março", f"mês {d * 10 + s}"), {})
                for d in range(12) for s in range(4)]
        recs = provenance(entry("bosque", "sent_id_prefix"), records("bosque", rows))
        recs += provenance(entry("copy"), records("copy", [("x", rows[0][1], {})]))  # cross-corpus copy
        cluster(recs, threshold=0.95)
        return recs

    def test_stable_and_never_cutting_a_document_or_a_duplicate(self):
        recs = self.build()
        splits = assign_splits(recs, {"calibration": 0.5, "evaluation": 0.5})
        self.assertEqual(splits, assign_splits(recs, {"calibration": 0.5, "evaluation": 0.5}))
        self.assertFalse(leakage(recs, splits)["contaminated"])
        self.assertEqual(splits["copy:x"], splits["bosque:CF0-0"])
        self.assertEqual(len(set(splits.values())), 2)

    def test_planted_contamination_is_reported(self):
        recs = self.build()
        splits = assign_splits(recs, {"calibration": 0.5, "evaluation": 0.5})
        other = {"calibration": "evaluation", "evaluation": "calibration"}
        cut = dict(splits, **{"bosque:CF3-1": other[splits["bosque:CF3-1"]]})      # paragraph of one document
        self.assertTrue(leakage(recs, cut)["group"])
        moved = dict(splits, **{"copy:x": other[splits["copy:x"]]})                 # duplicate across corpora
        report = leakage(recs, moved)
        self.assertTrue(report["cluster"] and report["normalized"])
        self.assertTrue(report["contaminated"])

    def test_fractions_must_sum_to_one(self):
        with self.assertRaises(ValueError):
            assign_splits(self.build(), {"a": 0.5, "b": 0.4})


class Versions(unittest.TestCase):
    def test_removed_added_and_changed_records(self):
        old = [{"source": "s", "record_id": "1", "original_sha256": "a"},
               {"source": "s", "record_id": "2", "original_sha256": "b"}]
        new = [{"source": "s", "record_id": "2", "original_sha256": "B"},
               {"source": "s", "record_id": "3", "original_sha256": "c"}]
        self.assertEqual(diff_manifests(old, new), {"added": [("s", "3")], "removed": [("s", "1")],
                                                    "changed": [("s", "2")]})


if __name__ == "__main__":
    unittest.main()
