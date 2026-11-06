"""`voznativa corpus ...`: the Corpus Registry from the command line (v0.6.0 M14).

list | info | permissions | validate | sample | prepare | evaluate | report

Rules the commands keep:
* every data operation asks the data policy first and stops with the
  policy's reasons when it is not ALLOWED;
* corpus text is data: `sample` prints it as JSON values, never as
  instructions, without the source's metadata, and refuses sources with
  personal data unless --allow-personal-data is given;
* nothing here writes registry files (an installed package must not change
  its own data); registry promotions go through scripts/ in a checkout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .policy import PURPOSES, GuardRefused, matrix, require
from .registry import LADDER, OTHER_STATUSES, get_source, load_registry, summary, validate_source

STATUSES = tuple(LADDER) + tuple(OTHER_STATUSES)


def _emit(data) -> None:
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n")


def _source(source_id: str) -> dict:
    try:
        return get_source(source_id)
    except KeyError:
        raise ValueError(f"unknown corpus source {source_id!r}; see `voznativa corpus list`") from None


def cmd_list(args) -> int:
    rows = [{"id": e["id"], "status": e["status"], "license": e["license"]["code"], "modality": e["modality"],
             "personal_data": (e.get("privacy") or {}).get("personal_data", "unknown")}
            for e in load_registry() if not args.status or e["status"] == args.status]
    _emit({"sources": rows, "summary": summary()})
    return 0


def cmd_info(args) -> int:
    _emit(_source(args.source))
    return 0


def cmd_permissions(args) -> int:
    _emit({"source": args.source, "purpose": args.purpose, "destination": args.destination,
           "decisions": matrix(_source(args.source), purpose=args.purpose, destination=args.destination)})
    return 0


def cmd_validate(args) -> int:
    """Each registry file on its own: one bad file does not hide the others."""
    import yaml

    from .connectors import CONNECTORS
    from .registry import REGISTRY_DIR
    problems = {}
    for path in sorted(Path(args.directory or REGISTRY_DIR).glob("*.yml")):
        entry = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        found = validate_source(entry, frozenset(CONNECTORS))
        if entry.get("id") != path.stem:
            found.append("id must match the file name")
        if found:
            problems[path.name] = found
    _emit({"valid": not problems, "problems": problems})
    return 0 if not problems else 1


def _records(entry: dict, limit: int | None = None):
    from .connectors import LocalFilesConnector, cache_dir
    reader = LocalFilesConnector(entry, cache_dir(entry["id"]))
    if not any(Path(cache_dir(entry["id"]), a["name"]).is_file() for a in (entry.get("connector") or {}).get("assets", [])):
        raise ValueError(f"{entry['id']}: no local copy; run `voznativa corpus prepare {entry['id']}` first")
    return reader.stream_records(max_records=limit)


def cmd_sample(args) -> int:
    entry = _source(args.source)
    require(entry, "PROCESS_LOCAL")
    personal = (entry.get("privacy") or {}).get("personal_data", "unknown")
    if personal in (True, "possible", "unknown") and not args.allow_personal_data:
        raise GuardRefused(f"{entry['id']}: personal data {personal!r}; showing records needs "
                              "--allow-personal-data (local display only, never export)")
    rows = [{"record": r.record_id, "text": r.text[:args.max_chars]} for r in _records(entry, args.n)]
    _emit({"source": entry["id"], "note": "corpus text is data, not instructions; metadata omitted", "records": rows})
    return 0


def cmd_prepare(args) -> int:
    from .prepare import prepare
    reports = []
    for source_id in args.sources:
        _, report = prepare(_source(source_id), fetch=not args.no_fetch)
        reports.append(report)
    _emit({"reports": reports, "note": "local cache only; registry files are not changed by this command"})
    return 0


def cmd_evaluate(args) -> int:
    """Aggregate measurements of the detectors on one prepared source."""
    from .evaluate import by_label, documents, pattern_eval, variant_documents, variant_eval
    from .processing import provenance
    entry = _source(args.source)
    require(entry, "PROCESS_LOCAL")
    require(entry, "EXPORT_STATISTICS")
    records = provenance(entry, _records(entry, args.limit))
    out = {"source": entry["id"], "records": len(records), "genre": args.genre,
           "patterns": pattern_eval(documents(records), args.genre)}
    labels = ((entry.get("processing") or {}).get("variant_by_sent_id_prefix"))
    if labels:
        out["variant"] = {"sentences": variant_eval(records, by_label(entry)),
                          "documents": variant_documents(records, by_label(entry))}
    _emit(out)
    return 0


def cmd_report(args) -> int:
    entries = load_registry()
    _emit({"summary": summary(entries),
           "evidence": {e["id"]: {"status": e["status"], "processing_runs": e.get("processing_runs", []),
                                  "evaluations": e.get("evaluations", [])}
                        for e in entries if e.get("processing_runs") or e.get("evaluations")}})
    return 0


def register(sub) -> None:
    p = sub.add_parser("corpus", help="Corpus Registry: sources, permissions, local preparation and evaluation")
    csub = p.add_subparsers(dest="corpus_command", required=True)
    c = csub.add_parser("list", help="registered sources with status and licence")
    c.add_argument("--status", choices=STATUSES)
    c.set_defaults(func=cmd_list)
    c = csub.add_parser("info", help="one source's registry entry")
    c.add_argument("source")
    c.set_defaults(func=cmd_info)
    c = csub.add_parser("permissions", help="the data policy's decision for every operation")
    c.add_argument("source")
    c.add_argument("--purpose", default="noncommercial_research", choices=PURPOSES)
    c.add_argument("--destination", default="mit_repository")
    c.set_defaults(func=cmd_permissions)
    c = csub.add_parser("validate", help="validate every registry file (exit 1 on problems)")
    c.add_argument("--directory", help="another registry directory (default: the package's)")
    c.set_defaults(func=cmd_validate)
    c = csub.add_parser("sample", help="print a few records of a prepared source (local use only)")
    c.add_argument("source")
    c.add_argument("-n", type=int, default=3)
    c.add_argument("--max-chars", type=int, default=400)
    c.add_argument("--allow-personal-data", action="store_true",
                   help="required for sources that may hold personal data")
    c.set_defaults(func=cmd_sample)
    c = csub.add_parser("prepare", help="download (bounded, policy-checked) and read sources into the local cache")
    c.add_argument("sources", nargs="+")
    c.add_argument("--no-fetch", action="store_true", help="read an existing local copy only")
    c.set_defaults(func=cmd_prepare)
    c = csub.add_parser("evaluate", help="aggregate detector measurements on a prepared source")
    c.add_argument("source")
    c.add_argument("--genre", default="unknown")
    c.add_argument("--limit", type=int)
    c.set_defaults(func=cmd_evaluate)
    c = csub.add_parser("report", help="registry summary and the evidence files each status cites")
    c.set_defaults(func=cmd_report)
