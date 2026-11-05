"""Verification that moves a registry entry up the ladder with evidence.

* source: GET the official URL (hosts limited to the entry's own URLs); the
  page must answer 200 and contain one of the entry's identity terms.
* access: read real data bytes (capped) from a host the entry names: a file
  of a GitHub repository, or a file of a Hugging Face dataset. A listing or a
  landing page is not access.

The result is a record for ``verification.*``; a status is promoted only
when the record shows success. Failures are recorded too, never hidden.
"""
from __future__ import annotations

import json
import urllib.parse
from datetime import date

from .connectors import AccessError, HttpLimits, allowed_hosts, fetch, page_identifies

PROBE_BYTES = 65_536


def verify_source(entry: dict, today: str | None = None) -> dict:
    url = entry["urls"]["official"]
    record = {"date": today or date.today().isoformat(), "url": url, "method": "GET official page; identity terms"}
    try:
        page = fetch(url, allowed_hosts(entry))
    except AccessError as error:
        return dict(record, result="failed", failure=error.kind, detail=str(error))
    found = page_identifies(page["text"], entry.get("identity_terms") or [entry["name"]])
    ok = page["status"] == 200 and bool(found)
    return dict(record, result="verified" if ok else "not_identified", http_status=page["status"],
                final_url=page["url"], identity_terms_found=found)


def _github_probe(repo_url: str, hosts: set[str]) -> dict:
    owner_repo = urllib.parse.urlsplit(repo_url).path.strip("/")
    hosts = hosts | {"api.github.com", "raw.githubusercontent.com"}
    listing = json.loads(fetch(f"https://api.github.com/repos/{owner_repo}/contents/", hosts)["text"])
    files = [f for f in listing if f.get("type") == "file" and f.get("size", 0) > 0 and f.get("download_url")]
    data = [f for f in files if _is_data(f["name"])]
    if not data:
        raise AccessError("http", "no data file at the repository root")
    target = max(data, key=lambda f: f["size"])
    raw = fetch(target["download_url"], hosts, partial=PROBE_BYTES)
    return {"file": target["path"], "bytes_read": raw["bytes"], "declared_size": target["size"],
            "truncated": raw["truncated"]}


DATA_SUFFIXES = (".jsonl", ".json", ".csv", ".tsv", ".txt", ".conllu", ".xml", ".gz", ".bz2", ".xz", ".zip",
                 ".parquet", ".arrow", ".tar", ".wav", ".mp3", ".flac")


def _is_data(name: str) -> bool:
    low = name.lower()
    if low.startswith(("readme", "license", "licence", ".git", "contributing", "changelog", "citation",
                       "dataset_infos", "dataset_info")):
        return False
    return low.endswith(DATA_SUFFIXES) and "checksum" not in low and not low.endswith((".sha256", ".md5"))


def _hf_probe(dataset_url: str, hosts: set[str]) -> dict:
    dataset = urllib.parse.urlsplit(dataset_url).path.split("/datasets/", 1)[1].strip("/")
    info = json.loads(fetch(f"https://huggingface.co/api/datasets/{dataset}", hosts | {"huggingface.co"})["text"])
    if info.get("gated"):
        return {"gated": info["gated"], "sha": info.get("sha")}
    siblings = [s["rfilename"] for s in info.get("siblings", []) if _is_data(s["rfilename"].rsplit("/", 1)[-1])]
    if not siblings:
        raise AccessError("http", "dataset lists no data file")
    target = siblings[0]
    raw = fetch(f"https://huggingface.co/datasets/{dataset}/resolve/{info.get('sha')}/{target}",
                hosts | {"huggingface.co", "*.huggingface.co", "*.hf.co"}, partial=PROBE_BYTES)
    return {"file": target, "bytes_read": raw["bytes"], "truncated": raw["truncated"], "sha": info.get("sha"),
            "data_files_listed": len(siblings)}


def verify_access(entry: dict, today: str | None = None) -> dict | None:
    """None when the entry names no host this module can read data from."""
    urls = entry["urls"]
    hosts = allowed_hosts(entry)
    record = {"date": today or date.today().isoformat()}
    try:
        if urls.get("huggingface"):
            probe = _hf_probe(urls["huggingface"], hosts)
            if probe.get("gated"):
                return dict(record, method="Hugging Face API", result="gated", detail=probe)
            return dict(record, method="Hugging Face API + file read", result="data_read", detail=probe)
        for value in urls.values():
            if isinstance(value, str) and urllib.parse.urlsplit(value).hostname == "github.com":
                return dict(record, method="GitHub API + raw file read", result="data_read",
                            detail=_github_probe(value, hosts))
    except (AccessError, ValueError, KeyError) as error:
        return dict(record, method="data read", result="failed", detail=str(error)[:300])
    return None


def apply(entry: dict, source: dict | None, access: dict | None) -> dict:
    """The entry with its verification records and the status they justify.
    Only CATALOGUED/SOURCE_VERIFIED entries are promoted here; higher rungs
    need connectors and processing runs."""
    out = dict(entry)
    verification = dict(out.get("verification") or {})
    if source:
        verification["source"] = source
    if access:
        verification["access"] = access
    out["verification"] = verification
    citation_only = (out.get("urls") or {}).get("official_kind") not in {"project_site", "data_host"}
    if out["status"] in {"CATALOGUED", "SOURCE_VERIFIED"} and not citation_only:
        if source and source["result"] == "verified":
            out["status"] = "SOURCE_VERIFIED"
            if access and access["result"] == "data_read":
                out["status"] = "ACCESS_VERIFIED"
        if access and access["result"] == "gated":
            out["status"], out["status_reason"] = "AWAITING_PERMISSION", "gated dataset: access needs approval"
    return out
