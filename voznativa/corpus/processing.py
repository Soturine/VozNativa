"""Provenance, normalisation, deduplication and stable splits.

* Originals are never modified: a ``ProvenanceRecord`` keeps the original
  text's sha256 next to the canonical copy used for analysis.
* Grouping keys (work, author, speaker, interview, recording, document) come
  from the registry entry (``processing.group_by``): every segment of a
  group lands in the same split.
* Exact duplicates (same canonical text) and near duplicates (MinHash over
  word shingles, with LSH banding) are clustered across sources; a cluster
  is split as one unit, so a republication or a lightly edited copy cannot
  sit in calibration and evaluation at once.
* ``leakage`` checks a split and reports any group, cluster or text that
  crosses it; ``diff_manifests`` reports added, removed and changed records
  between two processing runs (removed documents, new versions).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field

from ..text import canonical, fold, normalize_surface, sentences

SHINGLE = 5
NUM_PERM = 64
BANDS = 16                      # 16 bands x 4 rows: candidates from ~0.5 Jaccard
NEAR_THRESHOLD = 0.8
_PRIME = (1 << 61) - 1
_SEEDS = [(int.from_bytes(hashlib.sha256(f"a{i}".encode()).digest()[:8], "big") | 1,
           int.from_bytes(hashlib.sha256(f"b{i}".encode()).digest()[:8], "big")) for i in range(NUM_PERM)]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class ProvenanceRecord:
    source: str
    asset: str
    asset_sha256: str | None
    record_id: str
    group: str
    original_sha256: str
    normalized_sha256: str
    text: str                      # canonical copy for analysis; the original stays in the source
    meta: dict = field(default_factory=dict)
    cluster: str | None = None

    def as_manifest(self) -> dict:
        """What a committed manifest may hold: identifiers and hashes, no text."""
        out = asdict(self)
        out.pop("text")
        out.pop("meta")
        return out


MANIFEST_OPERATIONS = ("EXPORT_STATISTICS", "EXPORT_SAMPLES", "REDISTRIBUTE", "SEND_TO_EXTERNAL_MODEL", "TRAIN_MODEL")


def document_license(meta: dict) -> str | None:
    """A per-document licence code carried by the reader (TEI ``licence``,
    a ``license`` column), or None when the record has none of its own."""
    lic = (meta or {}).get("licence") or (meta or {}).get("license")
    if isinstance(lic, dict):
        return lic.get("code")
    return lic if isinstance(lic, str) and lic else None


def manifest_row(entry: dict, record: "ProvenanceRecord") -> dict:
    """Manifest row with the document identity, its own licence and the
    policy state of each sensitive operation for that record (v0.7.0 CP2).
    A record of a per-document source without a licence of its own is
    decided as ``unknown`` and never inherits the corpus card."""
    from .policy import decide
    row = record.as_manifest()
    meta = record.meta or {}
    for key in ("doc_id", "par_id", "idno"):
        if meta.get(key):
            row[key] = meta[key]
    per_document = bool(entry.get("license", {}).get("per_document")) or entry.get("license", {}).get("code") == \
        "per_document"
    lic = document_license(meta) or ("unknown" if per_document else None)
    if lic:
        row["document_license"] = lic
    row["policy"] = {op: decide(entry, op, document_license=lic).state for op in MANIFEST_OPERATIONS}
    return row


def group_key(entry: dict, record) -> str:
    """The unit that must never be split: from ``processing.group_by`` (a meta
    field or ``sent_id_prefix``); the record itself when nothing is declared."""
    spec = ((entry.get("processing") or {}).get("group_by")) or "record"
    if spec == "sent_id_prefix":
        document = re.sub(r"-\d+$", "", record.record_id)  # CF1-3 -> CF1; no backslash in f-strings (3.11)
        return f"{entry['id']}:{document}"
    if spec == "record":
        return f"{entry['id']}:{record.record_id}"
    value = (record.meta or {}).get(spec)
    return f"{entry['id']}:{spec}={value}" if value not in (None, "") else f"{entry['id']}:{record.record_id}"


def provenance(entry: dict, records, asset_sha: dict | None = None) -> list[ProvenanceRecord]:
    out = []
    for r in records:
        norm = canonical(r.text)
        # The dedup key also ignores surface-only differences (spaces, quote glyphs, CRLF).
        key = normalize_surface(norm).strip()
        out.append(ProvenanceRecord(entry["id"], r.asset, (asset_sha or {}).get(r.asset), r.record_id,
                                    group_key(entry, r), sha256(r.text), sha256(key), norm, dict(r.meta)))
    return out


def segments(record: ProvenanceRecord) -> list[dict]:
    """Sentences of a record with offsets into its canonical text."""
    return [{"record": record.record_id, "index": s.index, "start": s.start, "end": s.end,
             "sha256": sha256(s.text)} for s in sentences(record.text)]


# --- near-duplicate detection ----------------------------------------------------------

def _shingles(text: str) -> set[str]:
    words = re.findall(r"\w+", fold(text))
    if len(words) < SHINGLE:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + SHINGLE]) for i in range(len(words) - SHINGLE + 1)}


def minhash(text: str) -> list[int]:
    hashes = [int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "big") for s in _shingles(text)]
    if not hashes:
        return [0] * NUM_PERM
    return [min((a * h + b) % _PRIME for h in hashes) for a, b in _SEEDS]


def jaccard(a: str, b: str) -> float:
    x, y = _shingles(a), _shingles(b)
    return len(x & y) / len(x | y) if x | y else 1.0


def cluster(records: list[ProvenanceRecord], threshold: float = NEAR_THRESHOLD) -> dict:
    """Assign ``cluster`` to every record: exact duplicates by normalized hash,
    near duplicates by LSH candidates confirmed with true Jaccard >= threshold.
    Returns counts and the cross-source duplicate pairs found."""
    parent = list(range(len(records)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        parent[find(i)] = find(j)

    by_hash: dict[str, int] = {}
    exact = 0
    for i, r in enumerate(records):
        if r.normalized_sha256 in by_hash:
            union(i, by_hash[r.normalized_sha256])
            exact += 1
        else:
            by_hash[r.normalized_sha256] = i
    rows = NUM_PERM // BANDS
    buckets: dict[tuple, list[int]] = {}
    signatures = {i: minhash(records[i].text) for i in by_hash.values()}
    for i, sig in signatures.items():
        for band in range(BANDS):
            buckets.setdefault((band, tuple(sig[band * rows:(band + 1) * rows])), []).append(i)
    near, checked, cross = 0, set(), []
    for members in buckets.values():
        for x in range(len(members)):
            for y in range(x + 1, len(members)):
                i, j = members[x], members[y]
                if (i, j) in checked or find(i) == find(j):
                    continue
                checked.add((i, j))
                if jaccard(records[i].text, records[j].text) >= threshold:
                    union(i, j)
                    near += 1
    for i, r in enumerate(records):
        root = find(i)
        r.cluster = f"c{records[root].normalized_sha256[:16]}"
    sources_by_cluster: dict[str, set] = {}
    for r in records:
        sources_by_cluster.setdefault(r.cluster, set()).add(r.source)
    cross = sorted(c for c, s in sources_by_cluster.items() if len(s) > 1)
    return {"records": len(records), "exact_duplicates": exact, "near_duplicate_links": near,
            "clusters": len(sources_by_cluster), "cross_source_clusters": len(cross)}


# --- stable splits and leakage --------------------------------------------------------

def split_unit(record: ProvenanceRecord) -> str:
    """Group and duplicate cluster together: the unit the split may not cut."""
    return record.cluster or record.group


def assign_splits(records: list[ProvenanceRecord], fractions: dict[str, float], salt: str = "voznativa-v0.6") -> dict:
    """Deterministic split by hashing each unit; units are formed by merging
    groups that share a duplicate cluster, so neither crosses a split."""
    if abs(sum(fractions.values()) - 1.0) > 1e-9:
        raise ValueError("split fractions must sum to 1")
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in records:
        parent[find(r.group)] = find(f"cluster:{r.cluster}" if r.cluster else r.group)
    names = sorted(fractions)
    out = {}
    for r in records:
        unit = find(r.group)
        point = int(hashlib.sha256(f"{salt}:{unit}".encode()).hexdigest()[:12], 16) / float(16 ** 12)
        acc = 0.0
        for name in names:
            acc += fractions[name]
            if point < acc or name == names[-1]:
                out[f"{r.source}:{r.record_id}"] = name
                break
    return out


def leakage(records: list[ProvenanceRecord], splits: dict[str, str]) -> dict:
    """Groups, duplicate clusters and identical texts (original or normalized)
    present in more than one split. Empty lists mean no contamination found."""
    def key(r):
        return f"{r.source}:{r.record_id}"

    seen: dict[str, dict[str, set]] = {"group": {}, "cluster": {}, "original": {}, "normalized": {}}
    for r in records:
        split = splits.get(key(r))
        if split is None:
            continue
        for kind, value in (("group", r.group), ("cluster", r.cluster), ("original", r.original_sha256),
                            ("normalized", r.normalized_sha256)):
            if value:
                seen[kind].setdefault(value, set()).add(split)
    report = {kind: sorted(v for v, s in values.items() if len(s) > 1) for kind, values in seen.items()}
    report["contaminated"] = any(report[k] for k in ("group", "cluster", "original", "normalized"))
    return report


def diff_manifests(old: list[dict], new: list[dict]) -> dict:
    """Records added, removed and changed (same id, other hash) between runs."""
    a = {(m["source"], m["record_id"]): m["original_sha256"] for m in old}
    b = {(m["source"], m["record_id"]): m["original_sha256"] for m in new}
    return {"added": sorted(set(b) - set(a)), "removed": sorted(set(a) - set(b)),
            "changed": sorted(k for k in set(a) & set(b) if a[k] != b[k])}
