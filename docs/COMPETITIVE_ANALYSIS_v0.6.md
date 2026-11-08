# Pesquisa competitiva v0.6 (CP11, consulta em 2026-11-05)

> **Estado: histórico (pesquisa da v0.6, datada).** Pesquisa mais recente: [v08/RESEARCH_LANDSCAPE.md](v08/RESEARCH_LANDSCAPE.md).

Esta pesquisa complementa a v0.5 (`docs/COMPETITIVE_ANALYSIS_v0.5.md`), feita no mesmo dia. Por isso as skills de humanização já analisadas não foram relidas. O foco são as áreas novas da v0.6: plataforma de corpora, gíria com tempo, comunidades e textos longos.

As fontes foram a API do GitHub (licença, último push, release) e buscas na web; os links estão no fim. Nada de terceiros foi copiado.

## Ferramentas de corpus e deduplicação

| Ferramenta | Estado lido | Licença | Relação com o que a v0.6 fez | Decisão |
|---|---|---|---|---|
| ChenghaoMou/text-dedup | último push 2026-03-09; última release `2023.09.20` | Apache-2.0 | MinHash/SimHash, filtro de Bloom e suffix array em escala de bilhões | **REJECT** como dependência. O MinHash próprio (64 permutações, 16 bandas, Jaccard ≥ 0,8 confirmado) processou 31.057 registros em 9,8 s. Uma dependência nova não traz ganho medido nessa escala. Reavaliar acima de ~1 milhão de registros |
| huggingface/datatrove | release `v0.10.1` (2026-09-30), push 2026-11-04 | Apache-2.0 | pipeline com assinatura, buckets e clusters, no mesmo desenho do `processing.py` | **MONITOR**: é a referência se o volume crescer. O VozNativa mantém a proveniência por registro e a divisão sem vazamento por grupo e cluster, coisas que a deduplicação genérica não faz |

## Gíria datada e léxicos

- **Não encontramos dataset aberto e datado de gíria PT-BR.** O dicionário de gíria de Gurgel (7ª ed., 2005, 27.500 verbetes) é obra comercial: **REJECT** como dado e, no máximo, referência secundária (E1). A literatura de lexicografia da gíria (Preti, ALFA) confirma que dicionários raramente marcam o período.
- **Decisão mantida:** atestar formas em corpora registrados, com período vindo do registro (`scripts/slang_attest.py`).
- **Próximo passo, EXPERIMENT:** o Carolina, com licença por documento (já suportada pela política), cobre 1970–2021 e pode dar atestações posteriores a 2018. É o que falta para qualquer entrada chegar à época `current`.

## Literatura de domínio público

- **OBras** (Santos, Freitas, Bick, 2018; Linguateca): corpus de obras literárias brasileiras em domínio público, "totalmente anotado e parcialmente revisado por humanos". O registro de origem não declara licença, só "openAccess". Entrou no Corpus Registry como `CATALOGUED`, e a política o trata como `UNKNOWN`. Seria um controle literário com revisão humana, coisa que o corpus de Machado da v0.6 não tem.

## Skills PT-BR novas

| Projeto | Estado | O que tem | Decisão |
|---|---|---|---|
| felipegomss/agent-skills | push 2026-03-26; sem licença declarada | skill de humanização PT-BR; nada sobre gíria, região, comunidade ou texto longo nas páginas lidas | **MONITOR**; sem licença, nada pode ser reaproveitado |
| listagens "humanizer-ptbr" e "humanizer-rules" (claudskills.com) | registros de SKILL.md | listas de padrões e de substituições | **MONITOR**; mesma família do blader |
| Humanizer PRO MCP | serviço hospedado com login e assinatura | sem PT-BR específico confirmado | **REJECT**: pago e fechado, sem evidência |

Nenhuma ferramenta encontrada trata gíria com período, comunidade de prática como pacote com taxonomia, ou texto longo com segmentação que preserve dependências. Isso é observação das páginas e repositórios lidos, não prova de ausência.

## Limites desta pesquisa

- Foram feitas buscas web padrão e leituras pela API do GitHub.
- Os SKILL.md das listagens não foram lidos na íntegra.
- O tamanho e a licença do OBras não foram verificados no site da Linguateca.

## Fontes

- https://github.com/ChenghaoMou/text-dedup
- https://github.com/huggingface/datatrove
- https://periodicos.fclar.unesp.br/alfa/article/view/4199
- https://revistas.gel.org.br/rg/article/download/347/250/806
- https://dspace.rcaap.pt/entities/publication/ebe94d50-e3ff-48f2-a90a-688addcb786f/full
- https://www.skills.sh/felipegomss/agent-skills
- https://claudskills.com/skills/humanizer-ptbr/
- https://mcpservers.org/pt-BR/servers/khadinakbarlabs/humanizer-pro-mcp
