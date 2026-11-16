# Dogfood agent-led com documento acadêmico longo e provider real (v0.8.1)

Estado: **concluído na branch** `dev/v0.8.1-dogfood-tg1` (criada de `dev/v0.8.0` = `702a448`; a tag `v0.8.0.dev0` está em `554d1b2`). Sem tag, sem release, sem CI disparada.

## Escopo e privacidade

- Documento: relatório técnico parcial de graduação em engenharia (PT-BR acadêmico), 89 parágrafos editáveis com cerca de 7.300 palavras, 12 tabelas, 7 figuras, 12 referências.
- **Nada do documento entra no repositório.** Entradas, saídas, prompts e respostas ficam em diretório externo. Aqui só há contagens, códigos de achado e fixtures **sintéticas, de outro domínio** (logística e compras), escritas para reproduzir cada defeito.
- O VozNativa não lê DOCX. Uma ferramenta do dogfood, fora do produto, faz DOCX → texto intermediário (um bloco por parágrafo editável; títulos como `## ...` para contexto; capa, sumário, abstract, legendas, tabelas, referências e a pergunta de pesquisa em negrito ficam fora) e texto → DOCX. A ida e volta sem alteração é idêntica em todas as partes do pacote (C14N), e cada aplicação confere de novo o hash de todo parágrafo e de toda célula protegidos.

## Ambiente

- Windows 10, CPython 3.12.6.
- Provider real: `claude -p` (Claude Code 2.1.317), modelo `claude-sonnet-5-5`, com `--tools ""`, `--no-session-persistence`, `--strict-mcp-config`, `--disable-slash-commands` e `--max-budget-usd 1.00` por chamada; `--provider-env minimal`. Um wrapper grava prompt, resposta e uso de cada chamada e tem teto próprio de chamadas.
- **Escritor e juiz são o mesmo modelo.** O motor registra `generator_relation: unknown` (as linhas de comando diferem num argumento), e os logs mostram o mesmo modelo nas duas funções. Nenhum julgamento deste dogfood é independente.

## Funcionalidades executadas

| Comando | Resultado |
|---|---|
| `doctor` | OK |
| `route` | sem `--genre`: `unknown` (empate technical × academic, 6,0 × 6,0); com `--genre academic`: explícito |
| `standards resolve`, `rubric` | `NOT_APPLICABLE`, 0 critérios: a norma institucional não está no Standards Registry |
| `diagnose --mode POLISH` | 6 `tense_switch` (info, baixa confiança), presente descritivo de relatório técnico |
| `plan` | 357 frases: 315 keep, 30 point_edit, 12 sentence_rewrite; 25 dos 30 pontos são estrangeirismos técnicos ("backend" etc.) |
| `patterns`, `analyze`, `ledger`, `integrity` | executados; `integrity` sem achados |
| `rewrite --long-form on` (execução 1, `702a448`) | 14 unidades, 16 chamadas reais (12 contadas), `needs_review`; 11 parágrafos alterados |
| `rewrite --long-form on --force` (execução 2, pacote `voznativa/` idêntico ao de `514a7b9`¹) | 23 chamadas reais = 23 contadas (19 de escrita, 4 do juiz), `needs_review`; 14 parágrafos alterados; o modelo respondeu NO_CHANGE em 6 das 14 unidades |
| `compare`, `audit --original`, `judge-prompt` | executados sobre as saídas |
| `review`, `blind-*` | NOT_RUN: exigem terminal interativo e um revisor humano assinando |

Custo observado: US$ 2,29 em 42 chamadas (teste, execução 1 e execução 2).

¹ A execução 2, o replay e a Assertiva rodaram numa revisão local, nunca enviada, com o mesmo pacote. Depois, os commits foram refeitos só para trocar fixtures de teste e textos que lembravam o documento por outros sintéticos (`git diff` do pacote entre as duas revisões: vazio).

## Defeitos encontrados e corrigidos

| Id | Defeito | Como apareceu | Prova em `702a448` | Correção |
|---|---|---|---|---|
| DF-01 | `--max-calls` não contava o juiz | execução real: 12 contadas, 16 feitas | orçamento 1 → 2 chamadas; 3 → 5 | o juiz gasta o mesmo orçamento; `judge_calls` no registro |
| DF-02 | documento longo autojulgado era aceito | ao escrever o teste do DF-01 | `rewrite` dá `needs_judgment`, `rewrite_document` dava `accepted` | `_generator_relation` atravessa os wrappers |
| DF-03 | um termo com duas grafias após a reescrita | execução real: "back-end" em 3 parágrafos, "backend" nos demais e nas tabelas | stub sintético | guard `term_variant` → `needs_review` |
| DF-04 | oração apagada podia dar verde | ao analisar um falso positivo da execução real | oração final com resultado concreto apagada → `no_deterministic_issues` | `possible_omission` por oração (frase alinhada e vizinhas); fórmulas e conectores do catálogo não contam |
| DF-05 | léxicos de marcadores sem gerúndio ("gerando", "indicando") e sem "por essa razão" | ao classificar as 5 reprovações críticas das execuções reais | 6 reescritas equivalentes sinalizadas; 2 remoções de nexo causal ou evidencial invisíveis | formas acrescentadas aos léxicos causal e evidencial |

Testes: `evals/test_v081_dogfood.py` (DF-01 a DF-03), `evals/test_v081_compare_omission.py` (DF-04) e `evals/test_v081_marker_forms.py` (DF-05). Em `702a448` todos os testes de defeito falham e os controles passam.

### Reprovações críticas das execuções reais (problemas semânticos detectados)

| Candidata | Achado crítico | Classificação | Depois do DF-05 |
|---|---|---|---|
| acréscimo de "três critérios — …" numa frase da conclusão | `span_added` | **verdadeiro positivo**: informação inserida | continua reprovada |
| "sem testar X" → "antes que X tenham sido testadas" | `negation_changed` | sentido mantido; reprovar é conservador | continua reprovada |
| "Por isso" → "Por essa razão" | `causality_changed` | falso positivo (DF-05) | `review_required` (sem crítico) |
| ", indicando X" → ", o que indica X" | `modality_changed` | falso positivo (DF-05) | `review_required` (sem crítico) |
| reordenação entre frases | `causality_moved` | não classificada | continua reprovada |

Não detectados pelos verificadores e achados na revisão humana: troca de singular por plural ("consequência" → "consequências"), enfraquecimento de verbo ("identificados" → "tratados") e acréscimo explicativo ("login" → "autenticação de acesso (login)"). Nenhum gera achado determinístico. Os dois primeiros estavam numa unidade `needs_review` por outros sinais; o terceiro estava numa unidade **`accepted`**: os dois votos do juiz (o mesmo modelo que escreveu) aprovaram o acréscimo. É a evidência concreta deste dogfood de que `accepted` com juiz não independente não dispensa revisão humana.

## Antes × depois sem ruído do modelo (replay)

Um provider de replay responde cada prompt com a resposta gravada para o prompt idêntico na execução 1.

| Motor | Texto final | Desfechos por unidade | Chamadas contadas | Guards | Relatório global |
|---|---|---|---|---|---|
| `702a448` (controle) | idêntico à execução 1 | idênticos | 12 | nenhum | idêntico |
| após a correção | idêntico | idênticos | 16 (= reais) | `term_variant` "backend" | os mesmos 4 códigos |

Uma versão intermediária do DF-04 acusava `possible_omission` num conector de abertura removido ("Dessa forma, ..."). O replay achou o falso alarme, que foi corrigido antes do commit.

## Qualificação

- Gate local (`validator`, `unittest`, `semantic:dev`, holdouts safety e strict, regressões de decisão e roteador, códigos de saída, gatilhos da CI) PASS na árvore de cada commit: 915 e 917 testes. Linha de base limpa em `702a448`: PASS, 905 testes.
- `ptbr-bench-v4` 22/22 e `ptbr-bench-v5` 36/36 (iguais à v0.8.0.dev0).
- Assertiva 0.10.1 `audit --execute` (run `6214fb019eb542a5`) no pacote idêntico ao final¹: suíte PASS em cópia isolada (1.202 invocações); wheel construído, instalado e importado; 1 achado `info` (checks da CI não classificados); 0 candidatos a falso verde.

## Revisão humana do resultado

Das 14 mudanças da execução 2, 6 foram aceitas e 8 rejeitadas: 5 eram só "backend" → "back-end", e as outras trocavam o número gramatical, enfraqueciam um verbo, acrescentavam palavras sem ganho ou trocavam "branch" por "ramo". Duas mudanças só da execução 1 foram aproveitadas: uma correção gramatical ("ao invés de" → "em vez de") e uma de registro formal. O verificador independente do dogfood (números, citações, unidades, identificadores, negação, modalidade e classe de evidência) não achou divergência em nenhuma candidata. Os sinais `predicate_missing` e `causality_changed` da divisão de frase foram conferidos e eram falsos positivos.

## Limitações registradas, sem correção nesta branch

- **Domínio técnico em texto acadêmico:** `genre_domains.academic: []` faz todo termo técnico em inglês virar sugestão de troca, mesmo em engenharia da computação. O DF-03 contém o dano. Mudar o domínio altera comportamento medido pelos benches e fica como recomendação.
- **Roteador:** relatório técnico-acadêmico sai `unknown` por empate.
- **Standards Registry:** sem a norma institucional; a conformidade foi verificada fora do produto.
- **`predicate_missing` em divisão de frase:** a divisão sugerida por `gerund_tail` ("…, tornando X" → "…. Por isso, X") é sinalizada como major. É sinal, não bloqueio.
- **Repetição deliberada:** construções de ressalva ("não substitui", "mas") se repetem dezenas de vezes no documento e carregam as limitações do estudo. Nenhum detector as aponta, o que é conservador e correto; variar a sintaxe fica para o autor.
- **Suporte a DOCX no produto:** não implementado. O documento usou só parágrafos com um formato de run (3 exceções tratadas à parte) e nenhum campo, hiperlink ou equação nativa, e mesmo assim a reinjeção exigiu regras específicas por documento. Um suporte geral precisa de um modelo de runs e de campos que o produto não tem; continua fora do escopo até haver demanda de usuários.
