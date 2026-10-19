"""Model providers for the Rewrite Engine.

A provider turns a prompt into candidate texts. The engine never depends on a
specific vendor: any agent CLI that reads a prompt on stdin and prints text
works through ``CommandProvider`` (``claude -p``, ``codex exec -``,
``gemini -p``, ``ollama run <model>``...). Inside an agent session the agent
itself is the model: ``voznativa rewrite-prompt`` prints the prompt and the
agent answers it, then checks its answer with ``voznativa compare``.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Protocol


class Provider(Protocol):
    id: str

    def generate(self, prompt: str, n: int = 1) -> list[str]: ...


class ProviderError(RuntimeError):
    pass


@dataclass
class StaticProvider:
    """Returns pre-written candidates in order; used by tests and benchmarks."""
    candidates: list[str]
    id: str = "static"
    calls: list[str] = field(default_factory=list)

    def generate(self, prompt: str, n: int = 1) -> list[str]:
        self.calls.append(prompt)
        out, self.candidates = self.candidates[:n], self.candidates[n:]
        return out


@dataclass
class CommandProvider:
    """Runs a command with the prompt on stdin and reads the answer from stdout.

    ``argv`` is executed without a shell. One process per candidate.
    """
    argv: list[str]
    timeout: float = 300.0
    id: str = ""

    def __post_init__(self):
        if not self.argv:
            raise ValueError("command provider needs a command")
        self.id = self.id or "command:" + " ".join(self.argv[:3])

    @classmethod
    def from_string(cls, command: str, timeout: float = 300.0) -> "CommandProvider":
        return cls(shlex.split(command, posix=os.name != "nt"), timeout)

    def generate(self, prompt: str, n: int = 1) -> list[str]:
        outputs = []
        for _ in range(n):
            try:
                done = subprocess.run(self.argv, input=prompt.encode("utf-8"), capture_output=True,
                                      timeout=self.timeout, check=False)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise ProviderError(f"{self.id}: {error}") from error
            if done.returncode != 0:
                raise ProviderError(f"{self.id} exited {done.returncode}: "
                                    f"{done.stderr.decode('utf-8', 'replace')[:500]}")
            outputs.append(done.stdout.decode("utf-8", "replace"))
        return outputs


# Emulate-1 (https://www.tryemulate.ai/docs/api). Mapping is based on the public
# docs; it has not been validated against the live service from this project.
EMULATE_URL = "https://www.tryemulate.ai/v1/humanize"
EMULATE_MIN_WORDS = 40
_EMULATE_FORMALITY = {"colloquial": "casual", "casual": "relaxed", "professional-natural": "balanced",
                      "professional-formal": "formal", "technical": "polished", "academic": "formal",
                      "journalistic": "polished"}
_EMULATE_SENTENCES = {"short": "punchy", "short-mixed": "punchy", "mixed": "mixed", "mixed-long": "flowing",
                      "long": "flowing"}


@dataclass
class EmulateProvider:
    """Optional system-level baseline. Sends only the source text (it cannot
    take VozNativa's prompt) and a style hint derived from the Voice Contract."""
    api_key: str
    style: dict = field(default_factory=dict)
    transport: Callable[[urllib.request.Request], bytes] | None = None
    id: str = "emulate-1:/v1/humanize"

    @staticmethod
    def style_from_contract(compact_contract: dict) -> dict:
        style = {}
        if compact_contract.get("register") in _EMULATE_FORMALITY:
            style["formality"] = _EMULATE_FORMALITY[compact_contract["register"]]
        if compact_contract.get("sentence_rhythm") in _EMULATE_SENTENCES:
            style["sentences"] = _EMULATE_SENTENCES[compact_contract["sentence_rhythm"]]
        return style

    def request(self, text: str) -> urllib.request.Request:
        if len(text.split()) < EMULATE_MIN_WORDS:
            raise ProviderError(f"Emulate /humanize requires at least {EMULATE_MIN_WORDS} words")
        body = json.dumps({"text": text, "style": self.style or None}).encode("utf-8")
        return urllib.request.Request(EMULATE_URL, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})

    def humanize(self, text: str) -> str:
        req = self.request(text)
        send = self.transport or (lambda r: urllib.request.urlopen(r, timeout=120).read())
        payload = json.loads(send(req).decode("utf-8"))
        if "text" not in payload:
            raise ProviderError(f"unexpected Emulate response: {str(payload)[:200]}")
        return payload["text"]

    def generate(self, prompt: str, n: int = 1) -> list[str]:
        raise ProviderError("Emulate takes the source text, not a prompt; use the engine's system mode")
