# Protocolo de avaliação (v0.8)

Como o VozNativa mede o que faz, e o que cada número pode e não pode dizer. Implementação: [`voznativa/evaluation.py`](../../voznativa/evaluation.py) e `voznativa evaluate`. Os runners antigos continuam (`voznativa eval` para uma suíte, `scripts/bench_v4.py`/`bench_v5.py`, `scripts/predicate_eval.py`); o núcleo da v0.8 lê as mesmas suítes no lugar, sem copiá-las nem editá-las.

## Rodar

```bash
voznativa evaluate evals/v08/datasets/gate-and-planner.json --out run.json --report run.md
voznativa evaluate --verify run.json      # coerência interna: exit 1 se resumo ou métricas não batem
voznativa evaluate --replay run.json      # reexecuta na revisão gravada: 0 REPRODUCED, 1 DIFFERENT, 3 NOT_REPLAYABLE
```

`--verify` **não** prova autenticidade: `results_sha256` é um resumo de integridade, não uma assinatura, e quem edita os resultados pode recalculá-lo. `--replay` reexecuta com o código e as entradas da revisão: prova reprodutibilidade nesta máquina, não autoria nem independência. Detalhes e o vazamento encontrado: [`INDEPENDENCE_AND_LEAKAGE.md`](INDEPENDENCE_AND_LEAKAGE.md).

Exit 0 só com estado `COMPLETE`. `INVALID` (especificação errada, arquivo congelado alterado, independência inventada) e `INCOMPLETE` (uma fonte ilegível) saem com 1 e nunca viram PASS.

## Conjunto de dados

Um `voznativa.eval_dataset` lista fontes: caminho relativo ao repositório (sem `..` nem caminho absoluto), adaptador (`semantic_suite`, `risk_sample`, `decision_suite`) e split. O split precisa concordar com o `MANIFEST.json` da própria suíte:

| Split | Significado | Pode ser alegado como |
|---|---|---|
| `frozen_regression` | congelado, já usado para corrigir | regressão |
| `development` | o código foi ajustado até passar | desenvolvimento |
| `prospective_holdout` | congelado antes da mudança, mesmo autor | holdout do desenvolvedor, não independente |
| `external_independent_holdout` | preparado ou validado por outra pessoa, com custódia | validação independente; **recusado** sem `independent: true` **e** um bloco `independence_evidence` cujo commit de congelamento contenha o arquivo com o hash do MANIFEST |
| `adversarial` | metamórfico e ataques | robustez |
| `real_provider_study` | provider real ou pessoas, com autorização | estudo; exige consentimento e orçamento |

Arquivo congelado é comparado com o sha256 do MANIFEST (com LF, para Windows e Linux concordarem); se mudou, o run é `INVALID`. Caminho que sai da raiz por link simbólico ou junção também é `INVALID`. Um texto compartilhado entre um holdout (`prospective_holdout`, `external_independent_holdout`) e outra fonte invalida o run; entre outros splits, a ligação é contada e listada (`leakage`).

## Eixos

Cada eixo é reportado à parte e **por split**; não existe nota única nem soma de splits.

| Eixo | Pergunta | Contagens |
|---|---|---|
| `semantic_risk` | o gate sinalizou (`fail` ou `review_required`) a candidata que muda o sentido e deixou passar a limpa? | `detected`, `missed`, `false_alarm`, `correct_clear`, `abstained`, `not_applicable` |
| `status_agreement` | o status exato é um dos esperados pelo caso? | concorda / discorda; casos sem status esperado ficam fora do denominador |
| `decision` | o planner chamou o modelo só quando devia? | `called_when_needed`, `missed_call`, `unnecessary_call`, `stayed_out_correctly` |

Taxas vêm com numerador, denominador e intervalo de Wilson de 95%. `not_applicable` (caso cujo status esperado mistura limpo e inseguro) não entra em denominador nenhum, mas é contado. Também é contado quantas candidatas foram aceitas sem identidade nem julgamento; o esperado é zero.

## Registro do run

`voznativa.eval_run` guarda revisão, árvore suja ou não, versão, Python e SO, o sha256 de cada entrada e da especificação, o sistema avaliado com o nível de evidência (`ENGINE_EXECUTED`), os braços não executados (`NOT_RUN` e o motivo), os resultados por caso **sem os textos** (só sha256) e `results_sha256`. `verify_run` recalcula o resumo e as métricas: um resultado editado, uma métrica inflada, um braço promovido de `NOT_RUN` ou um `COMPLETE` com problemas são apontados.

Níveis de evidência: `ENGINE_EXECUTED`, `AGENT_OBSERVED`, `EXTERNAL_VERIFIED`, `EXTERNAL_UNVERIFIED`, `DECLARED`, `INFERRED`, `HUMAN_OBSERVED`, `NOT_RUN`. Relatório importado não vira execução própria; juiz LLM precisa de identidade e da relação com o gerador.

## O que este protocolo ainda não cobre

- Braços que geram texto: a interface comum existe (`voznativa/arms.py`: B0 original e B2 determinístico rodam offline; B1, B3, B4 e B5 precisam de provider; B6 de ferramenta autorizada). Com stub de teste a evidência é `SYNTHETIC_FIXTURE`; com provider real, só no CP9 e com autorização.
- Revisão humana cega e holdout independente: dependem de pessoas reais; `NOT_RUN`.
- Eixos de qualidade editorial, voz, região e estrutura de documento longo: CP7/CP8.
