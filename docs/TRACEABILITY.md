# Requirements Traceability

This document prevents design ideas from disappearing into README prose. Status words: **implemented** (code + tests), **partial** (code with a documented gap), **specified** (documentation only), **not implemented**.

| Requirement | Current artifact | Status |
|---|---|---|
| Minimal skill/router | `SKILL.md`, `evals/test_skill_contract.py` | implemented: commands, flags and exit codes tested against the CLI |
| Context Router | `voznativa/router.py`, `voznativa route` | implemented: explicit hints first; weighted cues (E0) return `unknown` on weak evidence |
| Reference Selector / progressive disclosure | `references/index.yml`, `voznativa/references.py`, `voznativa refs` | implemented: word budget, skipped items reported |
| Project/Repository Context | `voznativa/project.py`, `voznativa project`, `voznativa ground` | implemented: files, identifiers, CLI subcommands/flags, documented commands, versions; facts only, never voice |
| Semantic/factual lock | `voznativa/compare.py`, `voznativa/ledger.py`, `voznativa compare` | implemented, deterministic and conservative; best outcome is `unverified` without a judgment |
| Protected span extraction | `voznativa/spans.py` (legacy wrappers in `scripts/`) | implemented: normalized keys for PT-BR money, dates, times, quantities, versions, identifiers, code, paths, quotes, entities |
| Claim-level Semantic Ledger | `voznativa/judge.py` (contract) | partial: deterministic markers + judge contract; no automatic claim extraction or NLI model |
| Semantic judge (LLM/human) | `voznativa judge-prompt`, `compare --judgment` | implemented contract; no bundled model; judgments recorded as evidence |
| Deterministic analyzer | `voznativa/analyze.py` | implemented (descriptive only; word lists E1, uncalibrated) |
| Register model | `references/registers.md`, `voznativa/data/voice_defaults.yml` | partial: register defaults per genre feed the Voice Contract; register mismatch detection not implemented |
| PT-BR pattern library | `references/patterns/` | specified: guidance for the rewriting model; no automatic pattern detector beyond connectors, metadiscourse and gerundism counts |
| Voice Profile | `voznativa/profile.py`, `voznativa profile`, `references/voice/schema.yml` | implemented: schema v2, per-habit evidence and confidence, maturity levels, no raw text or topic words |
| Voice Contract | `voznativa/contract.py`, `voznativa contract` | implemented: VOICE_STACK precedence with per-feature trace; constraints beat explicit requests |
| Idiolect documentation | `references/voice/idiolect.md` | specified |
| Regional model | `references/regions/` | specified; not calibrated (effective strength 0) |
| Community packs | `references/communities/` | draft scaffolds; terms are preserved, never inserted |
| Temporal slang | `references/slang/` | schema only; lexicon not calibrated (effective strength 0) |
| Corpus/evidence methodology | `docs/CORPUS_AND_EVIDENCE_STRATEGY.md`, `references/corpora/` | implemented documentation; no corpus ingested |
| Regional Overfit Guard | `voznativa/region.py` | baseline heuristic (E0 fixture markers); used as a review signal in the engine |
| Dialect Mixing Guard | `voznativa/region.py` | baseline heuristic |
| Voice Drift Guard | `voznativa/drift.py`, `voznativa/features.py` | implemented: length-normalized, against a profile or between windows; thresholds uncalibrated; review signal only |
| False Positive Guard | `references/patterns/false-positives.md`, NO_CHANGE path in the engine, `false_red` eval cases | partial: NO_CHANGE and false-red evals exist; no automatic "this edit was unnecessary" detector |
| Audit mode | `voznativa/audit.py` | partial: descriptive rates; semantic risk when the original is given; formulaicity/register still null |
| Rewrite engine | `voznativa/engine.py`, `voznativa rewrite`, `voznativa rewrite-prompt` | implemented: generate, validate, retry with feedback, return original; not run against a real external model in this repository |
| Provider adapter contract | `voznativa/providers.py` | implemented: command, static, Emulate (mapped from public docs, not validated live) |
| Competitive benchmark protocol | `docs/COMPETITIVE_BENCHMARK.md` | specified; no real run published |
| Benchmark deterministic runner | `voznativa/benchmark.py`, `voznativa benchmark` | implemented: tier 0, judgments by kind, manifest, missing outputs count as failures |
| Benchmark frozen cases | `benchmarks/cases/smoke.jsonl`, `benchmarks/cases/ptbr-v1.jsonl` | 2 + 8 synthetic cases; ptbr-v1 meets Emulate's 40-word minimum |
| Emulate-1 research comparison | `docs/COMPETITIVE_BENCHMARK.md`, `docs/RESEARCH_LOG.md` | documented |
| Optional model/adapter track | `docs/MODEL_ADAPTER_TRACK.md` | specified |
| Personal LoRA/PEFT adapter | research track | not implemented |
| Corpus-calibrated regional packs | roadmap v0.5 | not implemented |
| Human regional evaluation | roadmap v0.5/v0.8 | not implemented |
| Cross-genre eval suites | `evals/semantic/*.jsonl`, `evals/router/cases.jsonl`, `evals/test_*.py` | semantic: 50 dev + 24 + 16 holdout cases (author-written, synthetic); genre README folders are still scaffolds |
| Package/CLI | `pyproject.toml`, `voznativa/cli.py`, `scripts/voznativa.py` | implemented |
| Agent packaging | `.claude-plugin/`, `agents/openai.yaml`, README install table | implemented; validated by `scripts/validate_package.py` |
| Licensing | `docs/LICENSING.md` | proposal only; repository has no license |
| Detector-evasion promise | prohibited | enforced by design (no detector in any gate) |
| Identity inference | prohibited | enforced by `profile.validate` and the Voice Contract `do_not` list |

A checked item in `ROADMAP.md` must correspond to a real file, test, or documented invariant. A planned item must not be described as production-ready.
