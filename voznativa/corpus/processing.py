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
    extra_groups: list = field(default_factory=list)   # further keys of group_by (author, speaker...)

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


def group_keys(entry: dict, record) -> list[str]:
    """Every unit a record belongs to. ``processing.group_by`` may be a list
    (v0.7.0: ``[work, author]``): records sharing *any* of the keys land in the
    same split, so an author held out stays held out across all their works."""
    spec = ((entry.get("processing") or {}).get("group_by")) or "record"
    specs = spec if isinstance(spec, list) else [spec]
    return list(dict.fromkeys(group_key({**entry, "processing": {"group_by": s}}, record) for s in specs))


def group_key(entry: dict, record) -> str:
    """The unit that must never be split: from ``processing.group_by`` (a meta
    field or ``sent_id_prefix``); the record itself when nothing is declared.
    With a list, the first key."""
    spec = ((entry.get("processing") or {}).get("group_by")) or "record"
    if isinstance(spec, list):
        return group_keys(entry, record)[0]
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
                                    group_key(entry, r), sha256(r.text), sha256(key), norm, dict(r.meta),
                                    extra_groups=group_keys(entry, r)[1:]))
    return out


def segments(record: ProvenanceRecord) -> list[dict]:
    """Sentences of a record with offsets into its canonical text."""
    return [{"record": record.record_id, "index": s.index, "start": s.start, "end": s.end,
             "sha256": sha256(s.text)} for s in sentences(record.text)]


# --- near-duplicate detection ----------------------------------------------------------

_HISTORIC = ((re.compile(r"ph"), "f"), (re.compile(r"th"), "t"), (re.compile(r"y"), "i"),
             (re.compile(r"([bcdfglmnpt])\1"), r"\1"),          # double consonants (not rr/ss: they are phonemic)
             (re.compile(r"c(?=[ct])|p(?=t)"), ""))              # acção/acto/facto, prompto/escripto


def ortho_key(word: str) -> str:
    """A spelling key for duplicate detection only: pre-1943 Brazilian and
    current European spellings ("acção", "facto", "pharmacia", "sabbado")
    meet their modern Brazilian forms. Never used to change or judge text;
    collisions it creates ("pacto"/"pato") only make 5-word shingles meet
    when the other four words also do."""
    for rx, rep in _HISTORIC:
        word = rx.sub(rep, word)
    return word


def _shingles(text: str) -> set[str]:
    words = [ortho_key(w) for w in re.findall(r"\w+", fold(text))]
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


def cluster(records: list[ProvenanceRecord], threshold: float = NEAR_THRESHOLD, with_containment: bool = True) -> dict:
    """Assign ``cluster`` to every record: exact duplicates by normalized hash,
    near duplicates by LSH candidates confirmed with true Jaccard >= threshold,
    and (v0.7.0) texts contained in a longer text (``containment_links``).
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
    contained = containment_links(records, skip=lambda i, j: find(i) == find(j)) if with_containment else []
    for link in contained:
        union(link["contained"], link["container"])
    for i, r in enumerate(records):
        root = find(i)
        r.cluster = f"c{records[root].normalized_sha256[:16]}"
    sources_by_cluster: dict[str, set] = {}
    for r in records:
        sources_by_cluster.setdefault(r.cluster, set()).add(r.source)
    cross = sorted(c for c, s in sources_by_cluster.items() if len(s) > 1)
    return {"records": len(records), "exact_duplicates": exact, "near_duplicate_links": near,
            "containment_links": len(contained),
            "cross_source_containment_links": sum(records[x["contained"]].source != records[x["container"]].source
                                                  for x in contained),
            "clusters": len(sources_by_cluster), "cross_source_clusters": len(cross)}


# --- directional containment (v0.7.0 CP4, G2) ------------------------------------------

CONTAINMENT_THRESHOLD = 0.8     # share of the smaller text's shingles found in the larger one
MIN_CONTAINED_SHINGLES = 20     # ~24 words: a shorter text is "contained" by coincidence too easily
MAX_DOCUMENT_FREQUENCY = 20     # a shingle in more texts than this is boilerplate or a common quotation
SKETCH = 64                     # bottom-k shingles of the smaller text used to find candidates


def _shingle_hashes(text: str) -> set[int]:
    return {int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "big") for s in _shingles(text)}


def containment(a: str, b: str) -> float:
    """Share of ``a``'s shingles present in ``b`` (directional: a chapter in
    its novel scores ~1, the novel in its chapter scores ~chapter/novel)."""
    x, y = _shingles(a), _shingles(b)
    return len(x & y) / len(x) if x else 0.0


def containment_links(records: list, threshold: float = CONTAINMENT_THRESHOLD,
                      min_shingles: int = MIN_CONTAINED_SHINGLES, max_df: int = MAX_DOCUMENT_FREQUENCY,
                      skip=None) -> list[dict]:
    """Pairs where a text is contained in a longer one: a chapter in its novel,
    an excerpt in its document, a republished section. Jaccard (symmetric)
    misses these when the sizes differ (G2).

    Candidates come from an inverted index of shingles, without shingles that
    occur in more than ``max_df`` texts (shared formulas and famous quotations
    are not evidence of the same document); each candidate is confirmed with
    the exact containment over the remaining shingles."""
    sets = [_shingle_hashes(r.text) for r in records]
    postings: dict[int, list[int]] = {}
    for i, s in enumerate(sets):
        for h in s:
            postings.setdefault(h, []).append(i)
    common = {h for h, ids in postings.items() if len(ids) > max_df}
    links = []
    for i, s in enumerate(sets):
        rare = s - common
        if len(rare) < min_shingles:
            continue
        sketch = sorted(rare)[:SKETCH]
        hits: dict[int, int] = {}
        for h in sketch:
            for j in postings[h]:
                if j != i and len(sets[j]) > len(s):
                    hits[j] = hits.get(j, 0) + 1
        for j, n in hits.items():
            if n < threshold * len(sketch) * 0.75:          # cheap filter; the exact check decides
                continue
            if skip is not None and skip(i, j):
                continue
            score = len(rare & sets[j]) / len(rare)
            if score >= threshold:
                links.append({"contained": i, "container": j, "containment": round(score, 3),
                              "shingles": len(rare)})
    return links


# --- stable splits and leakage --------------------------------------------------------


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
        for extra in r.extra_groups:
            parent[find(extra)] = find(r.group)
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

    seen: dict[str, dict[str, set]] = {"group": {}, "extra_group": {}, "cluster": {}, "original": {},
                                       "normalized": {}}
    for r in records:
        split = splits.get(key(r))
        if split is None:
            continue
        for kind, value in (("group", r.group), ("cluster", r.cluster), ("original", r.original_sha256),
                            ("normalized", r.normalized_sha256), *(("extra_group", g) for g in r.extra_groups)):
            if value:
                seen[kind].setdefault(value, set()).add(split)
    report = {kind: sorted(v for v, s in values.items() if len(s) > 1) for kind, values in seen.items()}
    report["contaminated"] = any(report[k] for k in ("group", "extra_group", "cluster", "original", "normalized"))
    return report


def diff_manifests(old: list[dict], new: list[dict]) -> dict:
    """Records added, removed and changed (same id, other hash) between runs."""
    a = {(m["source"], m["record_id"]): m["original_sha256"] for m in old}
    b = {(m["source"], m["record_id"]): m["original_sha256"] for m in new}
    return {"added": sorted(set(b) - set(a)), "removed": sorted(set(a) - set(b)),
            "changed": sorted(k for k in set(a) & set(b) if a[k] != b[k])}
