# Normas, editais e rubricas (v0.8, CP10–CP11)

O que foi implementado da [visão de normas](../../architecture/V08_STANDARDS_VISION.md), com que fontes reais e com que limites.

## Implementado

| ID | Componente | Onde | Estado |
|---|---|---|---|
| ST-01 | Standards Registry: uma ficha YAML por fonte (autoridade, série, edição, publicação, vigência, ano do evento, tipos de documento, direitos sobre o texto, verificação, critérios com verificação própria), validação estrita | `voznativa/standards.py`, `voznativa/data/standards/` | IMPLEMENTED_AND_TESTED |
| ST-02 | Applicability Resolver: escolhe a edição **vigente na data do documento**, nunca a mais recente por padrão; edital de um ano não vale para outro | `standards.resolve`, `voznativa standards resolve` | IMPLEMENTED_AND_TESTED (replay histórico com fichas **sintéticas**) |
| ST-03 | Precedência: duas edições válidas da mesma série dão `CONFLICTED` e pedem uma pessoa; nenhuma escolha silenciosa. Precedência entre fontes de séries diferentes (edital × norma geral) ainda não tem campo próprio | `standards.resolve` | IMPLEMENTED_PARTIAL |
| ST-04 | `document_profile` opcional no Context Contract; sem ele, o contrato é idêntico | `router.route(..., document_profile=)`, `voznativa route --document-profile` | IMPLEMENTED_AND_TESTED |
| ST-05 | Rubric Engine: critério objetivo só é checado com fonte aplicável **e** critério ao menos `SOURCE_CITED`; subjetivo vira `NEEDS_JUDGMENT`; nenhuma nota, total ou peso inventado | `voznativa/rubric.py`, `voznativa rubric` | IMPLEMENTED_AND_TESTED (checagens: `word_range`, `line_range`, `required_sections`) |
| ST-06..ST-08 | exemplares, gerar → criticar → revisar, temas sintéticos | — | NOT_IMPLEMENTED (exigem avaliadores humanos para não virar autoavaliação) |

Escada de verificação: `CATALOGUED` (nomeada, não conferida) → `SOURCE_CITED` (URL oficial e data vistas na página oficial, com data da consulta) → `VERIFIED` (também o sha256 do arquivo oficial). `STALE`, `CONFLICTED`, `BLOCKED` explícitos. Decisões: `APPLICABLE` (só com `VERIFIED`), `APPLICABLE_UNVERIFIED` (`SOURCE_CITED`: critérios objetivos rodam, mas a fonte fica marcada como não conferida por hash), `UNKNOWN`, `NOT_APPLICABLE`, `CONFLICTED`, `STALE`, `BLOCKED`.

## Piloto Enem (fontes reais, verificação real)

| Ficha | Estado | O que foi conferido |
|---|---|---|
| `inep-enem-redacao-cartilha-2026` | `SOURCE_CITED` | página oficial do gov.br lida em 2026-11-07: título, Inep, publicação 18/09/2026, links de download, a descrição da redação (dissertativo-argumentativa; ponto de vista com argumentos; proposta de intervenção que respeite os direitos humanos). **O PDF não foi baixado**: o servidor do Inep fechou a conexão a partir desta máquina e a tentativa de contornar o bloqueio foi recusada pela política da sessão. Sem hash, não é `VERIFIED` |
| `inep-enem-redacao-cartilha-2025` | `CATALOGUED` | só fontes secundárias (imprensa, cursinhos); página oficial da edição não localizada. O resolver nunca a aplica |

Critérios: os três da página oficial são subjetivos e viram `NEEDS_JUDGMENT`. As "cinco competências de até 200 pontos" e o limite de linhas aparecem só em fontes secundárias: ficam `CATALOGUED` e `NOT_ENFORCED`, sem número registrado. Nenhuma redação exemplar, texto da cartilha ou nota foi copiada. O VozNativa não atribui nota do Enem.

**Para chegar a `VERIFIED`:** o mantenedor baixa o PDF oficial no navegador, e o sha256 dele entra na ficha com a data; os critérios lidos no arquivo passam a `VERIFIED` um a um, com a página de origem.

## Piloto acadêmico

NOT_RUN nesta rodada: nenhum manual institucional, edital de iniciação científica ou norma foi conferido na fonte oficial. As normas ABNT são pagas (só metadados e paráfrases poderiam entrar). O replay histórico do resolver usa fichas **sintéticas** (`universidade-exemplo`, rotuladas como tal nos testes) para provar a regra de edição por data; nenhuma delas descreve uma instituição real.

## Limites

- Precedência entre séries diferentes não tem campo próprio: hoje, duas fontes de séries diferentes aplicáveis ao mesmo documento são listadas lado a lado.
- As checagens objetivas são estruturais (tamanho, linhas, seções); citação e referência existentes continuam com `ground`/`diagnose`.
- `APPLICABLE_UNVERIFIED` roda checagens de critérios citados da página oficial; o relatório sempre mostra fonte, edição, vigência e estado de verificação.
