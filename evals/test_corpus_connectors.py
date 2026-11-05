"""v0.6.0 connectors: bounded reads of untrusted files. Offline: every case
builds its own files; downloads are refused before any network I/O."""
import copy
import gzip
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.corpus.connectors import (AccessError, LocalFilesConnector, ReadLimits, confined, download,  # noqa: E402
                                         open_text, purge)
from voznativa.corpus.policy import PolicyDenied  # noqa: E402

CONLLU = """# sent_id = CF1-1
# text = O prazo é sexta.
1\tO\to\tDET\t_\t_\t2\tdet\t_\t_
2\tprazo\tprazo\tNOUN\t_\t_\t3\tnsubj\t_\t_
3\té\tser\tAUX\t_\t_\t0\troot\t_\t_
4\tsexta\tsexta\tNOUN\t_\t_\t3\tobl\t_\tSpaceAfter=No
5\t.\t.\tPUNCT\t_\t_\t3\tpunct\t_\t_

# sent_id = CP2-1
# text = A equipa está a rever.
1\tA\to\tDET\t_\t_\t2\tdet\t_\t_
2\tequipa\tequipa\tNOUN\t_\t_\t3\tnsubj\t_\t_

"""


def entry(name, fmt, **reader):
    return {"id": "toy", "name": "Toy", "status": "CONNECTOR_READY",
            "connector": {"id": "local-files", "reader": {"format": fmt, **reader},
                          "assets": [{"name": name, "format": fmt}]}}


class Reading(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, name, data, fmt, limits=ReadLimits(), **reader):
        (self.root / name).write_bytes(data)
        connector = LocalFilesConnector(entry(name, fmt, **reader), self.root, limits)
        return list(connector.stream_records()), connector

    def test_conllu_sentences_keep_id_text_and_token_count(self):
        records, c = self.read("a.conllu", CONLLU.encode(), "conllu")
        self.assertEqual([(r.record_id, r.text, r.meta["tokens"]) for r in records],
                         [("CF1-1", "O prazo é sexta.", 5), ("CP2-1", "A equipa está a rever.", 2)])
        self.assertEqual(c.errors, [])

    def test_csv_quoted_multiline_field_and_a_cut_last_row(self):
        data = 'id,review_text,stars\n1,"bom,\nentrega rápida",5\n2,ruim,1\n3,"cortado no meio'.encode()
        records, c = self.read("r.csv", data, "csv", text_field="review_text", id_field="id")
        self.assertEqual([(r.record_id, r.text) for r in records], [("1", "bom,\nentrega rápida"), ("2", "ruim")])
        self.assertEqual(len(c.errors), 1)
        self.assertIn("unexpected end of data", c.errors[0]["error"])

    def test_csv_without_the_text_column_is_refused(self):
        with self.assertRaises(AccessError) as caught:
            self.read("r.csv", b"id,body\n1,x\n", "csv", text_field="review_text")
        self.assertEqual(caught.exception.kind, "malformed")

    def test_invalid_utf8_and_overlong_lines_are_recorded_then_budgeted(self):
        data = b'{"text": "ok"}\n' + b'\xff\xfe broken\n' + b'{"text": "' + b"x" * 2000 + b'"}\n' + b'{"text": "fim"}\n'
        limits = ReadLimits(max_line_bytes=1000, max_malformed=5)
        records, c = self.read("a.jsonl", data, "jsonl", limits)
        self.assertEqual([r.text for r in records], ["ok", "fim"])
        self.assertEqual([e["error"].split(" at")[0] for e in c.errors], ["invalid UTF-8", "line too long"])
        with self.assertRaises(AccessError) as caught:
            self.read("b.jsonl", b"\xff\n" * 10, "jsonl", ReadLimits(max_malformed=3))
        self.assertEqual(caught.exception.kind, "malformed")

    def test_record_cap_and_gzip(self):
        data = gzip.compress(("\n\n".join(f"parágrafo {i}" for i in range(50))).encode())
        (self.root / "p.txt.gz").write_bytes(data)
        c = LocalFilesConnector(entry("p.txt.gz", "txt"), self.root)
        self.assertEqual(len(list(c.stream_records(max_records=7))), 7)

    def test_gzip_bomb_is_stopped(self):
        bomb = gzip.compress(b"\n" * 30_000_000)
        (self.root / "bomb.txt.gz").write_bytes(bomb)
        c = LocalFilesConnector(entry("bomb.txt.gz", "txt"), self.root, ReadLimits(max_ratio=50))
        with self.assertRaises(AccessError) as caught:
            list(c.stream_records())
        self.assertEqual(caught.exception.kind, "decompression_bomb")

    def test_zip_member_leaving_the_archive_is_refused(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            z.writestr("../../escape.txt", "x")
        (self.root / "evil.zip").write_bytes(buffer.getvalue())
        with self.assertRaises(AccessError) as caught:
            open_text(self.root / "evil.zip", ReadLimits())
        self.assertEqual(caught.exception.kind, "path_traversal")

    def test_oversized_file_is_refused_before_reading(self):
        (self.root / "big.txt").write_bytes(b"x" * 5000)
        with self.assertRaises(AccessError) as caught:
            open_text(self.root / "big.txt", ReadLimits(max_file_bytes=1000))
        self.assertEqual(caught.exception.kind, "too_large")

    def test_integrity_compares_the_recorded_sha256(self):
        (self.root / "a.conllu").write_bytes(CONLLU.encode())
        e = entry("a.conllu", "conllu")
        e["connector"]["assets"][0]["sha256"] = "0" * 64
        self.assertFalse(LocalFilesConnector(e, self.root).validate_integrity()["ok"])
        e["connector"]["assets"][0].pop("sha256")
        self.assertTrue(LocalFilesConnector(e, self.root).validate_integrity()["ok"])


class Boundaries(unittest.TestCase):
    def test_paths_stay_inside_the_corpus_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(confined(root, "sub/a.txt"), (root / "sub" / "a.txt").resolve())
            for bad in ("../a.txt", "/etc/passwd", "sub/../../a.txt", "C:\\Windows\\win.ini", "..\\a.txt", ""):
                with self.assertRaises(AccessError, msg=bad) as caught:
                    confined(root, bad)
                self.assertEqual(caught.exception.kind, "path_traversal")

    def test_download_is_refused_by_policy_or_host_before_any_io(self):
        verified = {"source": {"date": "d", "url": "u", "method": "m", "result": "verified"},
                    "access": {"date": "d", "method": "m", "result": "data_read"}}
        base = {"id": "toy", "status": "ACCESS_VERIFIED", "verification": verified,
                "urls": {"official": "https://example.org/toy"}, "access": {"type": "open_download"},
                "license": {"code": "CC0-1.0", "per_document": False, "evidence": "t"},
                "privacy": {"personal_data": False}}
        with tempfile.TemporaryDirectory() as tmp:
            unknown = dict(copy.deepcopy(base), license={"code": "unknown", "per_document": False, "evidence": "t"})
            with self.assertRaises(PolicyDenied):
                download(unknown, {"name": "a.txt", "url": "https://example.org/a.txt"}, Path(tmp))
            for url in ("https://evil.example.com/a.txt", "http://example.org/a.txt"):
                with self.assertRaises(AccessError) as caught:
                    download(base, {"name": "a.txt", "url": url}, Path(tmp))
                self.assertEqual(caught.exception.kind, "host_not_allowed", url)
            with self.assertRaises(AccessError):
                download(base, {"name": "../a.txt", "url": "https://example.org/a.txt"}, Path(tmp))
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_purge_removes_the_local_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_dir = Path(tmp) / "toy"
            copy_dir.mkdir()
            (copy_dir / "a.txt").write_text("x", encoding="utf-8")
            self.assertTrue(purge("toy", copy_dir)["removed"])
            self.assertFalse(copy_dir.exists())
            self.assertFalse(purge("toy", copy_dir)["removed"])


if __name__ == "__main__":
    unittest.main()
