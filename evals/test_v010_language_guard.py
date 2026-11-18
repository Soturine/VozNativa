"""v0.10 CP11 (V010-GAP-16): English text is not checked or edited as Portuguese.

Found by the reciprocal dogfood: on Assertiva's English README, diagnose reported "as pytest" as a
Portuguese plural_agreement error and the planner planned 29 edits (42 English words as anglicisms).
Defect tests fail on v0.9.0; controls keep Portuguese text with English terms fully checked.
"""
import unittest

from voznativa.diagnose import diagnose
from voznativa.planner import plan
from voznativa.ptbr import language_of
from voznativa.router import route

ENGLISH = ("The audit reads the suite as written and reports what it could not observe. It does not change the "
           "project, and it runs the tests only in an isolated copy. When a check is not executed, the report "
           "says so; a passing run is not evidence that the assertions are strong. Use the report as such: "
           "as evidence, not as a verdict. Install it with pip and run the audit from the repository root.")
PORTUGUESE_WITH_TERMS = ("Os resultado do deploy mostram que o pipeline falhou. O time revisou o backend e o "
                         "frontend, mas o build ainda quebra quando o cache não é limpo.")


class LanguageGuard(unittest.TestCase):
    def test_language_detection(self):
        self.assertEqual(language_of(ENGLISH)["value"], "en")
        self.assertEqual(language_of(PORTUGUESE_WITH_TERMS)["value"], "pt")
        self.assertEqual(language_of("ok")["value"], "unknown")
        self.assertEqual(language_of("Rode `the and of to is are with for that this it` agora.")["value"],
                         "unknown")          # code is not language evidence

    def test_defect_english_is_not_diagnosed_as_portuguese(self):
        report = diagnose(ENGLISH, route(ENGLISH))
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual(report["language"]["value"], "en")

    def test_defect_english_is_not_planned_for_edits(self):
        p = plan(ENGLISH, route(ENGLISH))
        self.assertEqual(p["decision"], "no_change")
        self.assertEqual(p["language"]["value"], "en")

    def test_control_portuguese_with_english_terms_is_still_checked(self):
        kinds = {d["type"] for d in diagnose(PORTUGUESE_WITH_TERMS, route(PORTUGUESE_WITH_TERMS, genre="technical"))
                 ["diagnostics"]}
        self.assertIn("plural_agreement", kinds)
        self.assertEqual(plan(PORTUGUESE_WITH_TERMS, route(PORTUGUESE_WITH_TERMS, genre="technical"))["decision"],
                         "edit")

    def test_control_a_requested_destination_still_transforms(self):
        p = plan(ENGLISH, route(ENGLISH, genre="whatsapp"))
        self.assertIn(p["decision"], ("transform", "no_change"))      # a target is the user's request
        self.assertNotEqual(p["decision"], "edit")


if __name__ == "__main__":
    unittest.main()
