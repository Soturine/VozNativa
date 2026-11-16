# VozNativa 0.8.1

A patch release with nine fixes (DF-01 to DF-09). Every fix comes from one of two agent-led dogfoods that ran VozNativa's long-form engine on real academic documents, with a real model as writer and judge. No new features and no API changes. Not published on PyPI.

## Highlights

- **Long documents can be rewritten when they contain flattened math from a PDF.** Before this release, a token such as `C ∈Rm×n` made every edit a critical failure, and the whole document came back unchanged (13 of 13 units reverted in the dogfood).
- **The cost budget covers the judge.** `--max-calls` used to bound only the writer; judge votes were extra calls.
- **No self-approval of long documents.** A writer that judged its own long-form output was accepted; it now gets `needs_judgment`, as single texts already did.
- **`--mode PROOFREAD` no longer deletes words after one-letter labels** ("os lotes C, E e G" stayed intact only after the fix).

## Fixes

| Id | Area | What was wrong | What changed |
|---|---|---|---|
| DF-01 | long form | `--max-calls` did not count judge votes (real run: 12 counted, 16 made) | the judge spends the same budget; a refused vote leaves the unit unjudged; new `judge_calls` in the record |
| DF-02 | long form, integrity | a writer judging itself was not recognised as `same_agent` behind the budget wrapper, so its own verdict accepted the document | the relation check looks through the wrappers |
| DF-03 | long form | a term respelled in some units only ("backend" / "back-end") went unnoticed | document guard `term_variant`; outcome at least `needs_review` |
| DF-04 | compare | deleting a factual clause could pass as `no_deterministic_issues` | clause-level `possible_omission`; editorial formulas and connectives excluded |
| DF-05 | compare | gerunds and phrases ("gerando", "indicando", "por essa razão") missing from the causal/evidential lexicons: false criticals, and invisible removals | forms added; semantic suites unchanged |
| DF-06 | diagnose | a one-letter label followed by the conjunction or article ("E e", "A a") was a repeated word with `auto_fix` | different case on a one-letter pair is not a repetition |
| DF-07 | diagnose | false `acronym_redefined` contradictions from the six-word window | the expansion is the shortest run whose initials spell the acronym; otherwise there is no definition |
| DF-08 | compare | an entity extracted inside a token was never found as a whole word: critical `span_missing` on any edit | presence also counts by the same extraction on the other text |
| DF-09 | compare | a split sentence and a trailing citation far apart looked like a moved marker (critical) | sentences without content words are left out; a new unaligned sentence counts with its neighbour |

Each fix has a regression test with synthetic fixtures written in another domain. The tests fail on the code before the fix and pass after; controls pass on both. The tests are `evals/test_v081_dogfood.py`, `test_v081_compare_omission.py`, `test_v081_marker_forms.py`, `test_v081_diagnose_labels.py`, `test_v081_entity_in_token.py` and `test_v081_moved_groups.py`.

## Evidence from the dogfoods

The documents are private and are not in the repository. The public records contain counts, codes and synthetic examples only: [`DOGFOOD_TG1.md`](../v0.8/DOGFOOD_TG1.md) and [`DOGFOOD_TCC2.md`](../v0.8/DOGFOOD_TCC2.md).

- **Technical report** (about 7,300 words, converted from DOCX outside the product):
  - Two real runs. A replay with the recorded model answers reproduces the old engine byte for byte.
  - The fixed engine keeps the same text and unit outcomes, counts 16 calls instead of 12, and flags the split spelling.
- **Academic report available only as PDF** (about 8,300 words):
  - On 0.8.0.dev0 a real run kept no edit at all (13 of 13 units reverted).
  - On the same recorded answers, the fixed engine reverts none.
  - A new real run kept 39 edited paragraphs, all left for human review.
- **Human review mattered.** In both dogfoods it rejected candidates that the gates and a judge of the same model had passed: a dropped "também", a respelled technical term, and an added explanation.

## Qualification

Full record: [`RELEASE_QUALIFICATION.md`](RELEASE_QUALIFICATION.md).

- **Windows 10, CPython 3.12:** `scripts/qualify.py --scope release` passed every local gate, including the package gate (sdist → wheel → clean venv → smoke → suite against the wheel). Unit tests: 933 (931 pass, 2 skips with a recorded reason).
- **GitHub Actions, run #127, on the release commit:** 8/8 jobs on Linux and Windows with Python 3.11, 3.12 and 3.13, verified live.
- **Frozen benchmarks and predicate sample:** `ptbr-bench-v4` 22/22, `ptbr-bench-v5` 36/36, predicate sample unchanged (17/20, 1/18).
- **Assertiva 0.10.1 `audit --execute`:** suite pass in an isolated copy; wheel build, install and import pass; no false-green candidates.
- **Derivanta Engine 0.1.0:** comparable to 0.8.0.dev0, with 5 new informational maintainability candidates and none of higher severity.
- **Not run:**
  - local Linux containers (the Docker engine on the release machine was unresponsive; covered by the CI Linux jobs);
  - an independent holdout and blind human review (they need other people).

**Passing tests are not a proof of meaning.** They show that these defects are fixed and that the frozen suites did not regress. Apart from identity, no deterministic check proves that a rewrite preserves meaning, and VozNativa keeps asking for a judgment or a human review.

## Known limitations

- Units of a long document are rewritten separately and can converge on one new construction. No detector reports that.
- Two kinds of change are not reported:
  - removing a single content qualifier;
  - grammar errors such as agreement and government, so a unit without findings never reaches the model.
- DOCX and PDF are not read natively.
- DF-07 does not check acronyms built from inner letters.
- One timing test (`test_v08_compare_perf`) can exceed its bound under full-suite load on slow machines. Alone, it measures 12–13x on both versions.

## Install

From the release assets, after checking `SHA256SUMS.txt`:

```bash
python -m pip install voznativa-0.8.1-py3-none-any.whl
voznativa --version      # voznativa 0.8.1
voznativa doctor
```

Or from the tag:

```bash
python -m pip install "git+https://github.com/Soturine/VozNativa.git@v0.8.1"
```

Requires Python 3.11 or newer. No model, key or network access is needed for `doctor`, `demo`, `compare`, `plan`, `diagnose` and `route`.
