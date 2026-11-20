# Corpus e licenças da prova de fogo (v0.10.5)

Construído por `scripts/v0105_build_corpus.py` (determinístico). Texto em `~/.voznativa/fire-trial/items.jsonl`, **fora do repositório**; no Git só o manifesto `evals/v0105/corpus_manifest.json` (id, fonte, gênero, faixa, palavras, sha256 e direitos por operação).

## Direitos por operação

| Fonte | Base legal / licença | Análise local | Envio a provider (API) | Trecho publicado (site/fixture) | Itens |
|---|---|---|---|---|---|
| Machado de Assis (Gutenberg, Wikisource) | domínio público (autor m. 1908); entrada do registro CC0-1.0 | sim | sim | sim | 219 |
| Leis federais (planalto.gov.br, versões compiladas, redação revogada removida) | atos oficiais não protegidos (Lei 9.610/1998, art. 8º, IV) | sim | sim | sim | 35 |
| Resumos acadêmicos listados pela Crossref com licença `CC BY 4.0` | CC BY 4.0, atribuição pelo DOI | sim | sim | sim, com DOI | 84 |
| UD-GSD, UD-Bosque (só CETENFolha, PT-BR), UD-PetroGold, UD-DANTEStocks | anotação CC BY(-SA); **texto de origem sem licença declarada** | sim | **não** | **não** (só contagens e ids) | 61 |
| B2W-Reviews01 | CC BY-NC-SA 4.0 | sim | **não** (decisão conservadora) | **não** | 24 |

Uma licença da anotação nunca foi tratada como licença do texto. Nenhum documento pessoal do mantenedor (TCCs/TGs usados em rodadas anteriores) entrou nesta campanha. Machado de Assis escreveu poemas em francês: excluídos (prova em PT-BR); a grafia pré-reforma das edições antigas fica como está (é dado real e testa a escolha legítima `historical_spelling`).

## Cobertura

| Família | Itens | Gêneros |
|---|---|---|
| literário | 219 | conto, romance (trecho, capítulo, capítulos), poema, estrofe, crônica, crítica, discurso, advertência |
| acadêmico | 90 | resumos (8 áreas), tese/dissertação técnica |
| institucional/jurídico | 35 | lei (artigo, capítulo, íntegra) |
| jornalístico | 39 | notícia, notícia/blog |
| comercial/consumidor | 24 | avaliação positiva e negativa |
| redes sociais | 20 | tweet de mercado |

Faixas: micro 44, curto 145, médio 122, longo 108, documento 8.

**Não coberto** (sem fonte lícita disponível nesta rodada): mensagens e WhatsApp reais, e-mail, documentação técnica PT-BR escrita por pessoas, orientação de saúde, criativo, fala regional transcrita. Nenhum exemplo sintético foi posto no lugar deles e chamado de real.
## Piloto online pós-Prova de Fogo

A coleta de 20/11 reuniu cinco recortes autorizados em poesia, teatro, decreto, resumo acadêmico e manual técnico. A licença de C-ORAL-BRASIL I foi confirmada na fonte primária. Fala contemporânea, redações e notícia ficaram fora da geração por acesso ou direitos insuficientemente verificados. [Manifesto, fontes e condições](ONLINE_PILOT.md).
