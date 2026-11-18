# VozNativa v0.9.0 — Packaging, Integrations & Editorial Quality

**Published as a GitHub release (wheel, sdist, `SHA256SUMS.txt`). Not on PyPI.** MIT for VozNativa's own code, docs and data; third-party corpora, documents and models keep their own terms.

## Summary

v0.9.0 makes VozNativa easier to install, configure and integrate, and — the priority of this round — better at the two things the v0.8.1 dogfoods showed were weak: **long documents that improve locally but get worse globally**, and **meaning changes that pass the gates with every number and name intact**. It also adds a safe DOCX workflow, a scoped PDF workflow, and a contract for linguistic packs.

Passing tests and gates still do **not** prove that a rewrite preserves meaning. The best state without a judge or a person remains `unverified`; a judge of the same vendor is fallible evidence, not independence.

## Highlights

- **Meaning changes with values intact** are now review signals (`major`, never `critical`): an operational qualifier dropped, flipped or added (*automático → manual*, *presencial → online*, *estimado → confirmado*), a different event class (*assinou → recebeu*, *aprovou → analisou*), a fact turned into an intention, attempt, request or proposal (*concluiu → pretende concluir*, *pagou → solicitou o pagamento*), and aspect (*passou a*, *voltou a*). On sets frozen before the rules: development risks flagged 4/31 → 31/31 with false alarms 7/20 → 4/20; holdout, run once, 4/18 → 18/18 with 1/10 → 2/10.
- **Self-judgment is no longer accepted** when writer and judge are the same model behind command lines that differ in one argument (the case behind an accepted-then-rejected unit in the first v0.8.1 dogfood). Proven before × after with real calls.
- **Editorial consistency for long documents:** a `style_convergence` signal for openers the rewrite made the units converge on (the real case, 3 → 11 "Essa X permite…", is flagged; a second real document is not), and an editorial memory that tells later units which openers earlier units already added and which spelling the document uses.
- **Grammar diagnostics** that the planner acts on: plural agreement, impersonal *fazer*/*haver*, crase; before, a text whose only problem was grammar was `no_change` and the model was never called.
- **Technical terms:** a text with three or more technical terms is in the tech domain, so *backend*, *branch*, *deploy* are no longer suggested for replacement in an academic report on software.
- **DOCX:** `voznativa docx extract | apply | check` and `rewrite FILE.docx --docx-out NEW.docx`. Only plain-text paragraphs with one formatting are editable; everything else is protected with the reason; edits go to a new file and every other part is copied byte for byte. On a real 7,300-word report: round trip with all 27 parts byte-identical; a real rewrite through the product applied 19 paragraphs to a copy that passes `check`.
- **PDF (optional extra `voznativa[pdf]`):** traceable text per page with equations and code as protected placeholders; notes per page in a new PDF.
- **First use and configuration:** `doctor` names the category of each problem and checks the configured provider without calling it (`--probe-provider` makes one real call); user and project configuration files with documented precedence — a project file can never choose the command, server or credentials; `rewrite --dry-run`; `voznativa config`.
- **Providers:** a chat-completions adapter (`--api-url`, `--api-model`) for Ollama, llama.cpp, LM Studio or an authorised API; typed provider errors; provider identity in reports.
- **Packs:** one contract for every pack (no gate keys, no code, safe YAML, size and path limits, licence and provenance for external packs), external community packs from `VOZNATIVA_PACKS_DIR`, a contribution policy.

## Evidence

| Instrument | v0.8.1 | v0.9.0 |
|---|---|---|
| unit tests (Windows, CPython 3.12.6) | 933 (931 pass, 2 skipped) | 1,025 (1,023 pass, 2 skipped); same local gates on CPython 3.11.18 |
| GitHub Actions (manual dispatch) | 8/8 | 8/8 (run #130; run #129 failed on Windows short temp paths, which exposed and fixed a real privacy-gate defect) |
| `ptbr-bench-v4` / `ptbr-bench-v5` (frozen) | 22/22 / 36/36 | 22/22 / 36/36 |
| predicate sample (frozen in v0.7) | 17/20 risks, 1/18 false alarms | 19/20, 1/18 |
| frozen regression (Evaluation Core) | 86/89 detected, 1/33 false alarms | 88/89, 1/33 |
| v0.9 sets frozen before the rules: development / holdout (run once) | 4/31 · 7/20 / 4/18 · 1/10 | 31/31 · 4/20 / 18/18 · 2/10 |
| grammar diagnostics (development / holdout) | 0/11 / 0/6 | 11/11 / 6/6, no false alarm |
| same-model arms (12 texts; direct LLM call vs engine) | — | direct call changed 6/6 texts that needed no change; engine 0/6 |
| `compare` on 17,600 words (CPU) | 5.84 s | 5.48 s |

All sets were written by the same agent that wrote the rules: these numbers show conformance to the specification, not quality judged by readers. Three Assertiva `audit --execute` runs (the last one: suite PASS, 0 false-green candidates) and a Derivanta Engine comparison (COMPARABLE) were run on the candidate. Real-provider spend in the round: about USD 1.2. Full records: `docs/releases/v0.9/` (`RELEASE_QUALIFICATION.md`, `EVALUATION.md`, `SEMANTICS.md`, `EDITORIAL.md`, `DOCUMENTS.md`, `INTEGRATIONS.md`, `DOGFOOD.md`, `ASSURANCE.md`).

## Integrations actually run

| Integration | State |
|---|---|
| `claude -p` as provider (LLM-assisted mode) | real runs; writer and judge of different models from one vendor |
| Claude Code as agent-led host (skill in the project) | real session: skill discovered, real CLI used, NO_CHANGE and self-assessment handled |
| chat-completions adapter | tested against a local HTTP server with a fake model; **a real local model run is not recorded** |
| Codex, Gemini CLI | not run (not installed); install paths checked against the official docs |
| Emulate | blocked (no key) |

## Compatibility and migration

- **Behaviour change:** `--cmd "claude -p ..."` with `--judge-cmd "claude -p ..."` no longer accepts a rewrite on the judge's word: it is self-assessment. Use a judge with a different declared model, or a signed human review.
- `rewrite` options without a value on the command line now come from the configuration layer; with no configuration file the defaults are the same as in 0.8.1.
- `doctor --json` is `schema_version` 2 (fields added).
- New review signals can turn a `needs_judgment` into `needs_review`.
- The CLI is still not declared stable (that is for 1.0).

## Known limitations

- No independent holdout, no blind human review, no other-vendor judge; all sets and rules were written by the same agent.
- Event and qualifier classes are small authored lists; a verb or qualifier outside them abstains. Coreference and role changes without lexical cues remain out of reach.
- DOCX: text in headers, footers, footnotes, comments and text boxes, mixed formatting, fields and tracked changes are protected, not edited; rendering in Word or LibreOffice was not tested.
- PDF: no word boxes (notes are per page), no OCR, no reliable multi-column order, no inline math.
- Linux was qualified by the CI, not locally (Docker did not respond); macOS not tested.

## Install

```bash
python -m pip install voznativa-0.9.0-py3-none-any.whl          # from the release assets
python -m pip install "voznativa[pdf] @ git+https://github.com/Soturine/VozNativa.git@v0.9.0"
voznativa doctor
```

Verify the download with `SHA256SUMS.txt`.

## Checksums

The `SHA256SUMS.txt` asset lists the SHA-256 of the wheel and the sdist, both built from the exact tagged revision (`git archive v0.9.0`).
