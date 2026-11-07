"""v0.8 CP8: quality axes as labelled deterministic proxies (voznativa/axes.py).

Every axis must say ``signal`` on a representative defect, ``ok`` on its
control, and ``not_applicable`` (never ``ok``) when it has nothing to
measure. The report must state that it is not a quality score."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.axes import PROXY_NOTE, evaluate  # noqa: E402
from voznativa.profile import build  # noqa: E402
from voznativa.router import route  # noqa: E402

DRAFT = ("É importante destacar que o relatório trimestral será enviado até sexta-feira, 14/11/2025. "
         "Vale ressaltar que o orçamento não pode ultrapassar R$ 12.000,00.")
CLEAN = "O relatório trimestral será enviado até sexta-feira, 14/11/2025. O orçamento não pode passar de R$ 12.000,00."
EMAIL = ("Oi, Paula!\n\nConferi a planilha e está tudo certo. Pode mandar para o financeiro hoje à tarde.\n\n"
         "Abraço,\nRafa")


def axes(original, candidate, profile=None):
    return evaluate(original, candidate, route(original), profile)


class Axes(unittest.TestCase):

    def test_labelled_as_proxy(self):
        report = axes(DRAFT, CLEAN)
        self.assertEqual(report["note"], PROXY_NOTE)
        self.assertIn("not a quality", report["note"])

    def test_formula_removed_is_ok_formula_added_is_a_signal(self):
        good = axes(DRAFT, CLEAN)["axes"]["editorial"]
        self.assertEqual((good["status"], good["removed"]), ("ok", ["empty_metadiscourse"]))
        bad = axes(CLEAN, "É importante destacar que " + CLEAN[0].lower() + CLEAN[1:])["axes"]["editorial"]
        self.assertEqual(bad["status"], "signal")
        self.assertIn("empty_metadiscourse", bad["introduced"])

    def test_changing_a_text_that_needed_nothing(self):
        report = axes(EMAIL, EMAIL.replace("Conferi a planilha", "Verifiquei a planilha").replace("Abraço", "Atenciosamente"))
        self.assertEqual(report["axes"]["unnecessary_change"]["status"], "signal")
        self.assertEqual(axes(EMAIL, EMAIL)["axes"]["unnecessary_change"]["status"], "ok")

    def test_slang_introduced(self):
        report = axes(CLEAN, CLEAN.replace("O orçamento", "Mano, o orçamento"))
        self.assertEqual(report["axes"]["slang_and_epoch"]["status"], "signal")
        self.assertIn("slang_and_epoch", report["signals"])
        self.assertEqual(axes(DRAFT, CLEAN)["axes"]["slang_and_epoch"]["status"], "ok")

    def test_genre_drift_and_abstention(self):
        drift = axes(EMAIL, "oi paula, conferi a planilha, tá tudo certo, pode mandar pro financeiro hj kkk")["axes"]["genre"]
        self.assertEqual((drift["status"], drift["source"], drift["candidate"]), ("signal", "email", "whatsapp"))
        self.assertEqual(axes(EMAIL, EMAIL)["axes"]["genre"]["status"], "ok")
        # The router abstains on a short formal reply: the axis says so instead of passing.
        abstained = axes("vc viu o deploy? nn subiu ainda kkk", "A implantação ainda não ocorreu.")["axes"]["genre"]
        self.assertEqual(abstained["status"], "not_applicable")

    def test_voice_needs_a_profile(self):
        self.assertEqual(axes(DRAFT, CLEAN)["axes"]["voice"]["status"], "not_applicable")
        samples = ["vc viu o deploy? nn subiu ainda kkk tá osso hj", "bora fechar isso amanhã cedo? tô sem tempo hj",
                   "nn rolou o teste, vou rodar dnv mais tarde blz", "fechou, amanhã cedo eu vejo isso com calma"] * 5
        profile = build([{"text": s, "channel": "whatsapp"} for s in samples])
        report = axes("vc viu o deploy? nn subiu ainda kkk", "Prezados, informo que a implantação ainda não ocorreu.",
                      profile)
        voice = report["axes"]["voice"]
        self.assertEqual(voice["status"], "signal")
        self.assertGreater(voice["candidate_distance"], voice["source_distance"])
        same = axes("vc viu o deploy? nn subiu ainda kkk", "vc viu o deploy? nn subiu ainda kkk", profile)
        self.assertEqual(same["axes"]["voice"]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
