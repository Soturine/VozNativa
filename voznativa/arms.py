"""Benchmark arms B0-B6 behind one interface (v0.8 CP5; executed with real providers only in CP9).

Each arm turns a source text into an output for the same task, so arms can be
compared on the same cases with the same scoring:

| Arm | What it is | Needs |
|---|---|---|
| B0-original | the source, unchanged (lower bound: "do nothing") | nothing |
| B1-one-line | the provider with a one-line instruction, no VozNativa | provider |
| B2-deterministic | only VozNativa's authorised formal fixes (PROOFREAD), no model | nothing |
| B3-skill-prompt | the provider answering the Agent Skill prompt (``rewrite-prompt``), no gates | provider |
| B4-system | ``engine.rewrite``: router, planner, provider, gates, retries, fallback | provider |
| B5-ablation-no-gates | B3's first answer delivered without any gate (comparison only, never a mode) | provider |
| B6-external-tool | another tool (LanguageTool, a commercial humanizer...) | an authorised tool |

An arm without what it needs is ``NOT_RUN`` with the reason, never a pass.
A provider marked ``synthetic = True`` (a test stub) yields evidence
``SYNTHETIC_FIXTURE``; only a real provider, with authorisation and budget,
yields ``PROVIDER_EXECUTED``, and the provider id is recorded. Outputs are
scored by the same ``compare`` gate and must-preserve check for every arm.
"""
from __future__ import annotations

import hashlib
import time
from collections import Counter

ARMS = {
    "B0-original": {"needs": None, "description": "the source unchanged"},
    "B1-one-line": {"needs": "provider", "description": "one-line instruction to the provider, no VozNativa"},
    "B2-deterministic": {"needs": None, "description": "authorised formal fixes only (PROOFREAD), no model"},
    "B3-skill-prompt": {"needs": "provider", "description": "provider answers the Agent Skill prompt, no gates"},
    "B4-system": {"needs": "provider", "description": "engine.rewrite with router, planner, gates and fallback"},
    "B5-ablation-no-gates": {"needs": "provider", "description": "first answer to the Skill prompt, no gate "
                                                                "(comparison only, never offered as a mode)"},
    "B6-external-tool": {"needs": "external_tool", "description": "another tool, when authorised"},
}
ONE_LINE = ("Reescreva o texto abaixo em português brasileiro natural, mantendo o sentido, os fatos e os valores. "
            "Responda só com o texto reescrito.\n\n")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _evidence(provider) -> str:
    return "SYNTHETIC_FIXTURE" if getattr(provider, "synthetic", False) else "PROVIDER_EXECUTED"


def produce(arm: str, text: str, context: dict, provider=None, external_tool=None) -> dict:
    """The arm's output for ``text``. Never raises for a missing provider or
    tool: the result is NOT_RUN with the reason."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}; known: {sorted(ARMS)}")
    needs = ARMS[arm]["needs"]
    if needs == "provider" and provider is None:
        return {"arm": arm, "status": "NOT_RUN", "evidence": "NOT_RUN",
                "reason": "no provider given (a real one needs the maintainer's authorisation and a budget)"}
    if needs == "external_tool" and external_tool is None:
        return {"arm": arm, "status": "NOT_RUN", "evidence": "NOT_RUN", "reason": "no authorised external tool"}
    started = time.monotonic()
    extra = {}
    if arm == "B0-original":
        output, evidence = text, "ENGINE_EXECUTED"
    elif arm == "B2-deterministic":
        from .diagnose import diagnose, proofread
        output, evidence = proofread(text, diagnose(text, context), "PROOFREAD")["text"], "ENGINE_EXECUTED"
    elif arm == "B1-one-line":
        output, evidence = provider.generate(ONE_LINE + text, 1)[0].strip(), _evidence(provider)
    elif arm in ("B3-skill-prompt", "B5-ablation-no-gates"):
        from .engine import parse_candidate, skill_prompt
        output, _ = parse_candidate(provider.generate(skill_prompt(text, context), 1)[0], text)
        evidence = _evidence(provider)
    elif arm == "B4-system":
        from .engine import rewrite
        result = rewrite(text, context, provider)
        output, evidence = result["text"], _evidence(provider)
        extra = {"outcome": result["outcome"]}
    else:
        output, evidence = external_tool(text), "EXTERNAL_UNVERIFIED"
    return {"arm": arm, "status": "EXECUTED", "evidence": evidence, "output": output,
            "provider": getattr(provider, "id", None) if needs == "provider" else None,
            "seconds": round(time.monotonic() - started, 3), **extra}


def score(case: dict, produced: dict) -> dict:
    """Same scoring for every arm: the ``compare`` gate against the source and
    the must-preserve phrases with their polarity. No text is kept."""
    from .benchmark import invariant_preserved
    from .compare import compare
    row = {"id": case["id"], "arm": produced["arm"], "status": produced["status"], "evidence": produced["evidence"]}
    if produced["status"] != "EXECUTED":
        return dict(row, reason=produced["reason"])
    text, output = case["text"], produced["output"]
    report = compare(text, output)
    must = case.get("must_preserve") or []
    kept = [p for p in must if invariant_preserved(p, text, output)]
    return dict(row, gate=report["status"], changed=output != text, output_sha256=_sha(output),
                must_preserve={"kept": len(kept), "total": len(must)}, seconds=produced["seconds"],
                **({"outcome": produced["outcome"]} if "outcome" in produced else {}),
                **({"provider": produced["provider"]} if produced.get("provider") else {}))


def run(cases: list[dict], arms: list[str], context_of, provider=None, external_tool=None) -> dict:
    """Every arm on every case. ``context_of(case)`` gives the Context Contract.
    Summaries are per arm; a NOT_RUN arm has no rates at all."""
    rows = []
    for arm in arms:
        for case in cases:
            rows.append(score(case, produce(arm, case["text"], context_of(case), provider, external_tool)))
    summary = {}
    from .benchmark import wilson
    for arm in arms:
        mine = [r for r in rows if r["arm"] == arm]
        executed = [r for r in mine if r["status"] == "EXECUTED"]
        if not executed:
            summary[arm] = {"status": "NOT_RUN", "reason": mine[0]["reason"] if mine else "no cases"}
            continue
        gates = Counter(r["gate"] for r in executed)
        kept = sum(r["must_preserve"]["kept"] for r in executed)
        total = sum(r["must_preserve"]["total"] for r in executed)
        unsafe = gates["fail"]
        summary[arm] = {"status": "EXECUTED", "evidence": sorted({r["evidence"] for r in executed}),
                        "cases": len(executed), "changed": sum(r["changed"] for r in executed),
                        "gate": dict(sorted(gates.items())),
                        "unsafe_outputs": {"k": unsafe, "n": len(executed), "wilson95": wilson(unsafe, len(executed))},
                        "must_preserve": {"kept": kept, "total": total, "wilson95": wilson(kept, total)}}
    return {"kind": "voznativa.arms_run", "schema_version": 1, "arms": arms, "summary": summary, "rows": rows,
            "note": "outputs are scored by the deterministic gate only; no gate result proves equivalence, "
                    "and a SYNTHETIC_FIXTURE arm says nothing about a real model"}
