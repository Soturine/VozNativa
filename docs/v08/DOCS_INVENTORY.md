# Inventário da documentação (v0.8, CP12)

Gerado em 2026-11-07 por `scripts/doc_inventory.py` (dependências) e classificado pelo agente (estado e nota). Estados: `CURRENT` (vale para a versão atual), `HISTORICAL` (registro de uma versão; não reescrito), `SUPERSEDED` (o assunto tem documento vigente em outro lugar), `DRAFT` (plano sem implementação). Nenhum documento ficou `CANDIDATE_DUPLICATE` sem decisão; nenhum está `INCOMPLETE`.

Totais: CURRENT 40, DRAFT 1, HISTORICAL 19, SUPERSEDED 1, de 61 documentos.

## Decisão de organização

A reorganização é **lógica, não física**. O inventário mostrou que documentos históricos são citados por registros de evidência imutáveis (`evals/assurance/runs/`), por testes (`test_hardening_h07`, `test_hardening_cp5b`), por scripts (`ci_evidence.py` tem `V07_EXECUTION_STATE.md` e `V07_RELEASE_QUALIFICATION.md` na allowlist; `validate_package.py` exige `DESIGN_SPEC.md`, `TRACEABILITY.md`, `COMPETITIVE_BENCHMARK.md`) e por dados (`pyproject.toml` e fichas de corpora citam `LICENSING.md`). Movê-los quebraria registros que não podem ser editados. Então:

- **Nenhum arquivo existente foi movido.** Mapa de caminhos antigos → novos: identidade para todos os documentos anteriores ao CP12.
- **Novos:** `docs/guide/` (`INSTALL`, `QUICKSTART`, `CLI` gerado, `AGENT_SKILL`, `TROUBLESHOOTING`) e este inventário.
- **Navegação:** `docs/README.md` organizado por público (começar, integrar, avaliar, manter, histórico), com o estado de cada documento.
- **Fonte única:** arquitetura vigente em `v08/ARCHITECTURE.md` (os documentos antigos levam aviso de estado); avaliação da v0.8 em `v08/EVAL_PROTOCOL.md` e `v08/EVAL_MATRIX.md` (`EVALUATION.md` guarda os números até a v0.7); requisitos até a v0.7 em `TRACEABILITY.md` e da v0.8 em `v08/TRACEABILITY.md`.
- **Fim da rodada:** quando a v0.8 fechar, `docs/v08/` deixa de ser área de execução; a consolidação da arquitetura num caminho sem versão fica para depois do CP18, com o mapa atualizado.

## Documentos

| Caminho | Estado | Versão | Palavras | Linkado por | Código/evidência que depende | Nota |
|---|---|---|---:|---:|---:|---|
| `CHANGELOG.md` | CURRENT | — | 5809 | 2 | 25 |  |
| `README.md` | CURRENT | — | 2618 | 1 | 46 | entrada do projeto |
| `ROADMAP.md` | CURRENT | — | 2590 | 2 | 26 | seção v0.8 acrescentada no CP12 |
| `SKILL.md` | CURRENT | — | 1708 | 3 | 37 | procedimento do agente; contrato testado |
| `benchmarks/README.md` | CURRENT | — | 198 | 0 | 46 |  |
| `docs/ARCHITECTURE_AND_RESEARCH.md` | SUPERSEDED | — | 672 | 3 | 5 | arquitetura das primeiras versões; vigente: v08/ARCHITECTURE.md |
| `docs/AS_IS_v0.6.0.md` | HISTORICAL | 0.6 | 900 | 1 | 10 |  |
| `docs/AS_IS_v0.7.0.md` | HISTORICAL | 0.7 | 620 | 2 | 10 |  |
| `docs/COMPETITIVE_ANALYSIS_v0.5.md` | HISTORICAL | 0.5 | 1056 | 1 | 0 | pesquisa datada |
| `docs/COMPETITIVE_ANALYSIS_v0.6.md` | HISTORICAL | 0.6 | 581 | 2 | 0 | pesquisa datada |
| `docs/COMPETITIVE_BENCHMARK.md` | CURRENT | — | 1069 | 1 | 1 | protocolo; exigido pelo validador |
| `docs/CORPUS_AND_EVIDENCE_STRATEGY.md` | CURRENT | — | 691 | 1 | 5 |  |
| `docs/DESIGN_SPEC.md` | HISTORICAL | — | 873 | 2 | 7 | tese de produto v0.1–v0.3; exigido pelo validador |
| `docs/ENGINEERING_PROFILE.md` | CURRENT | — | 1307 | 2 | 5 |  |
| `docs/EVALUATION.md` | HISTORICAL | — | 3650 | 2 | 7 | números até a v0.7; v0.8 em v08/EVAL_* |
| `docs/LICENSING.md` | CURRENT | — | 1071 | 2 | 9 | citado por pyproject e fichas de corpora |
| `docs/MODEL_ADAPTER_TRACK.md` | DRAFT | — | 513 | 1 | 5 | plano futuro, nada implementado |
| `docs/PLAN_v0.3.0.md` | HISTORICAL | 0.3 | 1793 | 1 | 1 | citado por evals/compat |
| `docs/PLAN_v0.4.0.md` | HISTORICAL | 0.4 | 881 | 1 | 1 |  |
| `docs/PLAN_v0.5.0.md` | HISTORICAL | 0.5 | 387 | 1 | 0 |  |
| `docs/PLAN_v0.7.0.dev1.md` | HISTORICAL | 0.7 | 2059 | 1 | 10 | citado por evals/test_hardening_h07.py |
| `docs/PLAN_v0.7.0.md` | HISTORICAL | 0.7 | 1426 | 1 | 6 |  |
| `docs/README.md` | CURRENT | — | 644 | 1 | 46 | hub por público (CP12) |
| `docs/REGIONAL_EVIDENCE.md` | CURRENT | — | 1283 | 1 | 7 | citado por regional.py e packs |
| `docs/RESEARCH_LOG.md` | CURRENT | — | 1416 | 3 | 5 | registro acumulado |
| `docs/TRACEABILITY.md` | CURRENT | — | 1883 | 3 | 8 | requisitos até a v0.7; exigido pelo validador |
| `docs/V07_CORPUS_INTEGRATION.md` | HISTORICAL | 0.7 | 2017 | 2 | 5 | execução da v0.7; citado por evidência |
| `docs/V07_DISCOVERY_REGISTER.md` | HISTORICAL | 0.7 | 2963 | 1 | 9 | execução da v0.7; citado por evidência |
| `docs/V07_DOGFOOD.md` | HISTORICAL | 0.7 | 1160 | 1 | 7 | execução da v0.7; citado por evidência |
| `docs/V07_EXECUTION_STATE.md` | HISTORICAL | 0.7 | 2613 | 3 | 8 | na allowlist de evidência de ci_evidence.py: não mover |
| `docs/V07_EXTERNAL_BENCHMARK.md` | HISTORICAL | 0.7 | 541 | 1 | 5 | execução da v0.7; citado por evidência |
| `docs/V07_INTEGRITY_AND_PROVENANCE.md` | CURRENT | 0.7 | 577 | 1 | 5 | integrity e proveniência ainda vigentes |
| `docs/V07_LINGUISTICS.md` | CURRENT | 0.7 | 918 | 1 | 7 | análise verbal ainda vigente |
| `docs/V07_OOD_BENCHMARK.md` | HISTORICAL | 0.7 | 645 | 2 | 5 | execução da v0.7; citado por evidência |
| `docs/V07_RELEASE_QUALIFICATION.md` | HISTORICAL | 0.7 | 1457 | 2 | 8 | na allowlist de evidência de ci_evidence.py: não mover |
| `docs/V07_VERIFICATION_MATRIX.md` | HISTORICAL | 0.7 | 692 | 1 | 5 | execução da v0.7; citado por evidência |
| `docs/V08_STANDARDS_VISION.md` | CURRENT | 0.8 | 1131 | 4 | 6 | visão, com nota do que foi implementado no CP10–CP11 |
| `docs/adr/ADR-0001-regional-evidence-packs.md` | CURRENT | — | 340 | 1 | 12 |  |
| `docs/adr/ADR-0002-linguistic-analysis.md` | CURRENT | — | 747 | 1 | 8 | citado por morph.py |
| `docs/adr/ADR-0003-standards-registry.md` | CURRENT | — | 153 | 1 | 4 | implementado no CP10 |
| `docs/guide/AGENT_SKILL.md` | CURRENT | — | 416 | 2 | 0 | novo no CP12 |
| `docs/guide/CLI.md` | CURRENT | — | 3302 | 2 | 0 | gerado do parser; teste de deriva |
| `docs/guide/INSTALL.md` | CURRENT | — | 241 | 1 | 0 | novo no CP12 |
| `docs/guide/QUICKSTART.md` | CURRENT | — | 446 | 4 | 0 | novo no CP12; comandos executados por teste |
| `docs/guide/TROUBLESHOOTING.md` | CURRENT | — | 330 | 2 | 0 | novo no CP12 |
| `docs/v08/ARCHITECTURE.md` | CURRENT | 0.8 | 978 | 5 | 2 | área de execução da v0.8 |
| `docs/v08/AS_IS.md` | CURRENT | 0.8 | 1082 | 4 | 1 | área de execução da v0.8 |
| `docs/v08/DOCS_INVENTORY.md` | CURRENT | 0.8 | 1261 | 1 | 0 | área de execução da v0.8 |
| `docs/v08/DOCUMENT_STANDARDS.md` | CURRENT | 0.8 | 618 | 4 | 0 | área de execução da v0.8 |
| `docs/v08/EVAL_MATRIX.md` | CURRENT | 0.8 | 621 | 4 | 0 | área de execução da v0.8 |
| `docs/v08/EVAL_PROTOCOL.md` | CURRENT | 0.8 | 688 | 5 | 0 | área de execução da v0.8 |
| `docs/v08/EXECUTION_STATE.md` | CURRENT | 0.8 | 1060 | 10 | 8 | área de execução da v0.8 |
| `docs/v08/GAP_REGISTER.md` | CURRENT | 0.8 | 1631 | 4 | 0 | área de execução da v0.8 |
| `docs/v08/INDEPENDENCE_AND_LEAKAGE.md` | CURRENT | 0.8 | 667 | 5 | 0 | área de execução da v0.8 |
| `docs/v08/PERFORMANCE.md` | CURRENT | 0.8 | 813 | 4 | 1 | área de execução da v0.8 |
| `docs/v08/PLAN.md` | CURRENT | 0.8 | 1515 | 7 | 0 | área de execução da v0.8 |
| `docs/v08/REAL_RUNS.md` | CURRENT | 0.8 | 532 | 2 | 0 | área de execução da v0.8 |
| `docs/v08/RESEARCH_LANDSCAPE.md` | CURRENT | 0.8 | 684 | 5 | 0 | área de execução da v0.8 |
| `docs/v08/SEMANTICS.md` | CURRENT | 0.8 | 959 | 3 | 0 | área de execução da v0.8 |
| `docs/v08/TRACEABILITY.md` | CURRENT | 0.8 | 1148 | 2 | 8 | área de execução da v0.8 |
| `examples/README.md` | CURRENT | — | 906 | 0 | 46 |  |
