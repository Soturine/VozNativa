**Pre-release. Not a stable release and not published on PyPI.** Install it from this release's wheel or from the tagged source. `0.8.0.dev0` is a development version: interfaces may still change before 1.0.

## What VozNativa is

A PT-BR rewrite engine and Agent Skill. It plans what a text needs, asks a model (or the host agent) for a rewrite, and checks the candidate with a deterministic semantic gate (`voznativa compare`) before anything is accepted.

## Highlights

**Evaluation System**
- `voznativa evaluate`: datasets read the existing suites in place, each with an explicit split that must agree with its MANIFEST; metrics per split and axis with denominators and Wilson intervals; nothing NOT_RUN is counted.
- `--verify` checks a record's internal consistency; `--replay` re-executes it with the code and inputs of its revision (`git archive`) and reports REPRODUCED, DIFFERENT or NOT_REPLAYABLE.
- An independent split needs `independence_evidence` (author, custodian, freezing commit, attestation); leakage between sources is detected, and a holdout sharing text with development makes the run INVALID.

**Contextual semantics**
- Minimal event frames in `compare`: dropped or changed recipient, giver/receiver swapped, an event turned into its converse (all `major`, never `critical`), including singular passives.
- New antonym classes for `polarity_flipped` (hire/fire, export/import, switch on/off, deferir/indeferir).
- Long documents: no false red when appending to a 17k-word document; `compare` on 30k words 24.7 s → 8.5 s with identical output; `spans.extract` no longer quadratic.

**Standards foundation**
- `voznativa standards list | resolve`: a registry of editais, manuals and exam guides with a verification ladder (CATALOGUED → SOURCE_CITED → VERIFIED) and an Applicability Resolver that picks the edition valid on the submission date (never "the latest").
- `voznativa rubric`: objective criteria only where the source applies and is at least SOURCE_CITED; subjective criteria marked NEEDS_JUDGMENT; no scores.

**Agent-led runtime and DX**
- A host agent judging its own candidate is recorded as an `agent_assessment` (AGENT_OBSERVED), never as an independent `accepted_by_llm`.
- The Skill's default flow runs `diagnose` before deciding NO_CHANGE.
- `voznativa doctor` and `voznativa demo` work offline with no model or key; input errors say what to do; user guides in `docs/guide/` with a CLI reference generated from the parser.

**Assurance and dogfood**
- Dogfood with Assertiva fixed 11 tests that passed while the code produced nothing; mutation testing found and fixed a missed singular passive.
- Dogfood with the Derivanta Engine aligned declared vocabularies with emitted values and completed the v0.8 traceability matrix.
- The local package gate runs the whole test suite against the installed wheel.

## Qualification

- Local: Linux CPython 3.11, 3.12 and 3.13 (containers) and Windows CPython 3.12, full local gate set; details in `docs/releases/v0.8/RELEASE_QUALIFICATION.md`.
- CI: one manual run on the tagged commit, [run #126](https://github.com/Soturine/VozNativa/actions/runs/42453909963) (`workflow_dispatch`), 8/8 jobs: Ubuntu and Windows × Python 3.11/3.12/3.13, plus the package job (sdist → wheel → clean venv → installed smoke) on both; verified live by `scripts/ci_evidence.py`.
- The tag points to `554d1b2`, the commit that run qualified; `main` continues with evidence-only commits.

## Known limitations

- **Semantic quality is not independently validated.** No independent holdout, no blind human review and no real-provider runs were executed for this version; every measured set was written by the development side. Agent self-assessments are labelled as such.
- A different event with no lexical relation (e.g. "assinou" → "recebeu") is only informational; the irregular participle "entregue" gets no event frame.
- The Enem 2026 guide is cited from its official page without a verified file hash; no academic standards source is verified.
- `compare` is still slower than linear on very long documents.

## Assets

- `voznativa-0.8.0.dev0-py3-none-any.whl` and `voznativa-0.8.0.dev0.tar.gz`, built from the tagged commit.
- `SHA256SUMS.txt` with the SHA-256 of both.

Full changelog: `CHANGELOG.md`; gaps and their states: `docs/releases/v0.8/GAP_REGISTER.md`.
