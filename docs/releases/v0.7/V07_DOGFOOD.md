# Dogfood cruzado da v0.7.0 — VozNativa ↔ Assertiva ↔ Derivanta Engine/Framework

> **Estado: histórico (execução da v0.7).** Registro daquela rodada, não reescrito; a rodada atual está em [v08/EXECUTION_STATE.md](../v0.8/EXECUTION_STATE.md).

Saída de ferramenta é hipótese. Classificação: `CONFIRMED`, `FALSE_POSITIVE`, `INCONCLUSIVE`, `ACCEPTED_RISK`, `DUPLICATE`, `UPSTREAM_GAP`. O mesmo agente construiu, rodou e julgou: autoavaliação com evidência de ferramenta, não qualificação independente. Histórico da v0.5/v0.6: `evals/assurance/DOGFOOD.md`.

## Instrumentos

| Ferramenta | Versão / revisão | Instalação |
|---|---|---|
| Assertiva | 0.10.1, `2618d95` (= `origin/main` em 2026-11-06) | venv próprio, wheel da tag `v0.10.1` |
| Derivanta Engine | 0.1.0, `17fa564` (= `origin/main`) | venv próprio |
| Derivanta Framework | `218761d` (= `origin/main`) | leitura |

## Execuções

| Run | CP | Revisão VozNativa | Comando | Exit | Resultado |
|---|---|---|---|---|---|
| `2026-11-06-v07-cp0` | CP0 | `bf8e1a4` | `derivanta-engine inspect . --maintainability --format json` | 0 | 97 candidatos INFO: 65 `HIGH_COMPLEXITY`, 30 `DUPLICATE_TABLE`, 2 `UNREFERENCED_DEFINITION` (mesmo conjunto do fim da v0.6) |
| `2026-11-06-v07-cp0` | CP0 | `bf8e1a4` | `assertiva audit . --output json` (estático) | 0 | 1 achado `UNCLASSIFIED_VERIFICATION` (info) |
| `2026-11-06-v07-cp14` | CP14 | `a5570a2` | `derivanta-engine inspect` + `compare` contra CP0 | 0 | COMPARABLE: 43 NEW, 97 PERSISTING (todos INFO) |
| `2026-11-06-v07-cp14` | CP14 | `3fb4163` | `derivanta-engine compare` depois das correções | 0 | 5 ABSENT (exatamente os corrigidos), 135 PERSISTING, 0 NEW |
| (sem registro) | CP14 | árvore editada durante a execução | `assertiva audit --execute` | 1 | `READ-ONLY VIOLATION`: a ferramenta abortou sem relatório porque o agente editou o projeto durante a execução (proteção correta; erro de procedimento do agente) |
| `2026-11-06-v07-cp14` | CP14 | `3fb4163` (limpa) | `assertiva audit --execute --timeout-s 1500` | 0 | unittest PASS, 660 invocações; wheel construído; testes contra o wheel NOT_RUN (AXF-VN-04); 1 INFO; revelou artefato ainda `0.6.0.dev0` |

## Achados

| ID | Ferramenta | Achado | Classificação | Correção local | Upstream | Estado |
|---|---|---|---|---|---|---|
| VN07-DF-001 | Engine `UNREFERENCED_DEFINITION` | `processing.split_unit` sem uso desde a v0.6 (e já incorreto: ignora chaves extras de grupo) | CONFIRMED | removido (`3fb4163`) | — | ABSENT no reteste |
| VN07-DF-002 | Engine `UNREFERENCED_DEFINITION` | `document.REWRITABLE` sem uso | CONFIRMED | removido | — | ABSENT |
| VN07-DF-003 | Engine `UNREFERENCED_DEFINITION` | `KINDS`/`EVIDENCE` dos adapters definidos sem validar nada | CONFIRMED | viraram validação de `Measurement` + teste | — | ABSENT |
| VN07-DF-004 | Engine `DUPLICATE_TABLE` | listas de modos e de políticas repetidas no CLI | CONFIRMED | um dono só (`diagnose.MODES`, `integrity.CLEAN_POLICIES`) | — | ABSENT (2) |
| VN07-DF-005 | Engine `DUPLICATE_TABLE` | 13 tabelas de terminações em `morph.py` | FALSE_POSITIVE (paradigmas flexionais repetem terminações por definição) | nenhuma | Engine PR #3 (`7e8e9ee`): DEF-VN-06 | encaminhado |
| VN07-DF-006 | Engine `DUPLICATE_TABLE` | listas de palavras coincidentes (`text.STOPWORDS` × `diagnose.LEGIT_REPEATS`; regex de lista do router × longform) | ACCEPTED_RISK / coincidência | nenhuma | — | aceito |
| VN07-DF-007 | Engine `HIGH_COMPLEXITY` | `rewrite_document` (54 caminhos), `build_plan` (47), `diagnose` (31) e outros | INFO (motor de refatoração, não defeito) | nenhuma nesta rodada; cada ramo tem teste | — | aceito |
| VN07-DF-008 | Assertiva `--execute` | testes contra o wheel NOT_RUN em projeto unittest | UPSTREAM_GAP (= AXF-VN-04) | — | Assertiva PR #8 (intake atualizada) | aberto |
| VN07-DF-009 | Assertiva `--mutate-tests ARQ` (AXF-VN-01) | seleção de arquivo vira diretório inicial do `discover` | CONFIRMED (reproduzido no código) | — | **corrigido upstream**: Assertiva PR #8 `3415828` (`test_command_for`; 5 testes + integração com Cosmic Ray; suíte 1273 passed, 19 skipped) | corrigido na branch, não liberado |
| VN07-DF-010 | Assertiva `--execute` | artefato ainda `voznativa-0.6.0.dev0` | CONFIRMED (VozNativa) | versão → `0.7.0.dev0` no CP15 | — | CP15 |
| VN07-DF-011 | processo | push na branch da PR #8 disparou 2 runs de Actions (o workflow da Assertiva roda em `push` e `pull_request`) | incidente do agente | runs cancelados; memória registrada; antes de push upstream, ler os gatilhos | — | registrado |

## Encaminhamento upstream

| Destino | PR | Estado em 2026-11-06 |
|---|---|---|
| Assertiva | #8 (`docs/voznativa-v05-dogfood-intake-20261105`, agora `3415828`) | aberta; **AXF-VN-01 corrigido** com testes; AXF-VN-02/03/04/05 abertos; intake atualizada |
| Derivanta Engine | #3 (`docs/voznativa-v05-dogfood-intake-20261105`, agora `7e8e9ee`) | aberta; feedback v0.7 (reteste ABSENT funcionou; DEF-VN-06 paradigmas; DEF-VN-05 persiste); nada corrigido no Engine |
| Derivanta Framework | — | nenhum item generalizável para a Constituição nesta rodada (a política anti-overfitting ficou no perfil derivado do projeto) |

## v0.7.0.dev1 (CP5)

Registro completo em `evals/assurance/runs/2026-11-06-h07-cp5/MUTATION.md`. Todas as execuções foram feitas num clone limpo de `c909f1d`, fora da árvore de trabalho.

| Ferramenta | Modo efetivamente executado | Resultado |
|---|---|---|
| Derivanta Engine 0.1.0 (`7e8e9ee`, depois `acd6ca3`) | `inspect --maintainability` em `e7506f5` e `c909f1d`; `compare` | COMPARABLE, 136 PERSISTING, 3 NEW (INFO). 2 NEW eram defeito do Engine (DEF-VN-07), **corrigido** na PR #3 com teste; o reteste dá exatamente 2 ABSENT. 1 `HIGH_COMPLEXITY` em `compare._predicate_issues` é risco aceito |
| Assertiva 0.10.1 | `audit --execute` (cópia isolada) e `audit --assessment` (avaliação do agente validada pela ferramenta) | unittest exit 0, 755 invocações; cobertura 90,0% de linhas e 81,1% de ramos; wheel build, instalação e import PASS, testes contra o wheel NOT_RUN (AXF-VN-04); mutação pelo engine não executada; `improve` não usado |
| Cosmic Ray 8.7.0 (pelo agente, não pela Assertiva) | rodadas A, B, C (parcial) e D com `-B` | A: 633 → 638 no mesmo conjunto da v0.7; sobreviventes da regra nova: 17 de 20 visados mortos por testes do CP5, 3 equivalentes |

| ID | Origem | Achado | Classificação | Decisão |
|---|---|---|---|---|
| VN07-DF-012 | Engine `UNREFERENCED_DEFINITION` | classes `TestCase` herdadas de uma base local tratadas como não referenciadas | defeito do Engine, reproduzido | corrigido upstream (Engine PR #3 `acd6ca3`); push sem Actions (o workflow só roda em push na `main`) |
| VN07-DF-013 | Engine `HIGH_COMPLEXITY` | `compare._predicate_issues` com 21 caminhos | verdadeiro (motivo de refatoração) | risco aceito: a função acabou de ser mutada como está; refatorar com a mutação completa na próxima rodada |
| VN07-DF-014 | Assertiva `UNCLASSIFIED_VERIFICATION` | 5 passos da CI não classificados | CONTEXTUAL | a CI roda só por `workflow_dispatch`; a prova é o run verificado por SHA |
| VN07-DF-015 | Cosmic Ray C (não sinalizado por nenhuma ferramenta estática) | ramos da regra de predicado sem oráculo (janela de vizinhas, radical, laços, frase sem verbo) | lacuna de teste, confirmada por mutante | 8 testes no CP5; replay: 17 mortos de 20 |
| VN07-DF-016 | `tools/verify.py` do Engine | gate FAIL num venv sem o extra `mcp` | ambiente | `pip install "mcp>=2.3,<3"` no venv do repositório; sugestão de BLOCKED registrada no feedback |
| VN07-DF-017 | Assertiva PR #8 | gatilhos `push` e `pull_request` | política de CI | **BLOCKED_BY_CI_POLICY**: nada enviado à branch; comentário permitido (evento `issue_comment` não configurado), não usado |

