# Avaliação da v0.9 (CP7): antes × depois, braços, mutação

Objetivo: mostrar o que mudou entre a `v0.8.1` e a v0.9 com os **mesmos instrumentos**, eixo por eixo, sem somar nada num "score". Todos os conjuntos foram escritos pelo mesmo agente que escreveu as regras; nenhum número aqui é julgamento humano ou avaliação independente.

## Método

- `scripts/v09_before_after.py --before <checkout da v0.8.1>`: roda o engine de cada versão sobre os **mesmos dados** (os do checkout atual, com congelados byte-idênticos). Registro: `evals/v09/runs/before-after-2026-11-18.json`.
- `scripts/v09_prospective_eval.py`: conjuntos da v0.9 congelados antes das regras ([SEMANTICS.md](SEMANTICS.md)).
- `scripts/v09_arms.py`: braços com o **mesmo modelo** e os mesmos textos. Registro: `evals/v09/runs/arms-haiku-2026-11-18.json`.
- `scripts/experiments/v09_cp7_mutants.py`: mutação dirigida das salvaguardas novas, numa worktree descartável. Registro: `evals/assurance/runs/2026-11-18-v09-cp7/MUTANTS.json`.
- Intervalos: Wilson 95% onde o Evaluation Core os calcula; amostras pequenas, intervalos largos.

## Preservação semântica (falsos verdes e falsos vermelhos)

| Conjunto | `v0.8.1` sensibilidade | v0.9 sensibilidade | `v0.8.1` falso alarme | v0.9 falso alarme |
|---|---|---|---|---|
| gate-and-planner, development | 61/61 | 61/61 | 0/17 | 0/17 |
| gate-and-planner, regressão congelada | 86/89 (0,906–0,988) | **88/89** (0,939–0,998) | 1/33 | 1/33 |
| eventos (v0.8), development | 14/15 | **15/15** | 2/13 | 2/13 |
| eventos (v0.8), holdout | 11/12 | 11/12 | 3/12 | **2/12** |
| amostra de predicados (v0.7) | 17/20 | **19/20** | 1/18 | 1/18 |
| v0.9 semântico, development | 4/31 | **31/31** | 7/20 | **4/20** |
| v0.9 semântico, holdout (uma execução) | 4/18 | **18/18** | 1/10 | 2/10 (1/10 após correção pós-holdout) |
| `ptbr-bench-v4` / `ptbr-bench-v5` | 22/22 / 36/36 | 22/22 / 36/36 | — | — |

## Diagnóstico (erros de alta confiança)

| Conjunto | `v0.8.1` | v0.9 |
|---|---|---|
| v0.9 diagnóstico, development: erros / falsos alarmes | 0/11 / 0/11 | **11/11** / 0/11 |
| v0.9 diagnóstico, holdout | 0/6 / 0/6 | **6/6** / 0/6 |

## Edição desnecessária (texto que já está bom)

| Instrumento | `v0.8.1` | v0.9 |
|---|---|---|
| planner sobre os 49 textos que as suítes congeladas marcam como "não mudar" | 2/49 com plano de edição | 2/49 (os mesmos: `dc-029`, `pt-204`) |
| braço A2 (engine) sobre 6 textos bons, modelo real | — | 0/6 alterados |

## Braços com modelo real (mesmo modelo, mesmos textos)

12 textos sintéticos (`evals/v09/arms/texts.jsonl`): 6 com fórmulas e restrições, 6 já bons (WhatsApp, e-mail, técnico, acadêmico, literário, aviso). Modelo `claude-haiku-5-5` nos dois braços, sem ferramentas, ambiente mínimo; uma execução por braço; 18 chamadas, **US$ 0,021**.

| Braço | Textos bons alterados | Fórmulas restantes nos 6 que precisavam | Sinal crítico | Textos com sinal major/crítico | Chamadas |
|---|---|---|---|---|---|
| A0 original | 0/6 | 12 | 0 | 0 | 0 |
| A1 LLM direto (uma instrução, sem plano nem gate) | **6/6** | 4 | 1 | 5 | 12 |
| A2 engine (`rewrite`) | **0/6** | 0 | 0 | 0 | 6 |

Leitura com cuidado:

- O eixo semântico usa o próprio `compare` do engine, que o braço A2 já precisa satisfazer: ele é favorecido por construção. Lendo as 5 saídas sinalizadas do A1 (avaliação do agente, `AGENT_OBSERVED`): **1 mudança real** ("vale" → "passa a valer" e "Nesse sentido" → "Por isso", acréscimo de início e de causa) e **4 falsos alarmes** do `compare` ("será feita" → "será", "vai ser" → "é", crases de código em `data`, "a tarde inteira" → "a tarde toda"). Não é correto dizer que o LLM direto foi 5× pior em sentido.
- O que a medição sustenta: o LLM direto **alterou todos os textos que não precisavam mudar** (inclusive o literário e uma mensagem de WhatsApp) e deixou fórmulas em 4 casos; o engine não chamou o modelo nos 6 textos bons (`no_change` pelo planner) e removeu as fórmulas dos outros 6.
- Naturalidade, clareza e voz não foram medidas por pessoas: **NOT_RUN**. Os textos de saída estão no registro para um juiz ou um revisor.

## Eixos não medidos nesta rodada

| Eixo ou braço | Estado | Motivo |
|---|---|---|
| juiz de outro fornecedor | NOT_RUN | só um fornecedor de modelo disponível nesta máquina |
| revisão humana cega | NOT_RUN | sem revisores cadastrados (`evals/reviewers/registry.json` vazio) |
| holdout independente | NOT_RUN | ninguém além do agente escreveu conjuntos |
| braço Skill-only e engine com memória editorial em documento longo, várias execuções | NOT_RUN | uma execução por braço foi feita no CP3 ([EDITORIAL.md](EDITORIAL.md)); repetir com n suficiente fica para depois da release |
| detectores de IA (H0/H1/A0/A1) | NOT_RUN | sem acesso a detectores reais autorizado; a infraestrutura só mede, nunca otimiza evasão |
| latência e custo por braço | medido acima (chamadas, US$); latência por texto no registro | — |

## Mutação dirigida (CP7.7)

20 mutantes nas salvaguardas da v0.9 (qualificadores, classes de evento, governadores de estado, sinônimos na mesma classe, leitura de substantivo, relação gerador × juiz, diagnóstico gramatical, DOCX, envelope de packs, configuração, dry-run, memória editorial, gate de privacidade). Primeira execução: 17 mortos, **2 sobreviventes** (não havia controle de "manual"/"final" como substantivo reescrito, nem de pronome oblíquo antes de verbo no presente) e 1 mutante que não se aplicou. Com os dois controles acrescentados e o padrão corrigido: **20/20 mortos**. Os módulos antigos (`router`, `morph`, `compare` fora das funções novas) não foram mutados nesta rodada.

## Desempenho

Critério R9 e o teste de tempo: [EDITORIAL.md](EDITORIAL.md#desempenho-cp34) (17.600 palavras: 5,84 s → 4,95 s de CPU).
