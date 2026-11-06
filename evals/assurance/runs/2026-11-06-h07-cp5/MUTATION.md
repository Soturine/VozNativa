# CP5 da v0.7.0.dev1: mutação e dogfood

Windows 11, CPython 3.12.10, Cosmic Ray 8.7.0 num venv próprio. Todas as rodadas usam `python -B` no comando de teste e cópias `git archive`, nunca a árvore de trabalho; o motivo é a VN07-DISC-046. A mutação foi executada por mim com Cosmic Ray, não pelo engine da Assertiva: é evidência observada, não `ENGINE_EXECUTED`.

## Rodadas

| Rodada | Módulo e revisão | Seleção | Executados | Mortos | Sobreviventes | Arquivo |
|---|---|---|---|---|---|---|
| A | `temporal.py` de `80f3da3` (byte a byte o da rodada 2 da v0.7) | todos | 875 | **638** | 237 | `cosmic-ray-A-temporal-v07module.json` |
| B | `temporal.py` de `c909f1d` (com o contrato do CP2) | todos | 922 | 674 | 248 | `cosmic-ray-B-temporal-c909f1d.json` |
| C | `compare.py` de `c909f1d` | linhas 76 e 429–583 (271 de 2004) | **132 de 271** (interrompida a pedido do mantenedor) | 82 | 50 | `cosmic-ray-C-compare-partial.json` |
| D | `document.py` de `c909f1d` | amostra semeada de 120 de 454 (semente 20261106) | 120 | 68 | 52 | `cosmic-ray-D-document-sample.json` |

**Comparabilidade.**

- **A × rodada 2 da v0.7:** é a comparação válida. O módulo é o mesmo, as 875 chaves (operador, ocorrência, linha) são as mesmas, e a suíte é a mesma mais `test_hardening_h07`. Os mortos passaram de 633 para 638, e a diferença são exatamente os 5 mutantes de identidade reclassificados no CP1. Nenhum mutante foi de morto para sobrevivente. Com `-B`, isso descarta que a rodada da v0.7 tenha tido mortes falsas por bytecode velho.
- **B não é comparável à rodada 2**, porque o módulo mudou e são 922 mutantes. Não comparo porcentagens.
- **C** é uma amostra dirigida e parcial. Não vale como mutação de `compare.py`.
- **D** é uma amostra aleatória de um módulo. Não vale como mutação completa de `document.py`.

## C: a regra nova de predicados

Os 50 sobreviventes da execução parcial estão em duas faixas:

- **`_moved_signal_issues` (código da v0.7), linhas 435–453:** 14 sobreviventes. Mais adiante.
- **Regra nova e `_tense_issues` / `_time_reference`, linhas 464–567:** 36 sobreviventes.

**Regra nova, linhas 500–583.** Reapliquei os 20 sobreviventes de `_event_anchors` e `_predicate_issues` contra os testes acrescentados no CP5 (`replay-*.json`, sem bytecode). Resultado: 17 morreram e 3 são equivalentes.

| Linha | Mutante | Decisão | Argumento ou teste |
|---|---|---|---|
| 519 | `lemma[:-2]` → `[:-1]` | **morto** | `test_nominalization_with_another_vowel_keeps_the_action` ("enviará" → "o envio") |
| 520 | `content == set(lemmas)` → `>=` | equivalente | `content` é um filtro de `lemmas`, então `content ⊆ lemmas` e `>=` só é verdadeiro quando são iguais |
| 530 | `continue` → `break` (laço de tokens) | **morto** | `test_every_anchor_of_a_sentence_is_checked` |
| 533 | `a["source"] == "regular"` → `is` | equivalente no CPython | `"regular"` é literal de `morph.py` (origem interna, internado na compilação) |
| 554 | `sim < ALIGN_MIN_SIMILARITY` → `is` | **morto** | `test_weakly_similar_sentences_are_not_compared` |
| 559 | `if not before: continue` → `break` | **morto** | `test_a_sentence_after_one_without_verbs_is_still_checked` (a 1ª versão do teste não chegava a esta linha) |
| 561 | janela `j-1`, `j`, `j+1`: 14 mutantes | **13 mortos**, 1 equivalente | `test_the_verb_may_move_to_a_neighbouring_sentence` e `test_the_window_works_away_from_the_first_sentence`. `k < len` → `k != len` é equivalente porque `k ≤ j+1 ≤ len` |
| 567 | `continue` → `break` (laço de âncoras) | **morto** | `test_every_anchor_of_a_sentence_is_checked` |

Os 139 mutantes selecionados e não executados (parte de `_predicate_issues`, `_order_issues` e trechos das linhas 76 e 429–583 que ficaram para o fim da fila) são **NOT_RUN**. A mutação completa da regra fica para a próxima rodada.

**`_tense_issues` e `_time_reference`, linhas 464–491:**

- 6 mutantes na anotação `str | None`: equivalentes no caminho executável.
- Linha 481, filtro de alinhamento (`<` → `==`, `<=`, `is`, `or` → `and`), e linha 482 (`continue` → `break`): lacunas de teste. Não foram cobertas nesta rodada.
- Linha 487, `len(b) == 1` → `<= 1`: equivalente, porque o lema está nos dois perfis e então `len(b) ≥ 1`. `!=` → `is not` na mesma linha: lacuna.
- Linhas 490 e 491: índices da mensagem `name()`. A mensagem é texto, sem oráculo.

Tudo isso vai para o backlog B-M2.

**`_moved_signal_issues` (v0.7), linhas 435–453:**

- 435 (`&` → `|`): equivalente, porque `Counter` devolve 0 para rótulo ausente e o laço pula.
- 436–448: lacunas reais. Faltam teste com dois rótulos em que só o segundo se move (437/444 `break`), teste com o ganho numa frase não alinhada (447/448) e teste com contagem padrão (445/446).
- 453: índice do exemplo no texto da issue.

Backlog B-M2.

## B: sobreviventes executáveis de `temporal.py` atual

Dos 248 sobreviventes, cerca de 208 são anotações e 40 são executáveis. A separação foi feita por heurística sobre a linha mutada; a lista completa está no JSON.

- **Mudança trazida pelo CP2:** os mutantes `count > 0` → `!= 0` e `get("count", 0)` → `get("count", ±1)` (linhas 141, 317 e 401) agora são **equivalentes por invariante imposto**. O validador garante `count` inteiro ≥ 0 e presente, e `_load` sempre valida. Na v0.7 eles eram "invariante não imposto".
- **Lacuna de baixo risco:** `count > 1` na linha 317 sobrevive. Falta uma atestação com `count == 1` dentro da época. Backlog B-M1.
- **Os mesmos do CP1, em linhas novas:** os de identidade `is` (230, 268, 271, 285, 291, 108, 191) são equivalentes no CPython ou pela linguagem, como em `evals/assurance/runs/2026-11-06-h07-cp1/IDENTITY_TRIAGE.md`. Os de ordem sobre conjunto fechado (145, 151, 268, 274, 291, 345) são os mesmos argumentos do `MUTATION.md` da v0.7.
- **`continue` → `break` na linha 82** (`_attestation_problems`, ramo de valor ausente): sobrevive porque, com `count` ausente, `words` raramente é inválido no mesmo registro. Lacuna de baixo risco (B-M1).

## D: amostra de `document.py`

Os 52 sobreviventes se dividem assim:

| Classe | Linhas | Quantidade | Decisão |
|---|---|---|---|
| anotações | 63, 64, 180 | 12 | equivalentes no caminho executável |
| constantes e padrões | 33 (`SCHEMA_VERSION`), 42 (`frozen`), 44, 46, 49 (padrões de `Limits`) | 5 | lacuna: nenhum teste fixa os padrões |
| corte de segmentos | 87–96 | 13 | **lacuna real**: fronteiras de `segment_words`, recuo para corte seguro |
| núcleo e bordas | 116–123 | 6 | lacuna: aparas de espaço e índices de borda |
| inventário e validação do plano | 126–168 | 11 | lacuna: limite de 80 valores, `schema_version`/`sha256` adulterados por campo, ordem de unidades |
| outros | 104, 143, 190, 204 | 5 | lacuna |

Nada foi corrigido nesta rodada. O backlog B-M3 pede oráculos de fronteira para o corte e para a recusa de plano adulterado campo a campo.

## Dogfood

**Derivanta Engine** (`inspect --maintainability` e `compare` num clone limpo):

- `e7506f5` × `c909f1d`: COMPARABLE, 136 PERSISTING e 3 NEW, todos INFO.
  - 2 × `UNREFERENCED_DEFINITION` em classes `unittest` herdadas de uma base local: **defeito do Engine reproduzido (DEF-VN-07)**. Corrigido na Engine PR #3, commit `acd6ca3`, com teste que falha sem a correção; `tools/verify.py` exit 0. O reteste dá exatamente esses 2 ABSENT, 137 PERSISTING e 0 NEW.
  - 1 × `HIGH_COMPLEXITY` em `compare._predicate_issues` (21 caminhos, limiar 15): verdadeiro como motivo de refatoração. Risco aceito nesta rodada, porque a função acabou de ser mutada como está.
- **Separação do que é de quem:** a análise semântica dos achados foi feita por mim, o agente. O Engine produz candidatos estáticos (hipóteses); só o DEF-VN-07 foi reproduzido como defeito.

**Assertiva 0.10.1** (`audit . --execute` num clone limpo de `c909f1d`, exit 0):

- unittest exit 0, com 755 invocações (cada `subTest` conta como invocação).
- Cobertura de 90,0% das linhas e 81,1% dos ramos (projeto).
- Wheel: build, instalação, import e fechamento de dependências PASS. Testes contra o wheel NOT_RUN (AXF-VN-04).
- Mutação e controles negativos pelo engine: não executados.
- 1 achado `UNCLASSIFIED_VERIFICATION`, que classifiquei como CONTEXTUAL.

A avaliação do agente foi anexada com `assertiva audit . --assessment` (exit 0) e validada pela ferramenta contra o run `4e9ef681af3d48ae` (`assertiva-assessment-c909f1d.json`, `assertiva-assessed-c909f1d.json`). Não usei `assertiva improve` nem `--mutate` do engine. A 0.10.1 instalada ainda tem o AXF-VN-01 (corrigido na PR #8, ainda não liberado), e a mutação já tinha sido feita com Cosmic Ray.
