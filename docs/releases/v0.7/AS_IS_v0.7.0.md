# Inventário AS-IS no início da v0.7.0 (2026-11-06, `bf8e1a4`)

> **Estado: histórico (v0.7).** Inventário do início daquela rodada; o atual é [v08/AS_IS.md](../v0.8/AS_IS.md).

Estados como em `docs/releases/v0.6/AS_IS_v0.6.0.md`: IMPLEMENTED, PARTIAL, BROKEN, UNCALIBRATED, NOT_RUN, EXTERNAL_BLOCKED. A classificação vem do código e das execuções desta sessão; números da v0.6 só valem com o SHA e o instrumento que os produziram.

## Baseline executada nesta sessão

| Item | Valor | Instrumento |
|---|---|---|
| Revisão | `bf8e1a4c4bf501b5c096ca1feb3eb41db26a3543` = `origin/main` = `origin/v0.6.0-dev`; árvore limpa | `git fetch --prune`, `git rev-parse` |
| Versão | `0.6.0.dev0` | `voznativa.__version__` |
| Sistema | Windows 11, CPython 3.12.10 (instalação do usuário, sem venv), PyYAML 6.0.3, build 1.6.1 | `scripts/qualify.py` |
| Testes | 460 executados: 457 PASS, 3 `expectedFailure` (G1, G2, G3), 0 skip | `qualify.py` gate `unittest` (31 s) |
| Suítes congeladas | semântica dev 77/77; holdouts 24/24, 16/16, 24/24, 32/32, 12/12 (seguros e estritos); decisão 28/30 (`dc-021`, `dc-029` conhecidos); router 15/16 (`rt-014` conhecido) | `qualify.py` |
| CLI e pacote | exit codes PASS; sdist → wheel → venv limpo → smoke fora do checkout PASS | `qualify.py` |
| Veredito local | INCOMPLETE (exit 3): `review:pty` NOT_RUN no Windows; CI, holdout independente e revisão humana NOT_RUN | `qualify.py --scope local` |
| CI remota | último run real: #123 em `40e19e4` (push, 8/8). Nenhum run em `bf8e1a4` | `gh run list -R Soturine/VozNativa` |
| Workflows | um arquivo (`.github/workflows/ci.yml`), gatilho único `workflow_dispatch` | leitura |
| Ferramentas | Assertiva 0.10.1 (`2618d95` = `origin/main`); Derivanta Engine 0.1.0 `17fa564` (= `origin/main`); Framework `218761d`. PR Assertiva #8 (`3d55391`) e Engine #3 (`d38214d`) abertas | `git fetch`, `gh pr view` |

## Corpora (33 fontes registradas)

| Estado | Fontes |
|---|---|
| EVALUATION_INTEGRATED | `ud-portuguese-bosque`, `b2w-reviews01` (prefixo ~8 MB), `machado-de-assis-corpus` (prefixo ~6 MB) |
| ACCESS_VERIFIED | `corpus-carolina` (licença por documento), `coraa-asr` (licença desconhecida) |
| SOURCE_VERIFIED | 13 |
| CATALOGUED | 15 |

Gêneros com texto integrado: notícia (Bosque), avaliação de produto (B2W), literatura do séc. XIX (Machado). Sem chat real, e-mail, acadêmico, jurídico, técnico, fala transcrita ou fórum.

## Mapa de interfaces e dados

```
Input ─▶ router.route (Context Contract v1) ─▶ ledger.build ─▶ patterns.detect + community.apply_to_report
      ─▶ planner.plan (NO_CHANGE sem modelo) ─▶ contract.resolve (Voice Stack) ─▶ engine.build_prompt
      ─▶ providers.generate ─▶ engine.validate_candidate (compare + guards) ─▶ retry | judge ─▶ result
```

- Corpus Evidence entra fora do caminho online: calibração de padrões (`scripts/corpus_calibrate.py`), atestação de gíria (`scripts/slang_attest.py` → `data/slang/attestations.yml`), controle literário (`scripts/corpus_longform.py`).
- `longform.py` (segmentação, dependências, política literária) **não** é chamado por `engine.py` nem pelo CLI `rewrite`: G4.
- Benchmarks (`voznativa/benchmark.py`, `scripts/bench_v*.py`) consomem o engine como caixa-preta.

## Componentes que a v0.7 toca

| Componente | Estado | Lacuna |
|---|---|---|
| Router (`router.py`) | IMPLEMENTED (contrato v1, gênero/canal/registro) | G1: quebra dura + `--` lida como WhatsApp; dimensões de época, variedade, região, estrutura não separadas; `unknown` sem proteções conservadoras |
| Dedup/splits (`corpus/processing.py`) | IMPLEMENTED (MinHash/Jaccard simétrico) | G2: contenção capítulo⊂romance não detectada |
| Gíria temporal (`temporal.py`) | IMPLEMENTED (léxico v2) | G3: "de boa" + palavra não detectado; 33 mutantes não triados |
| Long-form (`longform.py`) | PARTIAL | G4: sem reescrita por segmentos, sem validação global |
| Qualificação (`scripts/qualify.py`) | IMPLEMENTED | `ci:github-actions` aceita um JSON editável como prova única (VN07-DISC-002) |
| Corpus ingestion | IMPLEMENTED p/ CoNLL-U, CSV/TSV, JSONL, TXT, gzip/zip | sem TEI/XML |
| Detectores de IA externos | ausente | CP11 |
| Auditoria Unicode / proveniência | ausente | CP12 |

## O que **não** é novidade da v0.7

Provider adapter, router executável, retries, seleção, `compare`, esquemas JSON com `kind`/`schema_version`: existem desde a v0.3–v0.6 (`ROADMAP.md`, seção "v0.7 — Rewrite Engine Contract" marcada `[x]`). A v0.7.0 evolui esses contratos, não os reimplementa.
