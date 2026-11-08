# Desempenho (v0.8)

Medições locais: Windows 10, CPython 3.12.6, uma máquina, tempo de parede com `time.perf_counter` e memória de pico com `tracemalloc`. Não são números de outra máquina nem da CI. Entrada: Markdown do próprio repositório (README, SKILL, `docs/*.md`, material MIT) cortado em N palavras por `scripts/experiments/v08_spans_perf.py`; o texto tem datas, nomes, números, caminhos, código e tabelas.

## `spans.extract` (V08-GAP-02, CP2)

| Palavras | Spans | Antes (`6806f9f`) | Depois | Memória de pico depois |
|---:|---:|---:|---:|---:|
| 2.500 | 344 | 0,17 s | 0,09 s | 0,5 MiB |
| 5.000 | 728 | 0,45 s | 0,17 s | 0,9 MiB |
| 10.000 | 1.518 | 1,22 s | 0,34 s | 1,8 MiB |
| 20.000 | 2.453 | 2,87 s | 0,68 s | 3,7 MiB |
| 40.000 | 7.121 | 18,6 s | 1,6 s | 8,0 MiB |
| 80.000 | 6.902 | 30,1 s | 2,7–3,0 s | 15,6 MiB |
| 200.000 | 5.475 | não medido (extrapolação acima de 1 min) | 5,7–9,3 s (duas execuções) | 38,6 MiB |

Causa: para cada casamento, uma varredura completa da lista de faixas ocupadas; e, para cada palavra capitalizada, cópia do prefixo inteiro (`text[:start]`) e busca de regex ancorada no fim. Correção: mapa de bytes das faixas ocupadas e busca limitada ao trecho que um início de frase pode ocupar. A saída é **byte a byte idêntica** em 3.036 textos (82.487 spans, todos os campos) e nos resumos de 40 mil e 80 mil palavras. A contagem de spans cai acima de 40 mil palavras porque um bloco de código aberto no corte engole o resto do texto; é igual antes e depois.

## `morph.analyse_word`

Memoizado (cópia nova a cada chamada). Achado ao comparar antes e depois: a ordem das análises dependia de `PYTHONHASHSEED` (empates de comprimento vinham de um `set`). Agora a ordem é fixa. O conteúdo e todos os relatórios do `compare` (257 pares) são iguais antes e depois, com duas sementes.

## `compare` (aberto: V08-GAP-12 e V08-GAP-13)

| Palavras | `build_plan` antes | `build_plan` depois | `compare` (frase acrescentada) antes | depois |
|---:|---:|---:|---:|---:|
| 5.000 | 0,25 s | 0,09 s | 2,7 s | 1,6 s |
| 10.000 | 0,76 s | 0,16 s | 9,0 s | 4,5 s |
| 20.000 | — | 0,35 s | 26 s | 17 s |
| 40.000 | 9,1 s | 0,73 s | — | — |

**Atualização do CP7b (V08-GAP-12).** Documentos bem formados (arquivos inteiros do repositório; a candidata acrescenta uma frase), `scripts/experiments/v08_compare_perf.py`:

| Palavras | `compare` em `c353058` | depois do CP7b |
|---:|---:|---:|
| 5.727 | 1,99 s | 1,21 s |
| 10.566 | 5,17 s | 2,22 s |
| 20.106 | 11,31 s (`fail`, GAP-13) | 3,99 s |
| 30.492 | 24,70 s (`fail`, GAP-13) | 8,54 s |
| 41.264 | — | 12,39 s |

Mudanças, todas com saída idêntica (0 de 309 relatórios das suítes mudou; `_align` igual à varredura completa em centenas de pares; buscas de nome iguais ao `re.finditer` em 21.517 verificações): `_align` com índice invertido de radicais e tokens e atalho para o conjunto idêntico (Jaccard não passa de 1); busca de nomes por índice de palavras confirmada pelo mesmo padrão, com volta à varredura para caracteres de caixa irregular (lista derivada de `re._casefix`). Primeira versão listava um "K" ASCII entre os irregulares e mandava todo texto com K maiúsculo para a varredura lenta (correto, mas quadrático); corrigido e testado. Num documento sintético de pior caso, ×8 os blocos custava ×24 antes e ×12,6 depois. Resíduo: `_span_issues` → `contains_word` procura cada valor no texto inteiro; `ledger.build` é linear. A validação global de `rewrite_document` agora respeita `timeout_s` (devolve o original se o tempo acabar nela).

Texto anterior ao CP7b: o `compare` continua quadrático: alinhamento de frases todas contra todas (`_align`, ~1 milhão de Jaccard em 10 mil palavras), `_entity_anchors`, `_role_triples` e `signals.positions`. Como `rewrite_document` roda o `compare` no documento inteiro, um documento de 200 mil palavras levaria dezenas de minutos na validação global, e o `timeout_s` do plano não interrompe essa etapa. Mudar o alinhamento muda quais frases são pareadas, então a otimização vai para o CP7 com oráculos próprios.

**Falso vermelho (V08-GAP-13), corrigido no CP7a:** a causa não era o tamanho, e sim o desempate do alinhamento de frases (duas frases que diferem só por "não" têm os mesmos radicais; ganhava a primeira). Histórico do achado: com o texto de 16.562 palavras, acrescentar uma frase no fim dá `fail` (`modality_moved` e `negation_moved` críticos); com 16.406 palavras, não. O menor sufixo que ainda falha tem 15.415 palavras: depende da estrutura global do documento, não de um trecho. Em `rewrite_document`, isso faria a validação global reverter todas as unidades (direção segura, mas documento longo fica inutilizável). Reprodução: `text_of(16562)` em `scripts/experiments/v08_spans_perf.py`, sobre os docs de `6806f9f`.
