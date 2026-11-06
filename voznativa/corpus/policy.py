"""Data Policy: what an operation on a corpus source is allowed to do.

A technical control over identified terms, not legal advice. Each decision
is ALLOWED, DENIED, REQUIRES_PERMISSION (terms identified; they ask for a
permission) or UNKNOWN (terms not identified: someone must review; nothing
is presumed). Every decision carries its reasons, conditions and evidence.

Inputs that change a decision:

* the licence code of the source, or of the document when licences are
  per document (a corpus licence never stands in for its documents);
* how the host offers the data (``access.type``) and what is proven
  (``status``: data operations need verified access);
* the purpose (``noncommercial_research`` by default; ``commercial``);
* the destination of anything exported (``mit_repository`` by default:
  share-alike or no-derivatives material cannot be mixed into it);
* personal data (``privacy.personal_data``): samples and model calls with
  personal data need a permission whatever the licence says;
* documented permissions on the entry (``permissions``), which apply only
  to the operations, purpose and scope they name.
"""
from __future__ import annotations

from dataclasses import dataclass, field

OPERATIONS = ("DISCOVER", "READ_METADATA", "QUERY", "DOWNLOAD", "PROCESS_LOCAL", "DERIVE_FEATURES",
              "EXPORT_STATISTICS", "EXPORT_SAMPLES", "REDISTRIBUTE", "PUBLISH_DERIVATIVES", "SEND_TO_EXTERNAL_MODEL",
              "TRAIN_MODEL")
STATES = ("ALLOWED", "DENIED", "REQUIRES_PERMISSION", "UNKNOWN")
PURPOSES = ("noncommercial_research", "commercial")
DATA_OPERATIONS = frozenset(OPERATIONS[3:])          # need the data, not only the catalogue
PUBLICATION = frozenset({"EXPORT_SAMPLES", "REDISTRIBUTE", "PUBLISH_DERIVATIVES"})
CC = {  # licence family -> (attribution, share_alike, non_commercial, no_derivatives)
    "CC0-1.0": (False, False, False, False),
    "CC-BY-4.0": (True, False, False, False),
    "CC-BY-SA-4.0": (True, True, False, False),
    "CC-BY-NC-4.0": (True, False, True, False),
    "CC-BY-NC-SA-4.0": (True, True, True, False),
    "CC-BY-ND-4.0": (True, False, False, True),
    "CC-BY-NC-ND-4.0": (True, False, True, True),
}
SHARE_ALIKE_COMPATIBLE = {"CC-BY-SA-4.0": {"CC-BY-SA-4.0"}, "CC-BY-NC-SA-4.0": {"CC-BY-NC-SA-4.0"}}


@dataclass
class Decision:
    operation: str
    state: str
    reasons: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.state == "ALLOWED"

    def as_dict(self) -> dict:
        return {"operation": self.operation, "state": self.state, "reasons": self.reasons,
                "conditions": self.conditions, "evidence": self.evidence}


class GuardRefused(PermissionError):
    """A data guard outside the licence decision refused (e.g. personal data
    shown without the explicit flag). The CLI maps it, like PolicyDenied, to
    exit 77; an unreadable file stays a usage error (64)."""


class PolicyDenied(PermissionError):
    def __init__(self, decision: Decision, source_id: str):
        super().__init__(f"{source_id}: {decision.operation} is {decision.state}: {'; '.join(decision.reasons)}")
        self.decision = decision


def _license_decision(code: str, op: str, purpose: str, destination: str) -> Decision:
    d = Decision(op, "UNKNOWN")
    if code in CC:
        attribution, share_alike, non_commercial, no_derivatives = CC[code]
        if attribution:
            d.conditions.append(f"attribute the source ({code})")
        if non_commercial and purpose == "commercial":
            return Decision(op, "DENIED", [f"{code} forbids commercial use"], d.conditions)
        if op == "TRAIN_MODEL":
            if code == "CC0-1.0":
                return Decision(op, "ALLOWED", ["CC0 dedication"])
            return Decision(op, "REQUIRES_PERMISSION",
                            [f"training on {code} material is not settled by the licence text; ask the rights holder"],
                            d.conditions)
        if op == "PUBLISH_DERIVATIVES" and no_derivatives:
            return Decision(op, "DENIED", [f"{code} forbids adapted material"], d.conditions)
        if op in PUBLICATION and (share_alike or no_derivatives) and destination == "mit_repository":
            return Decision(op, "DENIED",
                            [f"{code} material cannot be published inside the MIT-licensed repository"
                             + (" (share-alike)" if share_alike else " (no derivatives)")],
                            d.conditions + ["publish apart, under the source licence"])
        if op in PUBLICATION and share_alike and destination not in SHARE_ALIKE_COMPATIBLE.get(code, set()):
            return Decision(op, "DENIED", [f"{code} requires the same licence for what is shared"], d.conditions)
        if op == "SEND_TO_EXTERNAL_MODEL" and (non_commercial or no_derivatives):
            return Decision(op, "REQUIRES_PERMISSION",
                            [f"sending {code} text to a third-party model provider is a disclosure the licence "
                             "does not clearly cover"], d.conditions)
        return Decision(op, "ALLOWED", [f"{code} permits it"], d.conditions)
    if code == "query_only":
        if op == "QUERY":
            return Decision(op, "ALLOWED", ["the host offers a query interface"], ["respect the service's terms"])
        if op == "EXPORT_STATISTICS":
            return Decision(op, "UNKNOWN", ["terms for publishing statistics of query results not identified"])
        return Decision(op, "DENIED", ["the source is offered for querying only"])
    if code == "research_only":
        if purpose == "commercial":
            return Decision(op, "DENIED", ["research-only terms"])
        if op in {"PROCESS_LOCAL", "DERIVE_FEATURES", "EXPORT_STATISTICS"}:
            return Decision(op, "REQUIRES_PERMISSION", ["research-only terms granted per request"])
        return Decision(op, "DENIED" if op in PUBLICATION | {"SEND_TO_EXTERNAL_MODEL", "TRAIN_MODEL"} else
                        "REQUIRES_PERMISSION", ["research-only terms"])
    if code == "elra_licence":
        return Decision(op, "REQUIRES_PERMISSION", ["distributed under an ELRA licence that must be obtained"])
    reason = {"none_stated": "no licence is stated by the source", "unknown": "the licence was not identified",
              "per_document": "licences vary per document and no document licence was given",
              "per_subset": "licences vary per subset and no subset was named"}.get(code, f"unrecognised code {code!r}")
    return Decision(op, "UNKNOWN", [reason + ": review before using it"])


def decide(entry: dict, operation: str, purpose: str = "noncommercial_research", destination: str = "mit_repository",
           document_license: str | None = None) -> Decision:
    """The decision for one operation on one source (or one of its documents)."""
    if operation not in OPERATIONS:
        raise ValueError(f"operation must be one of {OPERATIONS}")
    if purpose not in PURPOSES:
        raise ValueError(f"purpose must be one of {PURPOSES}")
    source_id = entry["id"]
    evidence = [f"registry:{source_id} licence {entry['license']['code']} ({entry['license'].get('evidence')})"]
    if operation in {"DISCOVER", "READ_METADATA"}:
        return Decision(operation, "ALLOWED", ["public catalogue information"], evidence=evidence)
    access = (entry.get("access") or {}).get("type")
    if operation in DATA_OPERATIONS:
        if entry["status"] in {"CATALOGUED", "SOURCE_VERIFIED"}:
            return Decision(operation, "UNKNOWN", [f"no verified access path (status {entry['status']})"],
                            evidence=evidence)
        if entry["status"] in {"RESTRICTED", "AWAITING_PERMISSION", "UNAVAILABLE", "DEPRECATED"}:
            return _with_permission(entry, Decision(operation, "REQUIRES_PERMISSION",
                                                    [f"status {entry['status']}: {entry.get('status_reason')}"],
                                                    evidence=evidence), purpose)
        if operation == "DOWNLOAD" and access in {"registration", "request"}:
            return _with_permission(entry, Decision(operation, "REQUIRES_PERMISSION",
                                                    [f"the host gives data only after {access}"],
                                                    evidence=evidence), purpose)
    code = entry["license"]["code"]
    if entry["license"].get("per_document") or code == "per_document":
        if document_license:
            code = document_license
            evidence.append(f"document licence {document_license}")
        elif operation not in {"QUERY", "DOWNLOAD", "PROCESS_LOCAL", "DERIVE_FEATURES", "EXPORT_STATISTICS"}:
            return Decision(operation, "UNKNOWN", ["licences vary per document: decide per document"],
                            evidence=evidence)
        else:
            code = "per_document_local"
    if code == "per_document_local":
        decision = Decision(operation, "ALLOWED", ["local use of documents whose licences are each recorded"],
                            ["keep the per-document licence with every derived record"])
    else:
        decision = _license_decision(code, operation, purpose, destination)
    decision.evidence = evidence + decision.evidence
    personal = ((entry.get("privacy") or {}).get("personal_data", "unknown"))
    if decision.allowed and operation in {"EXPORT_SAMPLES", "SEND_TO_EXTERNAL_MODEL", "REDISTRIBUTE"} \
            and personal in {True, "possible", "unknown"}:
        decision = Decision(operation, "REQUIRES_PERMISSION",
                            [f"personal data is {personal!s} for this source: samples or model calls need a "
                             "documented permission and a privacy review"], decision.conditions, decision.evidence)
    return _with_permission(entry, decision, purpose)


def _with_permission(entry: dict, decision: Decision, purpose: str) -> Decision:
    """A documented permission turns REQUIRES_PERMISSION/UNKNOWN (or a licence
    DENIED it explicitly covers) into ALLOWED for what it names, nothing else."""
    if decision.allowed:
        return decision
    for grant in entry.get("permissions") or []:
        if decision.operation in grant.get("operations", []) and purpose in grant.get("purposes", [purpose]) \
                and grant.get("granted_by") and grant.get("evidence") and grant.get("date"):
            return Decision(decision.operation, "ALLOWED",
                            [f"documented permission from {grant['granted_by']} ({grant['date']})"],
                            decision.conditions + list(grant.get("conditions", [])),
                            decision.evidence + [grant["evidence"]])
    return decision


def require(entry: dict, operation: str, **kwargs) -> Decision:
    """The decision when ALLOWED; PolicyDenied otherwise (fail closed)."""
    decision = decide(entry, operation, **kwargs)
    if not decision.allowed:
        raise PolicyDenied(decision, entry["id"])
    return decision


def matrix(entry: dict, **kwargs) -> dict:
    return {op: decide(entry, op, **kwargs).as_dict() for op in OPERATIONS}
