# Dogfood recíproco: VozNativa ↔ Assertiva ↔ Derivanta (v0.10, CP11)

> Cada cenário diz o que **rodou de verdade** (`REAL_EXECUTED`), o que é estático (`STATIC_ONLY`) e o que ficou bloqueado. Ferramentas instaladas a partir de clones isolados dos remotos (`Assertiva` `b615b13` = `v1.0.1`; `Derivanta-Engine` `37ba01a`, `v0.1.0`), em venvs próprios; os checkouts locais do mantenedor não foram tocados. Identidade Git só local (noreply), sem trailer de IA.

## Matriz de cenários

| # | Direção | Auditor → alvo | Comando | Resultado | Estado |
|---|---|---|---|---|---|
| A1 | A | Derivanta 0.1.0 → VozNativa `v0.9.0` e candidato (mesmo caminho) | `inspect --maintainability --format json`; `compare` | `COMPARABLE`; 15 novos, 198 persistentes, 1 ausente (detalhe em [`MAINTAINABILITY.md`](MAINTAINABILITY.md)) | REAL_EXECUTED (estático por natureza) |
| A2 | A | Assertiva 1.0.1 → VozNativa `v0.9.0` | `audit --execute --python <venv só com dependências>` | suíte nativa **PASS, 1.402 invocações**; 2 achados: `ARTIFACT_QUALIFICATION_FAILED` (ver C2) e `UNCLASSIFIED_VERIFICATION` | REAL_EXECUTED |
| B1 | B | VozNativa → README de Assertiva e de Derivanta (inglês) | `diagnose`, `plan`, `route` | **defeito do VozNativa** (V010-GAP-16): inglês lido como português — "as pytest" virou `plural_agreement`, 42 palavras inglesas planejadas como estrangeirismo, plano `edit` com 29 edições | REAL_EXECUTED → VERIFIED_FIXED |
| B2 | B | instalação seguindo o README de Assertiva num venv novo | `pip install -e .` | falha `No module named 'setuptools'` com `PIP_NO_BUILD_ISOLATION=0` no ambiente; o README do Derivanta documenta o caso, o da Assertiva não | REAL_EXECUTED |
| C1 | C | Derivanta: falsos candidatos achados em A1 | teste vermelho → correção → `tools/verify.py` → replay em VozNativa | ver abaixo | VERIFIED_FIXED (merge BLOCKED) |
| C2 | C | Assertiva: causa atribuída ao projeto quando o ambiente não tem o backend de build | teste vermelho → correção → suíte → replay | ver abaixo | em andamento |

## B1 — VozNativa lia inglês como português (defeito do próprio VozNativa)

- **Reprodução** (`v0.9.0` e candidato antes da correção): README da Assertiva → 5 `ERROR_CONFIRMED` de `plural_agreement` ("as pytest", "as already", "as such"…: o "as" inglês lido como artigo), plano `edit` com 29 `point_edit` (42 estrangeirismos). Um `rewrite` mandaria o modelo "corrigir" inglês como português.
- **Correção**: `ptbr.language_of` (palavras funcionais exclusivas de cada língua; código removido antes; inglês exige ≥ 8 e o triplo das portuguesas). Em inglês, `diagnose` não roda as regras gramaticais do português (e diz por quê) e o `plan` vira `no_change`, exceto quando o usuário pede um destino (adaptar/traduzir continua sendo pedido explícito).
- **Prova**: `evals/test_v010_language_guard.py` (5 testes; defeitos vermelhos em `v0.9.0`; controle: texto português com termos ingleses continua checado e planejado). Replay real: READMEs de Assertiva e Derivanta → 0 diagnósticos, `no_change`; README do VozNativa (português) continua analisado. Conjuntos congelados inalterados.

## C1 — Derivanta: dois falsos sinais (corrigido no repositório dono)

1. **Classe de teste herdada vista como "não referenciada"**: `class CountContract(LexiconFile)` com `LexiconFile(unittest.TestCase)` virava `UNREFERENCED_DEFINITION`; só subclasses diretas de `TestCase` eram reconhecidas. O unittest descobre as herdadas. VozNativa tinha 4 desses falsos candidatos.
2. **`SyntaxWarning` do código inspecionado no stderr do Engine** (`<unknown>:1: SyntaxWarning: invalid escape sequence '\s'`): o detector de código comentado faz `ast.parse` de comentários; um comentário com `"\s"` vazava o aviso como se fosse do Engine.

| Passo | Evidência |
|---|---|
| teste vermelho | dois testes novos em `tests/integration/test_maintainability.py` falharam antes da mudança (`GrandChild` listado; avisos capturados) |
| correção | `core/maintainability.py`: `_local_test_classes` (fecho transitivo no módulo) e `_parse` (silencia só `SyntaxWarning` do código inspecionado) |
| suíte do dono | `tools/verify.py` PASS: lint, format, types, **958 testes**, conformance (Windows, CPython 3.12; `PYTEST_DEBUG_TEMPROOT` curto, como o README do Derivanta orienta) |
| controle | classe comum em arquivo de teste continua candidata; código com escape inválido continua analisado e a linha comentada contada; autoauditoria do Engine sem candidato novo (a primeira versão ignorava também `DeprecationWarning` e o detector de legado do próprio Engine apontou: removido) |
| replay | VozNativa, mesma revisão: `ENG-MAINT-UNREFERENCED` **4 → 0**; stderr **2 avisos → vazio**; complexidade e duplicação iguais |
| integração | branch `fix/maintainability-syntaxwarning-and-inherited-testcases`, commit `1ed4af8`, **PR #6** em `Soturine/Derivanta-Engine`; gate de privacidade PASS no patch. **Merge BLOCKED**: o controle de permissões da sessão negou o merge na `main` do Derivanta; o PR ficou aberto para o mantenedor. Sem versão nova (nenhum contrato mudou) |

## C2 — Assertiva: "corrija o empacotamento" quando faltava o backend de build no ambiente

- **Reprodução (A2)**: `pip wheel` do VozNativa falhou com `No module named 'setuptools'`: o ambiente da máquina tem `PIP_NO_BUILD_ISOLATION=0` (o pip lê como *desligar* o isolamento) e o interpretador do projeto não tinha `setuptools`. A Assertiva relatou `ARTIFACT_QUALIFICATION_FAILED` (alta) com a recomendação "Fix packaging (included packages, package data, metadata)" — o empacotamento do VozNativa gera o mesmo wheel no gate de pacote dele. Falso vermelho com recomendação enganosa, mesma forma que a própria Assertiva corrigiu para erros de coleta no 1.0.1 (`fee2c44`).
- **Correção** (branch `fix/artifact-build-backend-environment-cause`): `environment_build_cause` decide só quando **toda** verificação falha é um backend de build ausente (`setuptools`, `hatchling`, `flit_core`, `poetry`, `pdm`…) que não é pacote do próprio projeto; o achado mantém código e severidade (como o precedente) e ganha `dominant_cause` e recomendação que aponta o ambiente.
- **Teste**: `tests/test_artifact_build_backend_environment_cause.py` (6 testes; o arquivo nem carregava antes da mudança; controles: módulo do projeto, backend que é o próprio projeto, falha de empacotamento real mantém a recomendação padrão; um teste passa pela função que monta o achado, onde o precedente teve um defeito de ligação).
- **Falhas preexistentes na máquina** (não causadas pela mudança, reproduzidas no código sem a mudança): `test_install_failure_is_fail` (`StopIteration`) e `test_target_interpreter_with_inherited_site_dirs_keeps_its_dependencies`.

## Pendências desta seção

Preenchidas ao final do CP11: suíte completa da Assertiva com a correção, replay do `audit --execute` no candidato, integração (PR) e a auditoria final da Assertiva sobre o VozNativa candidato.
