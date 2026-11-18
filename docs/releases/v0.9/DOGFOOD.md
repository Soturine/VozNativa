# Dogfood da v0.9 (CP8): o engine de verdade, com provider real

Todos os cenários rodaram o **engine do produto** (`voznativa ...`), nunca uma reescrita feita à mão pelo agente. Provider: `claude -p` sem ferramentas, `--provider-env minimal`, por um wrapper fora do repositório que grava uso e custo; escritor `claude-haiku-5-5`, juiz `claude-sonnet-5-5` quando houve juiz (modelos diferentes, **mesmo fornecedor**: o juízo não é independente). Windows 10, CPython 3.12.6, 2026-11-18. Entradas sintéticas em `evals/v09/dogfood/`; saídas, prompts e o documento privado ficam fora do repositório.

## Cenários

| # | Cenário | Comandos | Resultado | Chamadas · US$ |
|---|---|---|---|---|
| S1 | erros gramaticais (`s1-gramatica.txt`) | `diagnose`, `plan`, `rewrite --judge-cmd` | **defeito encontrado**: `diagnose` viu "os relatório" e "fazem duas semanas" mas não "Houveram atrasos"; a reescrita corrigiu dois e foi `accepted` com o terceiro erro mantido. Corrigido (abaixo) e refeito: os três corrigidos, `accepted` | 3 · 0,047 (+ replay 3 · 0,047) |
| S2 | regras, números e qualificadores (`s2-regras.txt`) | `doctor`, `route`, `standards list`, `diagnose`, `patterns`, `plan`, `ledger`, `integrity`, `audit`, `rewrite`, `compare`, `judge-prompt`, `audit --original` | todos com o código de saída esperado; fórmulas cortadas; "automático", "diariamente", "parcial", "opcional", "até 40 minutos" e "só pode ser iniciada" preservados; `compare` sem sinal major; proveniência presente | 3 · 0,050 |
| S3 | voz do autor (3 amostras curtas) | `profile`, `rewrite --voice-sample` | perfil `explicit_only` (menos de 150 palavras nas amostras): o engine **não aplicou** hábitos de voz sem evidência suficiente e manteve o registro formal; fórmulas cortadas, `needs_judgment` | 1 · 0,003 |
| S4 | estrutura protegida (`examples/quickstart/documento-longo.md`) | `rewrite --long-form on` | 8 unidades: 6 `needs_judgment`, 2 protegidas (código e tabela nunca enviados, intactos no resultado) | 6 · 0,014 |
| S5 | DOCX real (relatório técnico do primeiro dogfood; privado) pelo fluxo do produto | `rewrite X.docx --docx-out Y.docx --genre academic` | 15 unidades: **9 `no_change` sem chamada**, 3 `needs_judgment`, 3 `needs_review`, 0 revertidas; 19 parágrafos aplicados numa cópia nova, **`docx check` PASS**, a cópia abre no python-docx; o original continua com o hash registrado no dogfood da v0.8.1; a memória editorial carregou as grafias `backend`/`frontend` do documento e **não houve grafia dupla** (o DF-03 da v0.8.1); a validação global pediu revisão com sinais de aspecto, qualificador, causalidade e condição | 9 · 0,039 |

Custo total do CP8 (dogfood): **US$ 0,20** em 27 chamadas.

## Defeito do ciclo (reproduzir → teste → causa → correção → suíte → replay)

| ID | Entrada sintética | Antes | Causa | Teste | Depois |
|---|---|---|---|---|---|
| V09-DF-01 | "Houveram falhas na entrega das cestas." | `diagnose` vazio para "houveram" + substantivo; plano sem razão gramatical; reescrita real aceita com o erro | o padrão de "haver" existencial exigia quantificador ou número depois do verbo | `test_v09_semantic_safeguards.Grammar.test_houveram_before_a_plural_noun` (falha antes, passa depois; controles "houveram por bem", "houveram de", auxiliar + particípio) | `existential_haver` com `auto_fix` "Houve"; replay real corrigiu os três erros do S1. Conjuntos congelados da v0.9 inalterados (11/11, 6/6, sem falso alarme) |

## Revisão das saídas

Leitura do agente (`AGENT_OBSERVED`, não independente; nenhuma revisão humana assinada nesta rodada): nas saídas de S1–S4 nenhum fato, número, condição ou negação mudou. No S5 a leitura ficou nas contagens e nos sinais (o documento é privado); a revisão humana das 19 edições cabe ao autor do documento, como na v0.8.1. Os `accepted` de S1 e S2 vêm de juiz de outro modelo do mesmo fornecedor: evidência falível, não equivalência provada.

## Limites

- Uma execução por cenário; um único modelo escritor.
- Hosts Codex e Gemini CLI, modelo local real e Emulate: ver [INTEGRATIONS.md](INTEGRATIONS.md).
- Uma falha transitória de memória (`MemoryError` em `test_corpus_tei`) apareceu uma vez com o replay do S5 rodando em paralelo à suíte; isolado e na suíte seguinte, passou.
