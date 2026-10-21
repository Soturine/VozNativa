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
                  "review_required": 2, "human_review_claimed": 2, "no_deterministic_issues": 3}


def cmd_review(args):
    """Interactive human review; refuses to run without a terminal."""
    from .compare import apply_judgment, compare
    from .review import interactive_review, key_path
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise ValueError("voznativa review needs an interactive terminal: a person must answer it. "
                         "Agents and scripts cannot record a human review.")
    original, candidate = _read(args.original), _read(args.candidate)
    report = compare(original, candidate)
    judgment = interactive_review(original, candidate, report, args.reviewer)
    Path(args.out).write_text(json.dumps(judgment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    from .judge import validate
    final = apply_judgment(report, validate(judgment, original, candidate))
    sys.stdout.write(f"saved {args.out} (signed with {key_path()}); status: {final['status']}\n")
    return EXIT_BY_STATUS.get(final["status"], 2)


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


def _protected(args) -> list[str]:
    """--protect TERM (repeatable) and --protect-file (one term per line, # comments)."""
    terms = list(getattr(args, "protect", None) or [])
    if getattr(args, "protect_file", None):
        terms += [line.strip() for line in _read(args.protect_file).splitlines()
                  if line.strip() and not line.strip().startswith("#")]
    return terms


def _protect_args(p):
    p.add_argument("--protect", action="append", help="term that must survive verbatim (repeatable)")
    p.add_argument("--protect-file", help="file with one protected term per line")


def cmd_ledger(args):
    from .ledger import build
    _emit(build(_read(args.text), _protected(args)).as_dict())


def cmd_compare(args):
    from .compare import apply_judgment, compare
    from .judge import validate
    original, candidate = _read(args.original), _read(args.candidate)
    report = compare(original, candidate, _protected(args))
    for path in args.judgment or []:
        report = apply_judgment(report, validate(json.loads(_read(path)), original, candidate))
    _emit(report)
    return EXIT_BY_STATUS.get(report["status"], 2)


def cmd_judge_prompt(args):
    from .compare import compare
    from .judge import grounding_prompt, prompt
    original, candidate = _read(args.original), _read(args.candidate)
    if args.fact or args.repo:
        # Create mode: the first argument is the request; the judge checks the
        # candidate against every authorized source, not only the request.
        from .engine import authorized_sources
        from .project import ground, scan
        facts, project = [_read(f) for f in args.fact or []], scan(args.repo) if args.repo else None
        _emit(None, grounding_prompt(authorized_sources(original, facts, project), candidate,
                                     ground(candidate, None, facts + [original], project)))
        return
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
    report = run(Path(args.cases), require_frozen=args.require_frozen)
    _emit(report)
    return 0 if report["passed"] == report["cases"] else 1


def cmd_benchmark(args):
    from .benchmark import run
    report = run(Path(args.cases), Path(args.outputs), Path(args.manifest) if args.manifest else None)
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
    from .compare import apply_judgment
    from .project import ground, scan
    candidate = _read(args.candidate)
    original = _read(args.original) if args.original else None
    request = _read(args.request) if args.request else ""
    facts, project = [_read(f) for f in args.fact or []], scan(args.repo) if args.repo else None
    report = ground(candidate, original, facts + ([request] if request.strip() else []), project)
    if args.judgment:
        from .engine import authorized_sources
        from .judge import validate_grounding
        sources = authorized_sources(request, facts, project, original=original)
        for path in args.judgment:
            report = apply_judgment(report, validate_grounding(json.loads(_read(path)), sources, candidate))
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


def _voice_inputs(args):
    from .profile import validate
    profile = json.loads(_read(args.profile)) if args.profile else None
    if profile and validate(profile):
        raise ValueError("invalid voice profile: " + "; ".join(validate(profile)))
    explicit = json.loads(args.set) if args.set else None
    return profile, explicit


def cmd_rewrite_prompt(args):
    from .contract import resolve
    from .engine import build_prompt
    from .references import select
    context = _route(args)
    profile, explicit = _voice_inputs(args)
    from .patterns import detect
    facts = [_read(f) for f in args.fact or []]
    text = _read(args.text)
    # Same targeting as `rewrite`, so the skill mode (agent as model) gets the findings too.
    findings = detect(text, context["genre"]["value"]) if context["task"] != "create" else None
    prompt = build_prompt(text, context, resolve(context, profile, explicit),
                          select(context, budget_words=args.budget), facts=facts,
                          inline_references=args.inline_refs, protect=_protected(args), findings=findings)
    _emit(None, prompt)


def _provider(spec: str | None, candidates_files: list[str] | None, timeout: float):
    from .providers import CommandProvider, EmulateProvider, StaticProvider
    if candidates_files:
        return StaticProvider([_read(f) for f in candidates_files])
    if not spec:
        raise ValueError("--cmd, --emulate or --candidate is required")
    if spec == "emulate":
        import os
        key = os.environ.get("EMULATE_API_KEY")
        if not key:
            raise ValueError("set EMULATE_API_KEY to use the Emulate provider")
        return EmulateProvider(key)
    return CommandProvider.from_string(spec, timeout)


def cmd_rewrite(args):
    from .engine import rewrite
    from .project import scan
    context = _route(args)
    profile, explicit = _voice_inputs(args)
    provider = _provider("emulate" if args.emulate else args.cmd, args.candidate, args.timeout)
    judge = _provider(args.judge_cmd, None, args.timeout) if args.judge_cmd else None
    result = rewrite(_read(args.text), context, provider, profile, explicit, attempts=args.attempts,
                     candidates=args.candidates, judge_provider=judge,
                     facts=[_read(f) for f in args.fact or []], project=scan(args.repo) if args.repo else None,
                     budget_words=args.budget, protect=_protected(args), force=args.force,
                     judge_votes=args.judge_votes)
    if args.text_only:
        _emit(None, result["text"])
    else:
        _emit(result)
    return {"accepted": 0, "no_change": 0, "needs_judgment": 3, "needs_review": 2, "returned_original": 1,
            "provider_error": 1}[
        result["outcome"]]



def cmd_patterns(args):
    from .patterns import detect
    from .router import infer_genre
    text = _read(args.text)
    genre = args.genre or infer_genre(text)["value"]
    _emit(detect(text, genre))



def cmd_blind_tasks(args):
    from .blind import build_tasks
    tasks = build_tasks(json.loads(_read(args.run)), focus=args.focus, seed=args.seed)
    Path(args.out).write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.stdout.write(f"{len(tasks['tasks'])} blind tasks written to {args.out}\n")


def cmd_blind_review(args):
    from .blind import review
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise ValueError("blind-review needs an interactive terminal: a person must answer it")
    answers = review(json.loads(_read(args.tasks)), args.reviewer, limit=args.limit)
    with open(args.out, "a", encoding="utf-8") as handle:
        for answer in answers:
            handle.write(json.dumps(answer, ensure_ascii=False) + "\n")
    sys.stdout.write(f"{len(answers)} signed answers appended to {args.out}\n")


def cmd_blind_summary(args):
    from .blind import load_jsonl, summarize
    _emit(summarize(json.loads(_read(args.tasks)), load_jsonl(Path(args.answers))))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voznativa", description="VozNativa PT-BR voice engine")
    parser.add_argument("--version", action="version", version=f"voznativa {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ledger", help="build the Semantic Ledger of a text")
    p.add_argument("text", help="file path or - for stdin")
    _protect_args(p)
    p.set_defaults(func=cmd_ledger)

    p = sub.add_parser("compare", help="compare a candidate against its source (gate)")
    p.add_argument("original")
    p.add_argument("candidate")
    p.add_argument("--judgment", action="append", help="judgment JSON from an LLM or human (repeatable)")
    _protect_args(p)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("review", help="record a signed human review (interactive terminal only)")
    p.add_argument("original")
    p.add_argument("candidate")
    p.add_argument("--reviewer", required=True, help="who is reviewing (name or id)")
    p.add_argument("--out", required=True, help="where to save the signed judgment JSON")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("blind-tasks", help="build blind pairwise review tasks from a benchmark run")
    p.add_argument("run", help="benchmark run JSON (benchmarks/runs/...)")
    p.add_argument("--out", required=True)
    p.add_argument("--focus", help="only pairs that include this arm")
    p.add_argument("--seed", type=int, default=0)
    p.set_defaults(func=cmd_blind_tasks)

    p = sub.add_parser("blind-review", help="answer blind tasks (interactive terminal only; signed)")
    p.add_argument("tasks")
    p.add_argument("--reviewer", required=True)
    p.add_argument("--out", required=True, help="JSONL file to append signed answers to")
    p.add_argument("--limit", type=int)
    p.set_defaults(func=cmd_blind_review)

    p = sub.add_parser("blind-summary", help="wins per arm from verified human answers")
    p.add_argument("tasks")
    p.add_argument("answers")
    p.set_defaults(func=cmd_blind_summary)

    p = sub.add_parser("judge-prompt", help="print the semantic-judge prompt for any LLM or reviewer")
    p.add_argument("original", help="the original text, or the request when --fact/--repo is given")
    p.add_argument("candidate")
    p.add_argument("--fact", action="append", help="fact source (repeatable): judge grounding instead of equivalence")
    p.add_argument("--repo", help="repository used as a fact source (grounding mode)")
    p.set_defaults(func=cmd_judge_prompt)

    p = sub.add_parser("patterns", help="editorial pattern findings (genre-aware; not an authorship score)")
    p.add_argument("text")
    p.add_argument("--genre", help="genre for exemptions (default: inferred)")
    p.set_defaults(func=cmd_patterns)

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
    p.add_argument("--require-frozen", action="store_true",
                   help="refuse to run unless MANIFEST.json lists the suite as frozen with a matching sha256")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("benchmark", help="score frozen benchmark outputs (deterministic tier)")
    p.add_argument("cases")
    p.add_argument("outputs")
    p.add_argument("--json", dest="json_path")
    p.add_argument("--manifest", help="JSON with system versions, models and run settings")
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
    p.add_argument("--request", help="the request the text was written for; a source only for facts it states")
    p.add_argument("--judgment", action="append", help="grounding judgment JSON (from judge-prompt --fact)")
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

    for name, helptext in (("rewrite-prompt", "print the rewrite prompt for the current agent to answer"),
                           ("rewrite", "run the generate -> validate -> retry loop with a provider")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("text", help="text to rewrite (or the request, with --task create)")
        p.add_argument("--profile")
        p.add_argument("--set", help="explicit voice instruction as JSON")
        p.add_argument("--budget", type=int, default=6000)
        _contract_args(p)
        _protect_args(p)
        if name == "rewrite-prompt":
            p.add_argument("--inline-refs", action="store_true", help="embed reference text instead of paths")
            p.set_defaults(func=cmd_rewrite_prompt)
        else:
            p.add_argument("--cmd", help='model command reading the prompt on stdin, e.g. "claude -p"')
            p.add_argument("--emulate", action="store_true", help="system baseline via EMULATE_API_KEY")
            p.add_argument("--candidate", action="append", help="pre-written candidate file (offline)")
            p.add_argument("--judge-cmd", help="command used as semantic judge")
            p.add_argument("--attempts", type=int, default=3)
            p.add_argument("--candidates", type=int, default=1)
            p.add_argument("--timeout", type=float, default=300.0)
            p.add_argument("--text-only", action="store_true")
            p.add_argument("--judge-votes", type=int, default=2,
                           help="independent judge calls that must all say equivalent (default 2)")
            p.add_argument("--force", action="store_true",
                           help="call the model even when the text has no editorial findings")
            p.set_defaults(func=cmd_rewrite)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = args.func(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        sys.stderr.write(f"voznativa: {error}\n")
        return 64
    return code or 0


if __name__ == "__main__":
    raise SystemExit(main())
