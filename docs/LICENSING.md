# Licenciamento: proposta e inventário de terceiros

**Estado:** o repositório ainda **não tem licença**. Este documento é uma proposta; nada aqui aplica licença ao projeto. Até a decisão, ninguém tem permissão legal para reutilizar o código.

## 1. Proposta para o VozNativa

| Artefato | Proposta | Motivo |
|---|---|---|
| Código (`voznativa/`, `scripts/`, `evals/*.py`) | Apache-2.0 | Permissiva, com concessão explícita de patentes e regra clara de NOTICE para contribuições. |
| Documentação e referências originais (`docs/`, `references/`, `SKILL.md`) | Apache-2.0 (mesma licença, para simplificar) ou CC BY 4.0 | Decidir junto com o código; CC BY 4.0 é mais comum para prosa. |
| Léxicos e dados próprios (`voznativa/data/*`) | Apache-2.0 | Escritos para o projeto (ver `evidence.basis` em cada arquivo); nenhum foi copiado de terceiros. |
| Casos de eval/benchmark (`evals/**/*.jsonl`, `benchmarks/cases/`) | Apache-2.0 | Sintéticos, escritos para o projeto; não contêm texto de corpus. |

Para aplicar: adicionar `LICENSE` (texto Apache-2.0), `NOTICE`, o campo `license` no `SKILL.md`/`pyproject.toml`/`.claude-plugin/plugin.json` e remover a nota "licença não definida" do README.

## 2. Regra de separação

Código, corpora, modelos e datasets têm licenças independentes. A licença do VozNativa **nunca** se estende a material de terceiros, e material de terceiros só entra no repositório quando:

1. a licença foi verificada na fonte oficial, com data;
2. a redistribuição é permitida para o uso pretendido;
3. a atribuição exigida está no `NOTICE` ou junto do artefato.

Hoje **nenhum** texto, léxico, modelo ou dataset de terceiros está incluído no repositório.

## 3. Inventário (verificado em 2026-10-19; atualizado em 2026-10-20)

"Verificado" = lido na fonte oficial ou na API da plataforma nesta data. "Reportado" = só em fonte secundária; precisa de checagem antes de uso.

### Corpora

| Fonte | Licença | Status | Consequência para o VozNativa |
|---|---|---|---|
| Corpus Carolina | 1.3 Ada (portal USP): cabeçalho CC BY-NC-SA 4.0. 2.0.1 Bea (card Hugging Face `carolina-c4ai/corpus-carolina`): `cc-by-4.0`, e os cabeçalhos dos arquivos dizem CC BY 4.0. A licença **por documento** varia: no recorte do piloto, 4.824 CC BY, 10 CC BY-SA, 2 CC BY-NC-SA, 1 GFDL (`evals/corpus/carolina-pilot.json`). | Verificado para a 2.0.1 (card e cabeçalhos); conflito com a 1.3 segue | Piloto só de metadados (nenhum texto guardado). Qualquer ingestão de texto teria de filtrar por licença de documento e atribuir; BY-SA e GFDL impõem a mesma licença a derivados. |
| C-ORAL-BRASIL I | CC BY-NC-SA 4.0 | Reportado (arXiv 2110.15731) | Uso não comercial; derivados sob a mesma licença. Centrado em Belo Horizonte/MG: não representa fala nacional. |
| CORAA ASR v1.1 | CC BY-NC-ND 4.0 | Reportado (documentação CORAA) | Sem derivados redistribuíveis; só estatística interna. |
| NURC-SP Corpus Mínimo | CC BY-NC-ND 4.0 | Reportado (2022, Portulan CLARIN) | Idem. Licença do NURC-SP Audio Corpus (2024) não verificada. |
| Projeto SP2010 | **Não encontrada** | Lacuna | Contatar GESOL-USP antes de qualquer uso. |
| ALiB | Publicações com direitos autorais; dataset aberto não identificado | Lacuna | Usado só como referência bibliográfica: o pack `br-norte-lex-mandioca` (v0.5.0) guarda formas, contagens e proporções publicadas por Romano (2020), com citação; nenhum texto do atlas ou do artigo é reproduzido. |
| ALIP (Iboruna, UNESP) | Sem licença definida; uso acadêmico com cadastro (CORAA, arXiv 2110.15731) | Reportado, não verificado no site | Não usar até haver termos de uso verificados. |
| PHPB | Termos não localizados | Lacuna | Diacrônico; fora do escopo de packs atuais. |

### Modelos (candidatos para trilhas opcionais)

| Modelo | Licença (card HF) | Status |
|---|---|---|
| `neuralmind/bert-base-portuguese-cased` (BERTimbau) | MIT | Verificado |
| `PORTULAN/albertina-900m-portuguese-ptbr-encoder` | "other" (ler a licença no repositório do modelo) | Verificar texto |
| `PORTULAN/gervasio-7b-portuguese-ptbr-decoder` | MIT | Verificado |
| `TucanoBR/Tucano-2b4` | Apache-2.0 | Verificado |
| `StyleDistance/mstyledistance` | MIT | Verificado |
| `maritaca-ai/sabia-7b` | campo ausente no card; fontes secundárias citam a licença LLaMA-1 (pesquisa) | Não usar sem verificação |
| `ruanchaves/bert-base-portuguese-cased-assin2-entailment` (NLI testado na v0.3.0) | **nenhuma declarada** no card; pesos em pickle | Usado só num experimento isolado em contêiner, sem redistribuir; rejeitado como gate |
| spaCy `pt_core_news_sm` 3.8.0 (testado na v0.3.0) | CC BY-SA 4.0 (spaCy em si: MIT) | Verificado. Não adotado; adotar exigiria tratar a licença ShareAlike do modelo |

### Datasets e ferramentas

| Recurso | Licença | Status |
|---|---|---|
| ASSIN2 (`nilc-nlp/assin2`) | `unknown` no card | Lacuna: não redistribuir; uso em pesquisa só após verificação |
| XFORMAL (`Elbria/xformal-FoST`) | repositório sem licença | Lacuna |
| NILC-Metrix | AGPL-3.0 | Verificado (GitHub). Não incorporar ao código; só como ferramenta externa opcional, em processo separado. |

### Skills e projetos comparados

| Projeto | Licença | Uso no VozNativa |
|---|---|---|
| blader/humanizer (`8c307f3`) | MIT | Estudado; nada copiado. |
| phuryn/work-humanizer (`0a90657`) | MIT | Estudado; benchmark do autor tratado como hipótese externa. |
| fabricioctelles/skills `humanizar` | Apache-2.0 (com NOTICE) | Estudado; nada copiado. Cópia exigiria preservar NOTICE. |
| mackswendhell/humanizer-pt-br | MIT | Estudado; nada copiado. |
| gabrielkashimarki/humanizer-ptbr | **sem licença** | Não reutilizar nada. |
| Emulate-1 | API proprietária | Só como sistema de comparação via API; nada embarcado. |

### Skills de terceiros usadas como braços de benchmark (v0.5.0)

Buscadas por commit no momento da execução para `benchmarks/.cache/` (ignorado pelo Git); **nunca** copiadas para o repositório.

| Skill | Commit | Licença |
|---|---|---|
| blader/humanizer | `0ef9fe5` | MIT |
| phuryn/work-humanizer | `0a90657` | MIT |
| fabricioctelles/skills `humanizar` | `ec4099f` | Apache-2.0 |
