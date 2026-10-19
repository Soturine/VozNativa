# Changelog

## Unreleased (0.2.0.dev0)

### Fixed (false greens found in the v0.1.0 audit; each has a regression test)
- `R$ 1.500,00` was split into `R$ 1` + `00`, so `R$ 1.500,00 -> R$ 1.900,00` passed the guard.
- Written dates (`18 de outubro de 2026`), times (`18h30`), percent with space, thousands separators and semver were fragmented into loose numbers; a date change inside the smoke case passed.
- Added numbers, dates and values were never detected; only omissions were.
- Values swapped between entities (`17 casos e 71 erros` -> `71 casos e 17 erros`) passed.
- Inline code, fenced code, paths, quotes and e-mails were not protected; URLs captured trailing punctuation.
- Benchmark `must_preserve` used substring matching (`pode` matched `não poderia`, `HTTP 409` matched `HTTP 4090`).
- Benchmark pass rate excluded missing outputs, so skipping hard cases raised the score.
- Analyzer counted `quando`, `comando` as gerunds and `semente` as an adverb; ignored `…` and spaced `–`.
- Regional guard compared region codes case-sensitively (`MG` != `mg`).
- CLI stdin was decoded with the console code page on Windows, which erased `não`.

### Added
- `voznativa` Python package and CLI (`ledger`, `compare`, `judge-prompt`, `analyze`, `audit`, `region`, `drift`, `eval`, `benchmark`); legacy `scripts/*.py` are thin wrappers with the same arguments.
- Semantic Ledger: per-sentence protected spans with normalized keys plus negation, modality, quantifier, condition, causality, commitment, attribution, aspect and metadiscourse markers (`voznativa/data/markers_pt_br.json`, evidence E1, uncalibrated).
- Conservative comparison policy: only identity is auto-accepted; deterministic success is `no_deterministic_issues` with `semantic_equivalence: "unverified"`.
- Judge contract for LLM or human verdicts; a judge never overrides a deterministic fail, and self-contradictory `equivalent` verdicts are downgraded.
- Behavioral eval suites: `evals/semantic/cases.jsonl` (dev), `holdout.jsonl`, `holdout2.jsonl`.
- Content-level package validator (frontmatter, version consistency, SKILL links, YAML/JSON/JSONL parsing).
- CI: package install, Windows runner, least-privilege permissions, eval gate.

### Changed
- `mechanicality` is now a set of descriptive rates; ordinary gerunds are no longer penalized.
- Voice Drift uses length-normalized features instead of raw counts.
- Canonical Voice Stack precedence lives only in `references/VOICE_STACK.md`; mandatory genre conventions are constraints, not preferences.

## 0.1.0 - 2026-09-30

Foundation release.

### Added
- concise Agent Skill router;
- Context Router / Semantic Ledger / Voice Stack architecture;
- deterministic text analyzer;
- overlap-safe protected-span Semantic Guard;
- idiolect-oriented Voice Profile baseline;
- Regional Overfit and Dialect Mixing baseline guard;
- PT-BR, regionality and temporal-slang specifications;
- research notes for existing humanizers, ALiB, NURC and Corpus Carolina;
- regression tests and GitHub Actions CI.

### Design decisions
- semantic preservation outranks naturalness;
- author samples outrank generic regional defaults;
- regionality is distribution, not decoration;
- no AI-authorship probability score;
- no promise of detector evasion;
- observed writing features must not be converted into personal-identity inference.
