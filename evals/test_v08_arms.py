"""v0.8 CP5: benchmark arms B0-B6 behind one interface (voznativa/arms.py).

No test here calls a real model: arms that need one run against a stub that
declares ``synthetic = True`` and must come out as SYNTHETIC_FIXTURE, never
as a provider measurement. Without a provider they are NOT_RUN."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import arms  # noqa: E402
from voznativa.engine import skill_prompt  # noqa: E402
from voznativa.router import route  # noqa: E402

TEXT = ("É importante destacar que o relatório será enviado até sexta-feira, 14/11/2025. "
        "O orçamento não pode ultrapassar R$ 12.000,00.")
UNSAFE = "O relatório será enviado até sexta-feira, 14/11/2025. O orçamento pode ultrapassar R$ 12.000,00."
CASE = {"id": "c1", "text": TEXT, "must_preserve": ["14/11/2025", "não pode"]}


class Stub:
    """Always answers the same text; records the prompts it got."""
    id = "stub-unsafe"
    synthetic = True

    def __init__(self, answer):
        self.answer, self.prompts = answer, []

    def generate(self, prompt, n=1):
        self.prompts.append(prompt)
        return [f"<final>{self.answer}</final>"] * n


def ctx(case):
    return route(case["text"])


class Arms(unittest.TestCase):

    def test_arms_without_what_they_need_are_not_run(self):
        result = arms.run([CASE], list(arms.ARMS), ctx)
        for arm, needs in ((a, s["needs"]) for a, s in arms.ARMS.items()):
            with self.subTest(arm=arm):
                self.assertEqual(result["summary"][arm]["status"], "NOT_RUN" if needs else "EXECUTED")
        self.assertNotIn("unsafe_outputs", result["summary"]["B4-system"])

    def test_offline_arms(self):
        b0 = arms.produce("B0-original", TEXT, ctx(CASE))
        self.assertEqual((b0["output"], b0["evidence"]), (TEXT, "ENGINE_EXECUTED"))
        errors = "O relatório foi enviado para o o cliente na terça-feira, 13/11/2026."
        b2 = arms.produce("B2-deterministic", errors, route(errors))
        self.assertEqual(b2["output"], "O relatório foi enviado para o cliente na terça-feira, 13/11/2026.")

    def test_a_stub_is_a_synthetic_fixture_never_a_measurement(self):
        stub = Stub(UNSAFE)
        out = arms.produce("B1-one-line", TEXT, ctx(CASE), stub)
        self.assertEqual(out["evidence"], "SYNTHETIC_FIXTURE")
        self.assertTrue(stub.prompts[0].startswith(arms.ONE_LINE))

    def test_b3_sends_exactly_the_skill_prompt(self):
        stub = Stub(TEXT)
        arms.produce("B3-skill-prompt", TEXT, ctx(CASE), stub)
        self.assertEqual(stub.prompts, [skill_prompt(TEXT, ctx(CASE))])

    def test_the_gates_are_what_separates_b4_from_b5(self):
        result = arms.run([CASE], ["B4-system", "B5-ablation-no-gates"], ctx, provider=Stub(UNSAFE))
        b4, b5 = result["summary"]["B4-system"], result["summary"]["B5-ablation-no-gates"]
        self.assertEqual(b5["unsafe_outputs"]["k"], 1, "without gates the negation loss is delivered")
        self.assertEqual(b4["unsafe_outputs"]["k"], 0, "the engine returns the original instead")
        b4_row = next(r for r in result["rows"] if r["arm"] == "B4-system")
        self.assertEqual(b4_row["outcome"], "returned_original")
        self.assertEqual(b5["must_preserve"]["kept"], 1)
        self.assertEqual(b4["must_preserve"]["kept"], 2)
        self.assertEqual(b4["evidence"], ["SYNTHETIC_FIXTURE"])

    def test_rows_keep_hashes_not_texts(self):
        result = arms.run([CASE], ["B0-original", "B5-ablation-no-gates"], ctx, provider=Stub(UNSAFE))
        dumped = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("orçamento pode ultrapassar", dumped)
        self.assertNotIn(TEXT, dumped)

    def test_unknown_arm(self):
        with self.assertRaises(ValueError):
            arms.produce("B9", TEXT, ctx(CASE))


class SkillPromptIsTheCliPrompt(unittest.TestCase):

    def test_rewrite_prompt_prints_skill_prompt(self):
        path = ROOT / "examples" / "quickstart" / "original.txt"
        done = subprocess.run([sys.executable, "-B", "-m", "voznativa", "rewrite-prompt", str(path)],
                              capture_output=True, cwd=ROOT)
        self.assertEqual(done.returncode, 0, done.stderr)
        text = path.read_text(encoding="utf-8-sig")         # as cli._read does (universal newlines)

        def lf(s):
            return s.replace("\r\n", "\n").rstrip("\n")
        self.assertEqual(lf(done.stdout.decode("utf-8")), lf(skill_prompt(text, route(text))))


if __name__ == "__main__":
    unittest.main()
