"""v0.9 CP6 (V09-GAP-21): pack contract, external packs and what a pack can never do.

* every bundled pack is valid under the envelope and its kind's validator;
* the example external pack (examples/packs/pesquisa-ux.yml) loads through
  VOZNATIVA_PACKS_DIR and has an observable effect: its preserved terms stop
  being anglicism findings in the plan when the community is requested;
* invalid packs are refused, never skipped: a key that would change a gate
  or run code, an invalid or huge regular expression, a path out of the
  pack, missing license or provenance, an id that is not the file name, a
  YAML object tag, an oversized file, a regional pack from the external
  folder, an id that would replace a bundled pack;
* a pack cannot relax the gates: compare gives the same report with and
  without the pack.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import packs  # noqa: E402

EXAMPLE = ROOT / "examples" / "packs" / "pesquisa-ux.yml"
TEXT = "Os participantes deram feedback detalhado, e os insights da pesquisa orientaram o novo protótipo.\n"


def cli(*args, env_extra=None, cwd=None):
    env = dict(os.environ, PYTHONPATH=str(ROOT), **(env_extra or {}))
    env.pop("VOZNATIVA_PACKS_DIR", None)
    env.update(env_extra or {})
    done = subprocess.run([sys.executable, "-B", "-m", "voznativa", *args], capture_output=True, env=env, cwd=cwd)
    return done.returncode, done.stdout.decode("utf-8"), done.stderr.decode("utf-8")


class Bundled(unittest.TestCase):

    def test_every_bundled_pack_is_valid_without_warnings(self):
        reports = [r for r in packs.inventory()["packs"] if r["source"] == "bundled"]
        self.assertGreaterEqual(len(reports), 5)
        for r in reports:
            with self.subTest(pack=r["file"]):
                self.assertEqual((r["errors"], r["warnings"]), ([], []))


@unittest.skipUnless(EXAMPLE.is_file(), "needs examples/packs from the checkout")
class ExternalPack(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.dir = self.tmp / "packs"
        self.dir.mkdir()
        self.text = self.tmp / "texto.txt"
        self.text.write_text(TEXT, encoding="utf-8")

    def write(self, name, body):
        (self.dir / name).write_text(body, encoding="utf-8")

    def plan_reasons(self, with_pack: bool):
        if with_pack:
            shutil.copy(EXAMPLE, self.dir / EXAMPLE.name)
        code, out, err = cli("plan", str(self.text), "--genre", "academic", "--community", "pesquisa-ux",
                             env_extra={"VOZNATIVA_PACKS_DIR": str(self.dir)})
        self.assertEqual(code, 0, err)
        plan = json.loads(out)
        return {x["text"].lower() for r in plan["sentences"] for x in r["reasons"]
                if x["id"] == "anglicism_out_of_domain"}

    def test_the_example_pack_is_valid(self):
        code, out, err = cli("packs", "validate", str(EXAMPLE))
        self.assertEqual(code, 0, out + err)

    def test_the_pack_has_an_observable_effect_in_the_plan(self):
        without = self.plan_reasons(with_pack=False)
        with_pack = self.plan_reasons(with_pack=True)
        self.assertTrue({"feedback", "insights"} <= without, without)
        self.assertFalse({"feedback", "insights"} & with_pack, with_pack)

    def test_a_pack_cannot_relax_the_gates(self):
        shutil.copy(EXAMPLE, self.dir / EXAMPLE.name)
        a = self.tmp / "a.txt"
        b = self.tmp / "b.txt"
        a.write_text("O feedback dos usuários não pode ser ignorado.\n", encoding="utf-8")
        b.write_text("O feedback dos usuários pode ser ignorado.\n", encoding="utf-8")
        reports = []
        for env in ({}, {"VOZNATIVA_PACKS_DIR": str(self.dir)}):
            code, out, _ = cli("compare", str(a), str(b), env_extra=env)
            reports.append((code, json.loads(out)["status"], json.loads(out)["issues"]))
        self.assertEqual(reports[0], reports[1])
        self.assertEqual(reports[0][1], "fail")

    def test_invalid_packs_are_refused_not_skipped(self):
        base = EXAMPLE.read_text(encoding="utf-8")
        cases = {
            "severity": ("pesquisa-ux.yml", base + "severity: info\n"),
            "regex": ("pesquisa-ux.yml", base.replace("legitimate_in: [academic, technical, corporate]\n",
                                                       "legitimate_in: [academic, technical, corporate]\n"
                                                       "  match_regex: \"(unclosed\"\n", 1)),
            "path": ("pesquisa-ux.yml", base + "source_file: ../../segredo.txt\n"),
            "license": ("pesquisa-ux.yml", base.replace("license: CC0-1.0\n", "")),
            "provenance": ("pesquisa-ux.yml", base.replace("  authors: [VozNativa maintainers]\n", "")),
            "id": ("outro-nome.yml", base),
            "yaml tag": ("pesquisa-ux.yml", base + "x: !!python/object/apply:os.system [\"echo oi\"]\n"),
            "bundled id": ("tech.yml", base.replace("id: pesquisa-ux", "id: tech")),
        }
        for label, (name, body) in cases.items():
            with self.subTest(case=label):
                for f in self.dir.glob("*.yml"):
                    f.unlink()
                self.write(name, body)
                code, out, err = cli("plan", str(self.text), "--community", "pesquisa-ux",
                                     env_extra={"VOZNATIVA_PACKS_DIR": str(self.dir)})
                self.assertEqual(code, 64, f"{label}: {out[:200]} {err}")
                self.assertIn("pack", err)

    def test_oversized_and_regional_external_packs(self):
        big = self.dir / "grande.yml"
        big.write_text("x: " + "a" * (packs.MAX_BYTES + 10), encoding="utf-8")
        self.assertIn("exceeds", packs.validate_file(big)["errors"][0])
        big.unlink()
        regional = packs.bundled_dirs()["regional"] / "br-norte-lex-mandioca.yml"   # checkout or installed wheel
        shutil.copy(regional, self.dir / regional.name)
        # The folder is read when a community pack is used; `packs list` checks it at any time.
        code, _, err = cli("plan", str(self.text), "--community", "tech",
                           env_extra={"VOZNATIVA_PACKS_DIR": str(self.dir)})
        self.assertEqual(code, 64)
        self.assertIn("only community packs", err)
        code, out, _ = cli("packs", "list", "--json", env_extra={"VOZNATIVA_PACKS_DIR": str(self.dir)})
        self.assertEqual(code, 0, "a regional pack is a valid pack; it is refused only as an external community pack")


class Envelope(unittest.TestCase):

    def test_forbidden_keys_anywhere(self):
        pack = {"schema_version": 2, "kind": "voznativa.community_pack", "id": "abc", "license": "MIT",
                "provenance": {"authors": ["x"], "created": "2026"}, "items": [{"term": "t", "guards": ["none"]}]}
        errors, _ = packs.envelope_problems(pack, "abc.yml", external=True)
        self.assertTrue(any("cannot change the gates" in e for e in errors), errors)

    def test_bundled_missing_metadata_is_a_warning_external_an_error(self):
        pack = {"schema_version": 2, "kind": "voznativa.community_pack", "id": "abc"}
        errors, warnings = packs.envelope_problems(pack, "abc.yml", external=False)
        self.assertEqual((len(errors), len(warnings)), (0, 2))
        errors, warnings = packs.envelope_problems(pack, "abc.yml", external=True)
        self.assertEqual((len(errors), len(warnings)), (2, 0))


if __name__ == "__main__":
    unittest.main()
