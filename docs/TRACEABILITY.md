# Requirements Traceability

This document prevents design ideas from disappearing into README prose.

| Requirement | Current artifact | Status |
|---|---|---|
| Minimal skill/router | `SKILL.md` | implemented |
| Context Router | `SKILL.md`, `docs/DESIGN_SPEC.md` | specified |
| Semantic/factual lock | `scripts/semantic_guard.py` | baseline implemented |
| Protected span extraction | `scripts/semantic_guard.py`, wrappers | baseline implemented |
| Deterministic analyzer | `scripts/analyze.py` | baseline implemented |
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
| Voice Drift Guard | `scripts/voice_drift.py` | baseline heuristic |
| Audit mode | `scripts/audit.py` + skill contract | baseline |
| Competitive benchmark protocol | `docs/COMPETITIVE_BENCHMARK.md` | specified |
| Benchmark deterministic runner | `scripts/benchmark_runner.py` | baseline implemented |
| Benchmark frozen smoke cases | `benchmarks/cases/smoke.jsonl` | initial cases |
| Emulate-1 research comparison | `docs/COMPETITIVE_BENCHMARK.md` | documented |
| Optional model/adapter track | `docs/MODEL_ADAPTER_TRACK.md` | specified |
| Provider adapter contract | roadmap v0.7/v0.9 | not implemented |
| Personal LoRA/PEFT adapter | research track | not implemented |
| Rewrite engine | roadmap v0.7 | not implemented |
| Claim-level Semantic Ledger | roadmap v0.2 | not implemented |
| Corpus-calibrated regional packs | roadmap v0.5 | not implemented |
| Human regional evaluation | roadmap v0.5/v0.8 | not implemented |
| Cross-genre eval suites | `evals/` | scaffold + foundation tests |
| OpenAI agent interface | `agents/openai.yaml` | initial metadata |
| Assets/templates | `assets/` | initial templates |
| Detector-evasion promise | prohibited | enforced by design |
| Identity inference | prohibited | enforced by design |

A checked item in `ROADMAP.md` must correspond to a real file, test, or documented invariant. A planned item must not be described as production-ready.
