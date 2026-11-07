# Avaliação `gate-and-planner-v08`

- Estado: **COMPLETE**; revisão `047276d9cdec`; VozNativa 0.7.0.dev1; Python 3.12.6
- Sistema avaliado: `voznativa-gate@0.7.0.dev1` (ENGINE_EXECUTED, determinístico, sem modelo)
- Integridade: `results_sha256` 4e8a5a4c892482d8…

## Não executado

- rewrite arms B0-B6: NOT_RUN — this dataset evaluates the gate and the planner on fixed pairs; arms that generate text need a provider and a budget (CP9)
- human review: NOT_RUN — no human reviewers in this run

## development (109 casos)

_desenvolvimento: o código foi ajustado até passar; não é generalização._

- Sensibilidade a risco semântico: 61/61 (100.0%; IC95% 94.1%–100.0%)
- Falso alarme em candidatas limpas: 0/17 (0.0%; IC95% 0.0%–18.4%)
- Status exato esperado: 109/109 (100.0%; IC95% 96.6%–100.0%)
- Contagens: detected 61, missed 0, false_alarm 0, correct_clear 17, abstained 0, not_applicable 31
- Aceitas sem identidade nem julgamento: 0

## frozen_regression (176 casos)

_regressão: casos congelados, mas escritos pelo desenvolvedor e já usados para corrigir; não é generalização._

- Sensibilidade a risco semântico: 85/89 (95.5%; IC95% 89.0%–98.2%)
- Falso alarme em candidatas limpas: 1/33 (3.0%; IC95% 0.5%–15.3%)
- Status exato esperado: 108/108 (100.0%; IC95% 96.6%–100.0%)
- Contagens: detected 85, missed 4, false_alarm 1, correct_clear 32, abstained 0, not_applicable 24
- Aceitas sem identidade nem julgamento: 0
- Chamou o modelo quando devia: 14/14 (100.0%; IC95% 78.5%–100.0%)
- Chamadas desnecessárias: 1/16 (6.2%; IC95% 1.1%–28.3%)
- Decisão exata: 28/30 (93.3%; IC95% 78.7%–98.2%)

Nenhum número acima é validação independente: todos os conjuntos foram escritos pelo desenvolvedor do engine, salvo indicação em contrário na tabela de entradas.

| Entrada | Split | Adaptador | Congelado | Independente | sha256 (LF) |
|---|---|---|---|---|---|
| `evals/semantic/cases.jsonl` | development | semantic_suite | não | não | `66bb3ca8f493` |
| `evals/semantic/relations.jsonl` | development | semantic_suite | não | não | `22192553b37b` |
| `evals/semantic/holdout.jsonl` | frozen_regression | semantic_suite | sim | não | `ae479a2cc1c2` |
| `evals/semantic/holdout2.jsonl` | frozen_regression | semantic_suite | sim | não | `3981a4ef2018` |
| `evals/semantic/holdout-relations.jsonl` | frozen_regression | semantic_suite | sim | não | `ba5910076817` |
| `evals/semantic/holdout-v030.jsonl` | frozen_regression | semantic_suite | sim | não | `09c1b3dda119` |
| `evals/semantic/holdout-v040.jsonl` | frozen_regression | semantic_suite | sim | não | `fb4a9738605e` |
| `evals/predicates/cases-h07.jsonl` | frozen_regression | risk_sample | sim | não | `b08827c53b3a` |
| `evals/decision/cases.jsonl` | frozen_regression | decision_suite | sim | não | `e3667c609cc8` |
