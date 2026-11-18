# Consistência editorial em documentos longos (v0.9 CP3)

Por que existe: no segundo dogfood da v0.8.1, cada unidade melhorou sozinha e o documento piorou em conjunto. Os achados de `patterns` caíram de 37 para 8, mas frases abertas por "Essa X permite/promove/contribui" subiram de 3 para 11, porque as unidades convergiram para a mesma correção. Nenhum detector viu ([DOGFOOD_TCC2.md](../v0.8/DOGFOOD_TCC2.md)). Menos achados não era melhor texto.

## O que foi feito

`voznativa/editorial.py`, usado pelo `rewrite --long-form`:

| Peça | O que faz | O que não faz |
|---|---|---|
| `openings` | conta frases por tipo de abertura anafórica ou conectiva: demonstrativo + nome + **verbo de efeito** (`demonstrative_effect`: "Essa abordagem permite…", "Isso contribui…"), demonstrativo + nome, "Isso/Isto", conectivos fixos ("Além disso", "Dessa forma", "Com isso"…), gerúndio inicial | não conta artigos: cortar "É importante destacar que o relatório…" deixa "O relatório…", e isso não é convergência |
| `convergence` (guard global) | sinaliza a abertura que a reescrita **acrescentou**: ≥ 3 a mais que o original, ≥ 2× o original + 1, vinda de ≥ 2 unidades. Entra em `guards.introduced` como `style_convergence` (major) e o desfecho fica no mínimo `needs_review` | não reverte unidade (estilo é sinal, não erro); não sinaliza a forma que o autor já usava com a mesma frequência |
| `EditorialMemory` | estado entre unidades: aberturas já acrescentadas pelas unidades reescritas e a grafia que o documento usa para termos variáveis (pares de `community_packs/tech.yml`, ex. `backend`/`back-end`). A partir da 2ª abertura acrescentada de um tipo, o prompt das unidades seguintes pede para não acrescentar outras; a grafia do documento vai no prompt de toda unidade que contém o termo | não guarda frases (só rótulos, contagens e grafias, `schema_version` 1); não tem autoridade sobre fatos nem proteções; não força uma segunda passada |

O léxico de verbos de efeito foi fixado por critério linguístico (formas verbais de *permitir, possibilitar, promover, contribuir, garantir, favorecer, proporcionar, assegurar, viabilizar, facilitar, reforçar, evidenciar, demonstrar, tornar, representar, ampliar, fortalecer, otimizar, potencializar, consolidar, resumir*), não ajustado a um documento.

## Evidência

**Documentos reais (privados, fora do repositório; só contagens):**

| Documento e saída | `demonstrative_effect` original → final | Sinal da v0.9 |
|---|---|---|
| segundo dogfood, saída final (execução 3) | 3 → 11 | `style_convergence` (o caso que motivou a regra) |
| segundo dogfood, execução 2 | 3 → 5 | nenhum (abaixo do limiar) |
| primeiro dogfood, execuções 1 e 2 | 1 → 1 | nenhum (controle num segundo documento real) |

O caso motivador é desenvolvimento, não holdout: ele mostra que a regra vê o que se queria ver, não que ela generaliza. O segundo documento real é o único controle externo.

**Testes sintéticos** (`evals/test_v09_editorial.py`, domínio de irrigação e hortas): aberturas acrescentadas em várias unidades são sinalizadas; as do autor, as de uma unidade só e as aberturas por artigo não; um escritor de teste que ignora a memória termina com 5 aberturas e `style_convergence`; um que segue a nota termina com 2 (as das unidades anteriores à nota) e sem sinal; o estado da memória não contém frases.

**Provider real, mesmo documento sintético de 702 palavras (8 unidades), uma execução de cada (n = 1):**

| Modelo | Motor | Achados de `patterns` (16 no original) | Aberturas acrescentadas | Sinal | Chamadas | US$ |
|---|---|---|---|---|---|---|
| Haiku | `v0.8.1` | 2 | 1 efeito, 1 demonstrativo, 2 "Com isso" | — | 8 | 0,020 |
| Haiku | v0.9 | 0 | 1 efeito, 1 demonstrativo, 2 "Assim" (memória passou a evitar "Assim") | nenhum | 8 | 0,020 |
| Sonnet | `v0.8.1` | 0 | **3 efeito**, 1 "Com isso" | nenhum (a v0.9 sinalizaria 0 → 3) | 8 | 0,303 |
| Sonnet | v0.9 | 0 | 0 efeito, 1 demonstrativo, 2 "Com isso" (memória passou a evitar) | nenhum | 8 | 0,311 |

Leitura: a diferença de 3 para 0 aberturas de efeito com Sonnet **não** é atribuível à memória, porque a nota sobre esse tipo nunca foi emitida nessa execução (só a de "Com isso", a partir da 4ª unidade); é variação do modelo. O que está demonstrado é: o detector vê o padrão real; a memória registra o que as unidades acrescentam e chega ao prompt das seguintes; e, com escritor de teste, seguir a nota reduz a convergência. Medir o efeito da memória com modelo real exige várias execuções por braço num documento longo: fica para o CP7/CP8.

## Desempenho (CP3.4)

`evals/test_v08_compare_perf.py` falhou na v0.8.1 sob a carga da suíte inteira (19,4× e 21,2× com limite de 19×; 12–13× isolado). O método passou a medir **tempo de CPU do processo**, com **três repetições intercaladas** dos dois tamanhos e o mínimo de cada; o limite de 19× não mudou. Sob duas suítes rodando em paralelo nesta máquina, os métodos antigo e novo deram 11,3–12,8×: a falha da v0.8.1 não se reproduziu, então a mudança é de robustez de método, não uma correção demonstrada.

Critério R9 (`scripts/perf_compare.py`, mesmo método do CP0, CPU mínimo de 5 repetições):

| Palavras | `v0.8.1` (CP0) | v0.9 (CP3) |
|---|---|---|
| 2.200 | 0,41 s | 0,39 s |
| 8.800 | 2,09 s | 1,95 s |
| 17.600 | 5,84 s | 4,95 s |
| razão 800/100 blocos | 14,4× | 12,7× |

Sem regressão. As funções que o Derivanta apontou como complexas (`_moved_signal_issues`, `_omitted_clause_issues`, `_span_issues`) não foram refatoradas: nenhum defeito foi demonstrado nelas.
