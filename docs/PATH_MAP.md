# Mapa de caminhos da documentação

Na v0.8 (CP12, a pedido do mantenedor) os documentos saíram da raiz de `docs/` para pastas por assunto e por versão. Os nomes dos arquivos não mudaram. Todo link, teste, script e dado do repositório foi atualizado; os **registros de evidência imutáveis** (`evals/assurance/runs/`, `evals/compat/`, `benchmarks/runs/`, `evals/*/runs/`, `evals/qualification/`) continuam citando os caminhos antigos, e esta tabela os resolve.

| Pasta | Conteúdo |
|---|---|
| `docs/guide/` | uso: instalação, primeiros passos, CLI, Agent Skill, problemas comuns |
| `docs/architecture/` (+ `adr/`) | arquitetura das primeiras versões, especificação, visão de normas, trilha de modelos, decisões |
| `docs/evidence/` | corpora e Regional Evidence Packs |
| `docs/policy/` | licenças e política de dados |
| `docs/evaluation/` | avaliação até a v0.7 e protocolo de comparação |
| `docs/engineering/` | perfil de engenharia e rastreabilidade v0.1–v0.7 |
| `docs/research/` | registro de pesquisa externa |
| `docs/releases/v0.X/` | planos, inventários e registros de cada rodada; `v0.8/` é a rodada em curso |

| Caminho antigo | Caminho novo |
|---|---|
| `docs/ARCHITECTURE_AND_RESEARCH.md` | [`docs/architecture/ARCHITECTURE_AND_RESEARCH.md`](architecture/ARCHITECTURE_AND_RESEARCH.md) |
| `docs/AS_IS_v0.6.0.md` | [`docs/releases/v0.6/AS_IS_v0.6.0.md`](releases/v0.6/AS_IS_v0.6.0.md) |
| `docs/AS_IS_v0.7.0.md` | [`docs/releases/v0.7/AS_IS_v0.7.0.md`](releases/v0.7/AS_IS_v0.7.0.md) |
| `docs/COMPETITIVE_ANALYSIS_v0.5.md` | [`docs/releases/v0.5/COMPETITIVE_ANALYSIS_v0.5.md`](releases/v0.5/COMPETITIVE_ANALYSIS_v0.5.md) |
| `docs/COMPETITIVE_ANALYSIS_v0.6.md` | [`docs/releases/v0.6/COMPETITIVE_ANALYSIS_v0.6.md`](releases/v0.6/COMPETITIVE_ANALYSIS_v0.6.md) |
| `docs/COMPETITIVE_BENCHMARK.md` | [`docs/evaluation/COMPETITIVE_BENCHMARK.md`](evaluation/COMPETITIVE_BENCHMARK.md) |
| `docs/CORPUS_AND_EVIDENCE_STRATEGY.md` | [`docs/evidence/CORPUS_AND_EVIDENCE_STRATEGY.md`](evidence/CORPUS_AND_EVIDENCE_STRATEGY.md) |
| `docs/DESIGN_SPEC.md` | [`docs/architecture/DESIGN_SPEC.md`](architecture/DESIGN_SPEC.md) |
| `docs/ENGINEERING_PROFILE.md` | [`docs/engineering/ENGINEERING_PROFILE.md`](engineering/ENGINEERING_PROFILE.md) |
| `docs/EVALUATION.md` | [`docs/evaluation/EVALUATION.md`](evaluation/EVALUATION.md) |
| `docs/LICENSING.md` | [`docs/policy/LICENSING.md`](policy/LICENSING.md) |
| `docs/MODEL_ADAPTER_TRACK.md` | [`docs/architecture/MODEL_ADAPTER_TRACK.md`](architecture/MODEL_ADAPTER_TRACK.md) |
| `docs/PLAN_v0.3.0.md` | [`docs/releases/v0.3/PLAN_v0.3.0.md`](releases/v0.3/PLAN_v0.3.0.md) |
| `docs/PLAN_v0.4.0.md` | [`docs/releases/v0.4/PLAN_v0.4.0.md`](releases/v0.4/PLAN_v0.4.0.md) |
| `docs/PLAN_v0.5.0.md` | [`docs/releases/v0.5/PLAN_v0.5.0.md`](releases/v0.5/PLAN_v0.5.0.md) |
| `docs/PLAN_v0.7.0.dev1.md` | [`docs/releases/v0.7/PLAN_v0.7.0.dev1.md`](releases/v0.7/PLAN_v0.7.0.dev1.md) |
| `docs/PLAN_v0.7.0.md` | [`docs/releases/v0.7/PLAN_v0.7.0.md`](releases/v0.7/PLAN_v0.7.0.md) |
| `docs/REGIONAL_EVIDENCE.md` | [`docs/evidence/REGIONAL_EVIDENCE.md`](evidence/REGIONAL_EVIDENCE.md) |
| `docs/RESEARCH_LOG.md` | [`docs/research/RESEARCH_LOG.md`](research/RESEARCH_LOG.md) |
| `docs/TRACEABILITY.md` | [`docs/engineering/TRACEABILITY.md`](engineering/TRACEABILITY.md) |
| `docs/V07_CORPUS_INTEGRATION.md` | [`docs/releases/v0.7/V07_CORPUS_INTEGRATION.md`](releases/v0.7/V07_CORPUS_INTEGRATION.md) |
| `docs/V07_DISCOVERY_REGISTER.md` | [`docs/releases/v0.7/V07_DISCOVERY_REGISTER.md`](releases/v0.7/V07_DISCOVERY_REGISTER.md) |
| `docs/V07_DOGFOOD.md` | [`docs/releases/v0.7/V07_DOGFOOD.md`](releases/v0.7/V07_DOGFOOD.md) |
| `docs/V07_EXECUTION_STATE.md` | [`docs/releases/v0.7/V07_EXECUTION_STATE.md`](releases/v0.7/V07_EXECUTION_STATE.md) |
| `docs/V07_EXTERNAL_BENCHMARK.md` | [`docs/releases/v0.7/V07_EXTERNAL_BENCHMARK.md`](releases/v0.7/V07_EXTERNAL_BENCHMARK.md) |
| `docs/V07_INTEGRITY_AND_PROVENANCE.md` | [`docs/releases/v0.7/V07_INTEGRITY_AND_PROVENANCE.md`](releases/v0.7/V07_INTEGRITY_AND_PROVENANCE.md) |
| `docs/V07_LINGUISTICS.md` | [`docs/releases/v0.7/V07_LINGUISTICS.md`](releases/v0.7/V07_LINGUISTICS.md) |
| `docs/V07_OOD_BENCHMARK.md` | [`docs/releases/v0.7/V07_OOD_BENCHMARK.md`](releases/v0.7/V07_OOD_BENCHMARK.md) |
| `docs/V07_RELEASE_QUALIFICATION.md` | [`docs/releases/v0.7/V07_RELEASE_QUALIFICATION.md`](releases/v0.7/V07_RELEASE_QUALIFICATION.md) |
| `docs/V07_VERIFICATION_MATRIX.md` | [`docs/releases/v0.7/V07_VERIFICATION_MATRIX.md`](releases/v0.7/V07_VERIFICATION_MATRIX.md) |
| `docs/V08_STANDARDS_VISION.md` | [`docs/architecture/V08_STANDARDS_VISION.md`](architecture/V08_STANDARDS_VISION.md) |
| `docs/adr/ADR-0001-regional-evidence-packs.md` | [`docs/architecture/adr/ADR-0001-regional-evidence-packs.md`](architecture/adr/ADR-0001-regional-evidence-packs.md) |
| `docs/adr/ADR-0002-linguistic-analysis.md` | [`docs/architecture/adr/ADR-0002-linguistic-analysis.md`](architecture/adr/ADR-0002-linguistic-analysis.md) |
| `docs/adr/ADR-0003-standards-registry.md` | [`docs/architecture/adr/ADR-0003-standards-registry.md`](architecture/adr/ADR-0003-standards-registry.md) |
| `docs/v08/ARCHITECTURE.md` | [`docs/releases/v0.8/ARCHITECTURE.md`](releases/v0.8/ARCHITECTURE.md) |
| `docs/v08/AS_IS.md` | [`docs/releases/v0.8/AS_IS.md`](releases/v0.8/AS_IS.md) |
| `docs/v08/DOCS_INVENTORY.md` | [`docs/releases/v0.8/DOCS_INVENTORY.md`](releases/v0.8/DOCS_INVENTORY.md) |
| `docs/v08/DOCUMENT_STANDARDS.md` | [`docs/releases/v0.8/DOCUMENT_STANDARDS.md`](releases/v0.8/DOCUMENT_STANDARDS.md) |
| `docs/v08/EVAL_MATRIX.md` | [`docs/releases/v0.8/EVAL_MATRIX.md`](releases/v0.8/EVAL_MATRIX.md) |
| `docs/v08/EVAL_PROTOCOL.md` | [`docs/releases/v0.8/EVAL_PROTOCOL.md`](releases/v0.8/EVAL_PROTOCOL.md) |
| `docs/v08/EXECUTION_STATE.md` | [`docs/releases/v0.8/EXECUTION_STATE.md`](releases/v0.8/EXECUTION_STATE.md) |
| `docs/v08/GAP_REGISTER.md` | [`docs/releases/v0.8/GAP_REGISTER.md`](releases/v0.8/GAP_REGISTER.md) |
| `docs/v08/INDEPENDENCE_AND_LEAKAGE.md` | [`docs/releases/v0.8/INDEPENDENCE_AND_LEAKAGE.md`](releases/v0.8/INDEPENDENCE_AND_LEAKAGE.md) |
| `docs/v08/PERFORMANCE.md` | [`docs/releases/v0.8/PERFORMANCE.md`](releases/v0.8/PERFORMANCE.md) |
| `docs/v08/PLAN.md` | [`docs/releases/v0.8/PLAN.md`](releases/v0.8/PLAN.md) |
| `docs/v08/REAL_RUNS.md` | [`docs/releases/v0.8/REAL_RUNS.md`](releases/v0.8/REAL_RUNS.md) |
| `docs/v08/RESEARCH_LANDSCAPE.md` | [`docs/releases/v0.8/RESEARCH_LANDSCAPE.md`](releases/v0.8/RESEARCH_LANDSCAPE.md) |
| `docs/v08/SEMANTICS.md` | [`docs/releases/v0.8/SEMANTICS.md`](releases/v0.8/SEMANTICS.md) |
| `docs/v08/TRACEABILITY.md` | [`docs/releases/v0.8/TRACEABILITY.md`](releases/v0.8/TRACEABILITY.md) |
