# ptbr-bench-v5 e avaliação fora de distribuição (v0.7.0, CP10)

> **Estado: histórico (execução da v0.7).** Registro daquela rodada, não reescrito; a rodada atual está em [v08/EXECUTION_STATE.md](../v0.8/EXECUTION_STATE.md).

## Protocolo

- Suítes congeladas anteriores (v1–v4, holdouts) **não foram editadas**. O v4 foi reexecutado sem mudança de casos: 21/22 → 22/22 (o caso que passou a passar, `bv4-sl-03`, deu origem ao G3; a melhora não é evidência independente).
- `ptbr-bench-v5`: 36 casos sintéticos próprios, congelados com hash no commit `36dd20c` **antes de o runner existir** (`benchmarks/manifests/ptbr-bench-v5.json`, `cases_sha256 ab3f8125…`). O runner recusa rodar se o hash divergir.
- Eixos: gênero (e-mail, chat, notícia, técnico, jurídico, acadêmico, fórum, administrativo, corporativo, social, literatura, poesia, transcrição oral, relatório, avaliação), época (contemporânea, histórica), variedade (PT-BR, PT-BR não padrão, PT-PT como controle), extensão (frase, parágrafo, página, documento), tarefa (NO_CHANGE, revisão leve, mudança de canal, preservação, revisão, PROOFREAD).
- Métricas **separadas** por família (roteamento, proteções, decisão/falsa edição, porta semântica, gíria, variedade, long-form, diagnóstico), cada uma com intervalo de Wilson e com o **pior grupo** de cada eixo. Sem pontuação combinada.
- Braços com modelo, revisão humana e holdout independente: **NOT_RUN** (sem orçamento aprovado; sem revisores; sem autor externo).

## Resultados

| Rodada | Revisão | Casos | Família abaixo de 100% |
|---|---|---|---|
| 1ª execução (oficial, árvore limpa) | `e634a3b` | **34/36** | roteamento 14/16 |
| após correção | ver `benchmarks/runs/` (commit do CP10) | 36/36 | — (não independente para 2 casos) |

Por família na 1ª execução: decisão 13/13 (inclui 9 textos naturais que não devem ser editados e 2 rascunhos formulaicos que devem), porta semântica 9/9 (negação, número, condição, tempo verbal, negação deslocada entre parágrafos, modalidade; e dois controles que não podem falhar: reordenação e passiva), long-form 5/5 (sem perda e blocos protegidos, inclusive CRLF), gíria 4/4, variedade 4/4, diagnóstico 4/4, proteções 2/2.

As duas falhas da 1ª execução:

| Caso | Observado | Determinação | Correção |
|---|---|---|---|
| `bv5-nc-email` | gênero `unknown` (esperado `email`) | lacuna de implementação: a pista de fechamento só conhecia "Abraços" no plural | `(um )?abra[cç]os?` |
| `bv5-lit-hist-wrapped` | `time_of_text` `unknown` | lacuna: "janellas" e "Sahiram" fora da lista pré-reforma; só "elle" casou | formas `janella(s)`, `sahir/sahiu/sahiram/sahia`, `cavallo(s)` |

Nenhuma das duas falhas era perigosa: o roteador se absteve (`unknown`) em vez de errar.

## Regressão resolvida × desempenho em dados novos

O 36/36 pós-correção **não** é prova de generalização: as duas falhas da 1ª execução foram lidas e corrigidas, então esses dois casos deixaram de ser dados novos. O que conta como medida em dados não vistos é a **1ª execução (34/36)**, e mesmo ela é de casos escritos pelo mesmo agente que escreveu as regras. Desempenho em dados genuinamente novos (autores e fontes não usados para desenhar nada) continua sem medida independente: holdout de outra pessoa NOT_RUN.

## Experimentos fora de distribuição com dados reais

| Experimento | Estado | Evidência |
|---|---|---|
| Cross-corpus (7 fontes independentes, 6 domínios) | executado | `evals/corpus/runs/crossgenre-2026-11-06*.json` (`docs/releases/v0.7/V07_CORPUS_INTEGRATION.md`) |
| Transferência entre gêneros da morfologia verbal (notícia, blog, acadêmico, tweets) | executado | `evals/linguistics/runs/morph-2026-11-06.json` |
| Falsos positivos de diagnóstico em texto humano por fonte | executado | `evals/linguistics/runs/diagnose-2026-11-06.json` |
| Auditoria da abstenção do roteador (precisão das emitidas, cobertura útil, por fonte e tamanho) | executado | `evals/corpus/runs/router-audit-2026-11-06.json` |
| Invariância de formatação (CRLF, NFD, NBSP, quebras, tab, espaço duplo) | executado | `evals/test_global_guards.py`, `evals/test_router_v3.py` |
| Leave-one-author-out | NOT_RUN | só Machado tem autor declarado; os outros corpora não informam autoria |
| Leave-one-period-out | NOT_RUN | uma única fonte histórica (Machado); sem amostra para separar períodos |
| Transferência entre comprimentos com modelo | NOT_RUN | sem braço com modelo |

## Limites

n pequeno por grupo (muitos grupos com n = 1–3); casos, regras e runner do mesmo agente; o benchmark mede conformidade com a especificação, não qualidade para leitores. Nenhuma alegação de generalização além dos gêneros e variedades medidos.
