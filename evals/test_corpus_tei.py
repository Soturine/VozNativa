"""v0.7.0 CP2: safe TEI/XML ingestion, per-document licences and CoNLL-U documents.

Fixtures are written here (synthetic, own text); no third-party corpus text."""
import gzip
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.corpus import policy  # noqa: E402
from voznativa.corpus.connectors import (AccessError, LocalFilesConnector, ReadLimits, iter_lines,  # noqa: E402
                                         read_conllu, to_conllu_text)
from voznativa.corpus.tei import read_tei  # noqa: E402

NS = 'xmlns="http://www.tei-c.org/ns/1.0"'


def tei_doc(ident="d1", licence='<licence target="https://creativecommons.org/licenses/by/4.0/">CC BY</licence>',
            body="<p>Primeiro parágrafo com uma <note>nota de rodapé</note> no meio.</p>"):
    return f"""<TEI {NS} xml:id="{ident}"><teiHeader><fileDesc>
<titleStmt><title>Título do documento</title><author>Autora Exemplo</author></titleStmt>
<editionStmt><edition>2ª edição revista</edition></editionStmt>
<publicationStmt><idno>ID-{ident}</idno><availability status="free">{licence}</availability></publicationStmt>
<sourceDesc><bibl><date when="1899">1899</date></bibl></sourceDesc></fileDesc>
<profileDesc><langUsage><language ident="pt-BR"/></langUsage>
<textClass><keywords><term>literatura</term></keywords><catRef target="#prosa"/></textClass></profileDesc>
</teiHeader><text><body><head>CAPÍTULO I</head>{body}</body></text></TEI>"""


def read(xml: str, max_bytes: int = 1_000_000):
    import io
    errors = []
    return list(read_tei(io.BytesIO(xml.encode("utf-8")), errors, max_bytes)), errors


class TeiReader(unittest.TestCase):
    def test_metadata_and_structure_are_kept(self):
        (rid, text, meta), = read(tei_doc())[0]
        self.assertEqual(rid, "d1")
        self.assertEqual(meta["title"], "Título do documento")
        self.assertEqual(meta["authors"], ["Autora Exemplo"])
        self.assertEqual(meta["dates"], ["1899"])
        self.assertEqual(meta["idno"], "ID-d1")
        self.assertEqual(meta["language"], "pt-BR")
        self.assertEqual(meta["licence"]["code"], "CC-BY-4.0")
        self.assertIn("literatura", meta["typology"])
        self.assertIn("#prosa", meta["typology"])
        self.assertEqual(meta["edition"], "2ª edição revista")
        self.assertEqual(text, "CAPÍTULO I\n\nPrimeiro parágrafo com uma no meio.")
        self.assertEqual(meta["structure"]["note"], 1, "a dropped note is counted, not hidden")

    def test_verse_keeps_one_line_per_l(self):
        body = "<lg><l>Minha terra tem palmeiras,</l><l>Onde canta o sabiá;</l></lg><p>Prosa depois.</p>"
        (_, text, meta), = read(tei_doc(body=body))[0]
        self.assertIn("Minha terra tem palmeiras,\nOnde canta o sabiá;", text)
        self.assertEqual((meta["structure"]["lg"], meta["structure"]["l"]), (1, 2))

    def test_tei_corpus_yields_one_record_per_document(self):
        corpus = f"<teiCorpus {NS}><teiHeader/>" + tei_doc("a").replace(f" {NS}", "") + \
                 tei_doc("b").replace(f" {NS}", "") + "</teiCorpus>"
        records, _ = read(corpus)
        self.assertEqual([r[0] for r in records], ["a", "b"])

    def test_doctype_and_entities_are_refused_before_parsing(self):
        xxe = '<?xml version="1.0"?><!DOCTYPE TEI [<!ENTITY x SYSTEM "file:///etc/passwd">]><TEI>&x;</TEI>'
        laughs = ('<!DOCTYPE l [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;&a;"><!ENTITY c "&b;&b;&b;&b;">]>'
                  '<TEI>&c;</TEI>')
        lower = '<!doctype tei><TEI/>'
        for payload in (xxe, laughs, lower):
            with self.assertRaises(AccessError) as ctx:
                read(payload)
            self.assertEqual(ctx.exception.kind, "unsafe_xml")

    def test_malformed_and_wrong_root_fail_closed(self):
        for payload, kind in (("<TEI><text><p>sem fim", "malformed"), ("<html><p>x</p></html>", "malformed")):
            with self.assertRaises(AccessError) as ctx:
                read(payload)
            self.assertEqual(ctx.exception.kind, kind)

    def test_size_cap(self):
        with self.assertRaises(AccessError) as ctx:
            read(tei_doc(), max_bytes=100)
        self.assertEqual(ctx.exception.kind, "too_large")

    def test_document_without_text_is_an_error_not_a_record(self):
        records, errors = read(tei_doc(body=""))
        # The head alone is still text; drop it too.
        records, errors = read(tei_doc(body="").replace("<head>CAPÍTULO I</head>", ""))
        self.assertEqual(records, [])
        self.assertEqual(len(errors), 1)

    def test_connector_reads_gzipped_tei(self):
        with tempfile.TemporaryDirectory() as tmp:
            with gzip.open(Path(tmp) / "c.xml.gz", "wt", encoding="utf-8") as fh:
                fh.write(tei_doc())
            entry = {"id": "fixture", "connector": {"reader": {"format": "tei"},
                                                    "assets": [{"name": "c.xml.gz", "format": "tei"}]}}
            records = list(LocalFilesConnector(entry, Path(tmp)).stream_records())
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].meta["licence"]["code"], "CC-BY-4.0")


class PerDocumentLicences(unittest.TestCase):
    ENTRY = {"id": "fixture", "status": "LOCALLY_VALIDATED", "access": {"type": "open_download"},
             "license": {"code": "per_document", "per_document": True, "evidence": "fixture"},
             "privacy": {"personal_data": False}}

    def test_urls_map_to_codes_and_anything_else_is_unknown(self):
        cases = {"https://creativecommons.org/licenses/by-sa/4.0/": "CC-BY-SA-4.0",
                 "http://creativecommons.org/licenses/by-nc-nd/3.0/br/": "CC-BY-NC-ND-3.0",
                 "https://creativecommons.org/publicdomain/zero/1.0/": "CC0-1.0",
                 "https://example.org/terms": "unknown", None: "unknown",
                 "https://creativecommons.org/licenses/by-xx/4.0/": "unknown"}
        for url, code in cases.items():
            self.assertEqual(policy.license_from_url(url), code, url)

    def test_unknown_document_licence_never_becomes_allowed(self):
        for op in ("EXPORT_SAMPLES", "SEND_TO_EXTERNAL_MODEL", "TRAIN_MODEL", "REDISTRIBUTE"):
            d = policy.decide(self.ENTRY, op, document_license="unknown")
            self.assertNotEqual(d.state, "ALLOWED", op)

    def test_known_document_licence_decides_per_operation(self):
        self.assertEqual(policy.decide(self.ENTRY, "EXPORT_STATISTICS", document_license="CC-BY-4.0").state, "ALLOWED")
        nd = policy.decide(self.ENTRY, "PUBLISH_DERIVATIVES", document_license="CC-BY-NC-ND-4.0")
        self.assertEqual(nd.state, "DENIED")
        model = policy.decide(self.ENTRY, "SEND_TO_EXTERNAL_MODEL", document_license="CC-BY-NC-4.0")
        self.assertEqual(model.state, "REQUIRES_PERMISSION")

    def test_share_alike_3_may_go_to_4_but_not_reverse(self):
        self.assertEqual(policy.decide(self.ENTRY, "PUBLISH_DERIVATIVES", destination="CC-BY-SA-4.0",
                                       document_license="CC-BY-SA-3.0").state, "ALLOWED")
        self.assertEqual(policy.decide(self.ENTRY, "PUBLISH_DERIVATIVES", destination="CC-BY-SA-3.0",
                                       document_license="CC-BY-SA-4.0").state, "DENIED")


CONLLU = """# newdoc id = doc-A
# newpar id = doc-A-p1
# sent_id = s1
# text = Primeira frase.
1\tPrimeira\t_\t_\t_\t_\t_\t_\t_\t_
2\tfrase\t_\t_\t_\t_\t_\t_\t_\t_

# sent_id = s2
# text = Segunda frase.
1-2\tSegunda\t_\t_\t_\t_\t_\t_\t_\t_
1\tSeg\t_\t_\t_\t_\t_\t_\t_\t_
2\tunda\t_\t_\t_\t_\t_\t_\t_\t_

# newdoc id = doc-B
# sent_id = s3
# text = Outro documento.
# genre = blog
1\tOutro\t_\t_\t_\t_\t_\t_\t_\t_
"""


class ConlluDocuments(unittest.TestCase):
    def records(self):
        import io
        errors = []
        stream = io.BytesIO(CONLLU.encode("utf-8"))
        return list(read_conllu(iter_lines(stream, ReadLimits(), errors), errors)), errors

    def test_document_and_paragraph_carry_to_every_sentence(self):
        recs, errors = self.records()
        self.assertEqual(errors, [])
        self.assertEqual([(r[0], r[2]["doc_id"], r[2]["par_id"]) for r in recs],
                         [("s1", "doc-A", "doc-A-p1"), ("s2", "doc-A", "doc-A-p1"), ("s3", "doc-B", None)])
        self.assertEqual(recs[1][2]["tokens"], 2, "multiword range lines are not tokens")

    def test_last_sentence_keeps_its_metadata(self):
        recs, _ = self.records()
        self.assertEqual(recs[-1][2]["genre"], "blog")

    def test_reverse_view_round_trips_the_sentence_layer(self):
        recs, _ = self.records()
        import io
        again = list(read_conllu(iter_lines(io.BytesIO(to_conllu_text(recs).encode()), ReadLimits(), []), []))
        self.assertEqual([(r[0], r[1], r[2]["doc_id"], r[2]["par_id"]) for r in again],
                         [(r[0], r[1], r[2]["doc_id"], r[2]["par_id"]) for r in recs])


class ManifestAndCache(unittest.TestCase):
    def test_per_document_manifest_never_inherits_the_card(self):
        from voznativa.corpus.connectors import CorpusRecord
        from voznativa.corpus.processing import manifest_row, provenance
        entry = dict(PerDocumentLicences.ENTRY)
        recs = provenance(entry, [CorpusRecord("fixture", "a", "d1", "texto um", {"licence": {"code": "CC-BY-4.0"}}),
                                  CorpusRecord("fixture", "a", "d2", "texto dois", {"doc_id": "D2"})])
        with_lic, without = manifest_row(entry, recs[0]), manifest_row(entry, recs[1])
        self.assertEqual(with_lic["document_license"], "CC-BY-4.0")
        self.assertEqual(with_lic["policy"]["EXPORT_STATISTICS"], "ALLOWED")
        self.assertEqual(without["document_license"], "unknown")
        self.assertEqual(without["doc_id"], "D2")
        # CP14 (UNCHECKED_ALL, confirmed): a row missing its policy entries passed vacuously; both rows
        # must decide the same operations.
        self.assertEqual(set(without["policy"]), set(with_lic["policy"]))
        self.assertGreater(len(without["policy"]), 1)
        self.assertTrue(all(state != "ALLOWED" for op, state in without["policy"].items()
                            if op != "EXPORT_STATISTICS"), without["policy"])
        self.assertNotIn("text", without)

    def test_cache_inside_a_git_work_tree_is_refused(self):
        import os
        from voznativa.corpus.connectors import cache_dir
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".git").mkdir()
            old = os.environ.get("VOZNATIVA_CORPUS_CACHE")
            os.environ["VOZNATIVA_CORPUS_CACHE"] = str(Path(tmp) / "cache")
            try:
                with self.assertRaises(AccessError) as ctx:
                    cache_dir("x")
                self.assertEqual(ctx.exception.kind, "cache_in_repository")
            finally:
                if old is None:
                    os.environ.pop("VOZNATIVA_CORPUS_CACHE")
                else:
                    os.environ["VOZNATIVA_CORPUS_CACHE"] = old


if __name__ == "__main__":
    unittest.main()
