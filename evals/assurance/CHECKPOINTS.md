# Checkpoints da rodada "Continuous Assurance, v0.4 Hardening e v0.5.0 Regional Evidence"

Registro do que foi **implementado, validado, não validado e bloqueado** em cada checkpoint. Saídas das ferramentas em `runs/`.

## CP0 — baseline (2026-11-05) — concluído

- Estado confirmado: `main` = `0ba7bc2`, `origin/v0.4.0-dev` = `4044cfc` (44 commits à frente), árvores limpas.
- Executado: validador, 281 testes, 7 suítes semânticas (`holdout.jsonl` exit 1 por `ho-007`), decisão 28/30, Engine `inspect`/`evaluate`, Assertiva estática e `--execute`, 8 controles negativos.
- Baseline: `evals/baselines/v0.4.0-hardening-start.json`; análise: `runs/2026-11-05-cp0-baseline/ANALYSIS.md`.
- Divergências do pedido: `derivanta-engine review` não existe na 0.1.0; a Assertiva global tem metadados `0.5.5` (não usada).

## CP1 — perfil derivado — concluído

- `docs/engineering/ENGINEERING_PROFILE.md`: casos de uso, invariantes, máquina de estados do `rewrite`, fronteiras de confiança, requisitos de teste e achados estruturais.
- Sem ADR (nenhuma decisão material ainda).

## CP4/H1 — runner de qualificação — implementado e testado

- `scripts/qualify.py`: 13 gates, cada um em processo próprio com exit code preservado; estados PASS/FAIL/BLOCKED/NOT_RUN/SKIPPED/INCONCLUSIVE/WAIVED_BY_OWNER; relatório JSON UTF-8; sem pipelines de shell; reproduz o job `package` do CI (sdist → wheel → venv limpo → smoke).
- Falhas conhecidas explícitas em `evals/qualification/expectations.json`; evidência externa em `evals/qualification/external.json` (CI BLOCKED, holdout independente e revisão humana NOT_RUN).
- `evals/test_qualify.py` (10 testes): skip, nada coletado e erro de importação nunca viram PASS; falha nova não se esconde atrás de falhas conhecidas.
- Primeira execução (`--scope release`, Windows/3.12): o runner achou o próprio defeito de descoberta (crash classificado como FAIL, corrigido); `cli:exit-codes` **FAIL**: erro de uso sai com 2, o mesmo código de `review_required` do `compare` (defeito confirmado, ainda não corrigido).
- Não validado: Linux (gate `review:pty` só roda em POSIX), Python 3.11/3.13.

## CP4 — hardening da v0.4.0 — implementado e testado (2026-11-05)

| Item | Resultado | Evidência |
|---|---|---|
| H1 | runner `scripts/qualify.py`; exit 64 para erro de uso em todo comando (antes 2 = `review_required`); `baseline.py` conta todos os desfechos do unittest; falso verde NC1 corrigido (conjunto congelado fixo, decisão e benchmark com hash); registro de revisores validado; código morto e lista duplicada removidos | `8b103e7`…`9793d0d` |
| H2 | eixos de desfecho separados; `provider_error` nunca conta como sucesso; reanálise do oficial sem alterá-lo (v0.4.0: 12/15 tarefa cumprida ou pendente, 1 falha de sistema, invariantes 14/14 onde houve saída) | `286dfc8`, `H2_BENCHMARK_REANALYSIS.md` |
| H3 | `dc-021` erro de expectativa (contradiz o contrato do README); `dc-029` INCONCLUSIVE (limiar sem calibração); nada ajustado | `bbdc5d6`, `H3_PLANNER_CASES.md` |
| H4 | dia da semana sem preposição (falso vermelho de `bv2-li-02` e um falso verde), "2 da tarde", verbos multiplicadores (`ho-007` passa estrito), troca de papéis/ordem com substantivos comuns; probe 19/29 → 25/29; pronomes, troca entre frases e inflexão diferente ficam como limitação | `4af90ac`, `78502c1`, `c341967`, `24ba7e2`, `H4_SEMANTIC_LEDGER.md` |
| H5 | `signals.markers` indexado (compare 8k palavras 10,4 s → 0,96 s); `adherence` com poda por limite superior (loop sem modelo 48,6 s → 1,1 s); cache de ledger medido e rejeitado; testes diferenciais com mutantes mortos | `eb8ea99`, `a8c9d41`, `evals/perf/v0.4.0-dev-h5-*.json` |
| H5 (achado) | contração no primeiro termo de uma frase marcadora ("na função de" lido como causal) | `df42939` |
| H6 | chave de revisão criada com 0600 em uma chamada; testes do sanitizador de relatórios; varredura de caminhos/nomes nos arquivos versionados: limpa | `218e912` |

Não validado neste ponto: Linux (WSL disponível; vai no CP10), Python 3.11/3.13, comportamento com modelo depois das correções (nenhuma chamada paga feita no CP4).

## CP2/CP3 contínuos — Engine e Assertiva ao longo da rodada

| Momento | Engine | Assertiva |
|---|---|---|
| CP0 (`4044cfc`) | `inspect` 57 candidatos; `evaluate` HIGH, revisão independente exigida | estática + `--execute`: 281 PASS; 4 candidatos de falso verde → 1 confirmado (NC1) |
| CP4 (`66b918e`) | `compare` vs CP0: COMPARABLE, 3 ABSENT (corrigidos), 4 NEW | `--mutate --mutate-tests FILE`: nenhum mutante (AXF-VN-01); mutação feita pelo agente com Cosmic Ray |
| CP8 (`5d7ae60`) | Engine atual `17fa564`: `review` das conclusões do agente (3 CANDIDATE, 2 controles REJECTED); 2 duplicações NEW corrigidas | reprodutores sintéticos de AXF-VN-01…05 |
| CP10 (`caac7f7`) | `compare` vs CP0: COMPARABLE; 54 PERSISTING, 12 NEW (complexidade/duplicação de código novo, INFO), 3 ABSENT | `--execute`: 348 PASS; 1 candidato restante (contextual); assessment anexado e aceito |

## CP5 — v0.5.0 Regional Evidence — implementado e testado

Contrato de pack, piloto `br-norte-lex-mandioca`, integração em todas as camadas, CLI e Skill. Avaliação regional humana NOT_RUN. `docs/evidence/REGIONAL_EVIDENCE.md`, ADR-0001.

## CP6 — pesquisa competitiva — feita

`docs/releases/v0.5/COMPETITIVE_ANALYSIS_v0.5.md` (código e testes lidos pela API do GitHub; decisões ADOPT/ADAPT/EXPERIMENT/MONITOR/REJECT).

## CP7 — avaliação e benchmark v3

Testes metamórficos (acharam NFD/NBSP, corrigido); `ptbr-bench-v3` congelado e **NOT_RUN** (sem CLI de modelo; sem orçamento aprovado); runner verificado com modelo falso; protocolo humano pré-registrado, **NOT_RUN**.

## CP8 — dogfood cruzado — encaminhado

`evals/assurance/DOGFOOD.md`; Assertiva PR #8 e Derivanta-Engine PR #3 (registro, nada corrigido lá).

## CP9 — documentação e demonstração

README, ROADMAP, CHANGELOG, PLAN_v0.5.0, TRACEABILITY, EVALUATION, LICENSING sincronizados; `examples/v0.5.0-demo.md` regenerável (achou um falso verde de troca de papéis com edição junto, corrigido em `2eb903f`).

## CP10 — qualificação (`caac7f7`)

| Critério | Estado | Evidência |
|---|---|---|
| Testes nativos (348) | **PASS** em Windows 3.11/3.12 e Linux 3.11/3.12/3.13 | `runs/2026-11-05-cp10-final/qualify-*.json` |
| Avaliação semântica (dev + holdouts) | **PASS** (holdouts estritos sem falha conhecida restante) | idem |
| Suíte de decisões | **PASS** (sem regressão; `dc-021`, `dc-029` conhecidos e determinados) | idem, `H3_PLANNER_CASES.md` |
| Smoke da CLI e exit codes | **PASS** | gate `cli:exit-codes` |
| sdist → wheel → instalação isolada → smoke | **PASS** (BLOCKED só com o 3.12 do sistema Ubuntu sem `ensurepip`) | gate `package:sdist-wheel-smoke` |
| Revisão em pseudo-terminal | **PASS** no Linux; NOT_RUN no Windows | gate `review:pty` |
| Documentação e schemas | **PASS** (validador; demo regenera igual) | gate `validator`, `DemoV05` |
| Auditoria Assertiva | executada; 1 candidato contextual; assessment aceito | `assertiva-*.json` |
| Inspeção Derivanta Engine | executada; COMPARABLE com a baseline | `engine-*.json` |
| Benchmark com modelo (`ptbr-bench-v3`) | **NOT_RUN** | manifesto congelado |
| Python 3.13 no Windows, macOS | **NOT_RUN** (não instalados) | `evals/compat/v0.5.0-dev-caac7f7.json` |
| CI GitHub Actions | **BLOCKED** (cobrança) | `evals/qualification/external.json` |
| Holdout independente | **NOT_RUN** | idem |
| Revisão humana cega e regional | **NOT_RUN** | `evals/reviewers/PROTOCOL_v0.5.md` |

Veredito do runner: **INCOMPLETE** (exit 3) em todas as plataformas, só pelos critérios externos. A v0.5.0 **não está qualificada** e segue `0.5.0.dev0`.

## Correção (v0.6.0 CP0, 2026-11-05)

Esta rodada registrou o CI como **BLOCKED** (cobrança) até o CP10, sem conferir as execuções. Os dados do GitHub Actions mostram outra coisa: o bloqueio real foi #100–#106 (2026-10-20..21, jobs com 0 passos); a partir de #107 (`fc62e2a`) todos os pushes rodaram, incluindo #121 verde em `caac7f7` (a revisão qualificada no CP10) e #123 verde em `40e19e4` (8/8). O run #122 falhou em `40e19e4` no Windows 3.11 por um teste instável de timeout, cuja classe de defeito foi corrigida na v0.6.0 (`daca4bc`). As linhas acima ficam como foram escritas; a evidência correta está em `evals/qualification/external.json`.
