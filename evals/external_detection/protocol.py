"""H0/H1/A0/A1 protocol for the external detector benchmark (v0.7.0 CP11).

Groups (paired by ``pair``):

* H0 human original, with verifiable or consented authorship;
* H1 the same human text revised by VozNativa;
* A0 AI-generated with a known model, version and parameters;
* A1 the same AI text revised by VozNativa.

An item is sent to an external service only when its manifest entry says
``upload_permission: true`` *and* the caller authorised uploads for this run.
Corpus texts are refused unless the corpus policy allows SEND_TO_EXTERNAL_MODEL.
No group is ever filled by relabelling: an empty H0 is NOT_RUN, not zero.

Metrics are per detector and kept apart: false-positive rate on H0 and H1,
sensitivity on A0 and A1, paired label flips (0 -> 1 and 1 -> 0), and
counts of non-measurements by state. A score is never turned into an
authorship claim; a low score is not evidence of human authorship.
"""
from __future__ import annotations

from collections import Counter

GROUPS = ("H0", "H1", "A0", "A1")
PAIRS = (("H0", "H1"), ("A0", "A1"))


def validate_manifest(manifest: dict) -> list[str]:
    problems = []
    for item in manifest.get("items", []):
        if item.get("group") not in GROUPS:
            problems.append(f"{item.get('id')}: group must be one of {GROUPS}")
        if item.get("group") == "H0" and not item.get("authorship_evidence"):
            problems.append(f"{item.get('id')}: H0 needs authorship_evidence (verifiable or consented)")
        if item.get("group") in ("A0", "A1") and not item.get("generator"):
            problems.append(f"{item.get('id')}: AI items need generator (model, version, parameters)")
        if item.get("group") in ("H1", "A1") and not item.get("pair"):
            problems.append(f"{item.get('id')}: revised items need the id of their original in pair")
        if item.get("source_corpus"):
            problems.append(f"{item.get('id')}: corpus text needs a per-operation policy check before upload")
    return problems


def run(adapter, manifest: dict, allow_upload: bool) -> list[dict]:
    """Measure every item, or record why not. Live adapters need both the
    run-level authorisation and the item's own permission."""
    out = []
    live = getattr(adapter.caps, "kind", "live") == "live"
    for item in manifest.get("items", []):
        if live and not (allow_upload and item.get("upload_permission")):
            out.append({"detector": adapter.caps.name, "kind": "live", "item_id": item["id"], "group": item["group"],
                        "call_status": "NOT_RUN", "evidence_status": "NOT_RUN",
                        "reason": "upload not authorised for this run or this item (LIVE_NOT_RUN)"})
            continue
        m = adapter.measure(item["id"], item["text"], item.get("language")).as_dict()
        out.append({**m, "group": item["group"], "pair": item.get("pair")})
    return out


def _rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "rate": round(k / n, 4) if n else None}


def summarize(measurements: list[dict]) -> dict:
    """Per detector and kind: FP on human groups, sensitivity on AI groups,
    paired flips, and what was not measured. Mock and live never merge."""
    out = {}
    keys = sorted({(m["detector"], m["kind"]) for m in measurements})
    for detector, kind in keys:
        ms = [m for m in measurements if (m["detector"], m["kind"]) == (detector, kind)]
        labelled = {m["item_id"]: m for m in ms if m["evidence_status"] == "MEASURED" and m.get("ai_label") is not None}
        row = {"kind": kind, "not_measured": dict(Counter(m["evidence_status"] for m in ms
                                                          if m["evidence_status"] != "MEASURED"))}
        for g in GROUPS:
            members = [m for m in labelled.values() if m["group"] == g]
            positives = sum(bool(m["ai_label"]) for m in members)
            row[g] = {"items": len([m for m in ms if m["group"] == g]), "labelled": len(members),
                      ("false_positive_rate" if g.startswith("H") else "sensitivity"): _rate(positives, len(members))
                      if members else "NOT_RUN"}
        flips = {}
        for before, after in PAIRS:
            pairs = [(labelled.get(m["pair"]), m) for m in labelled.values() if m["group"] == after]
            pairs = [(a, b) for a, b in pairs if a is not None]
            flips[f"{before}->{after}"] = {
                "pairs": len(pairs),
                "ai_to_human_label": sum(a["ai_label"] and not b["ai_label"] for a, b in pairs),
                "human_to_ai_label": sum(b["ai_label"] and not a["ai_label"] for a, b in pairs)} if pairs else "NOT_RUN"
        row["paired_flips"] = flips
        out[f"{detector}:{kind}"] = row
    return {"kind": "voznativa.external_detection_summary", "schema_version": 1, "detectors": out,
            "interpretation": "vendor classifications of texts of known origin; not evidence of authorship; "
                              "a lower AI label after revision is not a goal and is never fed back to the engine"}
