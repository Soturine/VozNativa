# Documentação do VozNativa

Comece pelo [`README`](../README.md) do projeto. Esta página leva cada pessoa ao documento certo; o estado de cada documento (vigente, histórico, de execução) está no [inventário](v08/DOCS_INVENTORY.md).

## Começar

| Quero... | Documento |
|---|---|
| instalar no Windows, Linux ou macOS | [guide/INSTALL.md](guide/INSTALL.md) |
| ver funcionando sem modelo nem chave (`doctor`, `demo`) | [guide/QUICKSTART.md](guide/QUICKSTART.md#1-ver-funcionando) |
| conferir se uma reescrita mudou o sentido | [guide/QUICKSTART.md](guide/QUICKSTART.md#2-conferir-uma-reescrita) |
| entender `NO_CHANGE`, `needs_judgment`, `returned_original` | [guide/QUICKSTART.md](guide/QUICKSTART.md#4-desfechos-do-rewrite) |
| reescrever com um provider | [guide/QUICKSTART.md](guide/QUICKSTART.md#5-com-um-provider) |
| revisar um documento longo | [guide/QUICKSTART.md](guide/QUICKSTART.md#6-documento-longo-normas-e-avaliação) |
| usar como Agent Skill (Claude Code, Codex, Gemini CLI) | [guide/AGENT_SKILL.md](guide/AGENT_SKILL.md) e [`SKILL.md`](../SKILL.md) |
| consultar todos os comandos e opções | [guide/CLI.md](guide/CLI.md) (gerado do `--help`) |
| resolver um erro | [guide/TROUBLESHOOTING.md](guide/TROUBLESHOOTING.md) |
| saber o que é seguro, privado e licenciado | [LICENSING.md](LICENSING.md); seção "Segurança e limites" do [README](../README.md) |

## Entender e integrar (desenvolvedores)

| Documento | Conteúdo | Estado |
|---|---|---|
| [v08/ARCHITECTURE.md](v08/ARCHITECTURE.md) | os três modos (determinístico, assistido por modelo, conduzido por agente), componentes, contratos, fronteiras de confiança | vigente |
| [guide/CLI.md](guide/CLI.md) | referência da CLI | vigente, gerado |
| [v08/SEMANTICS.md](v08/SEMANTICS.md) | quadros de evento, destinatário, conversos; causas dos erros restantes | vigente |
| [v08/DOCUMENT_STANDARDS.md](v08/DOCUMENT_STANDARDS.md) | normas, editais, rubricas: o que existe e com que fontes | vigente |
| [REGIONAL_EVIDENCE.md](REGIONAL_EVIDENCE.md) | Regional Evidence Packs e abstenção | vigente (desde a v0.5) |
| [CORPUS_AND_EVIDENCE_STRATEGY.md](CORPUS_AND_EVIDENCE_STRATEGY.md) | corpora e níveis de evidência | vigente |
| [V07_LINGUISTICS.md](V07_LINGUISTICS.md), [V07_INTEGRITY_AND_PROVENANCE.md](V07_INTEGRITY_AND_PROVENANCE.md) | análise verbal e diagnóstico; integridade e proveniência | vigentes (desde a v0.7) |
| [adr/](adr/) ([0001](adr/ADR-0001-regional-evidence-packs.md), [0002](adr/ADR-0002-linguistic-analysis.md), [0003](adr/ADR-0003-standards-registry.md)) | decisões de arquitetura | vigentes |
| [MODEL_ADAPTER_TRACK.md](MODEL_ADAPTER_TRACK.md) | trilha opcional de modelos e adapters | plano futuro |
| [DESIGN_SPEC.md](DESIGN_SPEC.md), [ARCHITECTURE_AND_RESEARCH.md](ARCHITECTURE_AND_RESEARCH.md) | tese de produto e arquitetura das primeiras versões | históricos; a arquitetura vigente é a da v0.8 |

## Avaliação e evidência (pesquisadores)

| Documento | Conteúdo | Estado |
|---|---|---|
| [v08/EVAL_PROTOCOL.md](v08/EVAL_PROTOCOL.md), [v08/EVAL_MATRIX.md](v08/EVAL_MATRIX.md) | protocolo (`voznativa evaluate`, splits, replay) e matriz de eixos | vigentes |
| [v08/INDEPENDENCE_AND_LEAKAGE.md](v08/INDEPENDENCE_AND_LEAKAGE.md) | o que um registro prova; vazamento encontrado entre conjuntos | vigente |
| [v08/PERFORMANCE.md](v08/PERFORMANCE.md) | curvas de tempo e memória | vigente |
| [v08/REAL_RUNS.md](v08/REAL_RUNS.md) | execuções com provider e agente reais: cenários, consumo, autorização | vigente (NOT_RUN) |
| [EVALUATION.md](EVALUATION.md) | benchmarks v1–v4 e execuções com modelo até a v0.7 | histórico com números válidos para sua época |
| [V07_OOD_BENCHMARK.md](V07_OOD_BENCHMARK.md), [V07_CORPUS_INTEGRATION.md](V07_CORPUS_INTEGRATION.md), [V07_EXTERNAL_BENCHMARK.md](V07_EXTERNAL_BENCHMARK.md) | `ptbr-bench-v5`, 7 corpora, protocolo de detectores | históricos da v0.7 (o v5 tem uma ressalva de vazamento) |
| [COMPETITIVE_BENCHMARK.md](COMPETITIVE_BENCHMARK.md) | protocolo de comparação com alternativas | vigente como protocolo |
| [v08/RESEARCH_LANDSCAPE.md](v08/RESEARCH_LANDSCAPE.md), [RESEARCH_LOG.md](RESEARCH_LOG.md), [COMPETITIVE_ANALYSIS_v0.6.md](COMPETITIVE_ANALYSIS_v0.6.md), [COMPETITIVE_ANALYSIS_v0.5.md](COMPETITIVE_ANALYSIS_v0.5.md) | pesquisa externa por data | a da v0.8 é a mais recente; as outras, registro |

## Engenharia e garantia (mantenedores)

| Documento | Conteúdo | Estado |
|---|---|---|
| [v08/EXECUTION_STATE.md](v08/EXECUTION_STATE.md) | checkpoints da v0.8, commits e retomada | execução em curso |
| [v08/PLAN.md](v08/PLAN.md), [v08/AS_IS.md](v08/AS_IS.md), [v08/GAP_REGISTER.md](v08/GAP_REGISTER.md), [v08/TRACEABILITY.md](v08/TRACEABILITY.md) | plano, ponto de partida, lacunas, rastreabilidade da v0.8 | execução em curso |
| [v08/DOCS_INVENTORY.md](v08/DOCS_INVENTORY.md) | inventário e estado de cada documento | vigente |
| [TRACEABILITY.md](TRACEABILITY.md) | requisitos v0.1–v0.7 → artefato → estado | vigente para esses requisitos |
| [ENGINEERING_PROFILE.md](ENGINEERING_PROFILE.md) | perfil de engenharia derivado da Constituição do Derivanta | vigente |
| [LICENSING.md](LICENSING.md) | licenças de terceiros e política de dados | vigente |

## Histórico de versões

| Versão | Documentos |
|---|---|
| v0.8 (em curso) | [`v08/`](v08/EXECUTION_STATE.md); [V08_STANDARDS_VISION.md](V08_STANDARDS_VISION.md) (visão, com o que já foi implementado) |
| v0.7 | [PLAN_v0.7.0.md](PLAN_v0.7.0.md), [PLAN_v0.7.0.dev1.md](PLAN_v0.7.0.dev1.md), [AS_IS_v0.7.0.md](AS_IS_v0.7.0.md), [V07_EXECUTION_STATE.md](V07_EXECUTION_STATE.md), [V07_DISCOVERY_REGISTER.md](V07_DISCOVERY_REGISTER.md), [V07_VERIFICATION_MATRIX.md](V07_VERIFICATION_MATRIX.md), [V07_DOGFOOD.md](V07_DOGFOOD.md), [V07_RELEASE_QUALIFICATION.md](V07_RELEASE_QUALIFICATION.md) |
| v0.6 | [AS_IS_v0.6.0.md](AS_IS_v0.6.0.md) |
| v0.5 | [PLAN_v0.5.0.md](PLAN_v0.5.0.md) |
| v0.4 | [PLAN_v0.4.0.md](PLAN_v0.4.0.md) |
| v0.3 | [PLAN_v0.3.0.md](PLAN_v0.3.0.md) |
| todas | [../ROADMAP.md](../ROADMAP.md), [../CHANGELOG.md](../CHANGELOG.md) |

Documentos históricos ficam onde sempre estiveram: registros de evidência, testes e scripts citam esses caminhos, e mudá-los quebraria a rastreabilidade.
