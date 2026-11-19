# VozNativa 0.10.5 — PT-BR fire trial

0.10.5 is a qualification release. It runs the product on real Brazilian Portuguese that nobody wrote for the engine, through a real agent host, and fixes what that exposed. It is not a leap in writing quality, and it says so where the evidence says so.

**Results site:** `docs/observatory/index.html` (VozNativa Observatory). It is static and self-contained, and it opens offline. From any number it lets you drill down to the run, the aligned diff and the evidence behind it.

## What was tested

- **Corpus:** 427 real PT-BR texts in 28 genre labels and 5 length bands (micro to 12-thousand-word documents). The sources are Machado de Assis (public domain), federal laws (official acts) and CC BY 4.0 academic abstracts. UD treebanks and product reviews were used for local analysis only. Rights are recorded per operation: local analysis, sending to a model API, publishing an excerpt. Families with no lawful source this round (messages, e-mail, Portuguese technical docs, health, creative, transcribed regional speech) are declared missing. No synthetic text stands in for them.
- **Offline campaign:** 1,632 perturbations with a known answer. Some change the meaning (the `compare` gate must flag them), others are benign (it must not).
- **Live arms:** 12 tasks frozen before any product change × 3 repetitions × 4 arms × 2 versions, with the same writer model (Haiku) in every arm. The arms are: a direct LLM call; the **Skill in a real Claude Code session** whose request never names the Skill; the engine; and the engine without context. A blind judge (Sonnet; same vendor, so dependent) scores each output. A frozen internal holdout of 6 tasks ran once at the end.
- **Whole documents:** a full law, novel chapters, and a DOCX/PDF pair, each checked by an oracle that does not use the engine.
- **Reciprocal dogfood in four separate tracks:** Derivanta Framework (real agent sessions), Derivanta Engine (static CLI), Assertiva (`audit --execute`) and VozNativa itself.

## What improved (v0.10.0 → v0.10.5, same corpus, same method)

| Measure | v0.10.0 | v0.10.5 |
|---|---|---|
| Meaning changes that passed `compare` without a signal (1,632 perturbations) | 46 | **7** |
| False alarms on benign changes | 10 | **1** |
| Skill activated without being named (36 sessions) | 13 | **28** |
| Skill edited a text that should come back unchanged | 7 | **2** |
| Engine left unedited a text the task required to change | 9 | **4** |
| Engine, blind judge, "meets the request" (tasks better in ≥ 2 of 3 repetitions) | — | **+6, no loss** |

The direct-LLM arm does not use VozNativa and serves as the noise control. Over the same period it went from 9 to 10 unnecessary edits.

## What did not improve

- **The Skill is not better on quality.** The blind judge finds it more faithful in 3 tasks with no loss, but worse at meeting the request in 5 tasks and on naturalness in 4. The agent now reads a `review_required` as a block and undoes the edit (V105-GAP-16, open).
- The agent still skips the VozNativa flow in 20 of 36 sessions (V105-GAP-01, partial). In one task it claimed "all ideas kept" for an output the judge rated as a critical meaning change, which the gate could not detect (V105-GAP-17, open). The engine itself asked for judgment on that output and did not accept it.
- **Context and knowledge show no isolated gain.** The ablation removed the user's request together with the attributes, so it measures the request, not the knowledge.
- The router returns `unknown` for 260 of 427 real texts (V105-GAP-18, open). Declared context remains the reliable path.
- Published-text false alarms are unchanged: 2 `ERROR_CONFIRMED` items and 18 `edit` plans in both versions.

## Fixes (each with a test that is red on v0.10.0, a control and a replay on real text)

- Negation false green under negative concord (V105-GAP-05); a deleted sentence whose words occur elsewhere (GAP-06); hard-wrapped lines read as new spans and relations (GAP-07).
- `rewrite --mode POLISH/ADAPT` ignored without a detector finding (GAP-08). On v0.10.0 the engine never called the model in the 12 tasks.
- Digits glued to letters ("7a", "L1", "#petr4") are protected values (GAP-13).
- A document with one article per line and no blank line was a single long-form unit (GAP-14). The 12-thousand-word law now splits into 28 units, and its 80 articles keep their order.
- In legal text, the first word of a provision after "§ 3°" or "I -" was read as a proper name (GAP-15). The fix changes 21 of 144 real rewrites, all in law tasks, all by dropping that false signal.
- The Skill description now covers ordinary revision requests, and the minimal flow is `plan --attr pedido=…` → candidate → `compare` (GAP-09, GAP-02).
- A judgment read from a file now reports `relation_evidence: DECLARED` (GAP-11, found by a real Derivanta Framework audit session).
- Privacy gate: a bare number shared with a private document now counts only next to its neighbouring word, and the Watcher regex is back to `{2,60}` (GAP-04).

## Harness defects found and fixed during the round

The account hit its 5-hour limit mid-campaign, and 83 runs were recorded as results. Provider failures are now never results, and that campaign was discarded and rerun from scratch. A judge without an answer no longer writes empty scores. The document flow resolved a relative work path wrongly. The first Observatory page rendered empty sections and its browser QA passed it; the QA now runs 55 content, interaction, privacy and accessibility checks in Edge.

## Continuation (19/11)

- **Judgment files accept nothing** (D-03). In the Skill flow the agent that writes the candidate also writes the judgment file, so a relation declared there is a claim, not evidence. Only a judge the engine runs can accept. See `MIGRATION.md`.
- **Prospective holdout:** 10 tasks frozen before measuring, with authors and sources not used in development (Lima Barreto, João do Rio, Euclides da Cunha, Júlia Lopes de Almeida, Python docs in Portuguese, Agência Brasil). It confirms the engine gain (correct edit decisions 6 → 10 of 16, no critical error). **It shows no measurable writing-quality gain for the Skill**: more faithful than v0.10.0, but not better at meeting the request. The direct LLM edited every text that should have come back unchanged and had 7 critical errors in 20 outputs.
- **Valid ablation** (same request in every variant): attributes and knowledge show no measurable gain on their own.
- The Skill uses the VozNativa flow more often (steps before writing 0 → 9 of 20), but the agent still sometimes edits without any gate or delivers a rejected candidate. A written instruction does not guarantee host behaviour.
- New open findings: a verb change that alters meaning ("criam" → "criavam") passes `compare` (V105-GAP-22); the engine is still too conservative on tasks that require an edit (V105-GAP-23).

## Other tracks

- **Assertiva:** PR #11 refined. A backend that `build-system.requires` does not declare is now attributed to the project's configuration, not the environment. The remaining failure of Assertiva's own suite on this machine was shown to be environmental.
- **Derivanta Engine:** PR #6 refined so that a test class is decided by its ancestry, not by its name. A comparison across differently named folders reports `DIFFERENT_TARGET` with zero findings. That is not "nothing changed": compare the same folder instead.

## Cost and limits

The round used US$ 5.01 in API-equivalent cost (reported by the `claude` CLI), against a US$ 10 ceiling. The following were **not run**: blind human review, a third-party holdout, a judge from another vendor, a local model, Codex/Gemini, macOS and Word rendering. Nothing here claims "better writing for people". Passing tests show the listed defects fixed and the frozen suites not regressed; they do not prove semantic equivalence.

Not on PyPI. Install from the GitHub release assets (wheel and sdist, with `SHA256SUMS.txt`).
