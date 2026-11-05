# Plano v0.5.0 — Regional Evidence (com o hardening da v0.4.0)

Versão durante o desenvolvimento: `0.5.0.dev0`. **Código implementado não é versão qualificada.** Baseline: `evals/baselines/v0.4.0-hardening-start.json` (`4044cfc`). Registro por checkpoint: `evals/assurance/CHECKPOINTS.md`.

## Hardening da v0.4.0 (CP4) — implementado e testado

H1 runner de qualificação; H2 eixos de desfecho do benchmark; H3 determinações de `dc-021`/`dc-029` (sem ajuste de limiar); H4 ledger (probe 19/29 → 25/29); H5 desempenho (10× no `compare`, 45× no loop sem modelo); H6 privacidade. Detalhes e commits: `evals/assurance/CHECKPOINTS.md`, `CHANGELOG.md`.

## v0.5.0 — Regional Evidence

| WP | Estado | Evidência |
|---|---|---|
| Fontes primárias e registro | **feito** para ALiB, SP2010, C-ORAL-BRASIL, ALIP, PHPB, Carolina, NURC; só achados publicados do ALiB aceitos | `docs/REGIONAL_EVIDENCE.md` |
| Contrato versionado de pack | **implementado e testado** (validação, recusa de pack inválido) | `voznativa/regional.py`, `evals/test_regional.py`, ADR-0001 |
| Piloto | **implementado**; 1 referente, Região Norte, confiança baixa, `human_reviewed: false` | `br-norte-lex-mandioca.yml` |
| Integração (router, Voice Contract, Voice Profile, planner, overfit/mixing, ledger, CLI, Skill) | **implementado e testado** | `evals/test_regional.py` (15 testes, 3 controles negativos mortos) |
| Avaliação regional humana | **NOT_RUN**; protocolo pré-registrado | `evals/reviewers/PROTOCOL_v0.5.md` |
| Benchmark v3 | **congelado, NOT_RUN** (sem CLI de modelo no ambiente; orçamento não aprovado) | `benchmarks/manifests/ptbr-bench-v3.json`, `evals/test_bench_v3_harness.py` |
| Pesquisa competitiva | **feita** com decisões ADOPT/ADAPT/REJECT/MONITOR | `docs/COMPETITIVE_ANALYSIS_v0.5.md` |
| Dogfood cruzado | **feito e encaminhado** (Assertiva PR #8, Engine PR #3), nada corrigido lá | `evals/assurance/DOGFOOD.md` |

## Critérios para qualificar a v0.5.0

| Critério | Estado |
|---|---|
| 1. Gates locais (`scripts/qualify.py`) PASS no Windows e no Linux, Python 3.11–3.13 | ver `evals/qualification/` (registro do CP10) |
| 2. Sem regressão; holdouts congelados intactos e sem falso verde | gate `semantic:holdouts:*` |
| 3. `ptbr-bench-v3` executado oficialmente, com resultado por eixo e por braço | **NOT_RUN** |
| 4. Avaliação regional humana com revisores da região | **NOT_RUN** |
| 5. Herdados: holdout independente, revisão humana cega, CI verde | **abertos** (CI BLOCKED por cobrança) |

**A v0.5.0 não está qualificada** e continua `0.5.0.dev0`.
