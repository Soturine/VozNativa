"""v0.7.0 CP15 (README/DX addendum): the README cannot drift from the software.

* every relative link in README.md and docs/README.md resolves;
* every `voznativa <subcommand>` it mentions exists;
* the counts it states (sources, integrated sources, subcommands) match the code;
* every quickstart command runs and gives the documented outcome."""
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

README = (ROOT / "README.md").read_text(encoding="utf-8")
QS = ROOT / "examples" / "quickstart"
ENV = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8")


def subcommands() -> set:
    from voznativa.cli import build_parser
    parser = build_parser()
    action = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
    return set(action.choices)


def cli(*args):
    done = subprocess.run([sys.executable, "-m", "voznativa", *args], cwd=ROOT, capture_output=True, env=ENV)
    return done.returncode, done.stdout.decode("utf-8")


class Links(unittest.TestCase):
    def test_relative_links_resolve(self):
        for doc in (ROOT / "README.md", ROOT / "docs" / "README.md", QS / "README.md"):
            text = doc.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                with self.subTest(doc=doc.name, target=target):
                    self.assertTrue((doc.parent / target).exists(), f"{doc.name}: {target}")

    def test_anchors_point_to_headings(self):
        headings = {re.sub(r"[^\w\- ]", "", h.lower()).strip().replace(" ", "-")
                    for h in re.findall(r"(?m)^#{1,6} (.+)$", README)}
        for anchor in re.findall(r"\]\(#([^)]+)\)", README):
            self.assertIn(anchor, headings)


class CommandsAndCounts(unittest.TestCase):
    def test_every_mentioned_subcommand_exists(self):
        known = subcommands()
        mentioned = set(re.findall(r"voznativa ([a-z][a-z-]+)", README)) - {"rewrite-verse"}
        self.assertTrue(mentioned)
        self.assertEqual(mentioned - known, set())
        for name in re.findall(r"`([a-z][a-z-]+)(?: [A-Z…]|`)", README.split("## CLI", 1)[1].split("##", 1)[0]):
            self.assertIn(name, known | {"blind-"}, name)

    def test_stated_counts_match_the_code(self):
        from voznativa.corpus.registry import load_registry, summary
        s = summary(load_registry())
        self.assertIn(f"{s['sources']} fontes", README)
        self.assertIn(f"{s['by_status']['EVALUATION_INTEGRATED']} integradas", README)
        self.assertIn(f"lista os {len(subcommands())} subcomandos", README)

    def test_version_matches(self):
        from voznativa import __version__
        self.assertIn(f"`{__version__}`", README)
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(f'version: "{__version__}"', skill)
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["version"], __version__)


class Quickstart(unittest.TestCase):
    def test_first_use_commands(self):
        o, boa, ruim = (str(QS / n) for n in ("original.txt", "candidata-boa.txt", "candidata-ruim.txt"))
        code, out = cli("compare", o, boa)
        self.assertEqual((code, json.loads(out)["status"]), (3, "no_deterministic_issues"))
        code, out = cli("compare", o, ruim)
        report = json.loads(out)
        self.assertEqual((code, report["status"]), (1, "fail"))
        self.assertIn("negation_changed", {i["code"] for i in report["issues"] if i["severity"] == "critical"})
        self.assertEqual(json.loads(cli("plan", o)[1])["decision"], "edit")
        self.assertEqual(json.loads(cli("plan", str(QS / "email.txt"))[1])["decision"], "no_change")
        diag = json.loads(cli("diagnose", str(QS / "erros.txt"))[1])
        self.assertEqual({d["type"] for d in diag["diagnostics"]}, {"repeated_word", "weekday_date_mismatch"})
        code, text = cli("rewrite", str(QS / "erros.txt"), "--mode", "PROOFREAD", "--text-only")
        self.assertEqual(text.strip(), "O relatório foi enviado para o cliente na terça-feira, 13/11/2026.")
        self.assertEqual(json.loads(cli("route", str(QS / "email.txt"))[1])["genre"]["value"], "email")

    def test_stub_provider_short_and_long(self):
        stub = (QS / "stub_provider.py").as_posix()
        code, out = cli("rewrite", str(QS / "original.txt"), "--cmd", json.dumps([sys.executable, stub]))
        short = json.loads(out)
        self.assertEqual(short["outcome"], "needs_judgment")
        self.assertNotIn("É importante destacar", short["text"])
        self.assertIn("não pode ultrapassar R$ 12.000,00", short["text"])
        code, out = cli("rewrite", str(QS / "documento-longo.md"), "--long-form", "on", "--segment-words", "80",
                        "--cmd", json.dumps([sys.executable, stub]))
        long = json.loads(out)
        self.assertEqual((long["outcome"], long["provider_calls"], len(long["units"])), ("needs_judgment", 6, 8))
        self.assertEqual(sum(u["outcome"] == "protected" for u in long["units"]), 2)
        self.assertEqual(long["global_report"]["status"], "no_deterministic_issues")
        self.assertIn("```\nrelatorio --trimestre 3 --formato pdf\n```", long["text"])


if __name__ == "__main__":
    unittest.main()
