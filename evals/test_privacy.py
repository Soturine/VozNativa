"""Privacy of recorded runs (v0.3.0 M6.2, hardened in v0.4.0 M0.6).

Every secret below is fictitious. v0.3.0 --redact hid texts and raw answers
but stored the full model command (credentials included), error messages
that could quote the texts, the absolute path of the cases file and an
unkeyed sha256 that reverses a short text by guessing.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.providers import CommandProvider, ProviderError
from voznativa.redact import MASK, redact_argv, scrub_message, shield

SECRET_TEXT = "É importante destacar que o prazo SEGREDO-42 é sexta."
FAKE_KEY = "sk-ant-FAKE0123456789abcdefFAKE"
FAKE_TOKEN = "ghp_FAKEFAKEFAKEFAKEFAKE0123"

# Writer answers with the secret; the judge answers JSON whose claim quotes it with an
# invalid status (judge.validate's error message used to repeat the claim verbatim).
MODEL = f"""import json, sys
prompt = sys.stdin.read()
if "RESPONSE_SCHEMA" in prompt:
    print(json.dumps({{"verdict": "equivalent", "judge_id": "fake {FAKE_TOKEN}",
                       "claims": [{{"source": "o prazo SEGREDO-42", "status": "bogus"}}]}}))
else:
    print('<final>O prazo SEGREDO-42 é sexta.</final>')
"""
FAILING_MODEL = "import sys\nsys.stderr.write('echo: ' + sys.stdin.read())\nsys.exit(3)\n"


def run_integration(tmp: Path, model_source: str, label: str, *extra: str) -> tuple[subprocess.CompletedProcess, str]:
    model = tmp / "model.py"
    model.write_text(model_source, encoding="utf-8")
    cases = tmp / "private-cases-dir" / "cases.jsonl"
    cases.parent.mkdir()
    cases.write_text(json.dumps({"id": "p1", "genre": "corporate", "text": SECRET_TEXT}) + "\n", encoding="utf-8")
    command = [sys.executable, str(model), "--api-key", FAKE_KEY, f"ANTHROPIC_TOKEN={FAKE_TOKEN}",
               "-H", f"Authorization: Bearer {FAKE_TOKEN}"]
    done = subprocess.run([sys.executable, str(ROOT / "scripts" / "llm_integration.py"), "--cases", str(cases),
                           "--cmd", json.dumps(command), "--model-label", label, "--attempts", "1", *extra],
                          capture_output=True, text=True, cwd=ROOT)
    reports = sorted((ROOT / "evals" / "integration").glob(f"*{label}*"))
    try:
        content = reports[-1].read_text(encoding="utf-8") if reports else ""
    finally:
        for report in reports:
            report.unlink()
    return done, content


class RedactedIntegrationReports(unittest.TestCase):
    def assert_nothing_sensitive(self, content: str, tmp: Path):
        # The path is checked raw and JSON-escaped: on Windows "C:\\Users\\..." is what the
        # report contains, and a raw-only check passed there by accident (found on Linux).
        for secret in ("SEGREDO-42", FAKE_KEY, FAKE_TOKEN, "private-cases-dir", str(tmp), json.dumps(str(tmp))[1:-1],
                       Path(tmp).name):
            self.assertNotIn(secret, content)
        # An unkeyed sha256 would let anyone confirm a guessed text.
        self.assertNotIn(hashlib.sha256(SECRET_TEXT.encode("utf-8")).hexdigest(), content)

    def test_redact_keeps_no_text_secret_or_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            done, content = run_integration(Path(tmp), MODEL, "privacy-unit-test", "--redact")
            self.assertEqual(done.returncode, 0, done.stderr)
            report = json.loads(content)
            self.assertTrue(report["redacted"])
            self.assertIn(MASK, json.dumps(report["command"]))
            self.assertIn("judge", (report["results"][0]["judge_error"] or "") + "judge")
            self.assert_nothing_sensitive(content, Path(tmp))

    def test_provider_error_that_echoes_the_prompt_is_scrubbed(self):
        with tempfile.TemporaryDirectory() as tmp:
            done, content = run_integration(Path(tmp), FAILING_MODEL, "privacy-unit-fail", "--redact")
            self.assertEqual(json.loads(content)["results"][0]["outcome"], "provider_error")
            self.assert_nothing_sensitive(content, Path(tmp))

    def test_credentials_are_masked_even_without_redact(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, content = run_integration(Path(tmp), MODEL, "privacy-unit-plain")
            self.assertNotIn(FAKE_KEY, content)
            self.assertNotIn(FAKE_TOKEN, content)
            self.assertIn("SEGREDO-42", content)  # texts are kept on purpose without --redact

    def test_redact_key_makes_hashes_comparable_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp, "redact.key")
            hashes = []
            for label in ("privacy-unit-k1", "privacy-unit-k2"):
                sub = Path(tmp, label)
                sub.mkdir()
                _, content = run_integration(sub, MODEL, label, "--redact", "--redact-key", str(key))
                hashes.append(json.loads(content)["results"][0]["original"]["hmac_sha256"])
            self.assertEqual(hashes[0], hashes[1])
            self.assertNotIn(key.read_text(encoding="ascii"), content)


class RedactionHelpers(unittest.TestCase):
    def test_argv_masks_flags_assignments_and_known_formats(self):
        argv = ["claude", "-p", "--api-key", FAKE_KEY, "--token=abc123", "OPENAI_API_KEY=xyz",
                "-H", "Authorization: Bearer abc", f"--note={FAKE_TOKEN}", "--model", "claude-sonnet-5-5"]
        out = redact_argv(argv)
        self.assertEqual(out[:3], ["claude", "-p", "--api-key"])
        self.assertNotIn(FAKE_KEY, " ".join(out))
        self.assertNotIn("abc123", " ".join(out))
        self.assertNotIn("xyz", " ".join(out))
        self.assertNotIn("Bearer abc", " ".join(out))
        self.assertNotIn(FAKE_TOKEN, " ".join(out))
        self.assertEqual(out[-2:], ["--model", "claude-sonnet-5-5"])

    def test_messages_lose_secrets_quotes_and_known_sentences(self):
        message = f"claim status must be one of [...]: {{'source': 'o prazo SEGREDO-42'}} key={FAKE_KEY} " \
                  f"while reading: {SECRET_TEXT}"
        out = scrub_message(message, [SECRET_TEXT])
        self.assertNotIn("SEGREDO-42", out)
        self.assertNotIn(FAKE_KEY, out)
        self.assertIn("claim status must be one of", out)

    def test_absolute_paths_keep_only_the_file_name(self):
        from voznativa.redact import strip_paths
        self.assertEqual(strip_paths(r"C:\Users\ana\AppData\Local\Temp\x\model.py"), "<path>/model.py")
        self.assertEqual(strip_paths("command:/usr/bin/python /home/ana/m.py"), "command:<path>/python <path>/m.py")
        for keep in ("vence em 18/10/2026", "https://example.org/a/b", "e/ou"):
            self.assertEqual(strip_paths(keep), keep)

    def test_short_texts_are_not_reversible_by_plain_hash(self):
        a, b = shield("sim", b"k1"), shield("sim", b"k2")
        self.assertNotEqual(a["hmac_sha256"], b["hmac_sha256"])
        self.assertNotEqual(a["hmac_sha256"], hashlib.sha256(b"sim").hexdigest())

    def test_provider_id_and_errors_carry_no_credential(self):
        provider = CommandProvider([sys.executable, "--api-key", FAKE_KEY, "-c", "import sys; sys.exit(2)"],
                                   retries=0)
        self.assertNotIn(FAKE_KEY, provider.id)
        failing = CommandProvider([sys.executable, "-c", f"import sys; sys.stderr.write('token {FAKE_TOKEN}');"
                                                         "sys.exit(2)"], retries=0)
        with self.assertRaises(ProviderError) as caught:
            failing.generate("x")
        self.assertNotIn(FAKE_TOKEN, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
