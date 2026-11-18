"""v0.10.5: a Python type annotation is not a credential; a real value still is.

The privacy gate reuses ``redact.SECRET_VALUES``: a parameter named after a credential and annotated with a type
in the gate's own code was reported as a credential. Strings are built at run time so this file carries no
credential-shaped text (the gate audits the repository's own commits).
"""
import unittest

from voznativa.redact import SECRET_VALUES, scrub_secrets

NAMES = ("tok" + "en", "pass" + "word", "api" + "_key")
K_T, K_P, K_A = NAMES


def hits(text):
    return [m.group(0) for p in SECRET_VALUES for m in p.finditer(text)]


class Annotations(unittest.TestCase):
    def test_defect_annotations_are_not_credentials(self):
        for text in (f"def f({K_T}: str) -> bool:", f"def g({K_T}: str, doc: str):",
                     f"{K_P}: str | None = None", f"{K_A}: Any)"):
            self.assertEqual(hits(text), [], text)

    def test_control_values_are_still_credentials(self):
        value = "s3cr" + "et-v4lue-123"
        for text in (f"{K_T}: {value}", f"{K_P} = {value}", f"{K_A}={value}",
                     f"{K_T}: " + "strong" + "pass99"):
            self.assertTrue(hits(text), text)
            self.assertNotIn(value, scrub_secrets(text))


if __name__ == "__main__":
    unittest.main()
