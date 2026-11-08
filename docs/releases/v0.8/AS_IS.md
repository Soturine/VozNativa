# AS-IS da v0.8: o que existe em `c2708de` (0.7.0.dev1)

Auditoria do CP0 da rodada v0.8, feita em 2026-11-07 sobre `main` = `dev/v0.7.0-hardening` = `c2708dec3b4063c1f6443300a148e44aa9c4c48c`, conferido com `git fetch --prune` e `git rev-parse`. O código testado pela CI é `f9c1a78` (run #125, `workflow_dispatch`, 8/8); `c2708de` só acrescenta evidência. Os documentos anteriores ([`AS_IS_v0.7.0.md`](../v0.7/AS_IS_v0.7.0.md), [`V07_EXECUTION_STATE.md`](../v0.7/V07_EXECUTION_STATE.md)) continuam valendo como histórico; este arquivo registra o ponto de partida desta rodada e o que mudou de leitura.

## 1. Ambiente da auditoria

| Item | Valor |
|---|---|
| SO | Windows 10 Home 10.0.19045 |
| Python | CPython 3.12.6 (único instalado; `py -0p` não lista 3.11 nem 3.13) |
| Ferramentas | `gh` autenticado (Soturine); Docker Desktop 28.5.1 respondendo; distro WSL só `docker-desktop` (sem distro de uso); sem `uv`, sem `pipx` |
| Dependências do pacote | PyYAML 6.0.2 (única obrigatória) |
| Upstream (consulta `gh api`, 2026-11-07) | Assertiva `main` `2618d95` = release `v0.10.1`; PR #8 aberta em `3415828`. Derivanta Engine `main` `17fa564`; PR #3 aberta em `acd6ca3`. Derivanta Framework `main` `218761d`; PR #11 aberta |
| Workflows | VozNativa: só `workflow_dispatch` (gate `ci:workflow-triggers`). Assertiva: `ci.yml` (push e pull_request, ver `V07_EXECUTION_STATE`). Engine: `ci.yml` (push na `main`). Framework: `documentation-integrity.yml` (pull_request) |

Diferença em relação ao handoff da v0.7: o Docker agora responde, então a qualificação Linux local em contêiner pode deixar de ser BLOCKED (tentativa no CP16). Python 3.11 não está instalado nesta máquina: a qualificação Windows 3.11 depende de instalar um intérprete por usuário (sem instalação global) ou fica BLOCKED com motivo.

## 2. Baseline reproduzível

Comando: `python scripts/qualify.py --scope release --out <scratch>/baseline-c2708de-release.json` na árvore limpa. Registro em [`evals/assurance/runs/2026-11-07-v08-cp0/`](../../../evals/assurance/runs/2026-11-07-v08-cp0/).

| Gate | Estado |
|---|---|
| validator, unittest (726: 725 PASS + 1 skip POSIX), semantic:dev, semantic:holdouts:safety, semantic:holdouts:strict, decision:regression, router:regression, cli:exit-codes, package:sdist-wheel-smoke, ci:workflow-triggers | PASS |
| ci:github-actions | PASS (HEAD equivalente a `f9c1a78`, só evidência depois) |
| review:pty | NOT_RUN (POSIX) |
| holdout:independent, review:blind-human | NOT_RUN (dependem de pessoas) |
| Veredito | INCOMPLETE, exit 3, só por gates externos |

Benchmarks congelados na mesma revisão: `ptbr-bench-v4` 22/22, `ptbr-bench-v5` 36/36, amostra de predicados 16/20 riscos sinalizados e 1/18 falso alarme. São `DEVELOPMENT_REGRESSION`: casos, regras e runners escritos pelo mesmo agente; nenhum é `INDEPENDENT_GENERALIZATION`.

## 3. Mapa de módulos (9.565 linhas em `voznativa/*.py`, mais `voznativa/corpus/`)

| Camada | Módulos | Responsabilidade | Interface pública |
|---|---|---|---|
| Texto e valores | `text`, `numerals`, `spans`, `ptbr`, `features` | normalização, números por extenso, spans protegidos com chave normalizada, PT-PT × PT-BR | `spans.extract`, `numerals.find` |
| Semântica | `ledger`, `compare`, `morph`, `temporal`, `signals` | inventário, gate de comparação (872 linhas, maior módulo), análise verbal por regras, léxico temporal/gíria | `compare.compare`, `ledger.build`, `morph.verbs` |
| Contexto | `router`, `contract`, `profile`, `drift`, `region`, `regional`, `community`, `stuffing` | Context Contract v3 (14 dimensões), Voice Contract, perfis | `router.route`, `contract.resolve` |
| Diagnóstico e plano | `patterns`, `diagnose`, `planner`, `analyze`, `audit` | achados editoriais, diagnóstico tipado do original, plano por frase, modos | `diagnose.diagnose`, `planner.plan` |
| Execução | `engine`, `providers`, `judge`, `document`, `longform` | ciclo gerar → validar → repetir, provider por comando, juiz, plano de documento e reescrita por unidades | `engine.rewrite`, `engine.rewrite_document`, `document.build_plan/validate_plan/reassemble` |
| Fontes | `project`, `references`, `corpus/*` | grounding em repositório, referências, Corpus Registry (38 fontes, 7 integradas) | `project.ground`, `corpus` CLI |
| Avaliação | `evals`, `benchmark`, `blind`, `review`, `integrity`, `redact` | suítes JSONL de comportamento, pontuação de benchmark com eixos e Wilson, revisão cega e assinada, integridade de caracteres | CLI `eval`, `benchmark`, `blind-*`, `review` |
| Interface | `cli` (27 subcomandos), `__main__` | CLI | `voznativa`, `python -m voznativa` |

Scripts (`scripts/`, 47 arquivos): `qualify.py` (runner único de gates), `checkpoint.py` (run/steps/push com verificação remota), `ci_evidence.py`, `bench_v2..v5.py`, `predicate_eval.py`, `perf_probe.py`, `smoke_installed.py`, `validate_package.py`, além de experimentos e calibrações de corpora. Testes: 75 arquivos `evals/test_*.py` por descoberta `unittest`.

## 4. O que já existe para a v0.8 (reuso, não duplicação)

| Pedido da v0.8 | Já existe | Lacuna real |
|---|---|---|
| Contrato de caso e run de avaliação (§5.1) | `evals.provenance` (sha256 LF, revisão), `benchmark.run` (saídas por sistema, ausência conta como falha), `benchmark.summarize_axes` + `wilson`, `blind.*`, `qualify` com estados NOT_RUN/INCOMPLETE | schema único de caso/run com divisão (split), cluster de independência, nível de evidência e eixos; braços B0–B6 numa API comum; relatório legível |
| Splits e vazamento (§5.3) | `corpus` com contenção e splits sem vazamento (CP4 da v0.7), holdouts semânticos congelados, `MANIFEST.json` com sha256 | rótulo de split/independência por caso nas suítes de regressão; verificação automática de que congelados ficam byte-idênticos |
| EventFrame (§6.1) | `compare._role_triples`, `_event_anchors`, `_predicate_issues`, `morph.constructions` | destinatário/beneficiário, troca de evento com valores preservados ("assinou" → "recebeu" passa limpo), representação serializável |
| Standards (§7) | só a visão (`V08_STANDARDS_VISION.md`, ADR-0003 proposto) | todo ST-01..ST-08 |
| `doctor`/`demo` (§8) | `scripts/demo.py`, `scripts/smoke_installed.py`, quickstart com stub | nenhum subcomando `doctor`/`demo`; `examples/quickstart` exige saber caminhos |
| Desempenho (GAP-02) | `scripts/perf_probe.py`, `evals/perf/` | correção do O(n²) de `spans.extract` |

## 5. Contratos públicos que não podem quebrar sem migração

- Códigos de saída do `compare`: 0 ok, 1 fail, 2 review_required, 3 no_deterministic_issues (precisa de juiz). `no_deterministic_issues` **não** é equivalência.
- `kind`/`schema_version` dos JSON: `voznativa.document_plan` v1, `voznativa.document_rewrite_result` v1, `voznativa.qualification` v1, Context Contract v3, Corpus Registry.
- Desfechos do `rewrite`: `accepted`, `needs_judgment`, `needs_review`, `no_change`, `returned_original`, `provider_error`.
- `safe_to_auto_accept` e `semantic_equivalence` no relatório do `compare`.
- Assinatura de `document.reassemble(text, plan, replacements)` e `engine.rewrite_document(..., resume=..., verse_explicit=...)`.

## 6. Duplicação e código morto: o que foi verificado e o que não

Não removi nada no CP0. Candidatos vistos na leitura, a confirmar no CP15 com Derivanta e consumidores:

- `scripts/demo.py` e `scripts/demo_v05.py`, `scripts/bench_v2..v5.py`: runners históricos; servem para reproduzir registros antigos, não são mortos por definição.
- `voznativa/audit.py` (37 linhas) e `voznativa/analyze.py` sobrepõem `diagnose`/`patterns` na CLI (`audit`, `analyze`, `diagnose`, `patterns`): quatro portas para diagnóstico. Candidato a consolidação de UX no CP12, sem remover subcomando público sem depreciação.
- `build/` e `voznativa.egg-info/` estão na árvore de trabalho (ignorados pelo Git): artefatos locais, não do repositório.

## 7. Leituras desta auditoria que mudam o plano

1. **GAP-01 reproduzido** (antes era hipótese): ver [`GAP_REGISTER.md`](GAP_REGISTER.md), V08-GAP-01. E um defeito vizinho não listado no prompt: `rewrite_document(resume=...)` confia no desfecho e no texto de um registro anterior (V08-GAP-09).
2. **GAP-02 tem duas fontes prováveis** de custo quadrático em `spans.py`: a varredura linear de `occupied` a cada casamento e, em `_entities`, `text[:start]` + regex ancorada no fim para cada palavra capitalizada. Medir antes de mudar (CP2).
3. **Só um Python local.** A matriz Windows 3.11/3.12 do prompt precisa de um intérprete 3.11; Linux local via Docker deve ser tentado.
