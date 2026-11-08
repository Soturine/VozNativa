# VozNativa — Design Specification

> **Estado: histórico (v0.1–v0.3).** Tese de produto e especificação inicial, mantidas como registro. Arquitetura vigente: [v08/ARCHITECTURE.md](v08/ARCHITECTURE.md).

## Product thesis

VozNativa separates three different problems:

1. parecer menos mecânico;
2. soar natural em português brasileiro;
3. soar como **esta pessoa neste contexto**.

The third problem has priority when author samples exist.

## Functional pipeline

```text
INPUT
  -> Context Router
  -> Semantic Ledger / Fact Lock
  -> Deterministic Analyzer
  -> Pattern / Register Analysis
  -> Voice Stack
  -> Rewrite Engine
  -> Validation Gates
  -> OUTPUT
```

### Context Router

Classify, when relevant:

- academic;
- work/corporate;
- email;
- documentation;
- LinkedIn/social;
- conversation/WhatsApp;
- report;
- article;
- spoken script;
- technical;
- journalistic;
- marketing;
- literary.

### Semantic preservation

Protected content includes, at minimum:

- facts and supported claims;
- names;
- numbers;
- dates;
- citations and source attribution;
- URLs;
- code and identifiers;
- technical terminology;
- causal relations;
- negation;
- temporal state;
- modality such as may/must/can/probably;
- author intent.

Naturalness cannot override fidelity.

### PT-BR pattern families

Patterns are contextual evidence, never absolute blacklists:

- ENEM-like generic openings;
- bureaucratic/oficialês register outside its genre;
- corporate gerundism;
- excessive nominalization;
- mechanical use of "visando" / "a fim de";
- stacked formulaic connectors;
- repetitive mini-conclusions;
- excessively uniform paragraph shape;
- topic + explanation + mini-conclusion repeated mechanically;
- excessive abstract nouns;
- avoidance of simple verbs such as ser/ter/fazer;
- needless formal synonym rotation;
- literal translation from English;
- inconsistent PT-BR / PT-PT mixing;
- repetitive contrast formulas;
- excessive hedging;
- forced triads;
- unsupported promotional adjectives;
- obligatory optimistic closing;
- dramatic hooks/closers without informational value;
- formatting-by-rule.

### Registers

Supported design targets:

- colloquial;
- casual;
- professional;
- professional-natural;
- technical;
- academic;
- journalistic;
- marketing;
- spoken/script;
- personalized voice.

Humanizing an academic text does not mean making it slang-heavy. Humanizing WhatsApp does not mean writing like an official memo.

## Voice Stack

Default precedence:

```text
author samples
  > channel/context
  > community/sociolect
  > regional variation
  > pt-BR default
```

### Idiolect

Voice Profile may observe:

- sentence length and variance;
- paragraph shape;
- punctuation;
- recurring lexicon;
- avoided lexicon;
- preferred openers;
- preferred connectors;
- contractions;
- foreign terms;
- emoji habits;
- capitalization;
- self-correction;
- abbreviations;
- channel-specific differences.

Observed features must not be converted into guesses about identity.

## Regional variation

"Sotaque escrito" is shorthand. Written regionality primarily models:

- lexical variation;
- syntactic/morphosyntactic variation;
- forms of address;
- discourse markers;
- pragmatics;
- contractions;
- stylized spelling when explicitly appropriate;
- rhythm and explicitness.

Region is not equivalent to state-wide stereotypes. Packs may distinguish city/interior/capital only when supported by evidence.

Regionality is distribution, not decoration.

## Communities

Community vocabulary is separate from region. Planned packs include:

- tech;
- gaming;
- academia;
- engineering;
- corporate;
- legal;
- marketing;
- streaming;
- Discord/online communities.

A community pack is compositional and must not override author samples.

## Temporal slang

Slang entries are versioned observations with:

- term;
- region(s);
- community;
- contexts;
- observed_from / observed_until;
- register band;
- confidence;
- do_not_force;
- sources/provenance.

A term that was natural in 2014 is not automatically natural in 2026.

## Guards

### Semantic Guard
Checks protected content and, in future, claim-level meaning.

### False Positive Guard
Prevents the system from "correcting" legitimate author or genre choices.

### Regional Overfit Guard
Detects slang stuffing, repeated markers and caricature.

### Dialect Mixing Guard
Flags unsupported regional mixing while allowing real mixed repertoires when samples/context support them.

### Voice Drift Guard
Compares windows of long-form text and flags unexplained style changes.

## Audit mode

Audit should report operational dimensions rather than AI authorship probability:

- mechanicality;
- formulaicity;
- unnecessary formality;
- generic phrasing;
- formulaic connectors;
- repetitive parallelism;
- promotional tone;
- voice drift;
- regional overfit;
- register mismatch;
- semantic loss.

These are framework measurements, not proof of who wrote the text.

## Evaluation matrix

Evals are organized by:

- academic;
- WhatsApp;
- LinkedIn/social;
- corporate;
- technical;
- documentation;
- storytelling/literary;
- regional;
- slang;
- false-positive;
- adversarial;
- long-form drift.

Every candidate evaluation should separate:

- meaning preservation;
- fact preservation;
- voice preservation;
- naturalness;
- register correctness;
- PT-BR correctness;
- hallucination;
- over-humanization;
- under-humanization.

## Deterministic vs generative responsibilities

Deterministic code should handle what can be counted or compared reliably:

- sentence/paragraph metrics;
- punctuation counts;
- repeated openers;
- connector frequency;
- gerund/adverb patterns;
- lexical repetition;
- numeric/date/URL/citation spans;
- protected-span invariants;
- windowed style measurements.

The LLM handles:

- intention;
- tone;
- irony;
- register interpretation;
- pragmatic fit;
- semantic relations;
- rewriting.

## Evidence and corpus policy

Potential research sources include ALiB, NURC, Corpus Carolina/USP and other compatible corpora.

Do not import corpus content blindly. Every dataset or derived pack requires:

- provenance;
- license review;
- scope/population;
- time period;
- limitations;
- validation method.

## Non-goals

- AI detector evasion;
- authorship probability;
- identity inference from writing;
- dialect classification presented as fact;
- caricature-based regionalization;
- copying third-party taxonomies verbatim when independent design is possible.
