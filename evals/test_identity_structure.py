"""Regression tests for false greens found in the pre-push qualification audit."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.compare import compare
from voznativa.project import ground


class IdentityKeepsStructure(unittest.TestCase):
    def test_collapsing_a_markdown_list_is_not_identical(self):
        report = compare("Passos:\n- instalar\n- rodar", "Passos: - instalar - rodar")
        self.assertNotEqual(report["status"], "identical")
        self.assertFalse(report["safe_to_auto_accept"])

    def test_merging_paragraphs_is_not_identical(self):
        self.assertNotEqual(compare("Primeiro.\n\nSegundo.", "Primeiro. Segundo.")["status"], "identical")

    def test_layout_noise_is_still_identical(self):
        # Trailing spaces, CRLF, repeated spaces and extra blank lines do not change meaning or rendering.
        a = "Primeiro  item.\r\n\r\n\r\nSegundo item.   \n"
        b = "Primeiro item.\n\nSegundo item."
        self.assertEqual(compare(a, b)["status"], "identical")


if __name__ == "__main__":
    unittest.main()
