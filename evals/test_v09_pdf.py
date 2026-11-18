"""v0.9 CP5 (V09-GAP-13): PDF extraction with protected lines, and annotated copies.

The PDF is built here with pypdf's own objects (Helvetica, WinAnsi encoding):
a short report on a school vegetable garden with a hyphenated line break, a
ligature, a display equation and a line of code. Skipped when the optional
dependency pypdf is not installed (as in the suite against the wheel, which
installs only the declared dependencies).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import pypdf
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
except ImportError:   # optional dependency
    pypdf = None

from voznativa import pdf  # noqa: E402

LINES_PAGE_1 = ["A horta escolar produziu 40 quilos de alface no semestre.",
                "Os alunos registraram a colheita em planilhas sema-",
                "nais, conferidas pela professora de ciências.",
                "",
                "y = 2x + 3",
                "",
                "As planilhas semanais ficam na biblioteca."]
LINES_PAGE_2 = ["O sistema de rega usa um controlador simples:", "int litros = 5;", "",
                "A eficiência da rega foi maior no inverno."]


def _escape(line: str) -> bytes:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("cp1252")


def build_pdf(path: Path, pages, ligature=False) -> Path:
    writer = pypdf.PdfWriter()
    font = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"), NameObject("/Encoding"): NameObject("/WinAnsiEncoding")}))
    for lines in pages:
        page = writer.add_blank_page(595, 842)
        body = b"BT /F1 11 Tf 72 770 Td 16 TL " + b" ".join(b"(" + _escape(l) + b") Tj T*" for l in lines) + b" ET"
        stream = DecodedStreamObject()
        stream.set_data(body)
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject(
            {NameObject("/F1"): font})})
        page[NameObject("/Contents")] = writer._add_object(stream)
    with open(path, "wb") as fh:
        writer.write(fh)
    return path


@unittest.skipIf(pypdf is None, "optional dependency pypdf not installed")
class PdfWorkflow(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = build_pdf(self.tmp / "horta.pdf", [LINES_PAGE_1, LINES_PAGE_2])

    def test_extraction_keeps_pages_and_protects_equations_and_code(self):
        ir = pdf.extract(self.src)
        self.assertEqual(ir["summary"]["pages"], 2)
        texts = [e["text"] for e in ir["elements"]]
        self.assertIn("Os alunos registraram a colheita em planilhas semanais, conferidas pela professora de ciências.",
                      texts, "hyphen joined because 'semanais' occurs elsewhere")
        kinds = {(p["kind"], p["text"]) for p in ir["protected"]}
        self.assertEqual(kinds, {("equation", "y = 2x + 3"), ("code", "int litros = 5;")})
        self.assertIn("[[EQ-1-1]]", texts)
        self.assertEqual({e["page"] for e in ir["elements"] if "rega" in e["text"]}, {2})
        self.assertFalse(any(e["editable"] for e in ir["elements"] if e["type"] != "paragraph"))

    def test_unknown_hyphenation_is_kept_and_reported(self):
        src = build_pdf(self.tmp / "h.pdf", [["O lote foi entregue pelo forne-", "cedor na terça."]])
        ir = pdf.extract(src)
        self.assertIn("forne- cedor", ir["elements"][0]["text"])
        self.assertEqual(ir["hyphenation_kept"], [{"page": 1, "word": "fornecedor"}])

    def test_a_malformed_pdf_is_a_clear_error(self):
        bad = self.tmp / "quebrado.pdf"
        bad.write_bytes(b"%PDF-1.4\nisto nao e um pdf\n%%EOF")
        with self.assertRaises(ValueError) as ctx:
            pdf.extract(bad)
        self.assertIn("quebrado.pdf", str(ctx.exception))

    def test_ligatures_are_normalised(self):
        self.assertEqual(pdf.normalise("eﬁciência e ﬂuxo"), "eficiência e fluxo")

    def test_annotate_writes_a_new_file_and_never_the_original(self):
        before = self.src.read_bytes()
        out = self.tmp / "anotado.pdf"
        result = pdf.annotate(self.src, [{"page": 2, "text": "Sugestão: 'controlador simples' -> 'controlador'"}],
                              out)
        self.assertEqual(result["pages_annotated"], [2])
        self.assertEqual(self.src.read_bytes(), before)
        reader = pypdf.PdfReader(str(out))
        annots = reader.pages[1].get("/Annots")
        self.assertEqual(len(annots), 1)
        self.assertIn("controlador", annots[0].get_object()["/Contents"])
        self.assertIsNone(reader.pages[0].get("/Annots"))
        for bad, needle in ((self.src, "new file"), (out, "already exists")):
            with self.subTest(bad=bad.name), self.assertRaises(ValueError) as ctx:
                pdf.annotate(self.src, [{"page": 1, "text": "x"}], bad)
            self.assertIn(needle, str(ctx.exception))
        with self.assertRaises(ValueError):
            pdf.annotate(self.src, [{"page": 9, "text": "x"}], self.tmp / "z.pdf")

    def test_cli_extract_text_for_rewrite(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT))
        txt = self.tmp / "horta.txt"
        done = subprocess.run([sys.executable, "-B", "-m", "voznativa", "pdf", "extract", str(self.src), "--out",
                               str(self.tmp / "ir.json"), "--text", str(txt)], capture_output=True, env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["summary"]["protected"], 2)
        self.assertIn("[[CODE-2-1]]", txt.read_text(encoding="utf-8"))


class WithoutPypdf(unittest.TestCase):

    def test_missing_dependency_is_a_clear_error(self):
        real = sys.modules.get("pypdf")
        sys.modules["pypdf"] = None       # makes "import pypdf" raise ImportError
        try:
            with self.assertRaises(pdf.PdfUnavailable) as ctx:
                pdf.extract("qualquer.pdf")
            self.assertIn("pip install pypdf", str(ctx.exception))
        finally:
            if real is None:
                sys.modules.pop("pypdf", None)
            else:
                sys.modules["pypdf"] = real


if __name__ == "__main__":
    unittest.main()
