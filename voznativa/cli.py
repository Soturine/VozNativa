"""``voznativa`` command line.

Exit codes for ``compare`` and ``ground`` (usable as a gate in scripts and CI):
  0  identical, or accepted with a recorded judgment
  1  fail: deterministic violation
  2  review_required: a human must look
  3  no_deterministic_issues: equivalence unverified, a semantic judgment is required
Other commands exit 0 on success and 64 on usage errors.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__

EXIT_BY_STATUS = {"identical": 0, "accepted_by_llm": 0, "accepted_by_human": 0, "fail": 1,
                  "review_required": 2, "no_deterministic_issues": 3}


def _read(path: str) -> str:
    if path == "-":
        # Console code pages (cp1252/cp850 on Windows) would corrupt "não".
        data = sys.stdin.buffer.read() if hasattr(sys.stdin, "buffer") else sys.stdin.read()
        return data.decode("utf-8-sig") if isinstance(data, bytes) else data
    return Path(path).read_text(encoding="utf-8-sig")


def _emit(data, as_text: str | None = None) -> None:
    if as_text is not None:
        sys.stdout.write(as_text if as_text.endswith("\n") else as_text + "\n")
        return
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def cmd_ledger(args):
    from .ledger import build
    _emit(build(_read(args.text)).as_dict())


def cmd_compare(args):
    from .compare import apply_judgment, compare
    from .judge import validate
    report = compare(_read(args.original), _read(args.candidate))
    for path in args.judgment or []:
        report = apply_judgment(report, validate(json.loads(_read(path))))
    _emit(report)
    return EXIT_BY_STATUS.get(report["status"], 2)


def cmd_judge_prompt(args):
    from .compare import compare
    from .judge import prompt
    original, candidate = _read(args.original), _read(args.candidate)
    _emit(None, prompt(original, candidate, compare(original, candidate)))


def cmd_analyze(args):
    from .analyze import analyze
    _emit(analyze(_read(args.text)))


def cmd_audit(args):
    from .audit import audit
    profile = json.loads(_read(args.profile)) if args.profile else None
    _emit(audit(_read(args.text), _read(args.original) if args.original else None, profile))


def cmd_region(args):
    from .region import inspect
    _emit(inspect(_read(args.text), args.region))


def cmd_drift(args):
    from .drift import inspect
    profile = json.loads(_read(args.profile)) if args.profile else None
    _emit(inspect(_read(args.text), profile=profile))


def cmd_eval(args):
    from .evals import run
    report = run(Path(args.cases))
    _emit(report)
    return 0 if report["passed"] == report["cases"] else 1


def cmd_benchmark(args):
    from .benchmark import run
    report = run(Path(args.cases), Path(args.outputs))
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_path:
        Path(args.json_path).write_text(payload + "\n", encoding="utf-8")
    _emit(report)


def _contract_args(p):
    p.add_argument("--task", default="rewrite", choices=["rewrite", "audit", "create", "profile", "compare"])
    p.add_argument("--genre")
    p.add_argument("--channel")
    p.add_argument("--register")
    p.add_argument("--audience")
    p.add_argument("--region")
    p.add_argument("--region-strength", type=float, default=0.0)
    p.add_argument("--community")
    p.add_argument("--slang-strength", type=float, default=0.0)
    p.add_argument("--fact", action="append", help="fact source file (repeatable); never used for voice")
    p.add_argument("--voice-sample", action="append", help="text the author wrote (repeatable); never used for facts")
    p.add_argument("--voice-channel")
    p.add_argument("--repo", help="repository used as a fact source")


def _route(args):
    from .router import route
    return route(_read(args.text), task=args.task, genre=args.genre, channel=args.channel,
                 register=args.register, audience=args.audience, region=args.region,
                 region_strength=args.region_strength, community=args.community,
                 slang_strength=args.slang_strength, fact_sources=args.fact,
                 voice_samples=args.voice_sample, voice_channel=args.voice_channel, repo=args.repo)


def cmd_route(args):
    _emit(_route(args))


def cmd_refs(args):
    from .references import select
    contract = json.loads(_read(args.contract)) if args.contract else _route(args)
    _emit(select(contract, budget_words=args.budget))


def cmd_project(args):
    from .project import scan
    _emit(scan(args.path).summary())


def cmd_ground(args):
    from .project import ground, scan
    report = ground(_read(args.candidate), _read(args.original) if args.original else None,
                    [_read(f) for f in args.fact or []], scan(args.repo) if args.repo else None)
    _emit(report)
    return EXIT_BY_STATUS.get(report["status"], 2)


def cmd_profile(args):
    from .profile import build
    samples = [{"text": _read(path), "channel": args.channel, "date": args.date} for path in args.samples]
    _emit(build(samples))


def cmd_contract(args):
    from .contract import compact, resolve
    from .profile import validate
    context = json.loads(_read(args.context)) if args.context else _route(args)
    profile = json.loads(_read(args.profile)) if args.profile else None
    if profile:
        errors = validate(profile)
        if errors:
            raise ValueError("invalid voice profile: " + "; ".join(errors))
    explicit = json.loads(args.set) if args.set else None
    contract = resolve(context, profile, explicit)
    _emit(compact(contract) if args.compact else contract)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voznativa", description="VozNativa PT-BR voice engine")
    parser.add_argument("--version", action="version", version=f"voznativa {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ledger", help="build the Semantic Ledger of a text")
    p.add_argument("text", help="file path or - for stdin")
    p.set_defaults(func=cmd_ledger)

    p = sub.add_parser("compare", help="compare a candidate against its source (gate)")
    p.add_argument("original")
    p.add_argument("candidate")
    p.add_argument("--judgment", action="append", help="judgment JSON from an LLM or human (repeatable)")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("judge-prompt", help="print the semantic-judge prompt for any LLM or reviewer")
    p.add_argument("original")
    p.add_argument("candidate")
    p.set_defaults(func=cmd_judge_prompt)

    p = sub.add_parser("analyze", help="descriptive text measurements")
    p.add_argument("text")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("audit", help="diagnostics; add --original for semantic risk")
    p.add_argument("text")
    p.add_argument("--original")
    p.add_argument("--profile", help="Voice Profile JSON for drift against the author")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("region", help="regional overfit / dialect mixing baseline")
    p.add_argument("text")
    p.add_argument("--region")
    p.set_defaults(func=cmd_region)

    p = sub.add_parser("drift", help="voice drift across windows or against a profile")
    p.add_argument("text")
    p.add_argument("--profile")
    p.set_defaults(func=cmd_drift)

    p = sub.add_parser("eval", help="run a behavioral eval suite (JSONL)")
    p.add_argument("cases")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("benchmark", help="score frozen benchmark outputs (deterministic tier)")
    p.add_argument("cases")
    p.add_argument("outputs")
    p.add_argument("--json", dest="json_path")
    p.set_defaults(func=cmd_benchmark)

    p = sub.add_parser("route", help="build the Context Contract (genre, register, sources, flags)")
    p.add_argument("text")
    _contract_args(p)
    p.set_defaults(func=cmd_route)

    p = sub.add_parser("refs", help="select references for a contract (progressive disclosure)")
    p.add_argument("text", nargs="?", default="-")
    p.add_argument("--contract", help="existing contract JSON instead of routing the text")
    p.add_argument("--budget", type=int, default=6000, help="word budget for loaded references")
    _contract_args(p)
    p.set_defaults(func=cmd_refs)

    p = sub.add_parser("project", help="index a repository as a fact source")
    p.add_argument("path")
    p.set_defaults(func=cmd_project)

    p = sub.add_parser("ground", help="check that protected values in a text come from fact sources")
    p.add_argument("candidate")
    p.add_argument("--original")
    p.add_argument("--fact", action="append")
    p.add_argument("--repo")
    p.set_defaults(func=cmd_ground)

    p = sub.add_parser("profile", help="build a Voice Profile v2 from authorized samples (no raw text stored)")
    p.add_argument("samples", nargs="+")
    p.add_argument("--channel", help="channel of these samples (whatsapp, github_docs, email...)")
    p.add_argument("--date", help="ISO date of the samples")
    p.set_defaults(func=cmd_profile)

    p = sub.add_parser("contract", help="resolve the Voice Contract (VOICE_STACK precedence)")
    p.add_argument("text", nargs="?", default="-")
    p.add_argument("--context", help="Context Contract JSON instead of routing the text")
    p.add_argument("--profile", help="Voice Profile JSON")
    p.add_argument("--set", help='explicit instruction as JSON, e.g. {"emoji": "none"}')
    p.add_argument("--compact", action="store_true", help="flat feature -> value view for prompts")
    _contract_args(p)
    p.set_defaults(func=cmd_contract)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        sys.stderr.write(f"voznativa: {error}\n")
        return 64
    return code or 0


if __name__ == "__main__":
    raise SystemExit(main())
