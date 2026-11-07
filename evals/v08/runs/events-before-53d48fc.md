# Avaliação `events-v08`

- Estado: **COMPLETE**; revisão `53d48fcccd04`; VozNativa 0.7.0.dev1; Python 3.12.6
- Sistema avaliado: `voznativa-gate@0.7.0.dev1` (ENGINE_EXECUTED, determinístico, sem modelo)
- Integridade: `results_sha256` bce97c62b1c725a1…

## Não executado

- rewrite arms B0-B6: NOT_RUN — this dataset evaluates the gate and the planner on fixed pairs; arms that generate text need a provider and a budget (CP9)
- human review: NOT_RUN — no human reviewers in this run

## development (28 casos)

_desenvolvimento: o código foi ajustado até passar; não é generalização._

- Sensibilidade a risco semântico: 7/15 (46.7%; IC95% 24.8%–69.9%)
- Falso alarme em candidatas limpas: 2/13 (15.4%; IC95% 4.3%–42.2%)
- Status exato esperado: sem casos
- Contagens: detected 7, missed 8, false_alarm 2, correct_clear 11, abstained 0, not_applicable 0
- Aceitas sem identidade nem julgamento: 0

## prospective_holdout (24 casos)

_holdout prospectivo: congelado antes da mudança; mesmo autor, então não é independente._

- Sensibilidade a risco semântico: 5/12 (41.7%; IC95% 19.3%–68.0%)
- Falso alarme em candidatas limpas: 3/12 (25.0%; IC95% 8.9%–53.2%)
- Status exato esperado: sem casos
- Contagens: detected 5, missed 7, false_alarm 3, correct_clear 9, abstained 0, not_applicable 0
- Aceitas sem identidade nem julgamento: 0

Nenhum número acima é validação independente: todos os conjuntos foram escritos pelo desenvolvedor do engine, salvo indicação em contrário na tabela de entradas.

| Entrada | Split | Adaptador | Congelado | Independente | sha256 (LF) |
|---|---|---|---|---|---|
| `evals/events/cases-v08-dev.jsonl` | development | risk_sample | sim | não | `efbcadcf118d` |
| `evals/events/holdout-v08.jsonl` | prospective_holdout | risk_sample | sim | não | `68a09b8c4666` |
