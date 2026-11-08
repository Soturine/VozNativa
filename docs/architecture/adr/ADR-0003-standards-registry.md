# ADR-0003 — Standards Registry reaproveita o contrato do Corpus Registry (proposta)

Status: **proposto** (2026-11-06), não implementado. Contexto: adendo "Versioned Standards, Document Intelligence & Evaluation Framework"; visão em `docs/architecture/V08_STANDARDS_VISION.md`.

## Decisão proposta

Normas, editais, manuais, rubricas e templates serão registrados com o mesmo padrão do Corpus Registry: um YAML por fonte, validação estrita que nunca carrega parcialmente, escada de status que exige evidência por degrau (identidade, acesso, conteúdo verificado), verificação datada com URL e hash, e direitos por operação (consultar, citar regra parafraseada, redistribuir texto). Regras de aplicação (vigência, precedência) ficam no núcleo compartilhado; especificidades de instituição são packs declarativos.

## Alternativas

- Módulo por instituição (ENEM, ABNT...): rejeitado — duplica lógica e fixa versões.
- Regras embutidas em código: rejeitado — sem rastreabilidade de versão nem de vigência.

## Consequências

Nenhum código nesta rodada. A primeira implementação deve vir com testes de replay histórico e de conflito antes de qualquer regra real.
