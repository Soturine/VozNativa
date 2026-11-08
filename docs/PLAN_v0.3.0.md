# Plano v0.3.0 — Semantic Intelligence & Author Voice

> **Estado: histórico (v0.3).** Plano daquela rodada; o atual é [v08/PLAN.md](v08/PLAN.md).

Consolida o escopo que seria a v0.2.1 (pendências da auditoria de qualificação), o que estava previsto para a v0.3 (Voice Model) e as dependências diretas de v0.4 (padrões PT-BR) e v0.8 (avaliação). Nada sai do roadmap: itens absorvidos aparecem nas versões originais com "→ v0.3.0".

Baseline: `evals/baselines/v0.3.0-start.json` (commit `595d7ae`, checkout limpo, 156 testes, suítes e execuções reais registradas).

Status por WP: **pendente**, **em andamento**, **implementado** (código + testes), **validado** (implementado + evidência registrada), **parcial**, **bloqueado** (depende de algo fora do meu alcance).

## Critérios obrigatórios para declarar a v0.3.0 concluída

1. Todos os WPs marcados como obrigatórios estão *validados*.
2. Nenhuma regressão: todas as suítes de dev passam; nenhum holdout tem falso verde.
3. Um holdout semântico **independente** (outra pessoa, protocolo de `evals/semantic/INDEPENDENT_HOLDOUT.md`) foi executado uma vez e o resultado foi registrado, qualquer que seja.
4. Benchmark skill-only prospectivo executado com dataset congelado antes da execução, com resultados publicados por sistema.
5. Pelo menos uma rodada de revisão humana cega registrada (julgamentos assinados de pessoas reais).
6. CI verde em Linux e Windows, Python 3.11–3.13.

Os critérios 3, 5 e 6 dependem de pessoas ou da conta do GitHub. Enquanto não forem cumpridos, a v0.3.0 fica como `0.3.0.devN`, nunca como release.

## Status em 2026-10-20 (commit `558a7cc`): **v0.3.0 NÃO concluída**

| Critério | Situação |
|---|---|
| 1. WPs obrigatórios validados | todos os obrigatórios que dependem só de código estão validados (tabela abaixo); M4.4 resultados e M6.5 abertos |
| 2. Sem regressão | 199 testes OK; holdouts congelados sem falso verde na execução atual |
| 3. Holdout independente | **aberto**: precisa de outra pessoa (`evals/semantic/INDEPENDENT_HOLDOUT.md`) |
| 4. Benchmark prospectivo | **cumprido**: `ptbr-bench-v1` congelado (`264e232`) antes da execução oficial (`benchmarks/runs/ptbr-bench-v1-20261020T060615Z.json`) |
| 5. Revisão humana cega | **aberto**: instrumento pronto, nenhum julgamento humano registrado |
| 6. CI verde | **bloqueado**: GitHub Actions recusa por cobrança da conta. Matriz local verde em `evals/compat/v0.3.0-dev-e679038.json` (não substitui CI) |

| WP | Status | Evidência / observação |
|---|---|---|
| M1.1 | validado | `holdout-v030.jsonl` congelado (`0a713f9`); primeira execução 15/24; depois das correções 24/24 (não cego, `7af6135`) |
| M1.2 | validado | ho-007 e h3-add-* sinalizados; guarda de oração única evita o falso vermelho "sai" → "será publicado" |
| M1.3 | validado | `evals/test_numerals.py`; "um/uma" continua ambíguo |
| M1.4 | validado | rel-cause-005 detectado; só frases adjacentes |
| M1.5 | validado | rel-entity-003 detectado; só entidades nomeadas |
| M1.6 | experimento registrado, **não adotado** | `evals/experiments/syntax_roles.json`: 1 detecção nova em 167 casos, 0 falso vermelho; ganho pequeno não justifica modelo CC BY-SA |
| M1.7 | experimento registrado, **rejeitado** | `evals/experiments/nli_probe.json`: 26/97 violações, nenhuma que o gate já não pegasse; 9/56 falsos vermelhos em reescritas válidas |
| M1.8 | validado | `--protect`, `evals/test_protected_terms.py` |
| M2.1 | validado (com ressalva) | separa 6/6 rascunhos e 7/8 naturais; `bm-email-001` (natural) é sinalizado e fica fora do teste; casos escritos pelo desenvolvedor |
| M2.2 | validado | execução real: achados 29 → 6, nenhuma regressão semântica; 7 textos naturais sem chamada ao modelo |
| M2.3 | pendente (não obrigatório) | — |
| M3.1 | implementado; experimento **inconclusivo** | `voice_match_synthetic_a.json`: com perfil mais perto em 2/4, autor sintético |
| M3.2 | implementado | drift por janela no relatório; limiar sem calibração |
| M3.3 | bloqueado | precisa de amostras reais consentidas |
| M4.1 | validado | congelado antes da execução |
| M4.2 | validado | execução oficial + reexecução pós-mudança do braço engine (post hoc, `1dc14b5`) |
| M4.3 | bloqueado | precisa de chave da API do Emulate |
| M4.4 | instrumento validado; **resultados abertos** | `voznativa blind-tasks/blind-review/blind-summary`, testes em `evals/test_blind_review.py` |
| M5.1 | validado | `evals/corpus/carolina-pilot.json` (só metadados) |
| M6.1 | validado | retries com backoff; `provider_error` sem exceção; testes em `evals/test_engine.py` |
| M6.2 | validado | `--redact` em `scripts/llm_integration.py`; `evals/test_privacy.py` |
| M6.3 | validado | `examples/README.md`, gerado por `scripts/make_examples.py` de execuções gravadas |
| M6.4 | validado (local) | Linux 3.11/3.12/3.13 (Docker) e Windows 3.11/3.12/3.13; smoke do wheel em Linux 3.11–3.13 e Windows 3.12 |
| M6.5 | bloqueado | cobrança do GitHub Actions |

## M1 — Semantic Intelligence

| WP | Objetivo | Alterações | Testes / evidência | Limitações conhecidas | Concluído quando | Obrig. |
|---|---|---|---|---|---|---|
| M1.1 Holdout prospectivo v0.3 | medir os gaps antes de mexer no código | `evals/semantic/holdout-v030.jsonl`, congelado com hash no MANIFEST antes de qualquer correção | primeira execução registrada | escrito pelo desenvolvedor (não independente) | arquivo congelado + `first_run` registrado | sim |
| M1.2 Adições dentro da frase | pegar orações inventadas (ho-007) sem regra específica | novidade por oração (vírgula, relativa, aposto) | regressão ho-007 + casos dev; falsos vermelhos medidos | paráfrase longa pode pedir revisão | ho-007 sinalizado; dev sem regressão | sim |
| M1.3 Números por extenso | "vinte e três" = 23, "mil e quinhentos" = 1500, "meia dúzia" = 6 | parser de numerais compostos | testes de equivalência e de troca | "um/uma" ambíguo com artigo | equivalências e trocas detectadas | sim |
| M1.4 Causalidade entre frases | "X. Por isso, Y." invertido | orientação de conectores no início da frase | casos dev + holdout | só frases adjacentes | rel-cause-005 detectado | sim |
| M1.5 Papéis em voz ativa/passiva | "A Acme comprou a Beta" → "A Acme foi comprada pela Beta" | triplas agente–verbo–paciente com detecção de passiva | rel-entity-003 + novos casos | só entre entidades nomeadas, sem sintaxe completa | rel-entity-003 detectado; passivas legítimas passam | sim |
| M1.6 Sintaxe opcional (spaCy) | sujeito/objeto com substantivos comuns e pronomes | camada opcional `voznativa[syntax]`, desligada por padrão | experimento: ganho medido nas suítes versus heurística | modelo CC BY-SA 4.0, ~15 MB | adoção só se houver ganho medido sem novos falsos vermelhos | não |
| M1.7 NLI opcional | sinal extra para antônimos fora do léxico e omissões | experimento com modelo ASSIN2 | taxa de detecção e de falso vermelho nas suítes | torch pesado; nunca prova equivalência | relatório de viabilidade registrado | não |
| M1.8 Spans configuráveis | termos que o usuário quer intocados | `--protect` / arquivo de termos | testes | — | termos protegidos geram `span_missing` | sim |

## M2 — PT-BR Writing Quality

| WP | Objetivo | Alterações | Testes / evidência | Limitações | Concluído quando | Obrig. |
|---|---|---|---|---|---|---|
| M2.1 Detector de padrões | operacionalizar `references/patterns/` (oficialês, ENEM-ismo, conectivos empilhados, gerundismo, fórmulas, nominalização, fechamento vazio, promocional) | `voznativa patterns`, dados versionados com isenções por gênero | casos positivos e falsos positivos por gênero; separação entre rascunhos com cara de IA e textos naturais | descritivo, nunca score de autoria | separa os conjuntos `ptbr-ai-drafts-v1` e `ptbr-v1` sem falso positivo em gênero isento | sim |
| M2.2 Quando e quanto mudar | NO_CHANGE fundamentado; reescrita dirigida aos achados | engine usa os achados no prompt e decide NO_CHANGE antes de chamar o modelo quando não há achado | execução real comparando resíduo de padrões e status semântico antes/depois | depende de M2.1 | resíduo de padrões cai sem piorar o status semântico, em execução real registrada | sim |
| M2.3 Planejamento por documento | consistência entre parágrafos em textos longos | só se houver ganho medido | experimento | — | decisão registrada | não |

## M3 — Author Voice

| WP | Objetivo | Alterações | Testes / evidência | Limitações | Concluído quando | Obrig. |
|---|---|---|---|---|---|---|
| M3.1 Voice match mensurável | medir se a reescrita se aproxima do perfil do autor | métrica de distância candidata↔perfil no relatório do engine | execução real com e sem perfil | autores sintéticos não substituem amostras reais | distância registrada com e sem perfil | sim |
| M3.2 Estabilidade em texto longo | drift entre janelas de reescritas longas | drift aplicado por janela na saída do engine | casos longos | limiar não calibrado | drift reportado em reescritas longas | sim |
| M3.3 Calibração com amostras consentidas | calibrar limiares e confiança | — | — | **depende de amostras reais suas** | amostras recebidas e calibração registrada | não (bloqueado) |

## M4 — Evidence & Benchmarks

| WP | Objetivo | Alterações | Testes / evidência | Limitações | Concluído quando | Obrig. |
|---|---|---|---|---|---|---|
| M4.1 Protocolo prospectivo | dataset congelado antes da execução | `benchmarks/cases/ptbr-bench-v1.jsonl` + hash no manifest antes de gerar | — | casos escritos pelo desenvolvedor | congelado e commitado antes da execução | sim |
| M4.2 Runner skill-only | raw, prompt simples, blader, work-humanizer, VozNativa com o mesmo LLM | `scripts/bench_skill_only.py`; skills de terceiros buscadas no commit registrado | relatório por sistema: gates, resíduo de padrões, comprimento, custo, latência | o instrumento de fidelidade é o próprio gate do VozNativa (viés declarado); juiz LLM aplicado a todos | execução registrada | sim |
| M4.3 System-level (Emulate) | comparação separada | provider existente | — | **depende de chave de API** | — | não (bloqueado) |
| M4.4 Revisão humana cega | instrumento para pessoas avaliarem sem saber o sistema | `voznativa blind-review` (terminal, assinado), pacote randomizado | testes do instrumento; **nenhum resultado até haver pessoas** | — | instrumento pronto; resultados só quando houver julgamentos reais | sim (instrumento); resultados = critério 5 |

## M5 — Corpus Pilot

| WP | Objetivo | Alterações | Testes / evidência | Limitações | Concluído quando | Obrig. |
|---|---|---|---|---|---|---|
| M5.1 Carolina metadata-only | contar tipologia, período e licença por documento sem guardar texto | `scripts/carolina_metadata.py` (cabeçalhos TEI → agregados) | execução num recorte registrado; distribuição de licenças | recorte, não o corpus inteiro | agregados registrados com versão e hash do recorte | sim |

## M6 — Release Qualification

| WP | Objetivo | Concluído quando | Obrig. |
|---|---|---|---|
| M6.1 Providers robustos | retries com backoff, erro de provider não derruba o engine, timeout | testes de falha | sim |
| M6.2 Privacidade | relatórios de integração sem texto quando pedido; nada de amostra bruta em perfis | testes | sim |
| M6.3 Exemplos antes/depois | `examples/` com saídas reais e relatórios | arquivos gerados por execução real | sim |
| M6.4 Matriz de compatibilidade | Linux e Windows, 3.11–3.13, wheel isolado | rodada final registrada | sim |
| M6.5 CI | — | **bloqueado: cobrança do GitHub Actions** | sim (critério 6) |

## Pesquisa que embasa as decisões

Detalhes, versões e licenças em `docs/RESEARCH_LOG.md`.
