# Changelog

## Unreleased (0.8.0.dev0)

Work in progress on `dev/v0.8.0`, **not a release**. Plan: `docs/v08/PLAN.md`; state: `docs/v08/EXECUTION_STATE.md`; gaps: `docs/v08/GAP_REGISTER.md`.

### Fixed
- **Document plans could authorise themselves to rewrite verse (V08-GAP-01).** `validate_plan` read `verse_explicit` from the serialised plan, so a plan edited to say `true` (with its policy and unit actions edited to match) passed validation and let `reassemble` replace a poem. The authorisation now comes from the caller: `validate_plan(plan, text, verse_explicit=False)` and `reassemble(text, plan, replacements, verse_explicit=False)`; the plan's field must agree with the caller and grants nothing by itself. A non-boolean grant raises `TypeError`. **API change:** code that reassembles a plan built with `verse_explicit=True` must now pass `verse_explicit=True` to `reassemble`/`validate_plan`. `rewrite_document` and the CLI already pass the caller's flag.
- **`rewrite_document(resume=...)` trusted earlier records (V08-GAP-09).** A forged record with `outcome: accepted` made the whole document `accepted` with no provider call and no judge; a forged candidate could change a unit's block structure; a record without `action` crashed with `KeyError`. Now only the candidate text is reused: the record is rebuilt from the plan, the candidate must keep the unit's structure and pass the unit gates again, and the outcome is the more cautious of the gates and the earlier claim, so a judge's verdict is not inherited.

### Standards (CP10-CP11)
- `voznativa standards list | resolve` and `voznativa/standards.py`: a registry of editais, manuals, norms and exam guides (one YAML per source, strict validation, verification ladder CATALOGUED -> SOURCE_CITED -> VERIFIED) and an Applicability Resolver that picks the edition valid on the document's submission date, never the latest by default; two valid editions of one series are CONFLICTED for a person.
- Optional `document_profile` in the Context Contract (`route --document-profile`); without it the contract is unchanged.
- `voznativa rubric` (`voznativa/rubric.py`): objective criteria checked only where the source applies and the criterion is at least SOURCE_CITED; subjective criteria listed as NEEDS_JUDGMENT; no score, total or invented weight.
- Enem pilot with real sources: the 2026 essay guide is SOURCE_CITED from the official gov.br page (the PDF could not be downloaded from this machine, so no hash and no criterion read from the file); the 2025 guide is only CATALOGUED. The academic pilot is NOT_RUN (no institutional source verified). `docs/v08/DOCUMENT_STANDARDS.md`.

### Agent Skill (CP9)
- Agent-led pilot: this development session acted as the Skill's host agent on three authored texts, following `SKILL.md` as written (18 CLI runs, AGENT_OBSERVED; no API or paid service). It exercised NO_CHANGE, an edit, a rejected candidate corrected as the Skill instructs, and self-assessments recorded without acceptance. `evals/v08/agent-pilot/PILOT.md`.
- Fixed (V08-GAP-17, found by the pilot): the default flow decided NO_CHANGE from `patterns` alone, so a repeated word and a weekday/date contradiction (seen only by `diagnose`) went unreported. Step 1 now runs `diagnose` too: a formal `auto_fix` error is edited alone (`--mode PROOFREAD`), contradictions and ambiguities go to the user as suggestions.

### Fixed (V08-GAP-16)
- A host agent judging its own candidate was recorded as `accepted_by_llm`, like an independent model. Judgments now carry `generator_relation` (`same_agent`, `different_model`, `unknown`); `same_agent` + equivalent is kept as `agent_assessment` (AGENT_OBSERVED) and accepts nothing, the report requiring an independent judgment; a self-rejection still fails. The engine sets the relation itself (`same_agent` when the judge is the generator object or command line, otherwise `unknown`). `SKILL.md` tells the agent to declare it.

### Evaluation (CP8)
- `voznativa/axes.py`: per-candidate quality axes (editorial formulas, unnecessary change against the plan, slang and epoch terms, regional forms, genre drift, voice distance) built from the engine's detectors and labelled as deterministic proxies; `not_applicable` instead of a pass when there is nothing to measure. Not a quality score.
- Router audit reproduced on a fresh machine with the same result as v0.7 (precision 93.8%, useful coverage 8.8%, wrong 0.58% over 7,424 windows). A threshold curve (`scripts/experiments/v08_router_curve.py`, replaying the router's own rule) shows the current thresholds at the knee; low coverage comes from missing cues for news and blogs, not from thresholds. No threshold changed. `docs/v08/EVAL_MATRIX.md`.

### Performance (V08-GAP-12)
- `compare` on long documents: sentence alignment uses an inverted index and a shortcut for identical stem sets; entity-name lookups use a word index confirmed by the same regex, falling back to the full scan for characters with irregular case-insensitive matching. Output identical (0 of 309 suite reports changed; reference scans kept and tested). Well-formed 30k-word document 24.7 s -> 8.5 s. Residual: each protected value is still searched in the whole text.
- `rewrite_document`: the document time limit now covers the global validation, where each revert re-runs `compare`; out of time, the original is returned.

### Fixed (V08-GAP-13)
- False red on long documents: appending one sentence to a 17k-word document gave `fail` (`negation_moved`, `modality_moved`). Cause: sentence alignment broke ties by taking the first candidate, and two sentences that differ only by "não" have the same content stems, so in a document quoting both the negated one aligned to the positive one. Ties now go to the nearest position; a higher similarity still always wins. 0 of 309 suite reports changed; well-formed documents are clean up to 30k words; negation and modality guards still fail on real changes, including inside the twins. Side effect: swapping two such twins, silent before (a false green), now fails. Preferring an identical surface text was tried and rejected (an unchanged copy elsewhere hid a negation removed from the other). `evals/test_v08_alignment.py`.

### Semantics (V08-GAP-04)
- `compare` reads minimal event frames (`voznativa/events.py`): `recipient_dropped` / `recipient_changed` (a transfer verb's recipient is gone or another), `agent_recipient_swapped` (giver and receiver exchanged), `event_converted` (the verb became its converse with the same subject; with the roles swapped it is the same event and nothing is flagged). All major, never critical; frames abstain on time, purpose, fixed phrases and the object's article. Verb classes: `voznativa/data/verb_relations.json` (authored, E0).
- New antonym classes for the existing critical `polarity_flipped`: hire/fire, export/import, switch on/off, and finite forms of deferir/indeferir; explicit forms where a prefix would catch other words (contrato, importante).
- Measured on sets frozen before the code (same author, not independent): development 7/15 -> 14/15 risks flagged with false alarms unchanged at 2/13; prospective holdout, run once, 5/12 -> 11/12 with false alarms unchanged at 3/12; predicate sample 16/20 -> 17/20. Frozen suites and benchmarks unchanged. Still invisible: a different event with no lexical relation (assinou -> recebeu). `docs/v08/SEMANTICS.md`.

### Performance
- `spans.extract` is no longer quadratic (V08-GAP-02): 40k words 18.6 s -> 1.6 s, 80k 30.1 s -> 3.0 s on the same machine; `build_plan` on 40k words 9.1 s -> 0.73 s. Output is byte-identical on 3,036 texts and on the 40k/80k digests. `compare` is still quadratic on long documents (V08-GAP-12, open). Measurements: `docs/v08/PERFORMANCE.md`.
- `morph.analyse_word` is memoised (each call still returns new dicts).

### Fixed (determinism)
- The order of `morph.analyse_word` results depended on `PYTHONHASHSEED`; ties between endings of equal length are now ordered. Contents and every `compare` report are unchanged.

### Added
- `voznativa doctor`: installation check (Python, PyYAML, references, package data, temp dir, whether known provider variables are set, never their values); no network, reads no text; exit 1 only when something will not work.
- `voznativa evaluate` (Evaluation Core, `voznativa/evaluation.py`): a dataset spec reads the existing suites in place through adapters, each source with an explicit split that must agree with its MANIFEST (a developer-written suite cannot be an independent holdout; a changed frozen file makes the run INVALID). Axes `semantic_risk`, `status_agreement` and `decision` are reported separately and per split, with denominators and Wilson intervals; the run record keeps revision, versions, input hashes, per-case results without the texts and a results digest; `--verify` detects an edited record. Arms that need a model or people are listed as NOT_RUN. Protocol: `docs/v08/EVAL_PROTOCOL.md`.
- `voznativa evaluate --replay RUN`: re-executes a recorded run with the code and inputs of its revision (`git archive`, inputs checked by hash) and compares the digest: REPRODUCED, DIFFERENT or NOT_REPLAYABLE. `--verify` now states that it checks internal consistency only: `results_sha256` is not a signature, and a forger who recomputes it passes `--verify` but not `--replay` (tested).
- Independent splits need `independence_evidence` (author, custodian, the freezing commit holding the file with the MANIFEST hash, an attestation file); a bare `independent: true` makes the run INVALID. Paths that resolve outside the repository through a link or junction are refused.
- Leakage between sources (exact after folding, or word-trigram Jaccard >= 0.8) is reported per run; a text shared with a holdout makes the run INVALID. Repository audit (`scripts/experiments/v08_leakage_audit.py`): developer holdout case `ho-022` is a copy of development case `rel-agent-001`; one `ptbr-bench-v5` case repeats a development text committed before the benchmark was frozen, so 1 of its 36 "out of distribution" cases is not (the README says so). Frozen files unchanged.
- Benchmark arms B0-B6 behind one interface (`voznativa/arms.py`): B0 and B2 run offline; arms that need a provider are NOT_RUN without one; a test stub yields `SYNTHETIC_FIXTURE`. `engine.skill_prompt` is the prompt `rewrite-prompt` prints (moved out of the CLI, output byte-identical), so arm B3 sends exactly what the Agent Skill gives the host agent.
- `voznativa demo`: the quickstart offline on bundled texts (identical to `examples/quickstart/`, kept so by a test); no model, no key, no file written; `--json` for the structured result.

### Changed
- Expected input errors now say what to do, in Portuguese, with the same exit code 64: file not found (with the working directory), not UTF-8 (with the byte position), a directory instead of a file. `rewrite` without a provider points to `voznativa demo`.

### Assurance
- The package gate (`qualify` `package:sdist-wheel-smoke`, also the CI package job) now runs the **whole unittest suite against the installed wheel** (V08-GAP-06): the tracked tree without `voznativa/` and the packaging files, so fixtures exist but the code can only come from the wheel; the import origin is checked first. Local run: 748 tests, 746 PASS, 2 skips with stated reasons. `test_regional` reads its pack through the imported package; the `bench_v3` end-to-end test skips when the engine is not this checkout's (its own guard).

### Known
- False red on long documents (V08-GAP-13): appending one sentence to a 16.5k-word document gives `fail` (`modality_moved`, `negation_moved`). Open, scheduled with the `compare` work.

## Unreleased (0.7.0.dev1)

Stabilization of 0.7.0.dev0, **not a release and not qualified externally**. Plan and findings: `docs/PLAN_v0.7.0.dev1.md`; state: `docs/V07_EXECUTION_STATE.md` (section v0.7.0.dev1).

### Fixed
- `compare` false green: an action or commitment replaced by a light verb ("será enviado" -> "vai até") kept values and negation and passed as `no_deterministic_issues`. New `predicate_missing` (major, review) and `predicate_replaced` (info) from rule-based verb anchors; experimental, measured only on a non-independent sample (`evals/predicates/`).
- `tense_changed` read periphrastic and synthetic future ("vai depositar" / "depositará") as different tenses.
- Slang lexicon validation: attestation `count`/`words` must be integers >= 0, years integers with `from <= to`, `last_verified_at` an ISO date, `schema_version` an int. A string count used to crash with `TypeError`.
- README: the first-use example lost the action and was presented as the good candidate; the claim that the gates "prove" preservation is gone. The quickstart now shows a kept action, a removed negation and a lost action.
- Document plans (`document.validate_plan` / `reassemble`): a serialised plan whose unit `action` was flipped from `protect` to `rewrite` (or whose `kinds`, `blocks` or core offsets were edited, even with recomputed hashes) let `reassemble` replace a code block, table, separator or quotation. Protection is now derived again from the text and the policy; unit indices, block coverage, kinds and core offsets must match; replacements for unknown units or non-text replacements are refused. `rewrite_document` builds its own plan, so this affected the public plan API, not the CLI flow.
- A whitespace-only document crashed `build_plan`/`rewrite_document` with `AssertionError`; it is now returned unchanged (`no_change`).

### Assurance
- CI evidence (`scripts/ci_evidence.py`): after a green run, only non-executable records (`.json`, `.jsonl`, `.md`, `.txt`) under `evals/assurance/runs/` keep code equivalence; a harness `.py`, `conftest.py` or `pyproject.toml` there now invalidates it. The diff runs with `--no-renames`, so code moved into an evidence folder still shows the path it left. A qualifying run must be `workflow_dispatch` and carry exactly the jobs the workflow declares, matched by name (a duplicate can no longer hide a missing combination).
- Boundary oracles for `document.py` (segment cut, back-off, forced cut, core trimming, field-by-field refusal); replay of the 52 sampled survivors of CP5 round D.
- Mutation round C of `compare.py` complete (rows 76 and 429-583, 271 of 271: 201 killed, 70 survived; no mutant killed in CP5 survives now). Oracles for the sentence-level checks (`evals/test_compare_signal_oracles.py`): where a moved marker left and landed, the alignment threshold, and the abstentions of the tense and predicate checks; 44 of the 70 survivors killed by that file alone, 22 argued equivalent, 4 in backlog B-M2.
- Mutation triage of `temporal.py`: 5 of the 12 `==` -> `is` survivors called CPython-equivalent were test gaps (YAML, regex and CLI values are equal but not identical); now killed. Errata in the v0.7 `MUTATION.md`.
- Validator refuses a Markdown table row split across lines (two register rows were corrupted by a heredoc).

## Unreleased (0.7.0.dev0)

Development version, **not a release and not qualified externally** (no PyPI, no tag). Round state: `docs/V07_EXECUTION_STATE.md`; qualification: `docs/V07_RELEASE_QUALIFICATION.md`.

### Fixed (known gaps of 0.6)
- **G1** router: hard-wrapped literature with `--` dialogue was routed as WhatsApp. Inference runs on an unwrapped copy, `--` dialogue is a literary cue, chat needs two cue families; `unknown` with literary or historical evidence keeps the literary limits (`router.py`, `evals/test_router_v3.py`, 14 frozen oracles).
- **G2** dedup: a chapter inside its novel did not cluster. Directional containment over an inverted shingle index (`processing.containment_links`, `evals/test_containment.py`); 52 contained pairs crossed the earlier calibration/evaluation split.
- **G3** slang: "de boa" followed by a word was missed. Sense per occurrence by the class of the next word; old senses in pre-reform text and ambiguous forms without informal evidence are not counted (`temporal.observe`, `evals/test_slang_v07.py`).
- **G4** engine: no segmented rewrite. `engine.rewrite_document` and `rewrite --long-form` (`evals/test_document_rewrite.py`).
- `compare` false greens: a negation moved between sentences, a dependent paragraph moved, a short added sentence, a dropped negation in a rephrased sentence (`evals/test_global_guards.py`).
- CRLF text routed as `unknown` and seen as one paragraph; `--cmd` with a quoted Windows path failed; pre-reform Brazilian spelling read as PT-PT; "propina" alone read as PT-PT.

### Added
- Context Contract v3 (14 dimensions with value, source, confidence; `protections`).
- Document contract (`voznativa/document.py`): lossless units, protected blocks, inventory, carry, dependencies, limits.
- Verb morphology with abstention (`voznativa/morph.py`) and the `tense_changed` review signal; ADR-0002.
- Original-error awareness and editorial modes (`voznativa/diagnose.py`, `voznativa diagnose`, `rewrite --mode`).
- Character integrity audit and provenance record (`voznativa/integrity.py`, `voznativa integrity`, `provenance` in every rewrite result).
- Corpus: safe TEI/XML reader, per-document licences, `text_rights: unclear`, CC 3.0 licences, CoNLL-U documents; four UD treebanks integrated (GSD, PetroGold, PUD, DANTEStocks): 3 -> 7 sources in evaluation; cross-genre evaluator.
- `ptbr-bench-v5` (out-of-distribution conformance, frozen before its first run).
- External detector benchmark tooling (`evals/external_detection/`): adapters and the H0/H1/A0/A1 protocol; live runs NOT_RUN.
- Assurance: `scripts/checkpoint.py` (exit codes kept, push verified on the remote), `scripts/ci_evidence.py` (CI evidence verified live by SHA), gate `ci:workflow-triggers`.
- README rewritten as product and engineering entry point, checked by `evals/test_readme.py`; `examples/quickstart/`.

### Not done
- Model arms of the benchmarks, human reviews, independent holdout, live detector runs: NOT_RUN.
- Pronoun/coreference, agreement and government checks, narrative model: backlog (`docs/V07_LINGUISTICS.md`).
- Standards/rubrics line: vision and ADR only (`docs/V08_STANDARDS_VISION.md`).

## 0.6.0.dev0

Development version, **not a release and not qualified**. Inventory and gaps: `docs/AS_IS_v0.6.0.md`. Original VozNativa material is now MIT (`LICENSE`, `docs/LICENSING.md`). CI runs only by manual dispatch.

### Added
- **Corpus platform** (`voznativa/corpus/`):
  - **Registry** of 33 sources. Each status is a claim backed by a recorded verification: CATALOGUED, SOURCE_VERIFIED, ACCESS_VERIFIED, CONNECTOR_READY, LOCALLY_VALIDATED, EVALUATION_INTEGRATED.
  - **Data policy** that decides each of 12 operations from the identified licence, personal data and documented permissions, and fails closed.
  - **Bounded connectors:** host allowlist, Range prefixes, sha256, a cache outside the repo, and a decompression-bomb and path guard.
  - **Provenance:** a hash of the original and of the normalized text, MinHash near-duplicates and splits that never cut a group or a duplicate cluster, plus a leakage check.
  - **CLI:** `voznativa corpus list|info|permissions|validate|sample|prepare|evaluate|report`. Exit 77 when the policy refuses.
- **Sources read end to end:**
  - UD Portuguese-Bosque;
  - an 8 MB prefix of B2W-Reviews01;
  - a 6 MB prefix of a CC0 Machado de Assis corpus.

  All three are EVALUATION_INTEGRATED. Only aggregate counts are committed.
- **Calibration against human text** (`evals/corpus/CALIBRATION_v0.6.md`):
  - PT-PT markers: 0 false positives in 4,207 Brazilian sentences; recall 12% per sentence and 41–44% per document;
  - edit rate on published human text: 0.2–0.3%;
  - `dc-029` stays INCONCLUSIVE, and no threshold was changed.
- **Temporal slang** (`voznativa/temporal.py`, lexicon v2, `scripts/slang_attest.py`):
  - 30 entries, attested in dated corpora;
  - 4 reach E2 (2018 reviews), and none is attested after 2018;
  - epoch parsing and epoch notes;
  - generation is off;
  - an agent sense check, not a human one, is in `evals/corpus/SLANG_SENSE_CHECK.md`.
- **Community packs v2** (`voznativa/community.py`): a taxonomy and behaviours; 4 draft packs that preserve terms and never add them.
- **Shared stuffing guard** (`voznativa/stuffing.py`), reused by the regional guard.
- **Integration with explicit precedence:**
  - router `--epoch`;
  - Voice Contract temporal and community decisions;
  - planner sections and prompt lines;
  - engine review codes `slang_introduced`, `slang_stuffing`, `author_slang_removed` and `community_term_introduced`;
  - profile habits `slang.*`;
  - community context withdraws anglicism findings on preserved terms.
- **Long texts** (`voznativa/longform.py`):
  - a dependency map and lossless segmentation that reports every forced cut;
  - a literary policy: no rewrite of verse without an explicit request, and local edits only for literary prose.

  Evaluation on Machado de Assis is in `evals/corpus/LONGFORM_v0.6.md`. The engine does not yet rewrite by segments.
- **`ptbr-bench-v4`:** 22 cases frozen before any run. The deterministic arm scores 21/22. The model arms are NOT_RUN, and `ptbr-bench-v3` is unchanged and NOT_RUN.
- **Known gaps as expected-failure tests** (`evals/test_known_gaps_v06.py`):
  - router misreads wrapped literary dialogue;
  - chapter-in-novel containment is not detected;
  - the "de boa" recall limit.

### Fixed (each with a test)
- **Windows provider timeout:** orphaned grandchildren survived. A Job Object is now created before the process starts, which fixes the flaky CI #122.
- **CI evidence** is bound to the exact SHA, and is NOT_RUN on a dirty tree or without a green run of HEAD.
- **Literary text:**
  - Pre-1943 Brazilian spelling and characters' forms of address made 55% (Gutenberg) and 16% (Wikisource) of Machado's literary segments plan an edit.
  - In the literary genre, the PT-PT variant is now a note that never decides or gets acted on, and mixed forms of address are not a finding.
  - The note-only part was found by `ptbr-bench-v4`, in case `bv4-lt-03`.
- **Installed packages refused the corpus registry,** because evidence files exist only in the repository. This broke the installed smoke from `9f65145` to `43c2df8`, and the package gate was not run at those checkpoints.
- **`corpus_verify --only` overwrote the full verification record** of the same day. It was restored from git. No corpus run can replace another run's file now.
- **Long-text classifier:**
  - the case-insensitive heading regex;
  - paragraph openings that were always empty;
  - hard-wrapped prose read as verse;
  - "--" dialogue that was missed.
- `corpus info <unknown>` raised KeyError; it is now exit 64.

### Assurance (CP12)
- **Derivanta Engine** 0.1.0@17fa564: 98 INFO findings, all complexity or duplication candidates. One was acted on: the evidence ladder now has one owner.
- **Cosmic Ray** at `f5f2d30`, before the CP12 tests:
  - `stuffing.py`: 32 of 72 mutants survived;
  - `temporal.py`: 264 of 701 survived, most of them equivalent annotation mutants.

  Targeted tests were added; before/after numbers are in `evals/assurance/runs/2026-11-05-v06-cp12/`.

## 0.5.0.dev0 (development; continued as 0.6.0.dev0, never released)

Development version, **not a release and not qualified**. Plan and status: `docs/PLAN_v0.5.0.md`. Builds on the hardened v0.4.0 (`v0.4.0-dev` at `8a530f8`). The external criteria inherited from v0.3.0 (independent holdout, blind human review, CI) are still open.

### Fixed (v0.4.0 hardening; each has a regression test)
- Usage errors (unknown flag, missing argument) exited 2, the same code `compare` uses for `review_required`; every command now exits 64 (found by the new qualification runner).
- A frozen holdout could be edited with the test green if the manifest's `frozen` key was renamed (false green confirmed with a negative control after an Assertiva lead); the set of frozen suites is now pinned and the decision and benchmark cases are hash-checked too.
- Benchmark scoring counted a `provider_error` (original returned) as preserved invariants; rows are now classified on separate axes and the official `ptbr-bench-v2` run is rescored without being changed (v0.4.0: 14/14 invariants where an output exists and 1 system failure, not 15/15).
- Semantic Ledger: a bare weekday in a temporal slot ("começo segunda") was not a span (false red in `bv2-li-02` and a false green "segunda" → "terça"); "2 da tarde" did not equal "14h"; multiplier verbs ("triplicar a receita") were not values (`ho-007` now passes strictly; the frozen case is unchanged); role and order swaps between common nouns ("o cliente processou a empresa" reversed), also when the rewrite drops a formula, now need review (`role_or_order_swapped`).
- Decomposed accents (NFD) split "não" into "na" + "o" and changed 20 of 216 suite verdicts, some into false greens; a no-break space hid "fim do mês". Analysis runs on a canonical copy (NFC, plain spaces, no zero-width); the user's text is returned as given.
- An article contraction in a marker's first slot made "na função de gerente" causal and "pela conta de luz" a cause.
- The HMAC review key was written readable by other users and chmod-ed afterwards; it is created 0600 in one call.
- The installed-wheel smoke hid its real error behind a Windows `PermissionError`.
- The reviewer registry's relationship values were never validated; dead code and a duplicated command list removed.

### Performance
- `signals.markers` tries a phrase only where its first token occurs: `compare` on 8,000 words 10.4 s → 0.96 s; the comma-flood input 9.7 s → 0.10 s (identical markers, differential test).
- Plan adherence prunes sentence matching by difflib upper bounds: a model-free rewrite of 2,000 words 48.6 s → 1.1 s (same values). Ledger caching measured and rejected.

### Added
- `scripts/qualify.py`: single local qualification runner; each gate in its own process with its exit code; PASS / FAIL / BLOCKED / NOT_RUN / SKIPPED / INCONCLUSIVE / WAIVED_BY_OWNER; reproduces the CI package job; known failures and external evidence declared in `evals/qualification/`.
- Regional Evidence Packs (`voznativa/regional.py`, `voznativa/data/regional_packs/`, `docs/REGIONAL_EVIDENCE.md`, ADR-0001): versioned, validated contract; abstention by default; the author's observed form wins; pilot `br-norte-lex-mandioca` from published ALiB findings (counts and citations only). Wired into the Voice Contract, Voice Profile (`regional_form.*` counts), planner, `compare` (`regional_referent_changed`), engine (`regional_form_introduced`) and `voznativa regional packs|check`.
- Benchmark outcome axes (`voznativa.benchmark.outcome_axes`) with Wilson intervals; `ptbr-bench-v3` cases and manifest frozen (NOT_RUN) and its runner, with a fake-model harness test.
- Metamorphic tests of the gate (`evals/test_metamorphic.py`); H4 ledger probe; three targeted mutation runs recorded.
- Assurance records under `evals/assurance/` (Derivanta Engine and Assertiva runs, negative controls, dogfood ledger) and `scripts/assurance_record.py` (sanitized outputs with hashes).
- `examples/v0.5.0-demo.md` (`scripts/demo_v05.py`, no model): plan, review, returned original, planted instruction, regional abstention and option, provider outage.

## 0.4.0.dev0 (development; continued as 0.5.0.dev0, never released)

Development version, **not a release and not qualified**. Plan and status: `docs/PLAN_v0.4.0.md`. The v0.3.0 external criteria (independent holdout, blind human review round, CI) are still open and are not closed by anything below.

### Fixed (v0.3.0 audit gaps; each has a regression test)
- Eval reports mixed a missed detection with a different issue code: `ho-007` (frozen) is caught as `possible_addition` but asks for `span_added`. The strict count stays 23/24; reports now add `status_passed` and `failure_kind` (`false_green`, `false_red`, `severity_divergence`, `classification_divergence`). The case is unchanged.
- Create mode judged the output against the user's request only. The writer and a new grounding judge get the same labeled sources (fact files, repository docs, the request); a `supported` claim must quote evidence found in them. Values stated in the request count as sourced; `[DADO NECESSÁRIO]` gaps need review. `judge-prompt --fact/--repo` and `ground --request/--judgment` for skill mode.
- NO_CHANGE ignored an explicit change of destination: an e-mail asked for as WhatsApp came back untouched, and a model NO_CHANGE was accepted even then. Requested targets (genre or channel confidently different, register, audience, voice, region/community) now reach the prompt; a model NO_CHANGE on a changed destination is retried once and then sent to review; results name the NO_CHANGE kind.
- `blind-summary` counted repeated answers, ignored `original_sha256`, accepted any signed value as a choice and could not tell participants apart; the arm mapping was unsigned, so relabeling arms flipped results. Answers carry `task_sha256`; one answer per (task, key); disagreeing repeats are excluded; participants are listed by key.
- Review signatures were reported as one "verified". `review.assess` now separates integrity, key possession, declared identity and independence. An HMAC review is never independent (any process of the OS user can sign); reviewers can sign with their own SSH key (`--ssh-key`, `ssh-keygen -Y`), verified against `evals/reviewers/`.
- `--redact` stored the model command with its credentials, errors that quoted the texts, the cases path and an unkeyed sha256 of each text. Credentials are masked in every stored field (with or without `--redact`); free text is scrubbed; hashes are HMAC with a key not stored (`--redact-key` to compare runs).
- Providers: timeout now stops the process tree; output is capped; an empty answer is an error; a missing executable is not retried; Emulate network/HTTP/JSON errors become `provider_error` instead of a crash; agent CLIs started without their tool/sandbox switch get a warning; `--provider-env minimal`. The docs state that the empty working directory is not a sandbox.
- Prompts: a text containing `TEXTO>>>` could close its block and append instructions; blocks now close with a tag that carries a hash of the content. Candidates that add protocol tokens (`<final>`, a verdict, a binding) fail.
- `reunião segue quinta às 10h` lost the weekday span (false red on chat-style rewrites).
- `voznativa rewrite` raised `TypeError` on every call since v0.3.0 (`explicit` passed positionally); recorded runs had called the engine from Python, so nothing exercised the command. Found by the v0.4.0 benchmark.
- A model command printing in the Windows console code page reached the engine with accents replaced by U+FFFD.
- A judge timeout made the engine discard a candidate that had passed every gate (`provider_error`); it now ends as `needs_judgment`.
- A genre label close to the text's own (documentation on a technical README) was read as a destination change.

### Added
- Pattern Library v2 (`voznativa/data/patterns_pt_br.yml`): 27 patterns decided by genre, channel, position (opening/closing), function guards (durative gerund with a time anchor, list after a colon, attributed claims, domain senses) and frequency; 11 new families (ENEM formula, redundant connectives, gerund of consequence, misplaced officialese, closing formulas, formulaic triads, anaphora runs, repeated evaluation, pleonasm, corporate jargon, construction and collocation calques). Every pattern has rationale, legitimate uses, sources and positive + false-positive cases; a test enforces it. The weak findings needed for an edit grow with text length.
- PT-BR contextual layer (`voznativa/ptbr.py`): PT-PT forms with false friends marked meaning-sensitive, foreign terms by domain, forms of address, chat/speech forms against the target register; rewrite checks for introduced PT-PT, changed form of address and translated domain terms.
- Contextual Rewrite Planner (`voznativa/planner.py`, `voznativa plan`): per-sentence operation, reason, priority, what to preserve, dependencies, consistency and source warnings (weekday vs date); drives NO_CHANGE, the prompt and candidate ranking; results report unplanned edits and introduced findings.
- Evaluation: frozen `holdout-v040` (32 cases), frozen engine decision suite (`evals/decision/`, 30 cases), frozen `ptbr-bench-v2` with the v0.3.0 engine as an arm (`scripts/bench_v2.py`, `scripts/bench_model_wrapper.py`, `scripts/bench_engine_driver.py`), latency probe (`scripts/perf_probe.py`), LanguageTool experiment (not adopted).
- Reviewer registry for SSH-signed reviews (`evals/reviewers/`), empty.

## 0.3.0.dev0 (development; **not concluded**)

Not a release: the independent holdout, a blind human review round and CI are still open (`docs/PLAN_v0.3.0.md`).

### Added
- PT-BR number words (`vinte e três`, `mil e quinhentos reais`, `meia dúzia`, `meia hora`) compared with digits; durations compared in seconds.
- Claims inserted as a new clause inside a sentence (reported as `possible_addition`; an earlier version of this entry called it `claim_added`, a code that never existed), with a single-clause guard against false reds.
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
