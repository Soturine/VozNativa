# VozNativa 0.10.0 — Contextual Linguistic Intelligence & Continuous Knowledge

GitHub release only; not published on PyPI. Round records (plan with criteria frozen before development, gaps, evaluation, qualification): [`docs/releases/v0.10/`](.).

**What passing tests mean.** They show the listed defects fixed and the frozen suites not regressed. They do not prove semantic equivalence of any rewrite. Every dataset was written by the same agent that wrote the rules. No human review or independent holdout was run.

## Highlights

- **Open task context.** `--attr NAME=VALUE` takes any attribute, with no code change needed for a new genre ("roteiro de podcast", "ata", "legenda de vídeo"):
  - each attribute records where it came from (explicit, agent-proposed, inferred);
  - unknown, mixed and contradictory contexts are reported, together with the conservative choice made;
  - safety fields can't be set this way;
  - an agent's proposal (`voznativa context --interpret-prompt`) never overrides the user;
  - a standard such as the ENEM essay rubric is only offered, never applied, unless a document profile makes it applicable.
- **Linguistic knowledge with sources.** A registry of short statements, each tied to cited sources marked as prescriptive or descriptive, with licence and access.
  - The writer gets only what the text calls for, within a budget, and each entry says why it was included.
  - In informal or literary text, a legitimate variant is labelled as a variant, not as a rule.
  - Entries that read like instructions to a model are refused.
- **Diagnostic status.** Every finding now says what it means in context: `ERROR_CONFIRMED`, `ACCEPTABLE_VARIANT`, `STYLE_PREFERENCE`, `CONTEXT_DEPENDENT`, `LITERARY_CHOICE` or `UNCERTAIN`.
  - New rules: "daqui há", "seje/esteje", "menas", "a gente + -mos", "pra mim + infinitive", existential "ter".
  - Only confirmed errors are planned as edits.
- **Discourse relations.** `compare` now flags:
  - a concession turned into a cause, a contrast turned into a consequence, or a purpose turned into a cause;
  - a cause invented between two juxtaposed facts;
  - a dropped coordinated action ("revisado e enviado" → "revisado").
  
  A cause kept with a different connective is no longer a failure.
- **Model judges must show independence.** An LLM "equivalent" verdict accepts a candidate only when the judge's relation to the writer can be observed: different model, different provider, or the same vendor (recorded as partial independence). `unknown` no longer accepts. See [MIGRATION.md](MIGRATION.md).
- **Knowledge Watcher** (`voznativa knowledge check | status | proposals`). It checks official sources (PyPI, UD treebanks, Crossref, the Inep ENEM documents page) and turns each change into a proposal for a person.
  - It uses conditional GET and refuses private addresses.
  - It has no apply mode.
  - Scheduling is documented but not active.

## Fixed

- **English text was diagnosed and planned as Portuguese:** "as pytest" was flagged as a plural agreement error, and 42 English words were planned as anglicisms to replace. Found by running VozNativa on Assertiva's README.
- **The v0.9 plural-agreement rule fired on edited real text** (pronoun subjects, clitics, adverbs, split hyphens). In the UD Portuguese-GSD test split, 10 of its 11 confirmed errors were false. The fix was measured on the dev split, run once: 16 flags before, 11 after (6 of them real).
- **Four false alarms from the v0.9 model arms:**
  - a scheduled present ("vai ser no sábado" → "é no sábado");
  - backticks added around a word the source already had;
  - "a tarde inteira" → "a tarde toda";
  - a subjunctive vs. an infinitive auxiliary in a concessive clause.

  Each now has a control that stays flagged.
- **Changes that passed with no signal:** future → past through "foi", and "a tarde inteira" → "parte da tarde".
- **Two courtesy formulas were missing from the pattern library:** "venho por meio deste" and "é com grande satisfação que…".
- **The mutation harness could run stale bytecode for same-length mutants.** It now clears caches. v0.9's published 20/20 was re-checked and holds.
- **Two import cycles removed** (one introduced in this round, one inherited).

## Evidence

All numbers compare v0.9.0 with 0.10.0.

| Instrument | v0.9.0 | 0.10.0 |
|---|---|---|
| v0.10 semantic set, holdout (run once, both versions together) | 10/12 risks, 5/10 false alarms | **12/12, 0/10** |
| v0.10 diagnosis set, holdout | 1/5, 0/5 | **5/5, 0/5** |
| v0.10 context set, holdout | n/a | **4/4** |
| `ptbr-bench-v4` / `ptbr-bench-v5` / predicates | 22/22 / 36/36 / 19/20 and 1/18 | unchanged |
| Frozen regression (v0.8) and v0.9 sets | 88/89 and 1/33; 31/31 and 4/20 | unchanged |
| Real-model arms (Haiku, 10 texts frozen before the run): edits to texts that needed none | engine 0/4 | engine 0/4; the direct LLM edited 3/4 and dropped an exception clause |
| Open context and knowledge, ablation | — | **no measurable gain** (n = 1 per arm) |
| Targeted mutation of the new safeguards | — | 24/25 killed; the survivor is an equivalent mutant |
| `compare` CPU time at 17,600 words (interleaved in one session) | 6.25 s | 6.34 s |

## Reciprocal dogfood

VozNativa, Assertiva 1.0.1 and Derivanta Engine 0.1.0 were run on each other, with real executions.

- **Assertiva on VozNativa** (`audit --execute`): the native suite passed (1,402 invocations on v0.9.0; 1,495 on the candidate).
- **Derivanta on VozNativa**: before and after on the same path, comparable.
- **Defects fixed in their own repositories:**
  - Derivanta reported inherited test classes as unreferenced, and leaked the inspected code's `SyntaxWarning` to its stderr: [PR #6](https://github.com/Soturine/Derivanta-Engine/pull/6). Merge is left to the maintainer.
  - Assertiva attributed a missing build backend in the environment to the project's packaging: [PR #11](https://github.com/Soturine/Assertiva/pull/11).
  - VozNativa read English as Portuguese: fixed in this release.

## Integrations

| Integration | State |
|---|---|
| `claude -p` as writer (model arms) | REAL_EXECUTED |
| Chat-completions HTTP adapter | TESTED_WITH_STUB (no local model run) |
| Local model (llama.cpp, Ollama, LM Studio) | BLOCKED / NOT_RUN: executing the server was denied in v0.9 and not retried; Ollama and LM Studio not installed |
| Codex, Gemini CLI | NOT_RUN (not installed) |
| Emulate | BLOCKED (no key) |
| Knowledge Watcher sources | REAL_EXECUTED (6 sources; OpenAlex disabled: key and usage billing) |

## Migration

- **Judge relation:** `unknown` no longer accepts. Declare the judge model (`--model` in the judge command, or `--judge-api-model`).
- **Diagnosis schema 2:** adds `status` and `recommend_edit`.
- **Contract:** gains `task_context` only when attributes are given.
- **`rewrite` results:** gain `knowledge`.
- **`--provider-env inherit`:** now warns when it passes credential-like variables to the model process. The default is meant to become `minimal` in 0.11.

## Known limitations

- Coreference and role swaps across clauses are not detected.
- Relations are read only from explicit connectives.
- The knowledge statements were written for the project, and their sources weren't verified page by page.
- No human or independent evaluation was run.
- DOCX output was never rendered in Word.
- PDF extraction has no per-word boxes.

## Install

```bash
git clone https://github.com/Soturine/VozNativa.git && cd VozNativa
python -m pip install -e .          # optional: ".[pdf]"
voznativa doctor
voznativa context texto.txt --attr "genre=roteiro de podcast" --attr tone=leve
voznativa knowledge status
```

If `pip install -e .` fails with `Cannot import 'setuptools.build_meta'`, unset `PIP_NO_BUILD_ISOLATION`.
