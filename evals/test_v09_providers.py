"""v0.9 CP2: provider contract, chat-API adapter and generator/judge relation.

The chat-API adapter is exercised against a real HTTP server on 127.0.0.1
(``http.server`` from the standard library) that answers in the
chat-completions format. The model behind it is a fake: these tests prove
the HTTP contract, error mapping and engine integration, not the quality of
any model (status TESTED_WITH_STUB).
"""
import json
import os
import socket
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import engine  # noqa: E402
from voznativa.providers import (ChatAPIProvider, CommandProvider, ProviderError, StaticProvider,  # noqa: E402
                                 identity)
from voznativa.router import route  # noqa: E402

TEXT = ("É importante destacar que o relatório trimestral será enviado até sexta-feira, 14/11/2025. "
        "Vale ressaltar que o orçamento não pode ultrapassar R$ 12.000,00.")
GOOD = ("O relatório trimestral será enviado até sexta-feira, 14/11/2025. "
        "O orçamento não pode ultrapassar R$ 12.000,00.")
BAD = ("O relatório trimestral será enviado até sexta-feira, 14/11/2025. "
       "O orçamento pode ultrapassar R$ 12.000,00.")


class FakeChat(BaseHTTPRequestHandler):
    """Answers POST /v1/chat/completions according to ``server.script``: a list of
    (status, body-or-None, delay) consumed in order (the last one repeats)."""

    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        self.server.requests.append({"path": self.path, "body": body, "auth": self.headers.get("Authorization")})
        status, payload, delay = self.server.script[min(len(self.server.requests) - 1, len(self.server.script) - 1)]
        time.sleep(delay)
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def chat(content, usage=True):
    out = {"choices": [{"message": {"role": "assistant", "content": content}}]}
    if usage:
        out["usage"] = {"prompt_tokens": 100, "completion_tokens": 20}
    return out


class Server:
    def __init__(self, script):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), FakeChat)
        self.httpd.script, self.httpd.requests = script, []
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"

    @property
    def requests(self):
        return self.httpd.requests

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ChatAPIContract(unittest.TestCase):

    def run_with(self, script, **kw):
        server = Server(script)
        self.addCleanup(server.close)
        provider = ChatAPIProvider(server.url, "modelo-x", backoff=0.01, **kw)
        return server, provider

    def test_answer_and_reported_usage(self):
        server, p = self.run_with([(200, chat("olá"), 0)])
        self.assertEqual(p.generate("prompt", 2), ["olá", "olá"])
        self.assertEqual(server.requests[0]["path"], "/v1/chat/completions")
        self.assertEqual(server.requests[0]["body"]["model"], "modelo-x")
        self.assertEqual(server.requests[0]["body"]["messages"], [{"role": "user", "content": "prompt"}])
        self.assertEqual(p.usage, {"prompt_tokens": 200, "completion_tokens": 40, "reported_calls": 2})

    def test_missing_usage_is_not_estimated(self):
        _, p = self.run_with([(200, chat("olá", usage=False), 0)])
        p.generate("x")
        self.assertEqual(p.usage, {"prompt_tokens": 0, "completion_tokens": 0, "reported_calls": 0})

    def test_typed_errors(self):
        cases = [((404, {"error": "model 'modelo-x' not found"}, 0), "model_not_found", False),
                 ((400, {"error": {"message": "model not found"}}, 0), "model_not_found", False),
                 ((401, {"error": "unauthorized"}, 0), "auth", False),
                 ((429, {"error": "slow down"}, 0), "rate_limit", True),
                 ((503, {"error": "loading"}, 0), "server_error", True),
                 ((200, b"<html>not json</html>", 0), "invalid_response", False),
                 ((200, {"choices": []}, 0), "invalid_response", False),
                 ((200, chat("   "), 0), "empty_answer", True)]
        for step, kind, transient in cases:
            with self.subTest(kind=kind, status=step[0]):
                server, p = self.run_with([step], retries=0)
                with self.assertRaises(ProviderError) as ctx:
                    p.generate("x")
                self.assertEqual(ctx.exception.kind, kind)
                self.assertEqual(ctx.exception.transient, transient)

    def test_transient_error_is_retried(self):
        server, p = self.run_with([(503, {"error": "loading"}, 0), (200, chat("ok"), 0)], retries=1)
        self.assertEqual(p.generate("x"), ["ok"])
        self.assertEqual(len(server.requests), 2)

    def test_connection_refused_is_not_retried(self):
        p = ChatAPIProvider(f"http://127.0.0.1:{free_port()}/v1", "m", retries=3, backoff=5)
        started = time.perf_counter()
        with self.assertRaises(ProviderError) as ctx:
            p.generate("x")
        self.assertEqual(ctx.exception.kind, "connection_refused")
        self.assertLess(time.perf_counter() - started, 4, "a refused connection must not be retried with backoff")

    def test_timeout(self):
        _, p = self.run_with([(200, chat("tarde"), 2.0)], timeout=0.3, retries=0)
        with self.assertRaises(ProviderError) as ctx:
            p.generate("x")
        self.assertEqual(ctx.exception.kind, "timeout")

    def test_remote_url_needs_explicit_permission(self):
        with self.assertRaises(ValueError):
            ChatAPIProvider("https://api.example.com/v1", "m")
        self.assertTrue(ChatAPIProvider("https://api.example.com/v1", "m", allow_remote=True).id)
        for bad in ("ftp://localhost/v1", "localhost:8080/v1", "http:///v1"):
            with self.subTest(url=bad), self.assertRaises(ValueError):
                ChatAPIProvider(bad, "m")

    def test_key_comes_from_the_environment_and_never_reaches_a_message(self):
        chave_falsa = "chave-" + "x" * 24
        server, p = self.run_with([(401, {"error": "bad key " + chave_falsa}, 0)], api_key_env="VN09_TEST_KEY",
                                  retries=0)
        os.environ["VN09_TEST_KEY"] = chave_falsa
        self.addCleanup(os.environ.pop, "VN09_TEST_KEY", None)
        with self.assertRaises(ProviderError) as ctx:
            p.generate("x")
        self.assertEqual(server.requests[0]["auth"], f"Bearer {chave_falsa}")
        self.assertNotIn(chave_falsa, p.id)
        os.environ.pop("VN09_TEST_KEY")
        with self.assertRaises(ProviderError) as ctx:
            p.generate("x")
        self.assertEqual(ctx.exception.kind, "auth")


class ChatAPIThroughTheEngine(unittest.TestCase):
    """The adapter is a provider like any other: the gates still decide."""

    def rewrite(self, answers, **kw):
        server = Server([(200, chat(a), 0) for a in answers])
        self.addCleanup(server.close)
        p = ChatAPIProvider(server.url, "modelo-x")
        return engine.rewrite(TEXT, route(TEXT), p, attempts=len(answers), **kw), server

    def test_a_candidate_that_drops_the_negation_never_comes_back(self):
        result, server = self.rewrite([f"<final>{BAD}</final>"] * 3)
        self.assertEqual(result["outcome"], "returned_original")
        self.assertEqual(result["text"], TEXT)
        self.assertEqual(len(server.requests), 3)

    def test_a_clean_candidate_still_needs_a_judgment(self):
        result, _ = self.rewrite([f"<final>{GOOD}</final>"])
        self.assertEqual(result["outcome"], "needs_judgment")
        self.assertEqual(result["text"], GOOD)

    def test_same_model_as_judge_is_self_assessment(self):
        server = Server([(200, chat(f"<final>{GOOD}</final>"), 0)])
        self.addCleanup(server.close)
        writer = ChatAPIProvider(server.url, "modelo-x")
        judge = ChatAPIProvider(server.url, "modelo-x", id="outro-id")
        self.assertEqual(engine._generator_relation(writer, judge), "same_model")   # v0.10: named precisely


class GeneratorRelation(unittest.TestCase):

    def test_relation_by_declared_identity(self):
        cmd = lambda *a: CommandProvider(list(a))  # noqa: E731
        rel = engine._generator_relation
        # v0.8.1 first dogfood: same model, command lines differing in one argument
        self.assertEqual(rel(cmd("claude", "-p", "--model", "sonnet", "--log", "w"),
                             cmd("claude", "-p", "--model", "sonnet", "--log", "j")), "same_model")
        # v0.10: two models through the same vendor's CLI are same_vendor, not independent providers
        self.assertEqual(rel(cmd("claude", "-p", "--model=opus"), cmd("claude", "-p", "--model", "sonnet")),
                         "same_vendor")
        self.assertEqual(rel(cmd("claude", "-p", "--model", "claude-opus-5-5"), cmd("x", "--model", "gpt-5")),
                         "different_provider")
        self.assertEqual(rel(cmd("claude", "-p", "--tools", ""), cmd("claude", "-p")), "same_agent")
        self.assertEqual(rel(cmd("claude", "-p"), cmd("codex", "exec")), "unknown")
        self.assertEqual(rel(cmd("python", "a.py"), cmd("python", "b.py")), "unknown")
        self.assertEqual(rel(StaticProvider([]), StaticProvider([])), "unknown")
        self.assertEqual(rel(ChatAPIProvider("http://localhost:1/v1", "a"),
                             ChatAPIProvider("http://localhost:2/v1", "b")), "different_model")

    def test_identity_reads_only_what_is_configured(self):
        self.assertEqual(identity(CommandProvider(["C:\\Tools\\Claude.EXE", "-p", "-m", "haiku"])),
                         {"program": "claude", "model": "haiku"})
        self.assertEqual(identity(CommandProvider(["python", "x.py"])), {"program": "python", "model": None})
        self.assertEqual(identity(StaticProvider([])), {"program": None, "model": None})

    def test_command_errors_are_typed(self):
        with self.assertRaises(ProviderError) as ctx:
            CommandProvider(["programa-que-nao-existe-vn09"]).generate("x")
        self.assertEqual(ctx.exception.kind, "not_found")
        failing = CommandProvider([sys.executable, "-c", "import sys; sys.exit(4)"], retries=0)
        with self.assertRaises(ProviderError) as ctx:
            failing.generate("x")
        self.assertEqual(ctx.exception.kind, "exit_status")


if __name__ == "__main__":
    unittest.main()
