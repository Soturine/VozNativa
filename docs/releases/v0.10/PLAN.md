# Plano da v0.10.0 — inteligência contextual, conhecimento e dogfood recíproco

> Criado no CP0 (18/11/2026), **antes de qualquer mudança de comportamento**. Os critérios R1–R15 abaixo ficam congelados: podem ganhar gates novos (por exemplo, um bloqueador de segurança descoberto depois), nunca perder piso nem denominador. Base: `v0.9.0` (tag anotada `e83eb0c` → `main` `6b487f7`), branch `dev/v0.10.0`.

## Leitura crítica do pedido

O prompt mestre pede quinze checkpoints, cada um do tamanho de uma release. Uma rodada só não sustenta tudo com prova; prometer tudo seria repetir o erro que as v0.8/v0.9 evitaram (estado declarado sem execução). A regra desta rodada:

1. **Primeiro o que muda segurança e falso verde** (P0/P1): juiz de relação desconhecida aceito (`unknown` → `accepted_by_llm`), relações discursivas inventadas ou trocadas sem sinal, futuro → passado sem sinal (achado no CP0, `sf-10`), particípio coordenado perdido (V09-GAP-07).
2. **Depois o que reduz falso vermelho medido** (os quatro falsos alarmes do CP7 da v0.9) sem desligar checagens.
3. **Depois capacidades novas com contrato pequeno e verificável**: TaskContext aberto (extensão do contrato de contexto v3 do router, não um segundo motor), status de diagnóstico, registro de conhecimento, Knowledge Watcher em modo report/propose.
4. **Dogfood recíproco executado de verdade** (Assertiva, Derivanta, VozNativa) com correções no repositório dono.
5. O que exigir pessoa, chave, modelo local ou permissão fica `NOT_RUN`/`BLOCKED` com causa, sem fingir.

Desvios do prompt, com motivo:

- **Sem banco vetorial nem embeddings** na camada de conhecimento: o volume (dezenas a centenas de registros) cabe em seleção por metadados e termos; uma dependência pesada não se paga. Revisável se a medição mostrar perda de recall.
- **Sem LoRA/fine-tuning** (trilha opcional; custo e licença não justificam nesta rodada).
- **Agendamento hospedado do Watcher não é criado** sem consentimento explícito de custo/segredos: entrega `SCHEDULER_READY` (comando local + instruções de Task Scheduler/cron), não "monitoramento ativo".
- Documentação consolidada num conjunto menor de arquivos (o prompt permite): ver índice no fim.

## Checkpoints

| CP | Entrega | Prova mínima |
|---|---|---|
| CP0 | estado Git/GitHub, inventário, conjuntos congelados, baseline, critérios | este plano, `AS_IS`, `GAP_REGISTER`, `ROADMAP_RECONCILIATION`, `EXECUTION_STATE`, `evals/v010/MANIFEST.json` |
| CP1 | pesquisa (Letras, normas, ENEM, corpora, ferramentas, APIs) | `RESEARCH_REGISTER.md` com URL, data de consulta, licença, decisão |
| CP2 | TaskContext aberto (atributos extensíveis com proveniência), `unknown`/`mixed`, prompt de interpretação agent-led | conjunto `context` congelado, testes antes/depois |
| CP3 | registro de conhecimento linguístico + recuperação seletiva com orçamento, proveniência, offline, defesa de injeção | testes de seleção, proveniência e injeção |
| CP4 | status de diagnóstico (`ERROR_CONFIRMED` … `NO_CHANGE_EXPECTED`) e regras novas de alta confiança com variantes legítimas | conjunto `diagnose` congelado |
| CP5 | relações discursivas (explícitas e implícitas) no `compare` | conjunto `semantic` congelado (relações) |
| CP6 | relação do juiz (taxonomia ampliada; `unknown` não aceita), particípio coordenado, futuro/passado, falsos alarmes do CP7 | testes de defeito vermelho→verde, controles |
| CP7 | corpora e fontes reais: matriz de elegibilidade, perfil ENEM como gênero opcional | `CORPUS_ELIGIBILITY` (em `SOURCES_AND_CORPORA.md`), corpus efetivamente lido onde lícito |
| CP8 | Knowledge Watcher (conectores por contrato, cache, ETag, propostas, segurança de rede) | fixtures 403/429/5xx/redirect/tamanho/licença/fonte removida; fonte real consultada se a rede permitir |
| CP9 | manutenção: duplicações e código morto **provados** | `MAINTAINABILITY.md`, Derivanta antes/depois |
| CP10 | ablações com modelo real (contexto, memória, candidatos) | runs com custo, chamadas e limites |
| CP11 | dogfood recíproco nos três repositórios, correções no dono | `BIDIRECTIONAL_DOGFOOD.md`, commits/PRs separados |
| CP12 | benchmarks v0.9 × v0.10, mutação, perf | `EVALUATION.md` |
| CP13 | segurança, privacidade, docs, instalação | docs sincronizados |
| CP14 | qualificação, PR, merge, CI final, tag, release | `RELEASE_QUALIFICATION.md` |

## Critérios de release (congelados no CP0)

Números de base medidos no CP0 em worktree limpa de `v0.9.0` (ver `EXECUTION_STATE.md`).

| # | Critério | Piso |
|---|---|---|
| R1 | baseline da v0.9.0 reproduzida | `qualify.py --scope release --offline` em worktree da tag sem FAIL local; hashes dos conjuntos congelados (v0.8, v0.9) inalterados |
| R2 | sem regressão P0/P1 | testes de privacidade/segurança PASS; holdout v0.9 ≥ 18/18 riscos; regressão congelada v0.8 ≥ 88/89; nenhum falso verde novo conhecido sem correção ou risco aceito registrado |
| R3 | testes locais e pacote | `qualify.py --scope release` sem FAIL local na revisão final (sdist → wheel → venv → smoke → suíte contra o wheel) |
| R4 | benches e predicados ≥ v0.9 | v4 22/22, v5 36/36, predicados ≥ 19/20 com falso alarme ≤ 1/18; v0.9 development ≥ 31/31 com falso alarme ≤ 4/20; v0.9 holdout ≥ 18/18 com falso alarme ≤ 2/10. Piora só se for correção de falso vermelho documentada caso a caso |
| R5 | capacidades contextuais operacionais | conjunto `context` development 6/6; holdout reportado; execução com **modelo real** em ≥ 6 textos de gêneros não mapeados (inclui misto e desconhecido) com saída registrada; se nenhum modelo real disponível, R5 = NOT_RUN e a release não declara a capacidade como verificada em modelo |
| R6 | semântica, diagnóstico e edição desnecessária | v0.10 semantic development: sensibilidade ≥ 20/21 e falso alarme ≤ 2/13 (base 16/21, 5/13). Diagnose development ≥ 6/7 e falso alarme 0/9 (base 3/7, 0/9). Holdouts (rodados uma vez, no fim): sensibilidade ≥ base e falso alarme ≤ base, ambos medidos na mesma execução. Edição desnecessária com modelo real: o engine não altera mais textos bons do que a v0.9 no mesmo conjunto |
| R7 | Watcher seguro em report/propose | testes de rede negada, 403, 429, 5xx, redirect para endereço privado, resposta acima do limite, licença alterada, fonte removida e registro falso; nenhum modo aplica código; ≥ 1 fonte real consultada se a rede permitir (senão NOT_RUN registrado) |
| R8 | fontes e dados | matriz de elegibilidade por finalidade; nenhum texto restrito no Git (gate de privacidade + revisão) |
| R9 | dogfood recíproco real | Assertiva `audit --execute` e Derivanta (inspeção/compare) executados no VozNativa base e candidato; VozNativa executado em documentação real de Assertiva e Derivanta; cada defeito confirmado corrigido no repositório dono com teste vermelho→verde e suíte do dono, ou registrado BLOCKED com causa. NOT_RUN reprova R9 |
| R10 | mutação nos fluxos novos | mutantes dirigidos em relação do juiz, relações discursivas, status de diagnóstico, guarda de URL do Watcher e TaskContext: ≥ 90% mortos, sobreviventes triados |
| R11 | desempenho | `perf_compare.py` (CPU, 17.600 palavras) ≤ 1,15 × a medição da v0.9.0 feita no mesmo hardware nesta rodada; teste de tempo existente sem afrouxar limite |
| R12 | integrações honestas | cada integração com estado REAL/STUB/NOT_RUN; nenhuma alegação por leitura de manifest |
| R13 | privacidade | gate antes de cada push (patch de cada commit + mensagens), no intervalo inteiro e com `--tree` no fechamento; nenhum achado aberto |
| R14 | plataformas | Windows 3.12 e 3.11 locais; CI manual final 8/8 (Linux/Windows 3.11–3.13) na `main` |
| R15 | coerência de release | versão `0.10.0` em todos os lugares, tag anotada, wheel/sdist da tag, `SHA256SUMS` conferido depois do download, docs e links |

Externos (não obrigatórios, nunca PASS automático): revisão humana cega, holdout independente, juiz de outro fornecedor, Codex/Gemini, modelo local real, macOS, renderização DOCX no Word/LibreOffice.

## Orçamento

- Provider real: teto **US$ 5** na rodada inteira (writer/judge separados), registrado por campanha.
- GitHub Actions: uma CI manual final; novas execuções só para falha genuína.
- Rede: consultas de pesquisa e do Watcher limitadas, com `User-Agent` genérico (sem dados do mantenedor).

## Documentos da rodada (consolidados)

`PLAN` · `AS_IS` · `EXECUTION_STATE` (inclui baseline de desempenho) · `GAP_REGISTER` · `ROADMAP_RECONCILIATION` · `TRACEABILITY` · `DECISIONS` · `RESEARCH_REGISTER` (inclui política de fontes) · `SOURCES_AND_CORPORA` (licenças e elegibilidade) · `CONTEXT_AND_KNOWLEDGE` · `LINGUISTICS_AND_DISCOURSE` · `KNOWLEDGE_WATCHER` · `MAINTAINABILITY` · `BIDIRECTIONAL_DOGFOOD` · `EVALUATION` · `ASSURANCE` · `RELEASE_QUALIFICATION` · `RELEASE_NOTES` (inglês).
