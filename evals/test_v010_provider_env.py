"""v0.10 CP13 (V08-GAP-23): the inherit default warns when credentials reach the model command."""
import os
import unittest
from unittest import mock

from voznativa.providers import CommandProvider, inherited_credential_warnings


class InheritWarning(unittest.TestCase):
    def test_names_not_values_and_only_for_inherit(self):
        env = {"PATH": "x", "SERVICE_API_KEY": "s3cr3t-value", "GH_TOKEN": "tok-value", "HOME": "/h"}
        warning = inherited_credential_warnings("inherit", env)[0]
        self.assertIn("2 credential-like", warning)
        self.assertIn("SERVICE_API_KEY", warning)
        self.assertNotIn("s3cr3t-value", warning)
        self.assertNotIn("tok-value", warning)
        self.assertEqual(inherited_credential_warnings("minimal", env), [])
        self.assertEqual(inherited_credential_warnings("inherit", {"PATH": "x"}), [])

    def test_provider_carries_the_warning(self):
        with mock.patch.dict(os.environ, {"DEMO_SECRET": "v"}, clear=False):
            inherit = CommandProvider(["python", "-c", "print(1)"])
            minimal = CommandProvider(["python", "-c", "print(1)"], env="minimal")
        self.assertTrue(any("credential-like" in w for w in inherit.warnings))
        self.assertFalse(any("credential-like" in w for w in minimal.warnings))


if __name__ == "__main__":
    unittest.main()
