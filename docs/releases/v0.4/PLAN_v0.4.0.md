# Plano v0.4.0 — PT-BR Writing Intelligence & Hardening

> **Estado: histórico (v0.4).** Plano daquela rodada; o atual é [v08/PLAN.md](../v0.8/PLAN.md).

Une três fontes: os gaps da auditoria da v0.3.0 (M0), o escopo original da v0.4 no `ROADMAP.md` (biblioteca de padrões PT-BR, PT-BR x PT-PT, estrangeirismos) e o planejamento por documento que a v0.3.0 deixou pendente (M2.3, agora M3).

Baseline: `evals/baselines/v0.4.0-start.json` (commit `0ba7bc2`, checkout limpo, 199 testes, validador ok, suítes como na v0.3.0: holdout 23/24).

Versão durante o desenvolvimento: `0.4.0.dev0`. **Código implementado não é versão qualificada.**

## A v0.3.0 continua aberta

Nada nesta fase fecha os critérios externos da v0.3.0: holdout escrito por outra pessoa, rodada de revisão humana cega e CI verde. A v0.4.0 constrói sobre a v0.3.0 sem declará-la concluída.

## Critérios para qualificar a v0.4.0

1. Todo WP obrigatório *validado* (código, testes e evidência registrada).
2. Nenhuma regressão: suítes de dev passam; holdouts congelados inalterados e sem falso verde.
3. Benchmark prospectivo novo congelado antes da primeira execução, com resultado registrado por sistema e comparação com a baseline anterior.
4. Os critérios externos herdados da v0.3.0 (holdout independente, revisão humana cega, CI verde em Linux e Windows 3.11–3.13) cumpridos, ou dispensados explicitamente pelo mantenedor.

Os itens do critério 4 dependem de pessoas e da conta do GitHub.

## M0 — Hardening obrigatório da v0.3

| WP | Defeito confirmado | Correção | Regressão |
|---|---|---|---|
| M0.1 | `ho-007` contava como falha sem dizer que foi detectado | `failure_kind` e `status_passed` nos relatórios; caso congelado intacto, nota em `MANIFEST.json` | `evals/test_hardening_v040.py` |
| M0.2 | modo create julgava a saída contra o pedido, não contra as fontes | juiz de fundamentação com fontes rotuladas, evidência literal obrigatória; valores do pedido contam como fonte; lacunas `[DADO NECESSÁRIO]` pedem revisão | `evals/test_hardening_v040.py` |
| M0.3 | NO_CHANGE ignorava mudança explícita de destino | `transformation_targets`, bloco DESTINO PEDIDO, NO_CHANGE do modelo refeito e depois revisão, `no_change_reason` | `evals/test_hardening_v040.py` |
| M0.4 | `blind-summary` inflava contagens e aceitava mapeamento de braços adulterado | `task_sha256`, todos os hashes conferidos, uma resposta por tarefa e chave, participantes por chave | `evals/test_review_assurance.py` |
| M0.5 | "verified" misturava integridade, posse, identidade e independência | `review.assess`; assinatura SSH do revisor; registro `evals/reviewers/` | `evals/test_review_assurance.py` |
| M0.6 | `--redact` guardava credenciais do comando, erros com texto, caminho e sha256 adivinhável | `voznativa/redact.py`; HMAC com chave não gravada | `evals/test_privacy.py` |
| M0.7 | timeout matava só o filho; saída sem limite; erros do Emulate derrubavam o engine; diretório temporário descrito como isolamento; delimitador do prompt quebrável | árvore de processos, limite, erros embrulhados, avisos para CLIs de agente, `--provider-env minimal`, cercas com hash, tokens de protocolo | `evals/test_providers_hardening.py` |
| M0.8 | `claim_added` no CHANGELOG (o código é `possible_addition`); exemplos `--cmd "claude -p"` com ferramentas ligadas; "CI job" citado como verificação | documentação corrigida; teste do README ignora flags dentro de valores entre aspas | `evals/test_skill_contract.py` |

Achado durante o M0: `quinta às 10h` sem preposição não era dia da semana (falso vermelho em reescrita para chat). Corrigido. Limitação que fica: `é sexta` sem preposição nem horário continua sem span, então "O prazo é sexta." → "O prazo termina na sexta." dá `span_added` (falso vermelho conhecido).

Achados depois do M0, durante M4/M5 (todos com regressão): `voznativa rewrite` lançava `TypeError` em toda chamada desde a v0.3.0 (achado pelo benchmark; nenhum teste rodava o comando); saída cp1252 de providers no Windows virava U+FFFD; um juiz fora do ar fazia o engine descartar uma candidata válida; rótulo de gênero próximo (documentation x technical) virava mudança de destino; `--redact` mantinha caminhos absolutos (o teste passava no Windows por engano); CLIs de agente com caminho Windows não eram reconhecidos no Linux; testes de privacidade escreviam relatórios falsos em `evals/integration`.

## M1–M5: estado em 2026-10-21

| Milestone | Estado | Evidência |
|---|---|---|
| M0 Hardening | **implementado e testado** | 8 defeitos da auditoria + 7 achados na fase, cada um com teste |
| M1 Pattern Library v2 | **implementado e testado**; **não calibrado** | 27 padrões com justificativa, usos legítimos, fontes e casos positivos/falsos positivos (teste obrigatório); limiares e listas do desenvolvedor |
| M2 Contextual Intelligence | **implementado e testado**; **não calibrado** | `voznativa/ptbr.py`; LanguageTool avaliado e não adotado (`evals/experiments/languagetool_probe.json`); packs regionais e gíria não expandidos (sem evidência) |
| M3 Rewrite Planner | **implementado e testado** | `voznativa plan`, decisão 28/30 (1ª execução 27/30); múltiplas candidatas com modelo real não medidas (só desempate determinístico) |
| M4 Evals e benchmarks | **executado** | `holdout-v040` 32/32 (não discrimina); decisão v0.4 28/30 x v0.3 22/30; `ptbr-bench-v2` oficial (US$ 4,64); latência; nada disso é independente |
| M5 Qualificação | **local concluída**; CI **bloqueado** | matriz Linux/Windows 3.11–3.13 com wheel isolado (`evals/compat/v0.4.0-dev-4bd8fb1.json`); demo `examples/v0.4.0-demo.md`; cobertura 93% das linhas do pacote |

## Critérios de qualificação

| Critério | Situação |
|---|---|
| 1. WPs obrigatórios validados | implementados e testados; calibração com dados reais pendente (M1/M2) |
| 2. Sem regressão | 281 testes; holdouts congelados inalterados e sem falso verde |
| 3. Benchmark prospectivo | **cumprido**: `ptbr-bench-v2` congelado antes da execução, resultado por sistema e contra a v0.3.0 |
| 4. Critérios externos herdados | **abertos**: holdout independente, revisão humana cega (registro de revisores vazio), CI (cobrança do GitHub Actions) |

**A v0.4.0 não está qualificada** e continua `0.4.0.dev0`.
