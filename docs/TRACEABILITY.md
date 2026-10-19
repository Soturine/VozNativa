# Requirements Traceability

This document prevents design ideas from disappearing into README prose.

| Requirement | Current artifact | Status |
|---|---|---|
| Minimal skill/router | `SKILL.md` | implemented |
| Context Router | `SKILL.md`, `docs/DESIGN_SPEC.md` | specified |
| Semantic/factual lock | `voznativa/compare.py`, `voznativa/ledger.py`, `voznativa compare` | implemented, deterministic and conservative; best outcome is `unverified` without a judgment |
| Protected span extraction | `voznativa/spans.py` (legacy wrappers in `scripts/`) | implemented: normalized keys for PT-BR money, dates, times, quantities, versions, identifiers, code, paths, quotes, entities |
| Deterministic analyzer | `voznativa/analyze.py` | implemented (descriptive only; word lists E1, uncalibrated) |
| Register model | `references/registers.md` | specified |
| PT-BR pattern library | `references/patterns/` | initial library |
| Voice Profile | `scripts/voice_profile.py`, `references/voice/` | baseline implemented |
| Idiolect documentation | `references/voice/idiolect.md` | specified |
| Regional model | `references/regions/` | specified; not calibrated |
| Community packs | `references/communities/` | draft scaffolds |
| Temporal slang | `references/slang/` | schema only; lexicon not calibrated |
| Corpus/evidence methodology | `docs/CORPUS_AND_EVIDENCE_STRATEGY.md`, `references/corpora/` | implemented documentation |
| Regional Overfit Guard | `scripts/region_consistency.py` | baseline heuristic |
| Dialect Mixing Guard | `scripts/region_consistency.py` | baseline heuristic |
| Voice Drift Guard | `voznativa/drift.py`, `voznativa/features.py` | length-normalized; thresholds uncalibrated; review signal only |
| Audit mode | `voznativa/audit.py` | descriptive rates; semantic risk when the original is given; formulaicity/register still null |
| Competitive benchmark protocol | `docs/COMPETITIVE_BENCHMARK.md` | specified |
| Benchmark deterministic runner | `voznativa/benchmark.py` | tier 0 implemented; missing outputs count as failures; invariants are word-boundary and polarity aware |
| Benchmark frozen smoke cases | `benchmarks/cases/smoke.jsonl` | initial cases |
| Emulate-1 research comparison | `docs/COMPETITIVE_BENCHMARK.md` | documented |
| Optional model/adapter track | `docs/MODEL_ADAPTER_TRACK.md` | specified |
| Provider adapter contract | roadmap v0.7/v0.9 | not implemented |
| Personal LoRA/PEFT adapter | research track | not implemented |
| Rewrite engine | roadmap v0.7 | not implemented |
| Claim-level Semantic Ledger | `voznativa/judge.py` (contract) | partial: deterministic markers + judge contract; no automatic claim extraction or NLI model |
| Corpus-calibrated regional packs | roadmap v0.5 | not implemented |
| Human regional evaluation | roadmap v0.5/v0.8 | not implemented |
| Cross-genre eval suites | `evals/semantic/*.jsonl`, `evals/test_*.py` | semantic: 48 dev + 24 + 16 holdout cases (author-written, synthetic); genre READMEs still scaffolds |
| OpenAI agent interface | `agents/openai.yaml` | initial metadata |
| Assets/templates | `assets/` | initial templates |
| Semantic judge (LLM/human) | `voznativa judge-prompt`, `compare --judgment` | contract implemented; no bundled model; judgments recorded as evidence |
| Package/CLI | `pyproject.toml`, `voznativa/cli.py` | implemented |
| Detector-evasion promise | prohibited | enforced by design |
| Identity inference | prohibited | enforced by design |

A checked item in `ROADMAP.md` must correspond to a real file, test, or documented invariant. A planned item must not be described as production-ready.
