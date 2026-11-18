# Migração para a v0.10

## Juízo de modelo com relação desconhecida não aprova mais (CP6, D-02)

**Antes (até 0.9.0).** Um juízo `llm` com `generator_relation` ausente ou `unknown` e veredito `equivalent` levava `no_deterministic_issues` a `accepted_by_llm`. Dois comandos sem modelo declarado davam `unknown`, mesmo quando rodavam o mesmo modelo (V010-GAP-01).

**Agora.** Relações: `same_agent`, `same_model`, `same_vendor`, `different_model`, `different_provider`, `independence_verified`, `unknown`.

| Relação | Como o engine chega nela | `equivalent` aprova? |
|---|---|---|
| `same_agent` | mesmo objeto, mesma linha de comando, ou mesmo agente CLI sem modelo declarado | não (autoavaliação) |
| `same_model` | modelos declarados iguais (antes era `same_agent`) | não |
| `same_vendor` | modelos diferentes do mesmo fornecedor (prefixo do modelo ou CLI do fornecedor) | sim, com `judge_independence.level = partial` no relatório |
| `different_model` | modelos diferentes, fornecedor não observável | sim, `partial` |
| `different_provider` | fornecedores diferentes observados | sim |
| `independence_verified` | só em juízo entregue à mão com `independence_evidence` preenchido; o engine nunca a produz | sim (`declared`) |
| `unknown` | nada observável | **não** (vira `agent_assessment`, `requires: independent_judgment`) |

`not_equivalent` e `uncertain` continuam valendo de qualquer fonte (só tornam o resultado mais seguro).

**O que fazer.** Declare o modelo do escritor e do juiz: `--model` na linha de comando do agente (`claude -p --model …`), `--api-model`/`--judge-api-model` no adapter HTTP. Um juízo escrito à mão (`compare --judgment`) precisa dizer a relação. Quem escrevia `generator_relation: different_model` não muda nada.

## Diagnóstico (schema 2)

Cada diagnóstico ganhou `status` e `recommend_edit`; `class`, `type`, `action` e `fix` continuam iguais. O planner passa a planejar edição só para `ERROR_CONFIRMED` (antes: `formal_error` de quatro tipos; agora os mesmos quatro mais `daqui_ha`, `nonstandard_subjunctive`, `menas`, `a_gente_plural`).

## Contrato de contexto

Sem `--attr`/`--attrs-file`/`--context-proposal`, o contrato do router é idêntico ao da 0.9.0. Com eles, ganha o campo `task_context`.

## Resultado de `rewrite`

Ganha `knowledge` (ids das entradas de conhecimento que o escritor viu, papel, motivo, fontes). Campos existentes inalterados.
