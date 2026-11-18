# Referência da CLI

Gerada de `voznativa --help` e do `--help` de cada subcomando por `scripts/cli_reference.py`; um teste confere que este arquivo está igual ao que o parser produz. Guia de uso: [`QUICKSTART.md`](QUICKSTART.md).

Códigos de saída do `compare` (e do `rewrite` com `--judgment`): 0 `identical` ou aceito, 1 `fail`, 2 revisão (`review_required`, `human_review_claimed`), 3 `no_deterministic_issues` (precisa de juiz). Erro de uso ou de entrada: 64. Recusa da política de dados: 77.

## `voznativa`

```text
usage: voznativa [-h] [--version] {doctor,docx,packs,knowledge,pdf,config,demo,rubric,standards,evaluate,ledger,compare,review,blind-tasks,blind-review,blind-summary,judge-prompt,plan,integrity,diagnose,patterns,analyze,audit,region,regional,drift,eval,benchmark,route,context,refs,project,ground,profile,corpus,contract,rewrite-prompt,rewrite} ...

VozNativa PT-BR voice engine

positional arguments:
  {doctor,docx,packs,knowledge,pdf,config,demo,rubric,standards,evaluate,ledger,compare,review,blind-tasks,blind-review,blind-summary,judge-prompt,plan,integrity,diagnose,patterns,analyze,audit,region,regional,drift,eval,benchmark,route,context,refs,project,ground,profile,corpus,contract,rewrite-prompt,rewrite}
    doctor              check the installation (no network, reads no text); exit 1 when something
                        will not work
    docx                Word documents: extract the editable paragraphs, apply edits to a new
                        copy, check a copy against its original (the original is never written)
    packs               linguistic packs: list bundled and external ones (VOZNATIVA_PACKS_DIR),
                        validate a pack file against the contract; exit 1 when a pack is invalid
    knowledge           Linguistic Knowledge Registry: entries and sources (nature, licence,
                        access), what a text would retrieve and why; reference only, never a gate
    pdf                 PDF (optional dependency pypdf): traceable text extraction with protected
                        equations/code, and annotated copies; no editing of the PDF itself
    config              effective rewrite configuration: value and source of each option (flag >
                        project .voznativa.toml > user file > default); writes nothing
    demo                offline tour of compare, plan and diagnose on bundled texts (no model, no
                        key, no file written)
    rubric              criteria of the standard that applies to a document: objective checks only
                        where verified, subjective ones listed for judgment; never a score
    standards           Standards Registry: registered editais, manuals, norms and rubrics, and
                        which edition applies to a document (never the latest by default)
    evaluate            evaluation core: a dataset spec with splits, axes, provenance and
                        integrity (eval runs a single legacy suite); exit 0 COMPLETE, 1 INVALID or
                        INCOMPLETE
    ledger              build the Semantic Ledger of a text
    compare             compare a candidate against its source (gate)
    review              record a signed human review (interactive terminal only)
    blind-tasks         build blind pairwise review tasks from a benchmark run
    blind-review        answer blind tasks (interactive terminal only; signed)
    blind-summary       wins per arm from verified human answers
    judge-prompt        print the semantic-judge prompt for any LLM or reviewer
    plan                rewrite plan: what to change, why, how much (no model call)
    integrity           character-level integrity audit (invisible, bidi, tag, control,
                        homoglyph); not a watermark detector. Exit 2 when something is suspicious
    diagnose            typed diagnostics of the source: errors, contradictions, legitimate
                        choices, ambiguities (no model call, nothing changed)
    patterns            editorial pattern findings (genre-aware; not an authorship score)
    analyze             descriptive text measurements
    audit               diagnostics; add --original for semantic risk
    region              regional overfit / dialect mixing baseline
    regional            Regional Evidence Packs: list them or check what a requested region allows
    drift               voice drift across windows or against a profile
    eval                run a behavioral eval suite (JSONL)
    benchmark           score frozen benchmark outputs (deterministic tier)
    route               build the Context Contract (genre, register, sources, flags)
    context             open TaskContext: router dimensions plus any attribute (--attr), with
                        provenance, unknown/mixed/conflicts and the conservative choices made;
                        --interpret-prompt prints the prompt an agent answers to propose one
    refs                select references for a contract (progressive disclosure)
    project             index a repository as a fact source
    ground              check that protected values in a text come from fact sources
    profile             build a Voice Profile v2 from authorized samples (no raw text stored)
    corpus              Corpus Registry: sources, permissions, local preparation and evaluation
    contract            resolve the Voice Contract (VOICE_STACK precedence)
    rewrite-prompt      print the rewrite prompt for the current agent to answer
    rewrite             run the generate -> validate -> retry loop with a provider

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

## `voznativa analyze`

```text
usage: voznativa analyze [-h] text

positional arguments:
  text

options:
  -h, --help  show this help message and exit
```

## `voznativa audit`

```text
usage: voznativa audit [-h] [--original ORIGINAL] [--profile PROFILE] text

positional arguments:
  text

options:
  -h, --help           show this help message and exit
  --original ORIGINAL
  --profile PROFILE    Voice Profile JSON for drift against the author
```

## `voznativa benchmark`

```text
usage: voznativa benchmark [-h] [--json JSON_PATH] [--manifest MANIFEST] cases outputs

positional arguments:
  cases
  outputs

options:
  -h, --help           show this help message and exit
  --json JSON_PATH
  --manifest MANIFEST  JSON with system versions, models and run settings
```

## `voznativa blind-review`

```text
usage: voznativa blind-review [-h] --reviewer REVIEWER --out OUT [--limit LIMIT] [--ssh-key SSH_KEY] [--principal PRINCIPAL] tasks

positional arguments:
  tasks

options:
  -h, --help            show this help message and exit
  --reviewer REVIEWER
  --out OUT             JSONL file to append signed answers to
  --limit LIMIT
  --ssh-key SSH_KEY     sign with your own SSH private key (ssh-keygen -Y) instead of the local
                        HMAC key; the project verifies it with the public key in its registry
  --principal PRINCIPAL
                        name of your key in allowed_signers (default: --reviewer)
```

## `voznativa blind-summary`

```text
usage: voznativa blind-summary [-h] [--reviewers REVIEWERS] tasks answers

positional arguments:
  tasks
  answers

options:
  -h, --help            show this help message and exit
  --reviewers REVIEWERS
                        reviewer registry dir (allowed_signers + registry.json) for SSH signatures
```

## `voznativa blind-tasks`

```text
usage: voznativa blind-tasks [-h] --out OUT [--focus FOCUS] [--seed SEED] run

positional arguments:
  run            benchmark run JSON (benchmarks/runs/...)

options:
  -h, --help     show this help message and exit
  --out OUT
  --focus FOCUS  only pairs that include this arm
  --seed SEED
```

## `voznativa compare`

```text
usage: voznativa compare [-h] [--judgment JUDGMENT] [--protect PROTECT] [--protect-file PROTECT_FILE] original candidate

positional arguments:
  original
  candidate

options:
  -h, --help            show this help message and exit
  --judgment JUDGMENT   judgment JSON from an LLM or human (repeatable)
  --protect PROTECT     term that must survive verbatim (repeatable)
  --protect-file PROTECT_FILE
                        file with one protected term per line
```

## `voznativa config`

```text
usage: voznativa config [-h] [--json]

options:
  -h, --help  show this help message and exit
  --json      JSON instead of text
```

## `voznativa context`

```text
usage: voznativa context [-h] [--interpret-prompt] [--task {rewrite,audit,create,profile,compare}] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] [--audience AUDIENCE] [--region REGION] [--region-strength REGION_STRENGTH] [--community COMMUNITY] [--slang-strength SLANG_STRENGTH] [--epoch EPOCH] [--fact FACT] [--voice-sample VOICE_SAMPLE] [--voice-channel VOICE_CHANNEL] [--repo REPO] [--document-profile DOCUMENT_PROFILE] [--attr NAME=VALUE] [--attrs-file ATTRS_FILE] [--context-proposal CONTEXT_PROPOSAL] text

positional arguments:
  text

options:
  -h, --help            show this help message and exit
  --interpret-prompt    print the prompt for an agent to propose attributes (answer with
                        --context-proposal)
  --task {rewrite,audit,create,profile,compare}
  --genre GENRE
  --channel CHANNEL
  --register REGISTER
  --audience AUDIENCE
  --region REGION
  --region-strength REGION_STRENGTH
  --community COMMUNITY
  --slang-strength SLANG_STRENGTH
  --epoch EPOCH         reader's period: current, a year (1995) or a range (1994-1996)
  --fact FACT           fact source file (repeatable); never used for voice
  --voice-sample VOICE_SAMPLE
                        text the author wrote (repeatable); never used for facts
  --voice-channel VOICE_CHANNEL
  --repo REPO           repository used as a fact source
  --document-profile DOCUMENT_PROFILE
                        JSON file describing the document (type, authority, series, event year,
                        submission date); attaches the applicable standards
  --attr NAME=VALUE     open task attribute (repeatable), any name: tone=cordial, genre=roteiro de
                        podcast, purpose=convidar; a comma makes a list (genre=e-mail,post).
                        Context for the writer, never a rule that edits text; safety fields
                        (facts, protect, judge…) are refused
  --attrs-file ATTRS_FILE
                        JSON object of open task attributes (same rules as --attr)
  --context-proposal CONTEXT_PROPOSAL
                        JSON answer to `voznativa context --interpret-prompt` from an agent;
                        attributes without evidence are dropped and never override the user's
```

## `voznativa contract`

```text
usage: voznativa contract [-h] [--context CONTEXT] [--profile PROFILE] [--set SET] [--compact] [--task {rewrite,audit,create,profile,compare}] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] [--audience AUDIENCE] [--region REGION] [--region-strength REGION_STRENGTH] [--community COMMUNITY] [--slang-strength SLANG_STRENGTH] [--epoch EPOCH] [--fact FACT] [--voice-sample VOICE_SAMPLE] [--voice-channel VOICE_CHANNEL] [--repo REPO] [--document-profile DOCUMENT_PROFILE] [--attr NAME=VALUE] [--attrs-file ATTRS_FILE] [--context-proposal CONTEXT_PROPOSAL] [text]

positional arguments:
  text

options:
  -h, --help            show this help message and exit
  --context CONTEXT     Context Contract JSON instead of routing the text
  --profile PROFILE     Voice Profile JSON
  --set SET             explicit instruction as JSON, e.g. {"emoji": "none"}
  --compact             flat feature -> value view for prompts
  --task {rewrite,audit,create,profile,compare}
  --genre GENRE
  --channel CHANNEL
  --register REGISTER
  --audience AUDIENCE
  --region REGION
  --region-strength REGION_STRENGTH
  --community COMMUNITY
  --slang-strength SLANG_STRENGTH
  --epoch EPOCH         reader's period: current, a year (1995) or a range (1994-1996)
  --fact FACT           fact source file (repeatable); never used for voice
  --voice-sample VOICE_SAMPLE
                        text the author wrote (repeatable); never used for facts
  --voice-channel VOICE_CHANNEL
  --repo REPO           repository used as a fact source
  --document-profile DOCUMENT_PROFILE
                        JSON file describing the document (type, authority, series, event year,
                        submission date); attaches the applicable standards
  --attr NAME=VALUE     open task attribute (repeatable), any name: tone=cordial, genre=roteiro de
                        podcast, purpose=convidar; a comma makes a list (genre=e-mail,post).
                        Context for the writer, never a rule that edits text; safety fields
                        (facts, protect, judge…) are refused
  --attrs-file ATTRS_FILE
                        JSON object of open task attributes (same rules as --attr)
  --context-proposal CONTEXT_PROPOSAL
                        JSON answer to `voznativa context --interpret-prompt` from an agent;
                        attributes without evidence are dropped and never override the user's
```

## `voznativa corpus`

```text
usage: voznativa corpus [-h] {list,info,permissions,validate,sample,prepare,evaluate,report} ...

positional arguments:
  {list,info,permissions,validate,sample,prepare,evaluate,report}
    list                registered sources with status and licence
    info                one source's registry entry
    permissions         the data policy's decision for every operation
    validate            validate every registry file (exit 1 on problems)
    sample              print a few records of a prepared source (local use only)
    prepare             download (bounded, policy-checked) and read sources into the local cache
    evaluate            aggregate detector measurements on a prepared source
    report              registry summary and the evidence files each status cites

options:
  -h, --help            show this help message and exit
```

### `voznativa corpus evaluate`

```text
usage: voznativa corpus evaluate [-h] [--genre GENRE] [--limit LIMIT] source

positional arguments:
  source

options:
  -h, --help     show this help message and exit
  --genre GENRE
  --limit LIMIT
```

### `voznativa corpus info`

```text
usage: voznativa corpus info [-h] source

positional arguments:
  source

options:
  -h, --help  show this help message and exit
```

### `voznativa corpus list`

```text
usage: voznativa corpus list [-h] [--status {CATALOGUED,SOURCE_VERIFIED,ACCESS_VERIFIED,CONNECTOR_READY,LOCALLY_VALIDATED,EVALUATION_INTEGRATED,RESTRICTED,AWAITING_PERMISSION,UNAVAILABLE,DEPRECATED}]

options:
  -h, --help            show this help message and exit
  --status {CATALOGUED,SOURCE_VERIFIED,ACCESS_VERIFIED,CONNECTOR_READY,LOCALLY_VALIDATED,EVALUATION_INTEGRATED,RESTRICTED,AWAITING_PERMISSION,UNAVAILABLE,DEPRECATED}
```

### `voznativa corpus permissions`

```text
usage: voznativa corpus permissions [-h] [--purpose {noncommercial_research,commercial}] [--destination DESTINATION] source

positional arguments:
  source

options:
  -h, --help            show this help message and exit
  --purpose {noncommercial_research,commercial}
  --destination DESTINATION
```

### `voznativa corpus prepare`

```text
usage: voznativa corpus prepare [-h] [--no-fetch] sources [sources ...]

positional arguments:
  sources

options:
  -h, --help  show this help message and exit
  --no-fetch  read an existing local copy only
```

### `voznativa corpus report`

```text
usage: voznativa corpus report [-h]

options:
  -h, --help  show this help message and exit
```

### `voznativa corpus sample`

```text
usage: voznativa corpus sample [-h] [-n N] [--max-chars MAX_CHARS] [--allow-personal-data] source

positional arguments:
  source

options:
  -h, --help            show this help message and exit
  -n N
  --max-chars MAX_CHARS
  --allow-personal-data
                        required for sources that may hold personal data
```

### `voznativa corpus validate`

```text
usage: voznativa corpus validate [-h] [--directory DIRECTORY]

options:
  -h, --help            show this help message and exit
  --directory DIRECTORY
                        another registry directory (default: the package's)
```

## `voznativa demo`

```text
usage: voznativa demo [-h] [--json]

options:
  -h, --help  show this help message and exit
  --json      JSON result instead of text
```

## `voznativa diagnose`

```text
usage: voznativa diagnose [-h] [--mode {PRESERVE,REVIEW,PROOFREAD,POLISH,ADAPT,CREATE}] [--task {rewrite,audit,create,profile,compare}] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] [--audience AUDIENCE] [--region REGION] [--region-strength REGION_STRENGTH] [--community COMMUNITY] [--slang-strength SLANG_STRENGTH] [--epoch EPOCH] [--fact FACT] [--voice-sample VOICE_SAMPLE] [--voice-channel VOICE_CHANNEL] [--repo REPO] [--document-profile DOCUMENT_PROFILE] [--attr NAME=VALUE] [--attrs-file ATTRS_FILE] [--context-proposal CONTEXT_PROPOSAL] text

positional arguments:
  text

options:
  -h, --help            show this help message and exit
  --mode {PRESERVE,REVIEW,PROOFREAD,POLISH,ADAPT,CREATE}
                        report what this editorial mode would authorise
  --task {rewrite,audit,create,profile,compare}
  --genre GENRE
  --channel CHANNEL
  --register REGISTER
  --audience AUDIENCE
  --region REGION
  --region-strength REGION_STRENGTH
  --community COMMUNITY
  --slang-strength SLANG_STRENGTH
  --epoch EPOCH         reader's period: current, a year (1995) or a range (1994-1996)
  --fact FACT           fact source file (repeatable); never used for voice
  --voice-sample VOICE_SAMPLE
                        text the author wrote (repeatable); never used for facts
  --voice-channel VOICE_CHANNEL
  --repo REPO           repository used as a fact source
  --document-profile DOCUMENT_PROFILE
                        JSON file describing the document (type, authority, series, event year,
                        submission date); attaches the applicable standards
  --attr NAME=VALUE     open task attribute (repeatable), any name: tone=cordial, genre=roteiro de
                        podcast, purpose=convidar; a comma makes a list (genre=e-mail,post).
                        Context for the writer, never a rule that edits text; safety fields
                        (facts, protect, judge…) are refused
  --attrs-file ATTRS_FILE
                        JSON object of open task attributes (same rules as --attr)
  --context-proposal CONTEXT_PROPOSAL
                        JSON answer to `voznativa context --interpret-prompt` from an agent;
                        attributes without evidence are dropped and never override the user's
```

## `voznativa doctor`

```text
usage: voznativa doctor [-h] [--json] [--probe-provider]

options:
  -h, --help        show this help message and exit
  --json            JSON report instead of text
  --probe-provider  also send one short prompt to the configured provider command (may cost money;
                    uses the network if the provider does)
```

## `voznativa docx`

```text
usage: voznativa docx [-h] {extract,apply,check} ...

positional arguments:
  {extract,apply,check}
    extract             intermediate representation: paragraphs, types, editable or protected
                        (why)
    apply               write a NEW file with the edited paragraphs; protected ones are refused
    check               integrity of a copy: parts, bytes outside document.xml, protected
                        paragraphs

options:
  -h, --help            show this help message and exit
```

### `voznativa docx apply`

```text
usage: voznativa docx apply [-h] --out OUT file edits

positional arguments:
  file
  edits       JSON {"p3": "new text", ...} or an edited extract

options:
  -h, --help  show this help message and exit
  --out OUT   new .docx (must not be the original nor exist)
```

### `voznativa docx check`

```text
usage: voznativa docx check [-h] original candidate

positional arguments:
  original
  candidate

options:
  -h, --help  show this help message and exit
```

### `voznativa docx extract`

```text
usage: voznativa docx extract [-h] [--out OUT] file

positional arguments:
  file

options:
  -h, --help  show this help message and exit
  --out OUT   write the JSON here instead of printing it
```

## `voznativa drift`

```text
usage: voznativa drift [-h] [--profile PROFILE] text

positional arguments:
  text

options:
  -h, --help         show this help message and exit
  --profile PROFILE
```

## `voznativa eval`

```text
usage: voznativa eval [-h] [--require-frozen] cases

positional arguments:
  cases

options:
  -h, --help        show this help message and exit
  --require-frozen  refuse to run unless MANIFEST.json lists the suite as frozen with a matching
                    sha256
```

## `voznativa evaluate`

```text
usage: voznativa evaluate [-h] [--root ROOT] [--out OUT] [--report REPORT] [--verify RUN] [--replay RUN] [dataset]

positional arguments:
  dataset          voznativa.eval_dataset JSON (paths relative to --root)

options:
  -h, --help       show this help message and exit
  --root ROOT      repository root the dataset paths are relative to
  --out OUT        write the run record (JSON) here
  --report REPORT  write the readable report (Markdown) here
  --verify RUN     check a recorded run's internal consistency (digest and metrics); not
                   authenticity
  --replay RUN     re-execute a recorded run with the code and inputs of its revision; exit 0
                   REPRODUCED, 1 DIFFERENT, 3 NOT_REPLAYABLE
```

## `voznativa ground`

```text
usage: voznativa ground [-h] [--original ORIGINAL] [--fact FACT] [--repo REPO] [--request REQUEST] [--judgment JUDGMENT] candidate

positional arguments:
  candidate

options:
  -h, --help           show this help message and exit
  --original ORIGINAL
  --fact FACT
  --repo REPO
  --request REQUEST    the request the text was written for; a source only for facts it states
  --judgment JUDGMENT  grounding judgment JSON (from judge-prompt --fact)
```

## `voznativa integrity`

```text
usage: voznativa integrity [-h] [--clean] [--policy {tags,bidi_unbalanced,zero_width_outside_emoji,controls,soft_hyphen}] [--text-only] text

positional arguments:
  text

options:
  -h, --help            show this help message and exit
  --clean               remove only the classes named by --policy
  --policy {tags,bidi_unbalanced,zero_width_outside_emoji,controls,soft_hyphen}
  --text-only
```

## `voznativa judge-prompt`

```text
usage: voznativa judge-prompt [-h] [--fact FACT] [--repo REPO] original candidate

positional arguments:
  original     the original text, or the request when --fact/--repo is given
  candidate

options:
  -h, --help   show this help message and exit
  --fact FACT  fact source (repeatable): judge grounding instead of equivalence
  --repo REPO  repository used as a fact source (grounding mode)
```

## `voznativa knowledge`

```text
usage: voznativa knowledge [-h] {list,select,sources,check,status,proposals} ...

positional arguments:
  {list,select,sources,check,status,proposals}
    list                entries and sources of the registry (bundled + VOZNATIVA_KNOWLEDGE_DIR)
    select              entries this text calls for, within a character budget, with the reason
    sources             watched sources: official host, access, cost, what a change would affect
    check               ask due sources whether they changed (conditional GET, private addresses
                        refused); --mode propose stores snapshots and Change Proposals in
                        VOZNATIVA_WATCH_DIR (default ~/.voznativa/watch); nothing is applied
    status              offline view: last check and staleness of each source
    proposals           stored Change Proposals (state, difference, what they affect)

options:
  -h, --help            show this help message and exit
```

### `voznativa knowledge check`

```text
usage: voznativa knowledge check [-h] [--mode {report,propose}] [--offline] [--force] [--only ONLY]

options:
  -h, --help            show this help message and exit
  --mode {report,propose}
  --offline             fetch nothing: last snapshot and its age per source
  --force               check sources that are not due yet
  --only ONLY           source id (repeatable)
```

### `voznativa knowledge list`

```text
usage: voznativa knowledge list [-h] [--json]

options:
  -h, --help  show this help message and exit
  --json
```

### `voznativa knowledge proposals`

```text
usage: voznativa knowledge proposals [-h]

options:
  -h, --help  show this help message and exit
```

### `voznativa knowledge select`

```text
usage: voznativa knowledge select [-h] [--budget BUDGET] [--task {rewrite,audit,create,profile,compare}] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] [--audience AUDIENCE] [--region REGION] [--region-strength REGION_STRENGTH] [--community COMMUNITY] [--slang-strength SLANG_STRENGTH] [--epoch EPOCH] [--fact FACT] [--voice-sample VOICE_SAMPLE] [--voice-channel VOICE_CHANNEL] [--repo REPO] [--document-profile DOCUMENT_PROFILE] [--attr NAME=VALUE] [--attrs-file ATTRS_FILE] [--context-proposal CONTEXT_PROPOSAL] text

positional arguments:
  text

options:
  -h, --help            show this help message and exit
  --budget BUDGET
  --task {rewrite,audit,create,profile,compare}
  --genre GENRE
  --channel CHANNEL
  --register REGISTER
  --audience AUDIENCE
  --region REGION
  --region-strength REGION_STRENGTH
  --community COMMUNITY
  --slang-strength SLANG_STRENGTH
  --epoch EPOCH         reader's period: current, a year (1995) or a range (1994-1996)
  --fact FACT           fact source file (repeatable); never used for voice
  --voice-sample VOICE_SAMPLE
                        text the author wrote (repeatable); never used for facts
  --voice-channel VOICE_CHANNEL
  --repo REPO           repository used as a fact source
  --document-profile DOCUMENT_PROFILE
                        JSON file describing the document (type, authority, series, event year,
                        submission date); attaches the applicable standards
  --attr NAME=VALUE     open task attribute (repeatable), any name: tone=cordial, genre=roteiro de
                        podcast, purpose=convidar; a comma makes a list (genre=e-mail,post).
                        Context for the writer, never a rule that edits text; safety fields
                        (facts, protect, judge…) are refused
  --attrs-file ATTRS_FILE
                        JSON object of open task attributes (same rules as --attr)
  --context-proposal CONTEXT_PROPOSAL
                        JSON answer to `voznativa context --interpret-prompt` from an agent;
                        attributes without evidence are dropped and never override the user's
```

### `voznativa knowledge sources`

```text
usage: voznativa knowledge sources [-h]

options:
  -h, --help  show this help message and exit
```

### `voznativa knowledge status`

```text
usage: voznativa knowledge status [-h]

options:
  -h, --help  show this help message and exit
```

## `voznativa ledger`

```text
usage: voznativa ledger [-h] [--protect PROTECT] [--protect-file PROTECT_FILE] text

positional arguments:
  text                  file path or - for stdin

options:
  -h, --help            show this help message and exit
  --protect PROTECT     term that must survive verbatim (repeatable)
  --protect-file PROTECT_FILE
                        file with one protected term per line
```

## `voznativa packs`

```text
usage: voznativa packs [-h] {list,validate} ...

positional arguments:
  {list,validate}
    list           every pack with status, errors and warnings
    validate       validate pack files as external contributions (strict envelope)

options:
  -h, --help       show this help message and exit
```

### `voznativa packs list`

```text
usage: voznativa packs list [-h] [--json]

options:
  -h, --help  show this help message and exit
  --json
```

### `voznativa packs validate`

```text
usage: voznativa packs validate [-h] files [files ...]

positional arguments:
  files

options:
  -h, --help  show this help message and exit
```

## `voznativa patterns`

```text
usage: voznativa patterns [-h] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] text

positional arguments:
  text

options:
  -h, --help           show this help message and exit
  --genre GENRE        genre for exemptions (default: inferred)
  --channel CHANNEL    channel for exemptions (whatsapp, email, linkedin...)
  --register REGISTER  target register (orality and forms of address are judged against it)
```

## `voznativa pdf`

```text
usage: voznativa pdf [-h] {extract,annotate} ...

positional arguments:
  {extract,annotate}
    extract           paragraphs per page; equation and code lines become protected placeholders
    annotate          a NEW PDF with one note per page: JSON [{"page": 3, "text": "..."}]

options:
  -h, --help          show this help message and exit
```

### `voznativa pdf annotate`

```text
usage: voznativa pdf annotate [-h] --out OUT file notes

positional arguments:
  file
  notes

options:
  -h, --help  show this help message and exit
  --out OUT
```

### `voznativa pdf extract`

```text
usage: voznativa pdf extract [-h] [--out OUT] [--text TEXT] file

positional arguments:
  file

options:
  -h, --help   show this help message and exit
  --out OUT    write the JSON here
  --text TEXT  also write the plain text (blocks) here, for rewrite/compare
```

## `voznativa plan`

```text
usage: voznativa plan [-h] [--profile PROFILE] [--set SET] [--task {rewrite,audit,create,profile,compare}] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] [--audience AUDIENCE] [--region REGION] [--region-strength REGION_STRENGTH] [--community COMMUNITY] [--slang-strength SLANG_STRENGTH] [--epoch EPOCH] [--fact FACT] [--voice-sample VOICE_SAMPLE] [--voice-channel VOICE_CHANNEL] [--repo REPO] [--document-profile DOCUMENT_PROFILE] [--attr NAME=VALUE] [--attrs-file ATTRS_FILE] [--context-proposal CONTEXT_PROPOSAL] [--protect PROTECT] [--protect-file PROTECT_FILE] text

positional arguments:
  text

options:
  -h, --help            show this help message and exit
  --profile PROFILE
  --set SET             explicit voice instruction as JSON
  --task {rewrite,audit,create,profile,compare}
  --genre GENRE
  --channel CHANNEL
  --register REGISTER
  --audience AUDIENCE
  --region REGION
  --region-strength REGION_STRENGTH
  --community COMMUNITY
  --slang-strength SLANG_STRENGTH
  --epoch EPOCH         reader's period: current, a year (1995) or a range (1994-1996)
  --fact FACT           fact source file (repeatable); never used for voice
  --voice-sample VOICE_SAMPLE
                        text the author wrote (repeatable); never used for facts
  --voice-channel VOICE_CHANNEL
  --repo REPO           repository used as a fact source
  --document-profile DOCUMENT_PROFILE
                        JSON file describing the document (type, authority, series, event year,
                        submission date); attaches the applicable standards
  --attr NAME=VALUE     open task attribute (repeatable), any name: tone=cordial, genre=roteiro de
                        podcast, purpose=convidar; a comma makes a list (genre=e-mail,post).
                        Context for the writer, never a rule that edits text; safety fields
                        (facts, protect, judge…) are refused
  --attrs-file ATTRS_FILE
                        JSON object of open task attributes (same rules as --attr)
  --context-proposal CONTEXT_PROPOSAL
                        JSON answer to `voznativa context --interpret-prompt` from an agent;
                        attributes without evidence are dropped and never override the user's
  --protect PROTECT     term that must survive verbatim (repeatable)
  --protect-file PROTECT_FILE
                        file with one protected term per line
```

## `voznativa profile`

```text
usage: voznativa profile [-h] [--channel CHANNEL] [--date DATE] samples [samples ...]

positional arguments:
  samples

options:
  -h, --help         show this help message and exit
  --channel CHANNEL  channel of these samples (whatsapp, github_docs, email...)
  --date DATE        ISO date of the samples
```

## `voznativa project`

```text
usage: voznativa project [-h] path

positional arguments:
  path

options:
  -h, --help  show this help message and exit
```

## `voznativa refs`

```text
usage: voznativa refs [-h] [--contract CONTRACT] [--budget BUDGET] [--task {rewrite,audit,create,profile,compare}] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] [--audience AUDIENCE] [--region REGION] [--region-strength REGION_STRENGTH] [--community COMMUNITY] [--slang-strength SLANG_STRENGTH] [--epoch EPOCH] [--fact FACT] [--voice-sample VOICE_SAMPLE] [--voice-channel VOICE_CHANNEL] [--repo REPO] [--document-profile DOCUMENT_PROFILE] [--attr NAME=VALUE] [--attrs-file ATTRS_FILE] [--context-proposal CONTEXT_PROPOSAL] [text]

positional arguments:
  text

options:
  -h, --help            show this help message and exit
  --contract CONTRACT   existing contract JSON instead of routing the text
  --budget BUDGET       word budget for loaded references
  --task {rewrite,audit,create,profile,compare}
  --genre GENRE
  --channel CHANNEL
  --register REGISTER
  --audience AUDIENCE
  --region REGION
  --region-strength REGION_STRENGTH
  --community COMMUNITY
  --slang-strength SLANG_STRENGTH
  --epoch EPOCH         reader's period: current, a year (1995) or a range (1994-1996)
  --fact FACT           fact source file (repeatable); never used for voice
  --voice-sample VOICE_SAMPLE
                        text the author wrote (repeatable); never used for facts
  --voice-channel VOICE_CHANNEL
  --repo REPO           repository used as a fact source
  --document-profile DOCUMENT_PROFILE
                        JSON file describing the document (type, authority, series, event year,
                        submission date); attaches the applicable standards
  --attr NAME=VALUE     open task attribute (repeatable), any name: tone=cordial, genre=roteiro de
                        podcast, purpose=convidar; a comma makes a list (genre=e-mail,post).
                        Context for the writer, never a rule that edits text; safety fields
                        (facts, protect, judge…) are refused
  --attrs-file ATTRS_FILE
                        JSON object of open task attributes (same rules as --attr)
  --context-proposal CONTEXT_PROPOSAL
                        JSON answer to `voznativa context --interpret-prompt` from an agent;
                        attributes without evidence are dropped and never override the user's
```

## `voznativa region`

```text
usage: voznativa region [-h] [--region REGION] text

positional arguments:
  text

options:
  -h, --help       show this help message and exit
  --region REGION
```

## `voznativa regional`

```text
usage: voznativa regional [-h] [--region REGION] [--region-strength REGION_STRENGTH] [--genre GENRE] [--channel CHANNEL] [--profile PROFILE] {packs,check} [text]

positional arguments:
  {packs,check}
  text                  file path or - for stdin (check)

options:
  -h, --help            show this help message and exit
  --region REGION       macro region (norte, nordeste, ...) or state code; never inferred
  --region-strength REGION_STRENGTH
  --genre GENRE
  --channel CHANNEL
  --profile PROFILE     Voice Profile JSON: forms the author uses win over the pack
```

## `voznativa review`

```text
usage: voznativa review [-h] --reviewer REVIEWER --out OUT [--ssh-key SSH_KEY] [--principal PRINCIPAL] original candidate

positional arguments:
  original
  candidate

options:
  -h, --help            show this help message and exit
  --reviewer REVIEWER   who is reviewing (a declared name; not verified)
  --out OUT             where to save the signed judgment JSON
  --ssh-key SSH_KEY     sign with your own SSH private key (ssh-keygen -Y) instead of the local
                        HMAC key; the project verifies it with the public key in its registry
  --principal PRINCIPAL
                        name of your key in allowed_signers (default: --reviewer)
```

## `voznativa rewrite`

```text
usage: voznativa rewrite [-h] [--profile PROFILE] [--set SET] [--budget BUDGET] [--task {rewrite,audit,create,profile,compare}] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] [--audience AUDIENCE] [--region REGION] [--region-strength REGION_STRENGTH] [--community COMMUNITY] [--slang-strength SLANG_STRENGTH] [--epoch EPOCH] [--fact FACT] [--voice-sample VOICE_SAMPLE] [--voice-channel VOICE_CHANNEL] [--repo REPO] [--document-profile DOCUMENT_PROFILE] [--attr NAME=VALUE] [--attrs-file ATTRS_FILE] [--context-proposal CONTEXT_PROPOSAL] [--protect PROTECT] [--protect-file PROTECT_FILE] [--cmd CMD] [--emulate] [--candidate CANDIDATE] [--judge-cmd JUDGE_CMD] [--api-url API_URL] [--api-model API_MODEL] [--api-key-env API_KEY_ENV] [--api-allow-remote] [--judge-api-url JUDGE_API_URL] [--judge-api-model JUDGE_API_MODEL] [--attempts ATTEMPTS] [--candidates CANDIDATES] [--timeout TIMEOUT] [--provider-env {inherit,minimal}] [--provider-env-allow PROVIDER_ENV_ALLOW] [--text-only] [--judge-votes JUDGE_VOTES] [--force] [--long-form {auto,on,off}] [--segment-words SEGMENT_WORDS] [--max-calls MAX_CALLS] [--docx-out DOCX_OUT] [--dry-run] [--mode {PRESERVE,REVIEW,PROOFREAD,POLISH,ADAPT}] [--rewrite-verse] text

positional arguments:
  text                  text to rewrite (or the request, with --task create)

options:
  -h, --help            show this help message and exit
  --profile PROFILE
  --set SET             explicit voice instruction as JSON
  --budget BUDGET
  --task {rewrite,audit,create,profile,compare}
  --genre GENRE
  --channel CHANNEL
  --register REGISTER
  --audience AUDIENCE
  --region REGION
  --region-strength REGION_STRENGTH
  --community COMMUNITY
  --slang-strength SLANG_STRENGTH
  --epoch EPOCH         reader's period: current, a year (1995) or a range (1994-1996)
  --fact FACT           fact source file (repeatable); never used for voice
  --voice-sample VOICE_SAMPLE
                        text the author wrote (repeatable); never used for facts
  --voice-channel VOICE_CHANNEL
  --repo REPO           repository used as a fact source
  --document-profile DOCUMENT_PROFILE
                        JSON file describing the document (type, authority, series, event year,
                        submission date); attaches the applicable standards
  --attr NAME=VALUE     open task attribute (repeatable), any name: tone=cordial, genre=roteiro de
                        podcast, purpose=convidar; a comma makes a list (genre=e-mail,post).
                        Context for the writer, never a rule that edits text; safety fields
                        (facts, protect, judge…) are refused
  --attrs-file ATTRS_FILE
                        JSON object of open task attributes (same rules as --attr)
  --context-proposal CONTEXT_PROPOSAL
                        JSON answer to `voznativa context --interpret-prompt` from an agent;
                        attributes without evidence are dropped and never override the user's
  --protect PROTECT     term that must survive verbatim (repeatable)
  --protect-file PROTECT_FILE
                        file with one protected term per line
  --cmd CMD             model command reading the prompt on stdin, e.g. "claude -p" (or 'cmd' in
                        the user config file)
  --emulate             system baseline via EMULATE_API_KEY
  --candidate CANDIDATE
                        pre-written candidate file (offline)
  --judge-cmd JUDGE_CMD
                        command used as semantic judge
  --api-url API_URL     chat-completions server, e.g. http://localhost:11434/v1 (Ollama) or
                        http://localhost:8080/v1 (llama.cpp); local addresses only unless --api-
                        allow-remote
  --api-model API_MODEL
                        model name for --api-url
  --api-key-env API_KEY_ENV
                        environment variable holding the API key, if the server needs one
  --api-allow-remote    allow --api-url to name a non-local host (the text leaves this machine)
  --judge-api-url JUDGE_API_URL
                        chat-completions server for the judge (default: --api-url)
  --judge-api-model JUDGE_API_MODEL
                        model for the judge on a chat-completions server
  --attempts ATTEMPTS   tries per text or unit (default 3)
  --candidates CANDIDATES
                        candidates per try (default 1)
  --timeout TIMEOUT     seconds per provider call (default 300)
  --provider-env {inherit,minimal}
                        environment for --cmd/--judge-cmd: all variables (default inherit) or only
                        what a CLI needs to start; minimal keeps unrelated credentials out of the
                        model process
  --provider-env-allow PROVIDER_ENV_ALLOW
                        variable kept with --provider-env minimal (repeatable), e.g.
                        ANTHROPIC_API_KEY
  --text-only
  --judge-votes JUDGE_VOTES
                        independent judge calls that must all say equivalent (default 2)
  --force               call the model even when the text has no editorial findings
  --long-form {auto,on,off}
                        rewrite unit by unit with a global validation (default auto: texts longer
                        than 1.5x --segment-words); protected blocks never reach the model
  --segment-words SEGMENT_WORDS
                        target words per unit (long form; default 600)
  --max-calls MAX_CALLS
                        provider call budget for a long document (default 800)
  --docx-out DOCX_OUT   with a .docx input: the new .docx to write (the original is never written;
                        protected paragraphs never reach the model)
  --dry-run             show the plan, units, call budget and effective configuration; start no
                        provider
  --mode {PRESERVE,REVIEW,PROOFREAD,POLISH,ADAPT}
                        editorial mode: PRESERVE/REVIEW never change the text and call no model;
                        PROOFREAD applies only high-confidence formal fixes; POLISH/ADAPT rewrite
  --rewrite-verse       allow verse blocks to be rewritten (otherwise they are protected)
```

## `voznativa rewrite-prompt`

```text
usage: voznativa rewrite-prompt [-h] [--profile PROFILE] [--set SET] [--budget BUDGET] [--task {rewrite,audit,create,profile,compare}] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] [--audience AUDIENCE] [--region REGION] [--region-strength REGION_STRENGTH] [--community COMMUNITY] [--slang-strength SLANG_STRENGTH] [--epoch EPOCH] [--fact FACT] [--voice-sample VOICE_SAMPLE] [--voice-channel VOICE_CHANNEL] [--repo REPO] [--document-profile DOCUMENT_PROFILE] [--attr NAME=VALUE] [--attrs-file ATTRS_FILE] [--context-proposal CONTEXT_PROPOSAL] [--protect PROTECT] [--protect-file PROTECT_FILE] [--inline-refs] text

positional arguments:
  text                  text to rewrite (or the request, with --task create)

options:
  -h, --help            show this help message and exit
  --profile PROFILE
  --set SET             explicit voice instruction as JSON
  --budget BUDGET
  --task {rewrite,audit,create,profile,compare}
  --genre GENRE
  --channel CHANNEL
  --register REGISTER
  --audience AUDIENCE
  --region REGION
  --region-strength REGION_STRENGTH
  --community COMMUNITY
  --slang-strength SLANG_STRENGTH
  --epoch EPOCH         reader's period: current, a year (1995) or a range (1994-1996)
  --fact FACT           fact source file (repeatable); never used for voice
  --voice-sample VOICE_SAMPLE
                        text the author wrote (repeatable); never used for facts
  --voice-channel VOICE_CHANNEL
  --repo REPO           repository used as a fact source
  --document-profile DOCUMENT_PROFILE
                        JSON file describing the document (type, authority, series, event year,
                        submission date); attaches the applicable standards
  --attr NAME=VALUE     open task attribute (repeatable), any name: tone=cordial, genre=roteiro de
                        podcast, purpose=convidar; a comma makes a list (genre=e-mail,post).
                        Context for the writer, never a rule that edits text; safety fields
                        (facts, protect, judge…) are refused
  --attrs-file ATTRS_FILE
                        JSON object of open task attributes (same rules as --attr)
  --context-proposal CONTEXT_PROPOSAL
                        JSON answer to `voznativa context --interpret-prompt` from an agent;
                        attributes without evidence are dropped and never override the user's
  --protect PROTECT     term that must survive verbatim (repeatable)
  --protect-file PROTECT_FILE
                        file with one protected term per line
  --inline-refs         embed reference text instead of paths
```

## `voznativa route`

```text
usage: voznativa route [-h] [--task {rewrite,audit,create,profile,compare}] [--genre GENRE] [--channel CHANNEL] [--register REGISTER] [--audience AUDIENCE] [--region REGION] [--region-strength REGION_STRENGTH] [--community COMMUNITY] [--slang-strength SLANG_STRENGTH] [--epoch EPOCH] [--fact FACT] [--voice-sample VOICE_SAMPLE] [--voice-channel VOICE_CHANNEL] [--repo REPO] [--document-profile DOCUMENT_PROFILE] [--attr NAME=VALUE] [--attrs-file ATTRS_FILE] [--context-proposal CONTEXT_PROPOSAL] text

positional arguments:
  text

options:
  -h, --help            show this help message and exit
  --task {rewrite,audit,create,profile,compare}
  --genre GENRE
  --channel CHANNEL
  --register REGISTER
  --audience AUDIENCE
  --region REGION
  --region-strength REGION_STRENGTH
  --community COMMUNITY
  --slang-strength SLANG_STRENGTH
  --epoch EPOCH         reader's period: current, a year (1995) or a range (1994-1996)
  --fact FACT           fact source file (repeatable); never used for voice
  --voice-sample VOICE_SAMPLE
                        text the author wrote (repeatable); never used for facts
  --voice-channel VOICE_CHANNEL
  --repo REPO           repository used as a fact source
  --document-profile DOCUMENT_PROFILE
                        JSON file describing the document (type, authority, series, event year,
                        submission date); attaches the applicable standards
  --attr NAME=VALUE     open task attribute (repeatable), any name: tone=cordial, genre=roteiro de
                        podcast, purpose=convidar; a comma makes a list (genre=e-mail,post).
                        Context for the writer, never a rule that edits text; safety fields
                        (facts, protect, judge…) are refused
  --attrs-file ATTRS_FILE
                        JSON object of open task attributes (same rules as --attr)
  --context-proposal CONTEXT_PROPOSAL
                        JSON answer to `voznativa context --interpret-prompt` from an agent;
                        attributes without evidence are dropped and never override the user's
```

## `voznativa rubric`

```text
usage: voznativa rubric [-h] --document-profile DOCUMENT_PROFILE text

positional arguments:
  text

options:
  -h, --help            show this help message and exit
  --document-profile DOCUMENT_PROFILE
                        JSON file: document_type, submission_date, authority/series, event_year
```

## `voznativa standards`

```text
usage: voznativa standards [-h] {list,resolve} ...

positional arguments:
  {list,resolve}
    list          registered sources with edition, validity and verification
    resolve       which source applies to a document on its submission date

options:
  -h, --help      show this help message and exit
```

### `voznativa standards list`

```text
usage: voznativa standards list [-h]

options:
  -h, --help  show this help message and exit
```

### `voznativa standards resolve`

```text
usage: voznativa standards resolve [-h] --document-type DOCUMENT_TYPE --submission-date SUBMISSION_DATE [--authority AUTHORITY] [--series SERIES] [--event-year EVENT_YEAR]

options:
  -h, --help            show this help message and exit
  --document-type DOCUMENT_TYPE
  --submission-date SUBMISSION_DATE
                        YYYY-MM-DD
  --authority AUTHORITY
  --series SERIES
  --event-year EVENT_YEAR
```
