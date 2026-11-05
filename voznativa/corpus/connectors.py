"""Corpus Access: bounded, read-only connectors.

Every connector reads data as untrusted input: text from a corpus is data,
never an instruction, and nothing in it is executed. Limits are explicit
(bytes, records, time, redirects); exceeding one is an error, not a silent
truncation. Remote access goes only to hosts the registry entry names.
"""
from __future__ import annotations

import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

USER_AGENT = "voznativa-corpus-check/0.6 (+https://github.com/Soturine/VozNativa)"


class AccessError(RuntimeError):
    """Access failed or was refused by a limit; ``kind`` says which."""

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class HttpLimits:
    max_bytes: int = 2_000_000
    timeout_s: float = 20.0
    max_redirects: int = 3


def allowed_hosts(entry: dict) -> set[str]:
    """Hosts a registry entry authorises: the hosts of its own URLs."""
    hosts = set()
    for value in (entry.get("urls") or {}).values():
        for url in ([value] if isinstance(value, str) else value or []):
            host = urllib.parse.urlsplit(url).hostname
            if host:
                hosts.add(host.lower())
    return hosts


def host_allowed(host: str, hosts: set[str]) -> bool:
    """Exact host, the same host with or without ``www.``, or a ``*.suffix``
    wildcard the caller added explicitly (a data host's CDN)."""
    host = host.lower()
    bare = host.removeprefix("www.")
    for allowed in hosts:
        if allowed.startswith("*.") and host.endswith(allowed[1:]):
            return True
        if bare == allowed.removeprefix("www."):
            return True
    return False


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # redirects are followed by fetch(), host by host
        return None


def fetch(url: str, hosts: set[str], limits: HttpLimits = HttpLimits(), partial: int | None = None) -> dict:
    """GET ``url`` within ``limits``; every redirect target must be in ``hosts``.
    Returns status, final URL, content type, byte count and the text (decoded,
    capped). With ``partial=N`` only the first N bytes are requested (HTTP
    Range) and read; the result says ``truncated`` instead of failing.
    Raises AccessError with kind ``host_not_allowed``, ``too_large``,
    ``timeout``, ``http`` or ``network``."""
    opener = urllib.request.build_opener(_NoRedirect)
    current, started = url, time.monotonic()
    for _ in range(limits.max_redirects + 1):
        parts = urllib.parse.urlsplit(current)
        if parts.scheme not in {"https", "http"} or not host_allowed(parts.hostname or "", hosts):
            raise AccessError("host_not_allowed", f"{parts.hostname} is not a host of this registry entry")
        headers = {"User-Agent": USER_AGENT}
        if partial:
            headers["Range"] = f"bytes=0-{partial - 1}"
        request = urllib.request.Request(current, headers=headers)
        try:
            response = opener.open(request, timeout=limits.timeout_s)
        except urllib.error.HTTPError as error:
            if error.code in {301, 302, 303, 307, 308} and error.headers.get("Location"):
                current = urllib.parse.urljoin(current, error.headers["Location"])
                continue
            raise AccessError("http", f"HTTP {error.code} from {parts.hostname}") from None
        except (urllib.error.URLError, OSError) as error:
            reason = getattr(error, "reason", error)
            text = f"{type(reason).__name__}: {reason}".lower()
            kind = "timeout" if "timed out" in text else "tls" if "ssl" in text or "certificate" in text else "network"
            raise AccessError(kind, f"{type(reason).__name__} reaching {parts.hostname}") from None
        with response:
            if partial:
                data = response.read(partial)
                truncated = response.status == 206 or bool(response.read(1))
            else:
                data = response.read(limits.max_bytes + 1)
                truncated = False
                if len(data) > limits.max_bytes:
                    raise AccessError("too_large", f"more than {limits.max_bytes} bytes from {parts.hostname}")
            charset = response.headers.get_content_charset() or "utf-8"
            return {"status": response.status, "url": current, "content_type": response.headers.get_content_type(),
                    "bytes": len(data), "truncated": truncated, "seconds": round(time.monotonic() - started, 2),
                    "text": data.decode(charset, "replace")}
    raise AccessError("http", f"more than {limits.max_redirects} redirects")


def page_identifies(text: str, terms: list[str]) -> list[str]:
    """Identity terms found in a fetched page (case- and accent-insensitive)."""
    from ..text import fold
    page = fold(re.sub(r"\s+", " ", text))
    return [t for t in terms if fold(t) in page]


# Connectors by id; the registry checks that a CONNECTOR_READY source names one.
CONNECTORS: dict[str, type] = {}
