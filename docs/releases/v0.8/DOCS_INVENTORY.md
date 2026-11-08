# Inventário da documentação (v0.8, CP12)

Gerado em 2026-11-07 por `scripts/doc_inventory.py` (dependências) e classificado pelo agente (estado e nota). Estados: `CURRENT` (vale para a versão atual), `HISTORICAL` (registro de uma versão; não reescrito), `SUPERSEDED` (o assunto tem documento vigente em outro lugar), `DRAFT` (plano sem implementação). Nenhum documento ficou `CANDIDATE_DUPLICATE` sem decisão; nenhum está `INCOMPLETE`.

Totais: CURRENT 41, DRAFT 1, HISTORICAL 19, SUPERSEDED 1, de 62 documentos.

## Decisão de organização

Primeiro passo (`38a4050`): reorganização só lógica, porque documentos históricos são citados por registros de evidência imutáveis (`evals/assurance/runs/`), testes, scripts (`ci_evidence.py`, `validate_package.py`) e dados (`pyproject.toml`, fichas de corpora). Depois, **a pedido do mantenedor**, os documentos foram para pastas por assunto e por versão (`docs/guide`, `architecture`, `evidence`, `policy`, `evaluation`, `engineering`, `research`, `releases/v0.X`), com os nomes de arquivo mantidos:

- todo consumidor mutável foi atualizado (links recalculados a partir do local antigo, testes, `ci_evidence.EVIDENCE_PATHS`, `validate_package.py`, código, dados, `LICENSE`, `pyproject.toml`); o validador confere todos os links depois da mudança;
- os registros imutáveis continuam com os caminhos antigos; [`../../PATH_MAP.md`](../../PATH_MAP.md) resolve cada um;
- fonte única: arquitetura vigente em `docs/releases/v0.8/ARCHITECTURE.md` (os antigos levam aviso de estado); avaliação da v0.8 em `EVAL_PROTOCOL.md` e `EVAL_MATRIX.md` desta pasta; requisitos até a v0.7 em `docs/engineering/TRACEABILITY.md`, da v0.8 em `TRACEABILITY.md` desta pasta;
- depois do CP18, a arquitetura vigente pode ganhar um caminho sem versão; o mapa será atualizado.

## Documentos

| Caminho | Estado | Versão | Palavras | Linkado por | Código/evidência que depende | Nota |
|---|---|---|---:|---:|---:|---|
| `CHANGELOG.md` | CURRENT | — | 5809 | 2 | 26 |  |
| `README.md` | CURRENT | — | 2640 | 1 | 50 | entrada do projeto |
| `ROADMAP.md` | CURRENT | — | 2763 | 2 | 27 | seção v0.8 acrescentada no CP12 |
| `SKILL.md` | CURRENT | — | 1708 | 3 | 38 | procedimento do agente; contrato testado |
| `benchmarks/README.md` | CURRENT | — | 198 | 0 | 50 |  |
| `docs/PATH_MAP.md` | CURRENT | — | 418 | 2 | 0 | mapa de caminhos antigos para novos (CP12) |
| `docs/README.md` | CURRENT | — | 654 | 1 | 50 | hub por público (CP12) |
| `docs/architecture/ARCHITECTURE_AND_RESEARCH.md` | SUPERSEDED | — | 672 | 3 | 5 | arquitetura das primeiras versões; vigente: v08/ARCHITECTURE.md |
| `docs/architecture/DESIGN_SPEC.md` | HISTORICAL | — | 873 | 3 | 7 | tese de produto v0.1–v0.3; exigido pelo validador |
| `docs/architecture/MODEL_ADAPTER_TRACK.md` | DRAFT | — | 513 | 2 | 5 | plano futuro, nada implementado |
| `docs/architecture/V08_STANDARDS_VISION.md` | CURRENT | 0.8 | 1131 | 4 | 6 | visão, com nota do que foi implementado no CP10–CP11 |
| `docs/architecture/adr/ADR-0001-regional-evidence-packs.md` | CURRENT | — | 340 | 2 | 12 |  |
| `docs/architecture/adr/ADR-0002-linguistic-analysis.md` | CURRENT | — | 747 | 2 | 8 | citado por morph.py |
| `docs/architecture/adr/ADR-0003-standards-registry.md` | CURRENT | — | 153 | 2 | 4 | implementado no CP10 |
| `docs/engineering/ENGINEERING_PROFILE.md` | CURRENT | — | 1307 | 3 | 5 |  |
| `docs/engineering/TRACEABILITY.md` | CURRENT | — | 1883 | 3 | 8 | requisitos até a v0.7; exigido pelo validador |
| `docs/evaluation/COMPETITIVE_BENCHMARK.md` | CURRENT | — | 1069 | 2 | 1 | protocolo; exigido pelo validador |
| `docs/evaluation/EVALUATION.md` | HISTORICAL | — | 3650 | 2 | 7 | números até a v0.7; v0.8 em v08/EVAL_* |
| `docs/evidence/CORPUS_AND_EVIDENCE_STRATEGY.md` | CURRENT | — | 691 | 2 | 5 |  |
| `docs/evidence/REGIONAL_EVIDENCE.md` | CURRENT | — | 1283 | 2 | 7 | citado por regional.py e packs |
| `docs/guide/AGENT_SKILL.md` | CURRENT | — | 416 | 3 | 0 | novo no CP12 |
| `docs/guide/CLI.md` | CURRENT | — | 3302 | 3 | 2 | gerado do parser; teste de deriva |
| `docs/guide/INSTALL.md` | CURRENT | — | 241 | 2 | 0 | novo no CP12 |
| `docs/guide/QUICKSTART.md` | CURRENT | — | 446 | 5 | 3 | novo no CP12; comandos executados por teste |
| `docs/guide/TROUBLESHOOTING.md` | CURRENT | — | 330 | 3 | 0 | novo no CP12 |
| `docs/policy/LICENSING.md` | CURRENT | — | 1071 | 3 | 9 | citado por pyproject e fichas de corpora |
| `docs/releases/v0.3/PLAN_v0.3.0.md` | HISTORICAL | 0.3 | 1793 | 2 | 2 | citado por evals/compat |
| `docs/releases/v0.4/PLAN_v0.4.0.md` | HISTORICAL | 0.4 | 881 | 2 | 1 |  |
| `docs/releases/v0.5/COMPETITIVE_ANALYSIS_v0.5.md` | HISTORICAL | 0.5 | 1056 | 2 | 0 | pesquisa datada |
| `docs/releases/v0.5/PLAN_v0.5.0.md` | HISTORICAL | 0.5 | 387 | 2 | 0 |  |
| `docs/releases/v0.6/AS_IS_v0.6.0.md` | HISTORICAL | 0.6 | 900 | 2 | 10 |  |
| `docs/releases/v0.6/COMPETITIVE_ANALYSIS_v0.6.md` | HISTORICAL | 0.6 | 581 | 3 | 0 | pesquisa datada |
| `docs/releases/v0.7/AS_IS_v0.7.0.md` | HISTORICAL | 0.7 | 620 | 3 | 10 |  |
| `docs/releases/v0.7/PLAN_v0.7.0.dev1.md` | HISTORICAL | 0.7 | 2059 | 2 | 10 | citado por evals/test_hardening_h07.py |
| `docs/releases/v0.7/PLAN_v0.7.0.md` | HISTORICAL | 0.7 | 1426 | 2 | 6 |  |
| `docs/releases/v0.7/V07_CORPUS_INTEGRATION.md` | HISTORICAL | 0.7 | 2017 | 3 | 5 | execução da v0.7 |
| `docs/releases/v0.7/V07_DISCOVERY_REGISTER.md` | HISTORICAL | 0.7 | 2963 | 2 | 9 | execução da v0.7 |
| `docs/releases/v0.7/V07_DOGFOOD.md` | HISTORICAL | 0.7 | 1160 | 2 | 7 | execução da v0.7 |
| `docs/releases/v0.7/V07_EXECUTION_STATE.md` | HISTORICAL | 0.7 | 2613 | 3 | 9 | na allowlist de evidência de ci_evidence.py: não mover |
| `docs/releases/v0.7/V07_EXTERNAL_BENCHMARK.md` | HISTORICAL | 0.7 | 541 | 2 | 5 | execução da v0.7 |
| `docs/releases/v0.7/V07_INTEGRITY_AND_PROVENANCE.md` | CURRENT | 0.7 | 577 | 2 | 5 | integrity e proveniência ainda vigentes |
| `docs/releases/v0.7/V07_LINGUISTICS.md` | CURRENT | 0.7 | 918 | 2 | 7 | análise verbal ainda vigente |
| `docs/releases/v0.7/V07_OOD_BENCHMARK.md` | HISTORICAL | 0.7 | 645 | 3 | 5 | execução da v0.7 |
| `docs/releases/v0.7/V07_RELEASE_QUALIFICATION.md` | HISTORICAL | 0.7 | 1457 | 3 | 9 | na allowlist de evidência de ci_evidence.py: não mover |
| `docs/releases/v0.7/V07_VERIFICATION_MATRIX.md` | HISTORICAL | 0.7 | 692 | 2 | 5 | execução da v0.7 |
| `docs/releases/v0.8/ARCHITECTURE.md` | CURRENT | 0.8 | 1005 | 7 | 2 | área de execução da v0.8 |
| `docs/releases/v0.8/AS_IS.md` | CURRENT | 0.8 | 1082 | 5 | 1 | área de execução da v0.8 |
| `docs/releases/v0.8/DOCS_INVENTORY.md` | CURRENT | 0.8 | 1347 | 2 | 0 | área de execução da v0.8 |
| `docs/releases/v0.8/DOCUMENT_STANDARDS.md` | CURRENT | 0.8 | 618 | 6 | 0 | área de execução da v0.8 |
| `docs/releases/v0.8/EVAL_MATRIX.md` | CURRENT | 0.8 | 621 | 7 | 0 | área de execução da v0.8 |
| `docs/releases/v0.8/EVAL_PROTOCOL.md` | CURRENT | 0.8 | 696 | 6 | 1 | área de execução da v0.8 |
| `docs/releases/v0.8/EXECUTION_STATE.md` | CURRENT | 0.8 | 1076 | 12 | 9 | área de execução da v0.8 |
| `docs/releases/v0.8/GAP_REGISTER.md` | CURRENT | 0.8 | 1631 | 5 | 0 | área de execução da v0.8 |
| `docs/releases/v0.8/INDEPENDENCE_AND_LEAKAGE.md` | CURRENT | 0.8 | 667 | 6 | 0 | área de execução da v0.8 |
| `docs/releases/v0.8/PERFORMANCE.md` | CURRENT | 0.8 | 813 | 5 | 1 | área de execução da v0.8 |
| `docs/releases/v0.8/PLAN.md` | CURRENT | 0.8 | 1515 | 8 | 1 | área de execução da v0.8 |
| `docs/releases/v0.8/REAL_RUNS.md` | CURRENT | 0.8 | 532 | 3 | 0 | área de execução da v0.8 |
| `docs/releases/v0.8/RESEARCH_LANDSCAPE.md` | CURRENT | 0.8 | 684 | 6 | 0 | área de execução da v0.8 |
| `docs/releases/v0.8/SEMANTICS.md` | CURRENT | 0.8 | 959 | 4 | 0 | área de execução da v0.8 |
| `docs/releases/v0.8/TRACEABILITY.md` | CURRENT | 0.8 | 1148 | 3 | 8 | área de execução da v0.8 |
| `docs/research/RESEARCH_LOG.md` | CURRENT | — | 1416 | 4 | 5 | registro acumulado |
| `examples/README.md` | CURRENT | — | 906 | 0 | 50 |  |
