"""v0.9 CP5 (V09-GAP-13): safe DOCX workflow on a synthetic document built here.

The fixture is a minimal but valid WordprocessingML package written by the
test (a garden cooperative newsletter): a heading, plain paragraphs (one
split in two runs with the same formatting, one with characters that need
escaping), a list item, a paragraph with mixed formatting, one with a
hyperlink, one with a tab, one with a field, an empty one and a table. It
also declares ``mc:Ignorable`` prefixes, which a re-serialising XML library
would break.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import docx  # noqa: E402

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
NS = (f'{W} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
      'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14"')


def para(text, style=None, rpr="", extra=""):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f'<w:p w14:paraId="1A2B3C4D">{ppr}<w:r>{rpr}<w:t xml:space="preserve">{text}</w:t></w:r>{extra}</w:p>'


BODY = "".join([
    para("Boletim da cooperativa", style="Heading1"),
    '<w:p><w:r><w:rPr><w:sz w:val="22"/></w:rPr><w:t>A colheita de março </w:t></w:r>'
    '<w:r><w:rPr><w:sz w:val="22"/></w:rPr><w:t>rendeu 320 quilos de feijão.</w:t></w:r><w:proofErr w:type="spellStart"/></w:p>',
    para("É importante destacar que a feira &amp; o mutirão acontecem no sábado &lt;dia 12&gt;."),
    '<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>'
    '<w:r><w:t>Levar sementes de abóbora.</w:t></w:r></w:p>',
    '<w:p><w:r><w:t>Atenção: </w:t></w:r><w:r><w:rPr><w:b/></w:rPr><w:t>não regue ao meio-dia.</w:t></w:r></w:p>',
    '<w:p><w:r><w:t>Veja o </w:t></w:r><w:hyperlink r:id="rId9"><w:r><w:t>site</w:t></w:r></w:hyperlink></w:p>',
    '<w:p><w:r><w:t>Canteiro</w:t></w:r><w:r><w:tab/><w:t>Responsável</w:t></w:r></w:p>',
    '<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText> PAGE </w:instrText></w:r>'
    '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>',
    "<w:p/>",
    '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/></w:tblPr><w:tr><w:tc><w:tcPr><w:tcW w:w="2000"/></w:tcPr>'
    + para("Cebolinha") + "</w:tc></w:tr></w:tbl>",
    '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>',
])
DOCUMENT = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {NS}><w:body>{BODY}</w:body></w:document>'
PARTS = {
    "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/'
                           'package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.'
                           'openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application'
                           '/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
                           'officedocument.wordprocessingml.document.main+xml"/></Types>',
    "_rels/.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
                   'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
    "word/_rels/document.xml.rels": '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.'
                                    'openxmlformats.org/package/2006/relationships"><Relationship Id="rId9" Type="http:'
                                    '//schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target='
                                    '"https://example.org" TargetMode="External"/></Relationships>',
    "word/document.xml": DOCUMENT,
    "word/footer1.xml": f'<?xml version="1.0" encoding="UTF-8"?><w:ftr {W}>{para("Rodapé da cooperativa")}</w:ftr>',
}


def build(path: Path) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in PARTS.items():
            z.writestr(name, content)
    return path


class Fixture(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = build(self.tmp / "boletim.docx")
        self.ir = docx.extract(self.src)
        self.by_text = {e["text"]: e for e in self.ir["elements"]}


class Extract(Fixture):

    def test_types_and_protection_reasons(self):
        e = self.ir["elements"]
        self.assertEqual([x["type"] for x in e], ["heading", "paragraph", "paragraph", "list_item", "paragraph",
                                                  "paragraph", "paragraph", "paragraph", "paragraph", "table_cell"])
        self.assertTrue(e[1]["editable"], "two runs with the same formatting are one editable paragraph")
        self.assertEqual(e[1]["text"], "A colheita de março rendeu 320 quilos de feijão.")
        self.assertEqual(e[2]["text"], "É importante destacar que a feira & o mutirão acontecem no sábado <dia 12>.")
        reasons = {x["id"]: x["protected_reasons"] for x in e if not x["editable"]}
        self.assertEqual(reasons, {"p4": ["mixed formatting"], "p5": ["hyperlink"], "p6": ["tab"],
                                   "p7": ["field", "no text"], "p8": ["no text"]})
        self.assertIn("word/footer1.xml", self.ir["untouched_parts"])

    def test_extract_writes_nothing(self):
        before = self.src.read_bytes()
        docx.extract(self.src)
        self.assertEqual(self.src.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["boletim.docx"])


class Apply(Fixture):

    def test_round_trip_without_edits_keeps_every_part(self):
        out = self.tmp / "igual.docx"
        same = {x["id"]: x["text"] for x in self.ir["elements"] if x["editable"]}
        written = docx.apply(self.src, same, out)
        self.assertEqual(written["edited"], [])
        with zipfile.ZipFile(self.src) as a, zipfile.ZipFile(out) as b:
            self.assertEqual(a.namelist(), b.namelist())
            for name in a.namelist():
                self.assertEqual(a.read(name), b.read(name), name)
        self.assertEqual(docx.check(self.src, out)["status"], "PASS")

    def test_an_edit_changes_only_its_paragraph(self):
        out = self.tmp / "editado.docx"
        target = self.by_text["É importante destacar que a feira & o mutirão acontecem no sábado <dia 12>."]
        written = docx.apply(self.src, {target["id"]: "A feira & o mutirão acontecem no sábado <dia 12>."}, out)
        report = docx.check(self.src, out, allowed=written["edited"])
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["changed_paragraphs"], [target["id"]])
        self.assertTrue(report["outside_paragraphs_identical"])
        new = docx.extract(out)
        self.assertEqual(new["elements"][2]["text"], "A feira & o mutirão acontecem no sábado <dia 12>.")
        with zipfile.ZipFile(out) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        self.assertIn('mc:Ignorable="w14"', xml)
        self.assertIn('xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"', xml)
        self.assertIn("&amp; o mutirão", xml)
        self.assertNotIn("É importante destacar", xml)

    def test_formatting_of_the_first_run_is_kept(self):
        out = self.tmp / "fmt.docx"
        target = self.by_text["A colheita de março rendeu 320 quilos de feijão."]
        docx.apply(self.src, {target["id"]: "Em março, a colheita rendeu 320 quilos de feijão."}, out)
        with zipfile.ZipFile(out) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        self.assertIn('<w:r><w:rPr><w:sz w:val="22"/></w:rPr><w:t>Em março, a colheita', xml)

    def test_refusals(self):
        protected = next(x for x in self.ir["elements"] if x["protected_reasons"] == ["hyperlink"])
        cases = [({protected["id"]: "Veja a página"}, self.tmp / "a.docx", "protected"),
                 ({"p1": "duas\nlinhas"}, self.tmp / "b.docx", "one non-empty line"),
                 ({"p99": "x"}, self.tmp / "c.docx", "unknown element"),
                 ({"p1": "x"}, self.src, "new file")]
        for edits, out, needle in cases:
            with self.subTest(needle=needle), self.assertRaises(docx.DocxError) as ctx:
                docx.apply(self.src, edits, out)
            self.assertIn(needle, str(ctx.exception))
        existing = self.tmp / "existe.docx"
        existing.write_bytes(b"x")
        with self.assertRaises(docx.DocxError):
            docx.apply(self.src, {"p1": "Outro texto."}, existing)
        self.assertEqual(existing.read_bytes(), b"x")

    def test_dtd_and_entities_are_refused(self):
        hostile = self.tmp / "entidades.docx"
        with zipfile.ZipFile(self.src) as zin, zipfile.ZipFile(hostile, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = data.decode("utf-8").replace(
                        "?>\n", '?>\n<!DOCTYPE w [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;">]>\n', 1).encode("utf-8")
                zout.writestr(item, data)
        with self.assertRaises(docx.DocxError) as ctx:
            docx.extract(hostile)
        self.assertIn("DTD", str(ctx.exception))

    def test_not_a_docx(self):
        bad = self.tmp / "texto.docx"
        bad.write_text("não sou um zip", encoding="utf-8")
        with self.assertRaises(docx.DocxError):
            docx.extract(bad)


class Check(Fixture):

    def tamper(self, old, new):
        out = self.tmp / "adulterado.docx"
        with zipfile.ZipFile(self.src) as zin, zipfile.ZipFile(out, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = data.decode("utf-8").replace(old, new, 1).encode("utf-8")
                zout.writestr(item, data)
        return docx.check(self.src, out)

    def test_a_changed_protected_paragraph_fails(self):
        report = self.tamper("Veja o ", "Leia o ")
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("p5 was protected and changed", report["problems"])

    def test_a_change_outside_the_paragraphs_fails(self):
        report = self.tamper('w:w="2000"', 'w:w="2500"')
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("XML outside the paragraphs changed", report["problems"])


class TextBridge(Fixture):

    def test_blocks_map_back_and_headings_are_context_only(self):
        text, ids = docx.to_text(self.ir)
        self.assertTrue(text.startswith("## Boletim da cooperativa\n\nA colheita de março"))
        rewritten = text.replace("É importante destacar que a feira", "A feira").replace("## Boletim", "## Jornal")
        self.assertEqual(docx.from_text(self.ir, ids, rewritten),
                         {"p2": "A feira & o mutirão acontecem no sábado <dia 12>."})
        with self.assertRaises(docx.DocxError):
            docx.from_text(self.ir, ids, text + "\n\nUm parágrafo a mais.\n")


class RewriteCommand(Fixture):

    def test_rewrite_a_docx_into_a_new_file(self):
        stub = ROOT / "examples" / "quickstart" / "stub_provider.py"
        if not stub.is_file():
            self.skipTest("needs examples/quickstart/stub_provider.py from the checkout")
        out = self.tmp / "reescrito.docx"
        env = dict(os.environ, PYTHONPATH=str(ROOT), VOZNATIVA_CONFIG=str(self.tmp / "nenhum.toml"))
        done = subprocess.run([sys.executable, "-B", "-m", "voznativa", "rewrite", str(self.src), "--docx-out",
                               str(out), "--cmd", json.dumps([sys.executable, str(stub)]), "--segment-words", "40"],
                              capture_output=True, env=env, cwd=self.tmp)
        result = json.loads(done.stdout.decode("utf-8"))
        self.assertTrue(result["docx"]["applied"], result["docx"])
        self.assertEqual(result["docx"]["check"]["status"], "PASS")
        self.assertIn("A feira & o mutirão", docx.extract(out)["elements"][2]["text"])
        self.assertEqual(docx.extract(self.src)["source"]["sha256"], self.ir["source"]["sha256"])

    def test_a_docx_without_output_is_refused(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT), VOZNATIVA_CONFIG=str(self.tmp / "nenhum.toml"))
        done = subprocess.run([sys.executable, "-B", "-m", "voznativa", "rewrite", str(self.src), "--cmd", "x"],
                              capture_output=True, env=env, cwd=self.tmp)
        self.assertEqual(done.returncode, 64)
        self.assertIn("--docx-out", done.stderr.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
