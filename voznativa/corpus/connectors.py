"""Corpus Access: bounded, read-only connectors.

Every connector reads data as untrusted input: text from a corpus is data,
never an instruction, and nothing in it is executed. Limits are explicit
(bytes, records, time, redirects); exceeding one is an error, not a silent
truncation. Remote access goes only to hosts the registry entry names.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

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


# --- Records and limits ----------------------------------------------------------------

@dataclass(frozen=True)
class ReadLimits:
    max_file_bytes: int = 200_000_000          # on-disk size of one file
    max_decompressed_bytes: int = 500_000_000  # after gzip/zip
    max_ratio: float = 100.0                   # decompressed / compressed (bomb guard)
    max_records: int = 1_000_000
    max_line_bytes: int = 1_000_000
    max_malformed: int = 100                   # malformed rows tolerated before the read fails


@dataclass(frozen=True)
class CorpusRecord:
    """One unit read from a source: original text, never modified here."""
    source: str
    asset: str
    record_id: str
    text: str
    meta: dict


# --- Safe file access ---------------------------------------------------------------

def confined(root: Path, relative: str) -> Path:
    """``root/relative`` only if it stays inside ``root`` (no ``..``, no
    absolute path, no symlink leaving the root)."""
    if not relative or Path(relative).is_absolute() or PureWindowsPath(relative).is_absolute() \
            or ".." in Path(relative).parts or ".." in PureWindowsPath(relative).parts:
        raise AccessError("path_traversal", f"{relative!r} leaves the corpus directory")
    root = root.resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise AccessError("path_traversal", f"{relative!r} resolves outside the corpus directory")
    return target


class _CappedReader(io.RawIOBase):
    """Counts decompressed bytes and stops at the cap or the ratio limit."""

    def __init__(self, raw, compressed_size: int, limits: ReadLimits, owned=()):
        self.raw, self.compressed, self.limits, self.count = raw, max(1, compressed_size), limits, 0
        self.owned = owned  # e.g. the ZipFile behind a member stream

    def readable(self):
        return True

    def close(self):
        # Closing the stream must release the file itself: on Windows a leaked
        # handle keeps the cache file locked (ResourceWarning in CP4 tests).
        if not self.closed:
            try:
                self.raw.close()
            finally:
                for resource in self.owned:
                    resource.close()
        super().close()

    def readinto(self, buffer):
        data = self.raw.read(len(buffer))
        self.count += len(data)
        if self.count > self.limits.max_decompressed_bytes:
            raise AccessError("too_large", f"more than {self.limits.max_decompressed_bytes} decompressed bytes")
        if self.count > 1_000_000 and self.count / self.compressed > self.limits.max_ratio:
            raise AccessError("decompression_bomb", f"decompression ratio above {self.limits.max_ratio:g}")
        buffer[:len(data)] = data
        return len(data)


def open_text(path: Path, limits: ReadLimits, member: str | None = None):
    """A text stream (UTF-8, errors raised per line by the caller) for a plain,
    .gz or .zip file, with size, ratio and member-name checks."""
    size = path.stat().st_size
    if size > limits.max_file_bytes:
        raise AccessError("too_large", f"{path.name}: {size} bytes > {limits.max_file_bytes}")
    name = path.name.lower()
    if name.endswith(".gz"):
        raw = gzip.open(path, "rb")
    elif name.endswith(".zip"):
        archive = zipfile.ZipFile(path)
        names = [i for i in archive.infolist() if not i.is_dir()]
        for info in names:
            if info.filename.startswith(("/", "\\")) or ".." in PurePosixPath(info.filename).parts:
                raise AccessError("path_traversal", f"zip member {info.filename!r} leaves the archive")
            if info.file_size > limits.max_decompressed_bytes:
                raise AccessError("too_large", f"zip member {info.filename!r} declares {info.file_size} bytes")
        chosen = next((i for i in names if i.filename == member), names[0] if names and member is None else None)
        if chosen is None:
            raise AccessError("missing", f"no member {member!r} in {path.name}")
        raw = archive.open(chosen)
        size = chosen.compress_size
        return io.BufferedReader(_CappedReader(raw, size, limits, owned=(archive,)))
    else:
        raw = open(path, "rb")
    return io.BufferedReader(_CappedReader(raw, size, limits))


def iter_lines(stream, limits: ReadLimits, errors: list[dict]):
    """Lines decoded as strict UTF-8; an undecodable or oversized line is
    recorded in ``errors`` and skipped, up to the malformed budget."""
    for number, raw in enumerate(stream, 1):
        if len(raw) > limits.max_line_bytes:
            errors.append({"line": number, "error": "line too long"})
        else:
            try:
                yield number, raw.decode("utf-8").rstrip("\r\n")
                continue
            except UnicodeDecodeError as error:
                errors.append({"line": number, "error": f"invalid UTF-8 at byte {error.start}"})
        if len(errors) > limits.max_malformed:
            raise AccessError("malformed", f"more than {limits.max_malformed} malformed lines")


# --- Readers by format ----------------------------------------------------------------

def read_conllu(lines, errors):
    """One record per sentence: ``# sent_id``, ``# text`` and token count."""
    meta, tokens = {}, 0
    for number, line in lines:
        if not line.strip():
            if meta.get("text") is not None:
                yield meta.get("sent_id", f"line-{number}"), meta["text"], {"tokens": tokens, **{
                    k: v for k, v in meta.items() if k not in {"text", "sent_id"}}}
            meta, tokens = {}, 0
        elif line.startswith("#"):
            key, _, value = line[1:].partition("=")
            meta[key.strip()] = value.strip()
        elif line.count("\t") >= 9:
            tokens += 1 if line.split("\t", 1)[0].isdigit() else 0
        else:
            errors.append({"line": number, "error": "CoNLL-U token line without 10 columns"})
    if meta.get("text") is not None:
        yield meta.get("sent_id", "last"), meta["text"], {"tokens": tokens}


def read_delimited(lines, errors, delimiter: str, text_field: str, id_field: str | None):
    """RFC 4180 over the whole stream, so quoted fields may span lines. A row
    whose field count differs from the header is skipped and recorded; a
    broken quote (e.g. the cut last row of a byte prefix) ends the read and
    is recorded."""
    current = {"line": 0}

    def text_lines():
        for number, line in lines:
            current["line"] = number
            yield line + "\n"

    reader = csv.reader(text_lines(), delimiter=delimiter, strict=True)
    try:
        header = next(reader)
    except StopIteration:
        return
    if text_field not in header:
        raise AccessError("malformed", f"no column {text_field!r} in the header")
    while True:
        try:
            row = next(reader)
        except StopIteration:
            return
        except csv.Error as error:
            errors.append({"line": current["line"], "error": f"CSV: {error}"})
            return
        if len(row) != len(header):
            errors.append({"line": current["line"], "error": f"{len(row)} fields, header has {len(header)}"})
            continue
        record = dict(zip(header, row))
        yield record.get(id_field) if id_field else f"row-{reader.line_num}", record[text_field],             {k: v for k, v in record.items() if k != text_field}


def read_jsonl(lines, errors, text_field: str, id_field: str | None):
    for number, line in lines:
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append({"line": number, "error": f"JSON: {error.msg}"})
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get(text_field), str):
            errors.append({"line": number, "error": f"no string field {text_field!r}"})
            continue
        yield str(obj.get(id_field)) if id_field else f"row-{number}", obj[text_field], \
            {k: v for k, v in obj.items() if k != text_field}


def read_txt(lines, errors):
    """Paragraphs separated by blank lines."""
    buffer, start = [], None
    for number, line in lines:
        if line.strip():
            buffer.append(line)
            start = start or number
        elif buffer:
            yield f"p-{start}", "\n".join(buffer), {"first_line": start}
            buffer, start = [], None
    if buffer:
        yield f"p-{start}", "\n".join(buffer), {"first_line": start}


FORMATS = ("txt", "csv", "tsv", "jsonl", "json", "conllu")


# --- Connectors -------------------------------------------------------------------------

class LocalFilesConnector:
    """Reads registry assets from a local directory (the cache or a folder the
    user names). Configuration comes from ``connector.reader`` of the entry."""
    id = "local-files"
    capabilities = ("inspect", "metadata", "list_assets", "validate_access", "sample", "stream_records",
                    "read_record", "validate_integrity", "report_capabilities")

    def __init__(self, entry: dict, root: Path, limits: ReadLimits = ReadLimits()):
        self.entry, self.root, self.limits = entry, Path(root), limits
        self.reader = (entry.get("connector") or {}).get("reader") or {}
        self.errors: list[dict] = []

    def report_capabilities(self) -> dict:
        return {"id": self.id, "operations": list(self.capabilities), "formats": list(FORMATS),
                "compression": ["gz", "zip"], "limits": self.limits.__dict__}

    def metadata(self) -> dict:
        return {k: self.entry.get(k) for k in ("id", "name", "license", "modality", "period", "status")}

    def list_assets(self) -> list[dict]:
        out = []
        for asset in (self.entry.get("connector") or {}).get("assets", []):
            path = confined(self.root, asset["name"])
            out.append({"name": asset["name"], "format": asset.get("format", self.reader.get("format")),
                        "present": path.is_file(), "bytes": path.stat().st_size if path.is_file() else None})
        return out

    def validate_access(self) -> dict:
        assets = self.list_assets()
        missing = [a["name"] for a in assets if not a["present"]]
        return {"ok": bool(assets) and not missing, "missing": missing, "assets": len(assets)}

    def inspect(self) -> dict:
        return {"metadata": self.metadata(), "assets": self.list_assets(), "capabilities": self.report_capabilities()}

    def validate_integrity(self) -> dict:
        """sha256 of each present asset against the registry value, when recorded."""
        results = []
        for asset in (self.entry.get("connector") or {}).get("assets", []):
            path = confined(self.root, asset["name"])
            if not path.is_file():
                results.append({"name": asset["name"], "ok": False, "error": "missing"})
                continue
            digest = _sha256_file(path)
            expected = asset.get("sha256")
            results.append({"name": asset["name"], "sha256": digest,
                            "ok": expected is None or digest == expected, "expected": expected})
        return {"ok": all(r["ok"] for r in results) and bool(results), "assets": results}

    def stream_records(self, asset_name: str | None = None, max_records: int | None = None):
        cap = min(max_records or self.limits.max_records, self.limits.max_records)
        count = 0
        for asset in (self.entry.get("connector") or {}).get("assets", []):
            if asset_name and asset["name"] != asset_name:
                continue
            fmt = asset.get("format", self.reader.get("format"))
            if fmt not in FORMATS:
                raise AccessError("unsupported", f"format {fmt!r}")
            path = confined(self.root, asset["name"])
            with open_text(path, self.limits, asset.get("member")) as stream:
                lines = iter_lines(stream, self.limits, self.errors)
                rows = self._rows(fmt, lines)
                for record_id, text, meta in rows:
                    yield CorpusRecord(self.entry["id"], asset["name"], str(record_id), text, meta)
                    count += 1
                    if count >= cap:
                        return

    def _rows(self, fmt: str, lines):
        text_field = self.reader.get("text_field", "text")
        id_field = self.reader.get("id_field")
        if fmt == "conllu":
            return read_conllu(lines, self.errors)
        if fmt in {"csv", "tsv"}:
            return read_delimited(lines, self.errors, "," if fmt == "csv" else "\t", text_field, id_field)
        if fmt in {"jsonl", "json"}:
            return read_jsonl(lines, self.errors, text_field, id_field)
        return read_txt(lines, self.errors)

    def sample(self, n: int = 5) -> list[CorpusRecord]:
        return list(self.stream_records(max_records=n))

    def read_record(self, record_id: str) -> CorpusRecord | None:
        return next((r for r in self.stream_records() if r.record_id == record_id), None)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_dir(source_id: str) -> Path:
    """Local copies live outside any repository: $VOZNATIVA_CORPUS_CACHE or
    ~/.voznativa/corpora/<id>. Never committed, removable with purge()."""
    base = Path(os.environ.get("VOZNATIVA_CORPUS_CACHE") or Path.home() / ".voznativa" / "corpora")
    return base / source_id


def download(entry: dict, asset: dict, root: Path | None = None, purpose: str = "noncommercial_research") -> dict:
    """Fetch one registry asset into the local cache, after the policy allows
    DOWNLOAD. Streams to ``.part`` and renames only when complete; a byte cap
    makes the result an explicitly partial prefix; a recorded sha256 is checked."""
    from .policy import require
    decision = require(entry, "DOWNLOAD", purpose=purpose)
    root = Path(root or cache_dir(entry["id"]))
    target = confined(root, asset["name"])
    target.parent.mkdir(parents=True, exist_ok=True)
    hosts = allowed_hosts(entry) | set(asset.get("hosts", []))
    if urllib.parse.urlsplit(asset["url"]).scheme != "https" or             not host_allowed(urllib.parse.urlsplit(asset["url"]).hostname or "", hosts):
        raise AccessError("host_not_allowed", "asset URL is not https on a host of the registry entry")
    part = target.with_suffix(target.suffix + ".part")
    max_bytes = int(asset.get("max_bytes") or 100_000_000)
    request = urllib.request.Request(asset["url"], headers={"User-Agent": USER_AGENT})
    if asset.get("prefix_bytes"):
        request.add_header("Range", f"bytes=0-{int(asset['prefix_bytes']) - 1}")
    started, total = time.monotonic(), 0
    try:
        with urllib.request.urlopen(request, timeout=30) as response, open(part, "wb") as out:
            final_host = urllib.parse.urlsplit(response.geturl()).hostname or ""
            if not host_allowed(final_host, hosts):
                raise AccessError("host_not_allowed", f"redirected to {final_host}")
            for chunk in iter(lambda: response.read(1 << 16), b""):
                total += len(chunk)
                if total > max_bytes:
                    raise AccessError("too_large", f"more than {max_bytes} bytes")
                out.write(chunk)
            partial = response.status == 206
    except (urllib.error.URLError, OSError) as error:
        part.unlink(missing_ok=True)
        if isinstance(error, AccessError):
            raise
        raise AccessError("network", f"download interrupted: {type(error).__name__}") from None
    except AccessError:
        part.unlink(missing_ok=True)
        raise
    digest = _sha256_file(part)
    if asset.get("sha256") and not partial and digest != asset["sha256"]:
        part.unlink(missing_ok=True)
        raise AccessError("integrity", "sha256 differs from the registry")
    os.replace(part, target)
    return {"asset": asset["name"], "bytes": total, "sha256": digest, "partial": partial,
            "seconds": round(time.monotonic() - started, 2), "policy": decision.as_dict()}


def purge(source_id: str, root: Path | None = None) -> dict:
    """Remove the local copy of a source (revoked access, licence change).
    Derived artefacts record their inputs' sha256, so they can be invalidated."""
    import shutil
    target = Path(root or cache_dir(source_id))
    existed = target.exists()
    if existed:
        shutil.rmtree(target)
    return {"source": source_id, "removed": existed, "path_name": target.name}


class HuggingFaceMetadataConnector:
    """Metadata of a Hugging Face dataset through the Hub API, including the
    Croissant JSON-LD when the Hub offers it. Data files are fetched with
    ``download`` into the cache and read by ``LocalFilesConnector``; the
    ``datasets`` library is not required."""
    id = "hf-dataset"
    capabilities = ("metadata", "list_assets", "validate_access", "report_capabilities")

    def __init__(self, entry: dict):
        self.entry = entry
        url = (entry.get("urls") or {}).get("huggingface") or ""
        self.dataset = url.split("/datasets/", 1)[1].strip("/") if "/datasets/" in url else None
        self.hosts = allowed_hosts(entry) | {"huggingface.co"}

    def report_capabilities(self) -> dict:
        return {"id": self.id, "operations": list(self.capabilities)}

    def metadata(self) -> dict:
        if not self.dataset:
            raise AccessError("unsupported", "the entry names no Hugging Face dataset")
        info = json.loads(fetch(f"https://huggingface.co/api/datasets/{self.dataset}", self.hosts)["text"])
        out = {"dataset": self.dataset, "sha": info.get("sha"), "gated": info.get("gated"),
               "card_license": (info.get("cardData") or {}).get("license"), "files": len(info.get("siblings", []))}
        try:
            croissant = json.loads(fetch(f"https://huggingface.co/api/datasets/{self.dataset}/croissant",
                                         self.hosts)["text"])
            out["croissant"] = {k: croissant.get(k) for k in ("name", "license", "url", "conformsTo")}
        except AccessError as error:
            out["croissant"] = {"available": False, "reason": error.kind}
        return out

    def list_assets(self) -> list[dict]:
        info = json.loads(fetch(f"https://huggingface.co/api/datasets/{self.dataset}", self.hosts)["text"])
        return [{"name": s["rfilename"]} for s in info.get("siblings", [])]

    def validate_access(self) -> dict:
        meta = self.metadata()
        return {"ok": not meta.get("gated"), "gated": meta.get("gated"), "sha": meta.get("sha")}


# Connectors by id; the registry checks that a CONNECTOR_READY source names one.
CONNECTORS: dict[str, type] = {
    LocalFilesConnector.id: LocalFilesConnector,
    HuggingFaceMetadataConnector.id: HuggingFaceMetadataConnector,
}
