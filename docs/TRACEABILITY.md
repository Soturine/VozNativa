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
| Claim-level Semantic Ledger | `voznativa/judge.py` (contract), `voznativa/compare.py` (clause novelty) | partial: deterministic markers, clause-level additions and the judge contract; no automatic claim extraction; NLI tested and rejected (`evals/experiments/nli_probe.json`) |
| Relation checks | `voznativa/compare.py` (binding, role triples, causal direction, polarity, attribution) | partial: entity role swaps, agent/patient swaps between named entities including active/passive, attribution swaps, reversed causal direction within a sentence and across adjacent sentences, antonym flips (13 pairs). Not detected: pronouns and common nouns as agents, antonyms outside the lexicon, lower-case sources |
| PT-BR number words | `voznativa/numerals.py`, `voznativa/spans.py` | implemented: compound numerals, `meia dúzia`/`meia hora`, durations in seconds; `um/uma` ambiguous |
| User-protected terms | `compare/ledger/rewrite/rewrite-prompt --protect`, `--protect-file` | implemented |
| Semantic judge (LLM/human) | `voznativa judge-prompt`, `compare --judgment`, `voznativa/review.py` | implemented: judgments bound to the sha256 of both texts; model judges are always kind=llm; human verdicts accept only when signed by `voznativa review` (interactive terminal, per-user key); unsigned human JSON is `human_review_claimed`. The signature proves the key holder approved, not who they are |
| Deterministic analyzer | `voznativa/analyze.py` | implemented (descriptive only; word lists E1, uncalibrated) |
| Register model | `references/registers.md`, `voznativa/data/voice_defaults.yml` | partial: register defaults per genre feed the Voice Contract; register mismatch detection not implemented |
| PT-BR pattern library | `references/patterns/`, `voznativa/patterns.py`, `voznativa/data/patterns_pt_br.yml`, `voznativa patterns` | implemented: genre-aware detector with exemptions, `edit` / `no_change_candidate` decision used by the engine and by `rewrite-prompt`; descriptive, not an authorship score; cases written by the developer |
| Voice Profile | `voznativa/profile.py`, `voznativa profile`, `references/voice/schema.yml` | implemented: schema v2, per-habit evidence and confidence, maturity levels, no raw text or topic words |
| Voice Contract | `voznativa/contract.py`, `voznativa contract` | implemented: VOICE_STACK precedence with per-feature trace; constraints beat explicit requests |
| Idiolect documentation | `references/voice/idiolect.md` | specified |
| Regional model | `references/regions/` | specified; not calibrated (effective strength 0) |
| Community packs | `references/communities/` | draft scaffolds; terms are preserved, never inserted |
| Temporal slang | `references/slang/` | schema only; lexicon not calibrated (effective strength 0) |
| Corpus/evidence methodology | `docs/CORPUS_AND_EVIDENCE_STRATEGY.md`, `references/corpora/`, `scripts/carolina_metadata.py` | metadata-only Carolina pilot (`evals/corpus/carolina-pilot.json`); no text ingested |
| Regional Overfit Guard | `voznativa/region.py` | baseline heuristic (E0 fixture markers); used as a review signal in the engine |
| Dialect Mixing Guard | `voznativa/region.py` | baseline heuristic |
| Voice Drift Guard | `voznativa/drift.py`, `voznativa/features.py` | implemented: length-normalized, against a profile or between windows; the engine reports voice distance and long-text drift; thresholds uncalibrated; review signal only |
| False Positive Guard | `references/patterns/false-positives.md`, NO_CHANGE path in the engine, `false_red` eval cases | partial: the engine skips the model when the detector finds nothing (7/8 natural texts in a real run); no detector for an unnecessary edit after the fact |
| Audit mode | `voznativa/audit.py` | partial: descriptive rates; semantic risk when the original is given; formulaicity/register still null |
| Rewrite engine | `voznativa/engine.py`, `voznativa rewrite`, `voznativa rewrite-prompt` | implemented: findings-targeted prompt, NO_CHANGE without a model call, validate, retry with gate or judge feedback, agreeing judge votes, provider retries, `provider_error`, return original; run with claude-sonnet-5-5 (`evals/integration/`, `benchmarks/runs/`) |
| Blind human review | `voznativa/blind.py`, `voznativa blind-tasks/blind-review/blind-summary` | instrument implemented and tested; no human results yet |
| Privacy of recorded runs | `scripts/llm_integration.py --redact` | implemented: hashes, lengths and metrics only |
| Real-model integration | `scripts/llm_integration.py`, `evals/integration/*.json` | recorded runs against claude-sonnet-5-5 through the Claude Code CLI (no tools, empty working directory); not part of CI, not deterministic, not human review |
| Compatibility | CI matrix (blocked by GitHub billing); `evals/compat/v0.3.0-dev-e679038.json` | verified locally: Linux 3.11/3.12/3.13 (containers, suite + wheel smoke), Windows 3.12 (suite + wheel smoke) and 3.11/3.13 (embeddable, suite) |
| Provider adapter contract | `voznativa/providers.py` | implemented: command, static, Emulate (mapped from public docs, not validated live) |
| Competitive benchmark protocol | `docs/COMPETITIVE_BENCHMARK.md`, `scripts/bench_skill_only.py`, `benchmarks/manifests/ptbr-bench-v1.json` | skill-only run published (`benchmarks/runs/`); system-level (Emulate) not run |
| Benchmark deterministic runner | `voznativa/benchmark.py`, `voznativa benchmark` | implemented: tier 0, judgments by kind, manifest, missing outputs count as failures |
| Benchmark frozen cases | `benchmarks/cases/smoke.jsonl`, `ptbr-v1.jsonl`, `ptbr-ai-drafts-v1.jsonl`, `ptbr-bench-v1.jsonl` | 2 + 8 + 6 + 12 synthetic cases; ptbr-bench-v1 frozen before its first run |
| Emulate-1 research comparison | `docs/COMPETITIVE_BENCHMARK.md`, `docs/RESEARCH_LOG.md` | documented |
| Optional model/adapter track | `docs/MODEL_ADAPTER_TRACK.md` | specified |
| Personal LoRA/PEFT adapter | research track | not implemented |
| Corpus-calibrated regional packs | roadmap v0.5 | not implemented |
| Human regional evaluation | roadmap v0.5/v0.8 | not implemented |
| Cross-genre eval suites | `evals/semantic/*.jsonl`, `evals/semantic/MANIFEST.json`, `evals/router/cases.jsonl` | dev: 59 + 32 (relations); developer holdouts: 24 + 16 + 12 + 24 (v0.3.0), frozen with first-run results. None is independent validation (all written by the engine's developer); genre README folders are still scaffolds |
| Package/CLI | `pyproject.toml`, `setup.py`, `MANIFEST.in`, `voznativa/cli.py`, `scripts/voznativa_cli.py` | implemented: the wheel bundles references/ and assets/; verified sdist -> wheel -> clean venv outside the checkout (Linux container, CI job on Linux and Windows) |
| Agent packaging | `.claude-plugin/`, `agents/openai.yaml`, README install table | implemented; validated by `scripts/validate_package.py` |
| Licensing | `docs/LICENSING.md` | proposal only; repository has no license |
| Detector-evasion promise | prohibited | enforced by design (no detector in any gate) |
| Identity inference | prohibited | enforced by `profile.validate` and the Voice Contract `do_not` list |

A checked item in `ROADMAP.md` must correspond to a real file, test, or documented invariant. A planned item must not be described as production-ready.
