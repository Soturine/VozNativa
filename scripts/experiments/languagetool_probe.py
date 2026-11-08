#!/usr/bin/env python3
"""v0.4.0 M2 experiment: does LanguageTool add signal VozNativa lacks?

Runs a local LanguageTool server over every original text in the benchmark
case files and every real-model output recorded in benchmarks/runs/ and
evals/integration/, and records, per source, the error matches and the
matches each output INTRODUCES relative to its original. Matches are listed
so a person can read them; this script does not decide which are true.

    java -cp languagetool-server.jar org.languagetool.server.HTTPServer --port 8081
    python scripts/experiments/languagetool_probe.py --url http://127.0.0.1:8081
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from voznativa.benchmark import load_cases  # noqa: E402

# --- Minimal LanguageTool client (kept here: the tool was not adopted, see EVALUATION.md) ---
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
# Categories that describe errors, not style preferences.
ERROR_CATEGORIES = {"GRAMMAR", "TYPOS", "CONFUSED_WORDS", "PUNCTUATION", "CASING", "CRASE", "SEMANTICS"}


class LanguageToolError(RuntimeError):
    pass


def _check_url(url: str, allow_remote: bool) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise LanguageToolError(f"not a LanguageTool URL: {url}")
    if parsed.hostname not in LOCAL_HOSTS and not allow_remote:
        raise LanguageToolError("refusing to send text to a remote LanguageTool server; "
                                "use a local server or allow it explicitly")
    return url.rstrip("/")


def check(text: str, url: str, language: str = "pt-BR", allow_remote: bool = False, timeout: float = 60.0,
          disabled_rules: tuple = (), transport=None) -> list[dict]:
    """Matches for ``text``: rule id, category, message, offset, length, the
    matched text and up to three replacements."""
    endpoint = _check_url(url, allow_remote) + "/v2/check"
    body = {"text": text, "language": language}
    if disabled_rules:
        body["disabledRules"] = ",".join(disabled_rules)
    request = urllib.request.Request(endpoint, data=urllib.parse.urlencode(body).encode("utf-8"), method="POST")
    try:
        raw = transport(request) if transport else urllib.request.urlopen(request, timeout=timeout).read()
        payload = json.loads(raw.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise LanguageToolError(f"LanguageTool at {url} failed: {type(error).__name__}") from None
    out = []
    for m in payload.get("matches", []):
        start, length = m.get("offset", 0), m.get("length", 0)
        out.append({"rule": m.get("rule", {}).get("id"), "category": m.get("rule", {}).get("category", {}).get("id"),
                    "message": m.get("message"), "offset": start, "length": length, "text": text[start:start + length],
                    "replacements": [r.get("value") for r in m.get("replacements", [])[:3]]})
    return out


def errors(matches: list[dict]) -> list[dict]:
    return [m for m in matches if m["category"] in ERROR_CATEGORIES]


def introduced(original_matches: list[dict], candidate_matches: list[dict]) -> list[dict]:
    """Error matches in the candidate whose (rule, matched text) does not
    occur in the original: what the rewrite added."""
    before = Counter((m["rule"], m["text"].lower()) for m in errors(original_matches))
    out = []
    for m in errors(candidate_matches):
        key = (m["rule"], m["text"].lower())
        if before[key]:
            before[key] -= 1
        else:
            out.append(m)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8081")
    parser.add_argument("--out", default=str(ROOT / "evals" / "experiments" / "languagetool_probe.json"))
    args = parser.parse_args()
    originals, pairs = {}, []
    for path in sorted((ROOT / "benchmarks" / "cases").glob("*.jsonl")):
        for case in load_cases(path):
            originals[(path.stem, case["id"])] = case["text"]
    for path in sorted((ROOT / "benchmarks" / "runs").glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        texts = {r["id"]: r["output"] for r in run["rows"] if r["arm"] == "B0-original" and "output" in r}
        for row in run["rows"]:
            if row["arm"] != "B0-original" and "output" in row and row["id"] in texts:
                pairs.append({"source": f"{path.name}:{row['arm']}", "id": row["id"],
                              "original": texts[row["id"]], "output": row["output"]})
    for path in sorted((ROOT / "evals" / "integration").glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        for row in run.get("results", []):
            if isinstance(row.get("original"), str) and isinstance(row.get("final_text"), str) \
                    and row["final_text"].strip() != row["original"].strip():
                pairs.append({"source": path.name, "id": row["id"], "original": row["original"],
                              "output": row["final_text"]})

    report_originals = []
    for (suite, cid), text in sorted(originals.items()):
        found = errors(check(text, args.url))
        report_originals.append({"suite": suite, "id": cid, "words": len(text.split()),
                                 "errors": [{k: m[k] for k in ("rule", "category", "text", "message")} for m in found]})
    report_pairs = []
    for pair in pairs:
        new = introduced(check(pair["original"], args.url), check(pair["output"], args.url))
        report_pairs.append({"source": pair["source"], "id": pair["id"],
                             "introduced": [{k: m[k] for k in ("rule", "category", "text", "message", "replacements")}
                                            for m in new]})
    rules_orig = Counter(e["rule"] for r in report_originals for e in r["errors"])
    rules_new = Counter(e["rule"] for r in report_pairs for e in r["introduced"])
    by_arm = Counter()
    for r in report_pairs:
        by_arm[r["source"].split(":")[-1] if ":" in r["source"] else "engine-integration"] += len(r["introduced"])
    result = {
        "kind": "voznativa.experiment", "name": "languagetool_probe", "version": "v0.4.0 M2",
        "tool": {"name": "LanguageTool", "version": "6.6 (standalone, LanguageTool-stable.zip, build 2025-03-27)",
                 "license": "LGPL-2.1", "mode": "local HTTP server; default rules; language pt-BR"},
        "originals": {"texts": len(report_originals), "with_errors": sum(bool(r["errors"]) for r in report_originals),
                      "rules": dict(rules_orig.most_common())},
        "outputs": {"pairs": len(report_pairs), "with_introduced": sum(bool(r["introduced"]) for r in report_pairs),
                    "rules": dict(rules_new.most_common()), "introduced_by_arm": dict(by_arm)},
        "details": {"originals": report_originals, "pairs": report_pairs},
        "note": "matches are what LanguageTool reports, not verified errors; the reading is in docs/evaluation/EVALUATION.md",
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("originals", "outputs")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
