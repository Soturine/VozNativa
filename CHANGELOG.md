# Changelog

## Unreleased (0.3.0.dev0)

Work in progress, **not a release**: the independent holdout, a blind human review round and CI are still open (`docs/PLAN_v0.3.0.md`).

### Added
- PT-BR number words (`vinte e três`, `mil e quinhentos reais`, `meia dúzia`, `meia hora`) compared with digits; durations compared in seconds.
- Claims inserted as a new clause inside a sentence (`claim_added`), with a single-clause guard against false reds.
- Reversed causality across adjacent sentences (`X. Por isso, Y.`) and swapped agent/patient between named entities, including active ↔ passive.
- `--protect` / `--protect-file`: user terms that must survive (`span_missing`).
- `voznativa patterns`: genre-aware editorial findings (oficialês, ENEM-ismo, gerundismo, stacked connectives, formulas, support verbs, promotional, empty closings); descriptive, never an authorship score.
- Engine: returns NO_CHANGE without calling the model when there is no finding (`--force` overrides); targets the findings in the prompt; reports patterns before/after, voice distance to the profile and long-text drift.
- Engine: `--judge-votes` (default 2, all must agree) and one retry carrying the judge's reason after a rejection.
- Providers: retries with backoff; provider failures end as `provider_error` (exit 1) instead of a crash.
- Blind pairwise human review: `blind-tasks`, `blind-review` (signed answers), `blind-summary` (counts signed answers only).
- `scripts/llm_integration.py --redact`: stores hashes, lengths and metrics, no texts.
- Evidence: frozen `holdout-v030`, frozen `ptbr-bench-v1` with an official skill-only run, spaCy and NLI experiments (neither adopted), a synthetic-author voice experiment (inconclusive), a metadata-only Corpus Carolina pilot, `examples/` from recorded runs and a local compatibility matrix.

### Fixed
- `120 minutos` was read as 120 million (`mi` matched inside `minutos`).
- `só` was matched as the regional `sô` (accents were folded).
- Idioms read as markers in real runs: `não hesite em`, `conforme alinhado`, `cada vez mais`, `sempre à disposição`.
- `N horas` was taken as a clock time without a preposition.
- Integration and benchmark runners crashed when git was not installed.
- The installed-wheel smoke could not clean its temp dir on Windows.
- `rewrite-prompt` (skill mode) did not include the editorial findings that `rewrite` sends to the model.
- `eval` on a non-semantic file crashed with a `KeyError`; it now exits 64 with a clear message.

## 0.2.0.dev0 - 2026-10-19 (pushed to main; development version, not a release)

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
- Idiomatic `é só` / `só que` / `não só... mas` were read as restrictive quantifiers or negation (found in a real skill-mode rewrite).
- Pre-push qualification audit:
  - collapsing a Markdown list or merging paragraphs returned `identical`, the only auto-accepted status;
  - entity presence and grounding used substrings (`Ana` found in `banana`, `17` supported by `2017`);
  - negation flips in short sentences (`Não vou.` -> `Vou.`) only needed review;
  - a JSON file with `"kind": "human"` accepted a candidate on its own;
  - a non-editable install had no `references/`; `scripts/voznativa.py` could shadow the package;
  - the judge parser rejected a real model answer with a ```json fence and a trailing comma;
  - the Voice Contract -> Emulate style mapping was never applied.

### Added
- `voznativa` Python package and CLI (`ledger`, `compare`, `judge-prompt`, `analyze`, `audit`, `region`, `drift`, `eval`, `benchmark`); legacy `scripts/*.py` are thin wrappers with the same arguments.
- Semantic Ledger: per-sentence protected spans with normalized keys plus negation, modality, quantifier, condition, causality, commitment, attribution, aspect and metadiscourse markers (`voznativa/data/markers_pt_br.json`, evidence E1, uncalibrated).
- Conservative comparison policy: only identity is auto-accepted; deterministic success is `no_deterministic_issues` with `semantic_equivalence: "unverified"`.
- Judge contract for LLM or human verdicts; a judge never overrides a deterministic fail, and self-contradictory `equivalent` verdicts are downgraded.
- Behavioral eval suites: `evals/semantic/cases.jsonl` (dev), `holdout.jsonl`, `holdout2.jsonl`.
- Content-level package validator (frontmatter, version consistency, SKILL links, YAML/JSON/JSONL parsing).
- CI: package install, Windows runner, least-privilege permissions, eval gate.
- Context Router (`route`) with explicit-hint precedence and `unknown` on weak evidence; Reference Selector (`refs`) over `references/index.yml` with a word budget.
- Project/Repository Context (`project`, `ground`): repositories are fact sources; invented paths, subcommands and flags fail; values need an explicit source.
- Voice Profile v2 (`profile`): per-habit evidence, sample support and capped confidence; maturity levels; no raw text or topic words stored.
- Voice Contract resolver (`contract`) implementing VOICE_STACK precedence with a per-feature trace; mandatory genre constraints beat explicit requests; regional and slang strength stay 0 without evidence.
- Rewrite Engine (`rewrite`, `rewrite-prompt`) with command, static and Emulate providers; retries on the dominant failure; returns the original when nothing is safe.
- Benchmark: `ptbr-v1` cases (47-58 words), judgments applied by kind, manifest recording.
- `SKILL.md` rewritten as an operational router; Claude Code plugin manifests; Codex invocation policy; `scripts/voznativa_cli.py` entry point.
- `docs/EVALUATION.md`, `docs/RESEARCH_LOG.md`, `docs/LICENSING.md` (license proposal only; the repository still has no license).
- Relation checks: entity role swaps, attribution swaps, reversed causal direction inside a sentence (connector orientation, causative fazer/levar) and antonym flips (13 polarity pairs); `relations.jsonl` and the frozen `holdout-relations.jsonl` (blind first run 11/12).
- Judgments bound to the sha256 of both texts; `voznativa review` records signed human reviews from an interactive terminal; unsigned human JSON becomes `human_review_claimed`.
- `evals/semantic/MANIFEST.json`: author, frozen hash, first-run result and contamination per suite; `voznativa eval --require-frozen`.
- Wheel bundles `references/` and `assets/`; CI packaging job (sdist -> wheel -> clean venv -> commands outside the checkout) on Linux and Windows; PTY check of the interactive review.
- `scripts/llm_integration.py` and `evals/integration/`: recorded runs of the engine against a real external model.

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
