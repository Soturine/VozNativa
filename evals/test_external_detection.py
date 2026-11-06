"""v0.7.0 CP11: external detector adapters and the H0/H1/A0/A1 protocol.

All numbers here come from mocks or replays of hand-written fixture payloads
shaped like the vendors' documented responses; they are labelled kind=mock or
kind=replay and measure nothing about any real detector."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))

from external_detection.adapters import (COPYLEAKS, CopyleaksAdapter, GPTZeroAdapter, MockAdapter,  # noqa: E402
                                         OriginalityAdapter, ReplayAdapter, parse_copyleaks)
from external_detection.protocol import run, summarize, validate_manifest  # noqa: E402

LONG = "Texto de teste escrito para a suíte, sem conteúdo de terceiros. " * 8


def item(i, group, pair=None, **kw):
    base = {"id": i, "group": group, "text": LONG, "language": "pt"}
    if group == "H0":
        base["authorship_evidence"] = "fixture"
    if group in ("A0", "A1"):
        base["generator"] = {"model": "fixture", "version": "0", "parameters": {}}
    if pair:
        base["pair"] = pair
    return {**base, **kw}


MANIFEST = {"items": [item("h0a", "H0"), item("h1a", "H1", "h0a"), item("h0b", "H0"), item("h1b", "H1", "h0b"),
                      item("a0a", "A0"), item("a1a", "A1", "a0a")]}


class Contracts(unittest.TestCase):
    def test_manifest_rules(self):
        self.assertEqual(validate_manifest(MANIFEST), [])
        bad = {"items": [{"id": "x", "group": "H0", "text": LONG}, {"id": "y", "group": "A1", "text": LONG},
                         {"id": "z", "group": "Q", "text": LONG}, {**item("c", "A0"), "source_corpus": "b2w"}]}
        problems = " ".join(validate_manifest(bad))
        for needle in ("authorship_evidence", "generator", "pair", "group must be", "policy check"):
            self.assertIn(needle, problems)

    def test_live_never_runs_without_authorisation_or_key(self):
        for adapter in (CopyleaksAdapter(token=""), GPTZeroAdapter(key="")):
            rows = run(adapter, {"items": [item("h0a", "H0", upload_permission=True)]}, allow_upload=False)
            self.assertEqual(rows[0]["evidence_status"], "NOT_RUN")
        rows = run(CopyleaksAdapter(token="t"), {"items": [item("h0a", "H0")]}, allow_upload=True)
        self.assertEqual(rows[0]["evidence_status"], "NOT_RUN", "the item itself lacks upload_permission")
        self.assertIsNone(CopyleaksAdapter.__init__.__defaults__[0])

    def test_short_text_is_inconclusive_not_a_score(self):
        m = CopyleaksAdapter(token="t", transport=lambda *a: (200, {})).measure("s", "curto", "pt")
        self.assertEqual((m.call_status, m.evidence_status), ("NOT_RUN", "INCONCLUSIVE"))

    def test_http_error_is_blocked_and_sandbox_is_not_a_measurement(self):
        failing = CopyleaksAdapter(token="t", transport=lambda *a: (401, {"error": "bad token"}))
        self.assertEqual(failing.measure("x", LONG, "pt").evidence_status, "BLOCKED")
        sandbox = CopyleaksAdapter(token="t", sandbox=True,
                                   transport=lambda *a: (200, {"summary": {"human": 0, "ai": 1}, "results": []}))
        self.assertEqual(sandbox.measure("x", LONG, "pt").evidence_status, "INCONCLUSIVE")

    def test_copyleaks_parser_keeps_vendor_fields_and_derives_no_label(self):
        payload = {"summary": {"human": 0.2, "ai": 0.8}, "results": [{"classification": 2, "probability": 0.9}],
                   "modelVersion": "v-fixture", "scannedDocument": {"totalWords": 60, "actualCredits": 1}}
        parsed = parse_copyleaks(payload)
        self.assertEqual(parsed["raw_score"], {"summary_human": 0.2, "summary_ai": 0.8})
        self.assertEqual(parsed["model_version"], "v-fixture")
        m = CopyleaksAdapter(token="t", transport=lambda *a: (200, payload)).measure("x", LONG, "pt")
        self.assertIsNone(m.ai_label, "docs do not say whether summary is a probability; no label invented")

    def test_measurement_kind_and_state_are_closed_sets(self):
        from external_detection.adapters import Measurement
        with self.assertRaises(ValueError):
            Measurement("x", "simulated-live", "i", "PASS", "MEASURED", "s")
        with self.assertRaises(ValueError):
            Measurement("x", "mock", "i", "PASS", "PASS", "s")

    def test_unverified_contracts_do_not_pretend(self):
        self.assertEqual(OriginalityAdapter().measure("x", LONG).evidence_status, "UNSUPPORTED")
        m = GPTZeroAdapter(key="k", transport=lambda *a: (200, {"anything": 1})).measure("x", LONG)
        self.assertEqual(m.evidence_status, "INCONCLUSIVE")
        self.assertEqual(COPYLEAKS.contract, "verified")


class ProtocolMetrics(unittest.TestCase):
    def test_metrics_are_separate_and_mock_is_labelled(self):
        scores = {"h0a": 0.9, "h1a": 0.2, "h0b": 0.1, "h1b": 0.1, "a0a": 0.95, "a1a": 0.3}
        rows = run(MockAdapter(scores), MANIFEST, allow_upload=False)
        s = summarize(rows)["detectors"]["mock-detector:mock"]
        self.assertEqual(s["kind"], "mock")
        self.assertEqual(s["H0"]["false_positive_rate"], {"k": 1, "n": 2, "rate": 0.5})
        self.assertEqual(s["A0"]["sensitivity"], {"k": 1, "n": 1, "rate": 1.0})
        self.assertEqual(s["paired_flips"]["H0->H1"], {"pairs": 2, "ai_to_human_label": 1, "human_to_ai_label": 0})
        self.assertEqual(s["paired_flips"]["A0->A1"]["ai_to_human_label"], 1)

    def test_empty_groups_are_not_run_not_zero(self):
        s = summarize(run(MockAdapter({"a0a": 0.9}), {"items": [item("a0a", "A0")]}, False))
        row = s["detectors"]["mock-detector:mock"]
        self.assertEqual(row["H0"]["false_positive_rate"], "NOT_RUN")
        self.assertEqual(row["paired_flips"]["H0->H1"], "NOT_RUN")

    def test_replay_is_kept_apart_from_live(self):
        rec = {"a0a": {"summary": {"human": 0, "ai": 1}, "results": [], "modelVersion": "rec"}}
        replay = ReplayAdapter(COPYLEAKS, parse_copyleaks, rec, "fixture recording, not a real run")
        rows = run(replay, {"items": [item("a0a", "A0")]}, allow_upload=False)
        self.assertEqual((rows[0]["kind"], rows[0]["evidence_status"]), ("replay", "MEASURED"))
        self.assertIn("copyleaks-writer-detector:replay", summarize(rows)["detectors"])


if __name__ == "__main__":
    unittest.main()
