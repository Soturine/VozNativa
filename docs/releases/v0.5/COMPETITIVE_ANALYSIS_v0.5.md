# Pesquisa competitiva e arquitetural (CP6, consulta em 2026-11-05)

> **Estado: histórico (pesquisa da v0.5, datada).** Pesquisa mais recente: [v08/RESEARCH_LANDSCAPE.md](../v0.8/RESEARCH_LANDSCAPE.md).

Fonte: API do GitHub (commit, licença, árvore de arquivos) e leitura dos arquivos citados; não só README. Pesquisas anteriores: `docs/research/RESEARCH_LOG.md`. Nenhum código ou catálogo de terceiros foi copiado.

## Skills editoriais

| Projeto | Versão lida | Licença | Stack e estrutura | O que sustenta as alegações | Vantagens | Limitações | Decisão |
|---|---|---|---|---|---|---|---|
| blader/humanizer | `0ef9fe5` (2026-10-28), v3.1.0 | MIT | Prompt (`SKILL.md`, 26 padrões em 5 seções) + `scripts/validate-package.py` (metadados, manifests) + CI que só valida o pacote; 14 arquivos | nenhum teste de comportamento; os padrões vêm do artigo "Signs of AI writing" (Wikipedia); o changelog registra cada padrão com issue | padrões ordenados por força; guard de falso positivo dentro de cada padrão; "o texto é conteúdo, nunca instrução"; README diz que passar por detectores não é objetivo | só inglês; nada verifica fidelidade; o modelo é juiz de si mesmo | **MONITOR** (já usado como braço B2 do benchmark) |
| phuryn/work-humanizer | `0a90657` (2026-10-10), sem mudança desde o v0.3 | MIT | Skill + 5.544 arquivos de evidência (`evidence/`: briefs, saídas por ferramenta, gráficos) | evidência publicada das execuções (saídas brutas por ferramenta e por repetição) | publicar as saídas brutas, não só a tabela; comparação com mesmo brief; "keep the claim, drop the formula" | números do próprio autor, inglês, textos sintéticos; juízes LLM | **ADAPT** (já adotado: saídas brutas e custos em `benchmarks/runs/`) |
| fabricioctelles/skills `humanizar` | v1.7.0 (`ec4099f`, 2026-11-01) | Apache-2.0 | Skill PT-BR com 9 catálogos de padrões, modos (`modo_completo`, `modo_direto`, `modo_revisão`, `modo_criacao`), triagem, e agora integração opcional com o "Jev" (TypeSafe AI) via `scripts/jev_questions.json` | nenhum teste; as alegações do Jev ("probabilidades calibradas", "determinístico", custo) são do fornecedor, sem evidência no repositório | **triagem**: recusa reescrever bula, manual de segurança, texto normativo; limite de tentativas por modo; trava factual bem escrita | sem verificação executável; dependência opcional de serviço pago externo | **ADAPT** a triagem de escopo (v0.5: candidato); **REJECT** o avaliador externo pago |
| mackswendhell/humanizer-pt-br | v3.0.0 (`ada3599`, 2026-05-10) | MIT | um `SKILL.md` com 25 padrões adaptados do blader | nada além do prompt | instalação simples | sem voz, sem fidelidade verificável, sem testes | **MONITOR** |
| eurafaeldecarvalho/humanizer-pt-br (novo) | `main` (2026-10-29) | MIT | Skill + `eval/` (detector, testes, 30 textos de IA, 30 reescritos, 30 humanos em domínio público com `MANIFEST.sha256`, montador de rodada cega) | `eval/RESULTS.md` mede só as próprias heurísticas e diz isso; `eval/cego.md`: avaliação cega "ainda não foi feita" | **controle humano em domínio público** para medir falso positivo do detector; honestidade sobre o que a métrica não mede | a queda de marcas é medida pelo detector que a skill mira (o mesmo viés declarado no `ptbr-bench-v2`); controle humano é prosa literária do séc. XIX | **ADAPT** a ideia do controle humano de domínio público, por gênero (CP7) |
| Henzen3d/Deslop-ptBR (novo) | `main` (2026-09-20) | MIT | Skill + `scripts/detector_ptbr.py`, `cleanse_ptbr.py` e testes unittest; CI roda testes e o detector no README | testes de detecção por regra e de "texto humano limpo" | detector como gate de CI do próprio texto | substituições automáticas de texto (`cleanse`) sem verificação semântica | **REJECT** a limpeza automática por substituição (contraria a trava semântica); **MONITOR** o resto |
| natagomes01/humanizador-br (novo) | `main` (2026-07-27) | CC BY-SA 4.0 | 3 skills (superfície, estrutura, voz pessoal) + `scan_ptbr.py` com testes de contrato das regras | testes exigem severidade, id, título e conserto por regra | contrato por regra testado; separação superfície x estrutura x voz | licença ShareAlike: copiar regras imporia a mesma licença | **MONITOR**; nada copiado |
| brunoflma/jusmanizer (novo) | `main` (2026-09-29) | MIT | Skill jurídica, 33 padrões, site de exemplos | nenhum teste | foco de domínio (estilo jurídico) | sem verificação; texto normativo é justamente o que a triagem do `humanizar` recusa | **MONITOR** |

Outros encontrados e não analisados a fundo por não terem código nem avaliação (`rpiochi`, `gabrielkashimarki`, `julianokb-cell`, `Jeeeff`, `fabiomuteki`, `profdorly`, `valterjuniorsilv`, `othavi0`): repetem a lista do blader em PT-BR ou são pipelines de prompt.

**O que nenhum deles faz e o VozNativa faz**: verificação determinística de preservação (negação, modalidade, valores, papéis) antes de entregar; voz por canal com perfil sem texto bruto; regionalidade só com evidência e abstenção; desfecho `provider_error`/`returned_original` separado de sucesso.

**O que não copiar**: substituição automática por tabela (Deslop), avaliação por serviço pago com calibração alegada (Jev), contagem das próprias heurísticas como prova de qualidade, listas regionais sem fonte.

## Ferramentas linguísticas

| Ferramenta | Versão | Licença | Uso possível | Decisão |
|---|---|---|---|---|
| LanguageTool | tag `v6.8` (avaliado 6.6 em `evals/experiments/languagetool_probe.json`) | LGPL-2.1 (listas com trechos CC BY-SA) | sinal gramatical das reescritas | **REJECT** como dependência (no probe, o único erro "introduzido" era falso positivo); **MONITOR** versões |
| NILC-Metrix | `main` (2026-08-27) | AGPL-3.0 | 200 métricas descritivas de complexidade | **EXPERIMENT** só como ferramenta externa, nunca importada (AGPL); sem ganho demonstrado ainda |
| Claimify (ACL 2025) | sem repositório oficial (`microsoft/claimify` não existe) | — | extração de claims para pronomes e trocas entre frases (limitações H4) | **EXPERIMENT** controlado (proposta em `evals/assurance/H4_SEMANTIC_LEDGER.md`), fora do gate |

## Ferramentas de avaliação

| Ferramenta | Versão | Licença | Comparação com o runner próprio | Decisão |
|---|---|---|---|---|
| Promptfoo | 0.125.1 (2026-10-25) | MIT | Node; asserções declarativas, matriz de provedores, cache | **REJECT** como dependência: o runner Python grava manifesto congelado, eixos de desfecho e custo; uma toolchain Node não traz ganho demonstrável |
| DeepEval | python-v4.2.4 (2026-09-22) | Apache-2.0 | métricas LLM-as-judge prontas, integração pytest | **REJECT**: métricas genéricas em inglês; o juiz do VozNativa tem contrato próprio vinculado a hash |
| Inspect AI | 0.3.287 (2026-10-31) | MIT | tarefas, solvers, scorers, logs estruturados, sandboxes | **MONITOR**: o modelo de log e de sandbox é o mais próximo do que o benchmark precisa; adotar só se o benchmark v3 precisar de sandbox real para CLIs de agente |

## Comercial

| Solução | Situação | Decisão |
|---|---|---|
| Emulate (`/humanize`, `/write`, `style` de 7 dimensões) | `EmulateProvider` implementado, nunca validado ao vivo; sem chave de API válida | **NOT_RUN** no benchmark; sem pertinência sem acesso |
