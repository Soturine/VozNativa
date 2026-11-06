# Dogfood cruzado da v0.7.0 — VozNativa ↔ Assertiva ↔ Derivanta Engine/Framework

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
