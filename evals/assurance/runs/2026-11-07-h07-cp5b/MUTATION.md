# CP5B da v0.7.0.dev1: mutação e dogfood de fechamento

Windows 10, CPython 3.12.6, Cosmic Ray 8.7.0 num venv próprio. Todas as rodadas usam `python -B` e cópias `git archive`, nunca a árvore de trabalho (VN07-DISC-046). A mutação e os replays foram executados por mim, fora do engine da Assertiva: evidência `AGENT_OBSERVED`, não `ENGINE_EXECUTED`.

## Rodadas

| Rodada | Módulo e revisão | Seleção | Executados | Mortos | Sobreviventes | Arquivo |
|---|---|---|---|---|---|---|
| C (completa) | `compare.py`, blob `acd78af` (o mesmo em `c909f1d`, `d8aa669` e `ecf3dd2`), suíte de `d8aa669` | linhas 76 e 429–583 (271 de 2004) | **271 de 271** | **201** | 70 | `cosmic-ray-C-compare-complete.json` |
| Replay C | os 70 sobreviventes contra `evals/test_compare_signal_oracles.py` sozinho | sobreviventes registrados | 70 | **44** | 26 | `replay-C-compare-oracles.json` |
| Replay D | os 52 sobreviventes da amostra D do CP5 contra `evals/test_document_plan_oracles.py` sozinho | sobreviventes registrados | 52 | **25** | 27 | `replay-D-document-oracles.json` |

O replay (`replay_recorded_survivors.py`) recusa rodar se o módulo sem mutação falhar a suíte. Cada sobrevivente é reaplicado pela linha registrada e conferido contra o texto da linha (`STALE` se não bate). O módulo original é restaurado e conferido byte a byte ao final.

**Comparabilidade com o CP5.** As 271 chaves (linha, coluna, operador, ocorrência) são as mesmas da rodada C parcial do CP5 (132 de 271, `../2026-11-06-h07-cp5/cosmic-ray-C-compare-partial.json`). Nas 132 executadas nas duas rodadas:

- 82 continuaram mortas e 31 continuaram sobrevivendo.
- **Nenhum mutante passou de morto para sobrevivente.**
- 19 passaram de sobrevivente para morto, pelos testes do CP5.

Das 139 não executadas no CP5, 100 morreram e 39 sobreviveram. A rodada completa substitui a parcial como mutação da faixa selecionada, mas continua sendo uma faixa dirigida, não a mutação de `compare.py` inteiro.

## C: triagem dos 70 sobreviventes

**Mortos pelos oráculos novos (44).** Cada teste de `evals/test_compare_signal_oracles.py` chama a verificação diretamente, com alinhamento `(i, j, similaridade)` montado à mão:

| Linhas | Mutantes | Teste |
|---|---|---|
| 436 (`!=` → `>`, `<`), 437 (`continue` → `break`) | 3 | `test_a_net_increase_…` e `test_a_net_decrease_with_a_relocation_is_not_a_move` |
| 438 (`[0]` → `[-1]`), 445, 446 (padrão `0` → `-1`), 447 (8), 452 (3), 453 (2) | 16 | `test_the_issue_names_the_first_sentence_that_lost_and_the_first_that_gained`: uma frase nova desloca `j = i + 1`, uma frase inalterada vem antes, e o marcador sai de duas frases e chega em duas |
| 439 (`or` → `and`), 440 (`continue` → `break`) | 2 | `test_informational_categories_never_move_and_do_not_stop_the_check` |
| 443 (4), 444, 481 (4), 482, 555 | 11 | pares abaixo do limiar, exatamente no limiar, e par ignorado antes do par real |
| 487 (`== 1` → `>= 1`, 2; `!=` → `is not`) | 3 | `test_a_verb_with_two_tenses_on_either_side_abstains`; `test_the_same_construction_on_both_sides_is_no_change` (rótulos de construção são strings iguais e objetos distintos) |
| 490, 491 (2) | 3 | `test_the_message_names_both_tenses`, `test_a_periphrasis_is_named_by_its_construction` |
| 504 (`PREDICATE_MIN_STEM` 4 → 3) | 1 | `test_short_stems_abstain` ("pagar") |
| 520 (`==` → `is not`, `<=`) | 2 | `test_a_token_that_may_be_a_light_verb_abstains` ("conseguia": conseguir ou "conseguer") |
| 534 (`continue` → `break`) | 1 | `test_a_weak_ending_token_does_not_end_the_sentence` ("Durante…") |
| 561 (`0 <=` → `-1 <=`) | 1 | `test_the_window_does_not_wrap_to_the_last_sentence` |
| 568 (`[0]` → `[-1]`) | 1 | `test_the_issue_reports_the_first_lemma_of_the_anchor` ("vendia") |

A frase de 445 e 446: mudar só um dos dois padrões para `-1` cria `delta = -1` quando o rótulo falta nos dois lados. Antes do replay eu tinha argumentado equivalência; o replay mostrou que não era.

**Equivalentes (22):**

| Linha | Mutantes | Argumento |
|---|---|---|
| 464 | 11 | anotação `str \| None`; `from __future__ import annotations` faz com que nunca seja avaliada |
| 435 | `&` → `\|` | `before` e `after` são `Counter`: um rótulo de um lado só tem diferença líquida e cai no `continue` da linha 436 |
| 436 | `!=` → `is not` | contagens pequenas (cache de inteiros do CPython); equivalente só no CPython |
| 447 | `> 0` → `!= 0` | o ramo `delta < 0` já foi tomado; sobra `delta >= 0`, onde `!= 0` e `> 0` coincidem |
| 487 | `== 1` → `<= 1` (2) | os perfis de tempo nunca têm conjunto vazio para um lema presente |
| 520 col. 88 | `==` → `>=` | `content` é filtro de `lemmas`, então `>=` só vale na igualdade (já argumentado no CP5) |
| 533 | `==` → `>=`, `<=`, `is` | as origens são só `"regular"` e `"irregular"`, e `"irregular" < "regular"`. Análises irregulares têm `ending=None`, que nunca está em `WEAK_ENDINGS`. O `is` compara um literal de `morph.py`, internado na compilação |
| 561 | `<` → `!=`, `is not` | `k ≤ j + 1 ≤ len`, então `!= len` exclui o mesmo `k`. O `is not` vale pelo cache de inteiros |

**Backlog B-M2 (4):**

- **467, `split("@")[0]` → `[-1]`.** É uma hipótese de projeto, não um defeito. `_time_reference("progressive@inf")` devolve o rótulo em vez de abster, então "está terminando" → "precisa estar terminando" gera `tense_changed` (major). O mutante transformaria isso em abstenção. Pode ser alarme falso, quando o tempo vem de um modal não analisado, ou pode ser o sinal de aspecto desejado. Decido a regra antes de escrever o oráculo, e por isso não travei o comportamento atual com teste.
- **520 col. 22, `len(stems) == 1` → `>= 1`.** Falta uma ficha determinística. Um token com dois radicais longos e terminação forte não apareceu, e escolher o radical por `next(iter(set))` depende da semente de hash: um teste mataria o mutante só às vezes.
- **529, `or` → `and` (2).** Com a morfologia atual, os tokens de construção que voltam a ser analisados são auxiliares leves (recusados) ou o verbo principal, que dá a mesma âncora. Não achei ficha em que a diferença apareça.

## D: triagem dos 27 sobreviventes do replay de `document.py`

Os 52 sobreviventes da amostra D do CP5 (120 de 454, semente 20261106, `c909f1d`) foram reaplicados contra `evals/test_document_plan_oracles.py` sozinho: 25 morreram.

**Equivalentes (21):**

| Linha | Mutantes | Argumento |
|---|---|---|
| 63, 64, 180 | 12 | anotações sob `from __future__ import annotations` |
| 60 | `==` → `>=` | `"verse"` é o maior tipo em ordem alfabética |
| 90 | `== 0` → `<= 0` | o custo de corte nunca é negativo |
| 116 | `== 0` → `<= 0` | `n` nunca é negativo |
| 117 | `==` → `>=` | `n` nunca passa de `len(units) - 1` |
| 122 | `>` → `!=` | `core_end` nunca fica abaixo de `core_start` |
| 128 | `!=` → `is not` | os dois lados são o mesmo objeto `int` |
| 134 | `<` → `<=` | nenhum valor começa exatamente em `core_end`: o núcleo termina antes do espaço em branco |
| 162 | `!=` → `is not` | o cache de inteiros pequenos cobre o `schema_version` lido do JSON |
| 190 | `==` → `<=` | só há duas ações, e desde `ecf3dd2` `validate_plan` exige uma delas |

**Backlog B-M3 (6):**

- defaults de `Limits`: 44, 46 e 49;
- `frozen=True`, linha 42;
- teto de 80 valores, linha 134;
- `\|` → `^` nos nomes e siglas carregados, linha 126.

## Dogfood

Engine e Assertiva rodaram por mim, sobre um clone limpo de `ecf3dd2`.

- **Derivanta Engine 0.1.0** (PR #3, head `acd6ca3`). `inspect --maintainability --traceability traceability-h07-cp5b.json` deixa H07-017 a H07-020 como `LINKED_STATIC` / `TEST_DEFINED` / `NOT_EXECUTED`. No `compare` contra o CP5 (`c909f1d`): 137 persistem, 5 são novos e 2 ficam `NOT_OBSERVED_IN_SCOPE`, porque o escopo mudou com `--traceability`. Os 5 novos são todos `INFERRED`:
  - um `_load` duplicado num teste;
  - duas `DUPLICATE_TABLE`: os nomes dos jobs e `ALWAYS_PROTECTED` repetidos em teste. São oráculos independentes, intencionais;
  - a complexidade de `judge_run` (19) e de `validate_plan` (36): candidatos a refatoração, no backlog.

  Nenhum é defeito.
- **Assertiva 0.10.1.**
  - `audit --execute`: o run `13dbe2a46ce9496d` (sem cobertura) e o run `6f5ee4fc6a1743b1` (com coverage 7.17.2). O unittest passou com 815 invocações (814 passaram, 1 pulada), `ENGINE_EXECUTED`. Cobriu 90,27% das linhas e 81,36% dos ramos, contando os testes; só o produto, 7340 de 8650 linhas e 2717 de 3358 ramos. O wheel constrói, instala e importa; os testes contra o wheel ficaram `NOT_RUN`.
  - O único achado do engine é `UNCLASSIFIED_VERIFICATION`, disposição `CONTEXTUAL`.
  - A avaliação do agente (`assertiva-assessment-ecf3dd2.json`) foi anexada ao run 6f5ee4fc6a1743b1 (`assertiva-assessed-ecf3dd2.json`). Ela distingue os defeitos reproduzidos e corrigidos (`OBSERVED`), a hipótese da linha 467 (`INFERRED`) e o que segue `NOT_RUN`.

## O que esta rodada não prova

- A mutação de `compare.py` fora das linhas 76 e 429–583, a de `router.py`, `morph.py` e `diagnose.py`, e a mutação completa de `document.py`.
- Que os oráculos novos matem esses mutantes também na suíte inteira. O replay usou só o arquivo de oráculos; a suíte inteira só é mais forte.
- Equivalência semântica das reescritas, provedores reais, detectores ao vivo, holdout independente e revisão humana cega: `NOT_RUN`.
