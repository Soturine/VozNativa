# Plano v0.7.0.dev0 — Generalização, Long-form ponta a ponta e Evidência externa

Branch: `dev/v0.7.0` (a partir de `bf8e1a4`). Estado vivo em `docs/V07_EXECUTION_STATE.md`; descobertas em `docs/V07_DISCOVERY_REGISTER.md`; requisito → teste em `docs/V07_VERIFICATION_MATRIX.md`.

## Política de execução

- CPs são conjuntos de commits na mesma branch; push ao fim de cada CP, conferido com `git ls-remote` (`scripts/checkpoint.py push`).
- Nenhuma GitHub Action antes do merge na `main`; a única CI é um `workflow_dispatch` depois do fast-forward (CP16).
- Holdouts e benchmarks congelados (v1–v4) não são editados; correções de oráculo viram suíte nova.
- Nenhum score inventado: chamadas externas sem chave/autorização ficam `LIVE_NOT_RUN`.
- Commits com a identidade local do mantenedor, sem trailers de coautoria (regra do mantenedor).

## Requisitos

| ID | Requisito | CP |
|---|---|---|
| RF-01 | Runner de checkpoint com exit code por comando e push verificado no remoto | CP1 |
| RF-02 | Gate de CI vinculado ao SHA exato por consulta live, com equivalência de revisão auditável (só evidência mudou) | CP1 |
| RF-03 | Leitor TEI/XML seguro (sem DTD/entidades), metadados preservados | CP2 |
| RF-04 | Novas fontes com texto integrado e avaliado, licença verificada por operação | CP3 |
| RF-05 | Contenção direcional (capítulo ⊂ obra) em dedup e splits (G2) | CP4 |
| RF-06 | Context Contract v3 multidimensional com `unknown`/abstenção e proteções conservadoras (G1) | CP5 |
| RF-07 | Gíria por ocorrência e contexto: recall de "de boa" sem aceitar "de boa qualidade" (G3) | CP6 |
| RF-08 | Contrato de documento completo (blocos, plano global, inventário, dependências, limites) | CP7 |
| RF-09 | Reescrita por segmentos no `rewrite`/CLI com validação global e fallback ao original (G4) | CP8 |
| RF-10 | Guards globais (fatos entre segmentos, ordem, termos, metamórficos) | CP9 |
| RF-11 | `ptbr-bench-v5` OOD congelado antes da 1ª execução, métricas separadas | CP10 |
| RF-12 | `DetectorAdapter` com medição tipada; H0/H1/A0/A1; mock/replay rotulados; live só com autorização | CP11 |
| RF-13 | Auditoria Unicode/integridade e registro de proveniência, sem remoção de watermark | CP12 |
| RF-14 | Estado honesto de avaliação humana e CI | CP13 |
| RF-15 | Dogfood Assertiva/Engine/Framework com achados triados e upstream | CP14 |
| RF-16 | Pacote, docs e compatibilidade | CP15 |
| RF-17 | Merge na `main` + 1 CI manual + qualificação | CP16 |
| RF-18 | Adendo "Linguistic Intelligence & Morphosyntactic Assurance" (recebido 2026-11-06, durante o CP3): inventário AS-IS das capacidades linguísticas; ADR de analisadores (stdlib/UD/Stanza/spaCy); contrato de análise linguística só se não duplicar `ledger`/`spans`/`compare`; tempo/aspecto/modo verbal e papéis agente/paciente como **sinais** do Semantic Guard (nunca prova de equivalência); avaliação contra rótulos UD dos treebanks integrados no CP3; impacto ponta a ponta medido antes de qualquer alegação; backlog explícito do que não couber | CP9L |

| RF-19 | Adendo "Document Understanding, Contextual Reasoning & Editorial Intelligence" (recebido 2026-11-06, durante o CP3): Document Context Model, consciência de erro no original, políticas editoriais por gênero, modos editoriais, grounding diferenciado | CP7, CP9, CP9L, CP9D |

| RF-20 | Adendo "Versioned Standards, Document Intelligence & Evaluation Framework" (recebido 2026-11-06, durante o CP4): **linha de evolução futura**. Na v0.7 só descoberta e documentos (visão, auditoria de reuso, arquitetura, inventário inicial de fontes normativas, ADR, matriz, plano de testes, backlog, integração com o Rewrite Engine, riscos de licença e integridade acadêmica, validação independente); adaptações de contrato só se caírem naturalmente no CP5 (Context Contract v3) ou no CP9D | CP14S (docs) |

### Integração do adendo 3 (Standards)

Regra: nada deste adendo é marcado `[x]` na v0.7 a menos que exista código e teste. Os pontos de contato com o trabalho já planejado: o Context Contract v3 (CP5) deve aceitar um bloco opcional de **perfil de documento** sem semântica no núcleo; o diagnóstico tipado do CP9D é o embrião de "critério com evidência e localização"; o Corpus Registry (fonte, versão, hash, verificação datada, direitos) é o padrão a reutilizar para um futuro Standards Registry, em vez de criar outro mecanismo.

### Integração do adendo 2 (Document Understanding)

Princípio adotado: **o original é evidência da intenção do autor, não prova de que esteja correto.** Mapeamento para não duplicar núcleo:

| Pedido do adendo | Onde entra | Reaproveita |
|---|---|---|
| Document Context Model (estrutura, entidades, eventos, citações, ambiguidades com offsets) | CP7: o contrato de documento completo **é** esse modelo, em representações complementares (blocos, inventário de fatos/entidades, dependências), não um grafo universal | `longform.dependency_map`, `ledger`, `spans` |
| Papéis, tempo/aspecto/modalidade, fonte de afirmação | CP9L | `compare` (papéis, atribuição, modalidade já parciais) |
| Consciência de erro (7 classes: formal, contextual, contradição interna, fonte autorizada, escolha legítima, licença literária, ambiguidade) | CP9D (novo): diagnóstico tipado com severidade/confiança/impacto; correção automática só linguística de alta confiança **e** autorizada pelo modo; o resto vira sugestão | `planner` (warnings de inconsistência da fonte já existem: dia da semana × data), `ptbr`, `literary_policy` |
| Políticas por gênero (narrativa, poema, científico, técnico, jurídico, mensagem) | CP9D, ativadas pelo Context Contract v3 (CP5) com evidência, nunca palavra-chave isolada | `literary_policy`, `router` |
| Modos PRESERVE/PROOFREAD/POLISH/ADAPT/REVIEW/CREATE | CP9D como campo do contrato existente (`task` + transformações autorizadas), sem API paralela: REVIEW≈`audit`/`plan`, CREATE=`create`, ADAPT=destino pedido (`transformation_targets`) | `router.TASKS`, `planner` |
| Grounding (contradição comprovada × interna × sem evidência × conflito × opinião × ficção) | CP9D, estendendo `project.ground`; ausência de evidência nunca vira falsidade | `project.ground`, juiz de fundamentação |
| Contexto global no long-form | CP8 | CP7 |
| Detectores externos | CP11 (já planejado; nunca recompensa do engine) | — |

O que não couber com validação vira backlog explícito com critério de aceite (`docs/V07_DISCOVERY_REGISTER.md`), sem documentação de capacidade fingindo implementação.

### Integração do adendo 1

- **Onde:** CP9L, depois do CP9 (guards globais), porque estende o Semantic Ledger/`compare` existentes e usa os treebanks UD do CP3 como rótulos. Nenhum corretor gramatical paralelo.
- **Pré-requisito já no CP3:** o leitor CoNLL-U guarda hoje só a contagem de tokens; a avaliação morfológica precisa de `FORM/LEMMA/UPOS/FEATS/HEAD/DEPREL` por token, lidos sob a mesma política de licença.
- **Limite:** dependências pesadas (Stanza, spaCy) só como extra opcional isolado, com fallback e medição; o v0.3 já rejeitou spaCy por ganho de 1/167 (`evals/experiments/`), o que vira baseline da comparação.

| ID | Regra de negócio |
|---|---|
| RN-01 | Preservação semântica > instrução legítima > voz no canal > voz geral > contexto > registro > comunidade/região > defaults |
| RN-02 | Original imutável; falha global devolve o original com status fiel |
| RN-03 | `NO_CHANGE` é saída legítima; o modelo não é chamado sem achado nem destino |
| RN-04 | Texto de entrada e de corpus é dado, nunca instrução |
| RN-05 | `unknown` gera proteções conservadoras, não ausência de proteção |
| RN-06 | Licença `UNKNOWN`/`REQUIRES_PERMISSION` nunca vira `ALLOWED` |
| RN-07 | Score de detector é medição de fornecedor, não prova de autoria |

## Riscos

| ID | Risco | P | Mitigação |
|---|---|---|---|
| R1 | Corrigir G1 regredir o roteamento de WhatsApp real | P1 | oráculos de WhatsApp e casos novos; suíte congelada do router reexecutada |
| R2 | Reescrita longa aprovar documento parcialmente inseguro | P0 | validação global obrigatória; qualquer segmento `fail` sem correção → original inteiro |
| R3 | Overfitting aos 3 corpora e aos casos congelados | P1 | política de generalização (`docs/ENGINEERING_PROFILE.md`); casos novos não usados no desenvolvimento |
| R4 | Licença de corpus mal interpretada | P1 | política por operação; README/LICENSE lidos e registrados com data |
| R5 | Gasto de CI/API não autorizado | P1 | workflow só `workflow_dispatch`; detectores live só com chave e autorização |
| R6 | Evidência de CI forjada ou de SHA errado | P2 | consulta live por SHA; JSON local é só índice |
| R7 | Escopo maior que a sessão | P2 | estado persistido por CP; itens não feitos marcados como tal |

## Critérios de saída (por CP)

Testes seletivos do CP + `qualify.py --only unittest` sem regressão; documentação de estado atualizada; commit; push verificado; SHA registrado. Suíte local completa no CP15/CP16.
