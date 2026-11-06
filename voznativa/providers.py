"""Model providers for the Rewrite Engine.

A provider turns a prompt into candidate texts. The engine never depends on a
specific vendor: any agent CLI that reads a prompt on stdin and prints text
works through ``CommandProvider`` (``claude -p``, ``codex exec -``,
``gemini -p``, ``ollama run <model>``...). Inside an agent session the agent
itself is the model: ``voznativa rewrite-prompt`` prints the prompt and the
agent answers it, then checks its answer with ``voznativa compare``.

Isolation, honestly stated
--------------------------
``CommandProvider`` runs each call in a fresh EMPTY TEMPORARY DIRECTORY. That
is not a sandbox. The process still runs as the current user: it can read and
write any absolute path the user can, reach the network, and read every
variable of the environment it gets (``env="inherit"`` passes all of them,
credentials included). The empty directory only keeps a tool-using agent from
finding the caller's project by default. Real isolation needs the CLI's own
switches (``claude -p --tools ""``, ``codex exec --sandbox read-only``,
``gemini --sandbox``), a container or an OS sandbox; ``agent_cli_warnings()``
flags known agent CLIs launched without them. ``env="minimal"`` passes only
what a CLI needs to start plus the names in ``env_allow``.

The prompt text itself is untrusted: the engine wraps it in delimiters whose
tag carries a hash of the content, so a text cannot close the block early,
and rejects candidates that smuggle protocol tokens (``<final>``, a judge
verdict) the original did not have.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

MAX_OUTPUT_BYTES = 2_000_000
# Variables a CLI usually needs to start; everything else stays out with env="minimal".
MINIMAL_ENV = ("PATH", "PATHEXT", "HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA",
               "SYSTEMROOT", "SYSTEMDRIVE", "COMSPEC", "WINDIR", "TEMP", "TMP", "TMPDIR", "LANG", "LC_ALL",
               "LC_CTYPE", "TERM", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME")
# Known agent CLIs and the argument that turns their tools off or sandboxes them.
AGENT_CLIS = {
    "claude": (("--tools", "--disallowedTools", "--disallowed-tools"), 'claude -p --tools ""'),
    "codex": (("--sandbox", "-s"), "codex exec --sandbox read-only -"),
    "gemini": (("--sandbox", "-s"), "gemini --sandbox -p"),
}


class Provider(Protocol):
    id: str

    def generate(self, prompt: str, n: int = 1) -> list[str]: ...


class ProviderError(RuntimeError):
    """A provider call failed. ``transient`` says whether retrying can help."""

    def __init__(self, message: str, transient: bool = True):
        super().__init__(message)
        self.transient = transient


def agent_cli_warnings(argv: list[str]) -> list[str]:
    """Warnings for agent CLIs started without their tool/sandbox switch."""
    if not argv:
        return []
    # Split on both separators: a Windows path must be recognized on any OS.
    program = re.split(r"[\\/]", argv[0])[-1].lower().removesuffix(".exe").removesuffix(".cmd")
    if program not in AGENT_CLIS:
        return []
    switches, example = AGENT_CLIS[program]
    if any(a == s or a.startswith(s + "=") for a in argv[1:] for s in switches):
        return []
    return [f"{program} runs with its tools enabled: the empty working directory is not a sandbox, the model "
            f"can still read and write files by absolute path and use the network. Use e.g. `{example}`."]


def split_command(command: str, windows: bool | None = None) -> list[str]:
    """Shell-like split. On Windows ``shlex`` in non-POSIX mode keeps the
    quotes inside the tokens, so ``"C:\\Program Files\\x.exe" a`` named a
    program with quotes in its path (v0.7.0 CP8, VN07-DISC-020); surrounding
    quotes are removed and backslashes kept."""
    windows = os.name == "nt" if windows is None else windows
    if not windows:
        return shlex.split(command, posix=True)
    out = []
    for token in shlex.split(command, posix=False):
        if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
            token = token[1:-1]
        out.append(token)
    return out


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


def _decode(data: bytes) -> str:
    """UTF-8 when it is valid; otherwise the locale encoding. On Windows a
    command that prints through the console code page (cp1252/cp850) would
    otherwise turn every accent into U+FFFD."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        import locale
        return data.decode(locale.getpreferredencoding(False) or "utf-8", "replace")


class _WindowsJob:
    """A Windows Job Object holding the provider process and every process it
    starts. Terminating the job stops the whole tree without walking parent
    PIDs: `taskkill /T` cannot reach a grandchild whose parent already exited,
    and let a child escape on a GitHub Windows runner (CI run #122).

    Race-free use: create the job, start the process suspended
    (``creation_flags``), then ``adopt`` it (assign, then resume), so nothing
    the process starts can exist before it is in the job. Only used to stop
    the tree on timeout; a normal run keeps its children as before."""

    CREATE_SUSPENDED = 0x00000004

    def __init__(self):
        self.handle = None
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            ntdll = ctypes.WinDLL("ntdll")
            kernel32.CreateJobObjectW.restype = wintypes.HANDLE
            kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
            kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
            kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
            kernel32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                                           wintypes.DWORD, ctypes.c_void_p]
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
            handle = kernel32.CreateJobObjectW(None, None)
            if handle:
                self.handle, self.kernel32, self.ntdll = handle, kernel32, ntdll
        except (AttributeError, OSError, ValueError):
            self.handle = None

    @property
    def creation_flags(self) -> int:
        return self.CREATE_SUSPENDED if self.handle else 0

    def adopt(self, process: subprocess.Popen) -> None:
        """Assign the suspended process to the job, then resume it. If the
        assignment fails the process still resumes (taskkill stays the fallback)."""
        if not self.handle:
            return
        if not self.kernel32.AssignProcessToJobObject(self.handle, int(process._handle)):
            self.close()
        self.ntdll.NtResumeProcess(int(process._handle))

    def terminate(self, wait: float = 5.0) -> bool:
        """Terminate every process of the job and wait (bounded) until none is
        active: TerminateJobObject returns before the processes release their
        handles, and the provider's temporary files are still open until then."""
        if not self.handle or not self.kernel32.TerminateJobObject(self.handle, 1):
            return False
        import ctypes
        from ctypes import wintypes

        class Accounting(ctypes.Structure):  # JOBOBJECT_BASIC_ACCOUNTING_INFORMATION
            _fields_ = [("user", ctypes.c_int64), ("kernel", ctypes.c_int64), ("period_user", ctypes.c_int64),
                        ("period_kernel", ctypes.c_int64), ("page_faults", wintypes.DWORD),
                        ("total", wintypes.DWORD), ("active", wintypes.DWORD), ("terminated", wintypes.DWORD)]

        info = Accounting()
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            if not self.kernel32.QueryInformationJobObject(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info),
                                                           None) or info.active == 0:
                break
            time.sleep(0.05)
        return True

    def close(self) -> None:
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


def _kill_tree(process: subprocess.Popen, job: "_WindowsJob | None" = None) -> None:
    """Stop the process and whatever it started (agent CLIs spawn helpers)."""
    if job is not None and job.terminate():
        try:
            process.kill()
        except OSError:
            pass
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False)
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except OSError:
        pass
    try:
        process.kill()
    except OSError:
        pass


@dataclass
class CommandProvider:
    """Runs a command with the prompt on stdin and reads the answer from stdout.

    ``argv`` is executed without a shell, one process per candidate, by
    default in a fresh empty directory (see the module notes: that is not a
    sandbox). On timeout the whole process tree is stopped. Output larger than
    ``max_output_bytes`` or empty output is an error.
    """
    argv: list[str]
    timeout: float = 300.0
    id: str = ""
    isolate: bool = True
    calls: int = 0
    retries: int = 1          # extra tries after a transient failure (timeout, crash, non-zero exit, empty answer)
    backoff: float = 2.0      # seconds, doubled after each failure
    errors: list = field(default_factory=list)
    env: str = "inherit"      # "inherit" | "minimal"
    env_allow: tuple = ()     # extra variable names kept with env="minimal"
    max_output_bytes: int = MAX_OUTPUT_BYTES
    warnings: list = field(default_factory=list)

    def __post_init__(self):
        if not self.argv:
            raise ValueError("command provider needs a command")
        if self.env not in {"inherit", "minimal"}:
            raise ValueError("env must be 'inherit' or 'minimal'")
        from .redact import redact_argv
        # The id is recorded in reports; never let a credential in argv reach it.
        self.id = self.id or "command:" + " ".join(redact_argv(self.argv)[:3])
        self.warnings = agent_cli_warnings(self.argv)

    @classmethod
    def from_string(cls, command: str, timeout: float = 300.0, **options) -> "CommandProvider":
        """``command`` is a shell-like string or a JSON array of arguments
        (use the array form for arguments such as --tools "")."""
        stripped = command.strip()
        if stripped.startswith("["):
            argv = json.loads(stripped)
            if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
                raise ValueError("--cmd JSON must be an array of strings")
            return cls(argv, timeout, **options)
        return cls(split_command(command), timeout, **options)

    def _environment(self) -> dict | None:
        if self.env == "inherit":
            return None
        keep = set(MINIMAL_ENV) | set(self.env_allow)
        return {k: v for k, v in os.environ.items() if k.upper() in {n.upper() for n in keep}}

    def _once(self, prompt: str) -> str:
        from .redact import scrub_secrets
        self.calls += 1
        # ignore_cleanup_errors: a process that outlives the timeout can keep a
        # file open on Windows; its cleanup error must not replace the
        # ProviderError the caller needs (it used to surface as PermissionError).
        with tempfile.TemporaryDirectory(prefix="voznativa-provider-", ignore_cleanup_errors=True) as workdir, \
                tempfile.TemporaryDirectory(prefix="voznativa-capture-", ignore_cleanup_errors=True) as capture:
            out_path = os.path.join(capture, "stdout")
            err_path = os.path.join(capture, "stderr")
            # stdout/stderr go to files, so a runaway answer fills a temp file, not memory.
            with open(out_path, "wb") as out, open(err_path, "wb") as err:
                job = _WindowsJob() if os.name == "nt" else None
                try:
                    process = subprocess.Popen(
                        self.argv, stdin=subprocess.PIPE, stdout=out, stderr=err,
                        cwd=workdir if self.isolate else None, env=self._environment(),
                        start_new_session=os.name != "nt",
                        creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | job.creation_flags)
                        if job is not None else 0)
                except OSError as error:  # command not found, not executable: retrying cannot help
                    if job is not None:
                        job.close()
                    raise ProviderError(f"{self.id}: cannot start: {error.strerror or error}", transient=False) \
                        from error
                if job is not None:
                    job.adopt(process)
                try:
                    process.communicate(prompt.encode("utf-8"), timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    _kill_tree(process, job)
                    process.wait()
                    raise ProviderError(f"{self.id}: no answer after {self.timeout:g}s (process tree stopped)")
                finally:
                    if job is not None:
                        job.close()
            size = os.path.getsize(out_path)
            stderr = Path(err_path).read_bytes()[:2000].decode("utf-8", "replace")
            if process.returncode != 0:
                raise ProviderError(f"{self.id} exited {process.returncode}: {scrub_secrets(stderr)[:500]}")
            if size > self.max_output_bytes:
                raise ProviderError(f"{self.id}: answer of {size} bytes exceeds {self.max_output_bytes}",
                                    transient=False)
            answer = _decode(Path(out_path).read_bytes())
        if not answer.strip():
            raise ProviderError(f"{self.id}: empty answer")
        return answer

    def generate(self, prompt: str, n: int = 1) -> list[str]:
        outputs = []
        for _ in range(n):
            delay = self.backoff
            for attempt in range(self.retries + 1):
                try:
                    outputs.append(self._once(prompt))
                    break
                except ProviderError as error:
                    self.errors.append(str(error))
                    if attempt == self.retries or not error.transient:
                        raise
                    time.sleep(delay)
                    delay *= 2
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
    take VozNativa's prompt) and a style hint derived from the Voice Contract.
    Network, HTTP and format errors become ``ProviderError``; 429 and 5xx are
    retried. The API key never appears in an error message."""
    api_key: str
    style: dict = field(default_factory=dict)
    transport: Callable[[urllib.request.Request], bytes] | None = None
    id: str = "emulate-1:/v1/humanize"
    timeout: float = 120.0
    retries: int = 1
    backoff: float = 2.0
    max_output_bytes: int = MAX_OUTPUT_BYTES

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
            raise ProviderError(f"Emulate /humanize requires at least {EMULATE_MIN_WORDS} words", transient=False)
        body = json.dumps({"text": text, "style": self.style or None}).encode("utf-8")
        return urllib.request.Request(EMULATE_URL, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})

    def _send(self, req: urllib.request.Request) -> bytes:
        if self.transport:
            return self.transport(req)
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            return response.read(self.max_output_bytes + 1)

    def _once(self, text: str) -> str:
        req = self.request(text)
        try:
            raw = self._send(req)
        except urllib.error.HTTPError as error:
            raise ProviderError(f"{self.id}: HTTP {error.code}",
                                transient=error.code == 429 or error.code >= 500) from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as error:
            reason = getattr(error, "reason", error)
            raise ProviderError(f"{self.id}: network error: {type(reason).__name__}") from None
        if len(raw) > self.max_output_bytes:
            raise ProviderError(f"{self.id}: answer exceeds {self.max_output_bytes} bytes", transient=False)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError(f"{self.id}: answer is not JSON") from None
        if not isinstance(payload, dict) or not isinstance(payload.get("text"), str) or not payload["text"].strip():
            raise ProviderError(f"{self.id}: unexpected response (keys: {sorted(payload)[:5] if isinstance(payload, dict) else type(payload).__name__})")
        return payload["text"]

    def humanize(self, text: str) -> str:
        delay = self.backoff
        for attempt in range(self.retries + 1):
            try:
                return self._once(text)
            except ProviderError as error:
                if attempt == self.retries or not error.transient:
                    raise
                time.sleep(delay)
                delay *= 2
        raise AssertionError("unreachable")

    def generate(self, prompt: str, n: int = 1) -> list[str]:
        raise ProviderError("Emulate takes the source text, not a prompt; use the engine's system mode",
                            transient=False)
