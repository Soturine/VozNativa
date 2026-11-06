# Integração de corpora da v0.7.0 (CP3, 2026-11-06)

Fontes integradas à avaliação: **3 → 7**. A meta exploratória do plano era 8–12; não foi forçada. Os critérios da escada são os do Registry (`voznativa/corpus/registry.py`). Nenhum texto de terceiros é versionado: o cache fica em `VOZNATIVA_CORPUS_CACHE` (fora de qualquer repositório, verificado por `cache_dir`), e os relatórios versionados guardam só contagens, hashes e taxas.

## Fontes novas

| Fonte | Commit fixado | Licença (lida em 2026-11-06) | Direitos do texto | Gênero / variedade | Registros | Unidade de split |
|---|---|---|---|---|---|---|
| `ud-portuguese-gsd` | `c91edee` | CC BY-SA 4.0 | **unclear**: README v2.5 diz que a permissão do Google cobre as anotações, não o conteúdo web | blog, notícia / PT-BR | 12.020 | sentença (o arquivo não declara documento: vazamento de contexto de documento não excluível) |
| `ud-portuguese-petrogold` | `5814c7f` | CC BY-SA 4.0 | cobertos (corpus Petrolês tornado público pela Petrobras) | acadêmico, técnico (petróleo e gás) / PT-BR | 8.946 | documento (19) |
| `ud-portuguese-pud` | `0fdcc05` | CC BY-SA 3.0 | **unclear** (traduções profissionais de notícia e Wikipédia) | notícia, enciclopédia / tradução, variedade não declarada | 1.000 | documento (397) |
| `ud-portuguese-dantestocks` | `4268e8e` | CC BY 4.0 | **unclear** (tweets) | rede social, mercado / PT-BR | 4.042 | tweet (autores não informados: vazamento por autor não excluível) |
| `ud-portuguese-cintil` | — | CC BY-NC-ND 4.0 | — | PT-PT | — | **só catálogo** (ACCESS_VERIFIED): PT-PT e sem derivados |

Leitura: 0 erros nas quatro. Execuções: `evals/corpus/runs/verify-2026-11-06.json`, `prepare-2026-11-06.json`.

`text_rights: unclear` (VN07-DISC-009) também foi aplicado ao Bosque (frases da Folha de S.Paulo e do Público). Efeito: processamento local e estatísticas continuam permitidos; exportar amostras, redistribuir, publicar derivados, enviar a modelo externo e treinar deixam de poder ser `ALLOWED` pela licença do card. Uma negação mais forte da licença (ex.: share-alike dentro do repositório MIT) continua valendo.

## Integridade (7 fontes juntas)

`evals/corpus/runs/integrity-2026-11-06.json`: 57.374 registros; 917 duplicatas exatas; 244 ligações quase-duplicadas; 2 clusters entre fontes; vazamento entre `calibration` e `evaluation`: **0** em grupo, cluster, hash original e hash normalizado. Limitação: o PetroGold tem só 19 documentos e o hash por unidade deu 221 registros em calibração e 8.725 em avaliação.

## Avaliação cruzada (`scripts/corpus_crossgenre.py`)

Gêneros aceitáveis fixados no script **antes** da execução. Unidade: janela de até 150 palavras dentro de um grupo; até 1.500 por fonte e split, escolhidas por hash. Números do split `evaluation` (calibração entre parênteses quando diverge). Intervalos de Wilson no JSON.

| Fonte | Unidades | Roteador: abstenção | aceitável confiante | **errado confiante** | Falsa edição (detectores) | Gíria / mil palavras | PT-PT em texto BR |
|---|---|---|---|---|---|---|---|
| Bosque (CF+CP) | 1.112 | 98,4% | 0,4% | 1,3% (whatsapp 9) | 20,5% — puxada por `pt_pt_variant` (metade do Bosque é PT-PT) | 0 | n/a (misto) |
| B2W | 1.500 | 94,1% | 4,9% | 1,0% (corporate 14) | 0,1% | 0,33 | 0% |
| Machado | 147 (162) | 26,5% | 71,4% | 2,0% (whatsapp 3) | 1,4% | 0,05 (0,22) | **15,7%** |
| GSD | 1.500 | 99,6% | 0,4% | 0% | 0,7% | 0,06 | 0,6% |
| PetroGold | 1.491 (32) | 79,0% | 19,1% | 2,0% (documentation 10, whatsapp 10) | 1,7% | 0,02 | 0,1% |
| PUD | 202 | 100% | 0% | 0% | 1,0% | 0 | n/a |
| DANTEStocks | 1.500 | 82,5% | 17,4% | 0,1% | 0% | 0,34 (0,80) | 0% |

### O que os números mostram (insumo dos CPs seguintes)

1. **Gíria fora de época (CP6).** Em Machado, `mano` (83 ocorrências na calibração), `da hora`, `irado`, `pô` são casados pelo léxico: no séc. XIX "mano" é irmão, "irado" é zangado, "da hora" é literal. O léxico casa a forma sem época nem contexto. É falso positivo sistemático, não uso de gíria.
2. **Grafia histórica lida como PT-PT (CP5/CP6).** "acção", "facto", "projecto" em Machado são grafia brasileira anterior a 1943. O detector de variedade não considera a época do texto (`time_of_text`). As notas literárias não decidem edição (v0.6), por isso a falsa edição fica em 1,4%; o diagnóstico continua errado.
3. **Falso amigo invertido.** "propina" em tweets financeiros foi marcado como PT-PT (lá é mensalidade); no Brasil é suborno, e é o sentido provável.
4. **Roteador (CP5).** Erros confiantes são raros (≤ 2%), mas `whatsapp` aparece em notícia, texto acadêmico e literatura: a pista "linha começando em minúscula" dispara em texto com quebra dura. A abstenção alta é o comportamento pedido (abster-se em vez de errar), mas hoje `unknown` não aciona proteções conservadoras: G1.
5. **Detectores editoriais** têm falsa edição baixa (≤ 1,7%) em texto humano PT-BR dos 6 domínios medidos. O valor de 20,5% no Bosque é de PT-PT editado como PT-PT, coerente com o alvo PT-BR.

## Fontes antigas

`ud-portuguese-bosque`, `b2w-reviews01`, `machado-de-assis-corpus` ganharam a nova rodada de integridade e de avaliação como evidência adicional; as rodadas da v0.6 ficam intactas.

## Não feito, com motivo

- **Seleção estratificada de B2W e Machado** (os prefixos de ~8 MB e ~6 MB enviesam por ordem): adiado (VN07-DISC-014). Os registros de manifesto antigos seriam preservados como baseline; o custo é baixar os arquivos inteiros e redefinir as unidades. Critério de aceite: amostra por produto/categoria (B2W) e por obra (Machado), mesma política, novo manifesto, comparação com o prefixo.
- **Carolina** (TEI, licença por documento): o leitor TEI existe (CP2), mas o download do recorte não foi feito nesta rodada. Status permanece ACCESS_VERIFIED.
- **Fala transcrita (C-ORAL, NURC, SP2010, CORAA)**, **ALiB**, **PHPB**, **Tycho Brahe**: sem mudança de acesso verificada nesta rodada; ficam no catálogo, sem simular ingestão. CORAA sobrepõe ALIP, C-ORAL, NURC e SP2010 (relações já no Registry).
