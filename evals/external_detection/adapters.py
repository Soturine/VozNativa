"""External AI-detector adapters (v0.7.0 CP11): *measure*, never optimise.

A detector score is a vendor's fallible classification, not proof of
authorship. These adapters exist to measure how detectors classify texts of
known origin before and after a VozNativa revision; the engine never sees a
detector score and never iterates against one.

Every call returns a typed ``Measurement`` that keeps the vendor's raw score
and its documented meaning (``score_semantics``), the provenance of the
result (``kind``: live, replay or mock, never mixed) and two separate states:

* ``call_status``: PASS/FAIL of the technical call only;
* ``evidence_status``: MEASURED, or NOT_RUN / BLOCKED / UNSUPPORTED /
  INCONCLUSIVE when there is no evaluation evidence.

Contracts were read from the vendors' public docs on 2026-11-06; fields a
page did not state are marked unverified and never interpreted.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict, dataclass, field

KINDS = ("live", "replay", "mock")
EVIDENCE = ("MEASURED", "NOT_RUN", "BLOCKED", "UNSUPPORTED", "INCONCLUSIVE")


@dataclass(frozen=True)
class Capabilities:
    name: str
    model_version: str | None
    languages: tuple
    min_chars: int
    max_chars: int
    price_or_quota: str
    input_retention_policy: str
    permission_mode: str
    kind: str
    source_url: str
    last_verified: str
    contract: str            # verified | partial | unverified


@dataclass
class Measurement:
    detector: str
    kind: str
    item_id: str
    call_status: str
    evidence_status: str
    score_semantics: str
    raw_score: dict | None = None
    ai_label: bool | None = None          # vendor's own label, only when the vendor states one
    model_version: str | None = None
    reason: str | None = None
    usage: dict = field(default_factory=dict)
    sections: list = field(default_factory=list)

    def __post_init__(self):
        # A mock or a replay must never be read as a live measurement.
        if self.kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        if self.evidence_status not in EVIDENCE:
            raise ValueError(f"evidence_status must be one of {EVIDENCE}")

    def as_dict(self) -> dict:
        return asdict(self)


class DetectorAdapter:
    caps: Capabilities

    def validate_input(self, text: str, language: str | None = None) -> str | None:
        """None when the text can be sent; otherwise why not (INCONCLUSIVE)."""
        if len(text) < self.caps.min_chars:
            return f"text has {len(text)} characters; {self.caps.name} needs at least {self.caps.min_chars}"
        if len(text) > self.caps.max_chars:
            return f"text has {len(text)} characters; {self.caps.name} accepts at most {self.caps.max_chars}"
        if language and self.caps.languages and language not in self.caps.languages:
            return f"language {language} not in the documented list"
        return None

    def measure(self, item_id: str, text: str, language: str | None = None) -> Measurement:
        problem = self.validate_input(text, language)
        if problem:
            return Measurement(self.caps.name, self.caps.kind, item_id, "NOT_RUN", "INCONCLUSIVE",
                               self.caps.contract, reason=problem)
        return self._measure(item_id, text, language)

    def _measure(self, item_id, text, language) -> Measurement:  # pragma: no cover - abstract
        raise NotImplementedError


def _post(url: str, body: dict, headers: dict, timeout: float = 60.0) -> tuple[int, dict]:
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, {"error": error.read().decode("utf-8", "replace")[:500]}


# --- Copyleaks (contract verified: docs.copyleaks.com/reference/actions/writer-detector/check) -----

COPYLEAKS = Capabilities(
    name="copyleaks-writer-detector", model_version=None, languages=("pt", "en", "es", "fr", "de"),
    min_chars=255, max_chars=100_000, price_or_quota="paid credits per scan; sandbox mode free (no real result)",
    input_retention_policy="not stated on the check page; review the vendor terms before uploading",
    permission_mode="Bearer login token; uploads only items with explicit upload permission",
    kind="live", source_url="https://docs.copyleaks.com/reference/actions/writer-detector/check",
    last_verified="2026-11-06", contract="verified")


def parse_copyleaks(payload: dict) -> dict:
    """Keeps the vendor's fields; ``summary`` meaning (probability vs count) is
    not stated by the docs, so no label is derived from it."""
    summary = payload.get("summary") or {}
    sections = [{"classification": r.get("classification"), "probability": r.get("probability")}
                for r in payload.get("results") or []]
    return {"raw_score": {"summary_human": summary.get("human"), "summary_ai": summary.get("ai")},
            "model_version": payload.get("modelVersion"), "sections": sections,
            "usage": {k: (payload.get("scannedDocument") or {}).get(k)
                      for k in ("totalWords", "actualCredits", "expectedCredits")}}


class CopyleaksAdapter(DetectorAdapter):
    caps = COPYLEAKS
    URL = "https://api.copyleaks.com/v2/writer-detector/{scan}/check"

    def __init__(self, token: str | None = None, sandbox: bool = False, transport=_post):
        self.token = token or os.environ.get("COPYLEAKS_TOKEN")
        self.sandbox, self.transport = sandbox, transport

    def _measure(self, item_id, text, language):
        if not self.token:
            return Measurement(self.caps.name, "live", item_id, "NOT_RUN", "NOT_RUN", "unstated",
                               reason="no COPYLEAKS_TOKEN: live call not made")
        status, payload = self.transport(self.URL.format(scan=uuid.uuid4().hex[:24]),
                                         {"text": text, "sandbox": self.sandbox,
                                          **({"language": language} if language else {})},
                                         {"Authorization": f"Bearer {self.token}"})
        if status != 200:
            return Measurement(self.caps.name, "live", item_id, "FAIL", "BLOCKED", "unstated",
                               reason=f"HTTP {status}: {str(payload)[:200]}")
        parsed = parse_copyleaks(payload)
        evidence = "INCONCLUSIVE" if self.sandbox else "MEASURED"
        return Measurement(self.caps.name, "live", item_id, "PASS", evidence,
                           "summary.human/ai as returned; docs do not state whether probability or count",
                           reason="sandbox: test response, not a measurement" if self.sandbox else None,
                           **parsed)


# --- GPTZero (contract partial: docs.gptzero.me/api-reference) -------------------------------------

GPTZERO = Capabilities(
    name="gptzero-predict-text", model_version=None, languages=(), min_chars=1, max_chars=150_000,
    price_or_quota="API plan; 150,000 characters per request on API plans (docs)",
    input_retention_policy="not stated on the reference page", permission_mode="API key (header name unverified)",
    kind="live", source_url="https://docs.gptzero.me/api-reference/", last_verified="2026-11-06",
    contract="partial")


class GPTZeroAdapter(DetectorAdapter):
    """Endpoint and the modelVersion parameter are documented; the auth
    header and response field names were not on the page read. The raw
    payload is kept whole and never interpreted into a label."""
    caps = GPTZERO
    URL = "https://api.gptzero.me/v2/predict/text"

    def __init__(self, key: str | None = None, model_version: str | None = None, transport=_post):
        self.key = key or os.environ.get("GPTZERO_API_KEY")
        self.model_version, self.transport = model_version, transport

    def _measure(self, item_id, text, language):
        if not self.key:
            return Measurement(self.caps.name, "live", item_id, "NOT_RUN", "NOT_RUN", "unverified",
                               reason="no GPTZERO_API_KEY: live call not made")
        body = {"document": text, **({"modelVersion": self.model_version} if self.model_version else {})}
        status, payload = self.transport(self.URL, body, {"x-api-key": self.key})
        if status != 200:
            return Measurement(self.caps.name, "live", item_id, "FAIL", "BLOCKED", "unverified",
                               reason=f"HTTP {status}: {str(payload)[:200]}")
        return Measurement(self.caps.name, "live", item_id, "PASS", "INCONCLUSIVE", "unverified",
                           raw_score={"payload": payload}, model_version=self.model_version,
                           reason="response fields not verified against current docs: kept raw, not scored")


# --- Originality.ai (contract unverified) ----------------------------------------------------------

ORIGINALITY = Capabilities(
    name="originality-ai", model_version=None, languages=(), min_chars=1, max_chars=1, price_or_quota="unknown",
    input_retention_policy="unknown", permission_mode="unknown", kind="live",
    source_url="https://docs.originality.ai/", last_verified="2026-11-06", contract="unverified")


class OriginalityAdapter(DetectorAdapter):
    caps = ORIGINALITY

    def measure(self, item_id, text, language=None):
        return Measurement(self.caps.name, "live", item_id, "NOT_RUN", "UNSUPPORTED", "unverified",
                           reason="endpoint and fields could not be confirmed from the docs read on 2026-11-06")


# --- offline adapters, labelled as such ------------------------------------------------------------

class MockAdapter(DetectorAdapter):
    """Deterministic fake for contract tests. Its numbers are not measurements
    of anything and are labelled kind=mock everywhere."""

    def __init__(self, scores: dict[str, float], name: str = "mock-detector"):
        self.scores = scores
        self.caps = Capabilities(name, "mock-1", ("pt",), 1, 10**6, "free", "none", "none", "mock", "-",
                                 "2026-11-06", "verified")

    def _measure(self, item_id, text, language):
        score = self.scores.get(item_id)
        if score is None:
            return Measurement(self.caps.name, "mock", item_id, "FAIL", "INCONCLUSIVE", "mock probability",
                               reason="mock has no score for this item")
        return Measurement(self.caps.name, "mock", item_id, "PASS", "MEASURED", "mock probability of AI (fake)",
                           raw_score={"p_ai": score}, ai_label=score >= 0.5, model_version="mock-1")


class ReplayAdapter(DetectorAdapter):
    """Replays recorded vendor payloads (from a live run) through the same
    parser; results are kind=replay and carry the recording's provenance."""

    def __init__(self, inner_caps: Capabilities, parser, recordings: dict[str, dict], provenance: str):
        self.caps = Capabilities(**{**asdict(inner_caps), "kind": "replay"})
        self.parser, self.recordings, self.provenance = parser, recordings, provenance

    def _measure(self, item_id, text, language):
        payload = self.recordings.get(item_id)
        if payload is None:
            return Measurement(self.caps.name, "replay", item_id, "NOT_RUN", "NOT_RUN", "as recorded",
                               reason="no recording for this item")
        return Measurement(self.caps.name, "replay", item_id, "PASS", "MEASURED",
                           f"as recorded ({self.provenance})", **self.parser(payload))
