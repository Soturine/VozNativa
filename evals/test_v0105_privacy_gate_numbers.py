"""v0.10.5 (V105-GAP-04): a bare number shared with a private document is a finding only in the same context.

In v0.10 the gate flagged a regex quantifier ``{2,60}`` because "2,60" occurs in a private document, and the
Watcher's id regex was changed to ``{2,63}`` only to silence it; in v0.10.5 a word count (``2387``) and the gap
register describing that change were flagged the same way. A number alone says nothing about the document;
the same number next to the same word does. Identifiers with letters keep the old rule.
"""
import contextlib
import io
import json
import unittest

from evals import test_v09_privacy_gate as _v09

_Base = _v09.PrivacyGate

PRIVATE_WITH_NUMBERS = ("Diário da horta comunitária. A colheita rendeu 2,60 quilos de tomate no canteiro 4417, "
                        "segundo a planilha HORTA_NORTE_7781.")


class NumbersNeedContext(unittest.TestCase):
    # the v0.9 gate fixture (temporary repository, private file outside it), without inheriting its tests
    _commit = _Base._commit
    tearDown = _Base.tearDown

    def setUp(self):
        _Base.setUp(self)
        self.private.write_text(PRIVATE_WITH_NUMBERS, encoding="utf-8")

    def _findings(self, text):
        self._commit("x.md", text)
        out = self.outside / "r.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.gate.main(["--base", "HEAD~1", "--private", str(self.private), "--out", str(out)])
        return json.loads(out.read_text(encoding="utf-8"))["findings"]

    def test_defect_bare_numbers_in_unrelated_context_are_not_findings(self):
        findings = self._findings('ID_RE = re.compile(r"[a-z]{2,60}")\n{"words": 4417, "band": "longo"}\n')
        self.assertNotIn("private_tokens", findings)

    def test_control_same_number_with_the_same_neighbour_is_a_finding(self):
        self.assertIn("private_tokens", self._findings("A colheita rendeu 2,60 quilos.\n"))
        self.assertIn("private_tokens", self._findings("Ver o canteiro 4417 amanhã.\n"))

    def test_control_identifiers_with_letters_keep_the_old_rule(self):
        self.assertIn("private_tokens", self._findings('{"planilha": "HORTA_NORTE_7781"}\n'))


if __name__ == "__main__":
    unittest.main()
