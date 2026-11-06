# Qualificação da v0.7.0.dev0

Três coisas diferentes, nunca somadas:

- **Implementação concluída**: código + testes que rodaram e passaram.
- **Qualificação local**: `scripts/qualify.py` numa revisão, em plataformas nomeadas.
- **Qualificação externa**: CI do GitHub verificada ao vivo por SHA, holdout de outra pessoa, revisão humana cega, detectores reais.

Este documento é preenchido no fechamento (CP15/CP16) com os resultados reais; enquanto um item não rodou, ele diz NOT_RUN.

## O que a CI valida (e o que não valida)

O workflow `.github/workflows/ci.yml` (só `workflow_dispatch`) roda, em Linux e Windows com Python 3.11–3.13: instalação do pacote, `scripts/validate_package.py`, a suíte unittest, a suíte semântica dev, a revisão por pseudo-terminal (Linux) e, no job `package`, sdist → wheel → venv limpo → smoke fora do checkout. **Não** valida qualidade percebida, equivalência semântica de reescritas reais, revisão humana nem autoria. O gate `ci:github-actions` só é PASS com consulta ao vivo de um run completo e verde naquele SHA ou num ancestral do qual só mudaram arquivos de evidência (`scripts/ci_evidence.py`).

## Avaliação humana (CP13)

| Item | Instrumento | Estado |
|---|---|---|
| Revisão humana cega pareada | `voznativa blind-tasks / blind-review / blind-summary` (respostas assinadas, uma por tarefa e chave, mapeamento de braços vinculado) | instrumento PASS nos testes (`evals/test_blind_review.py`); **rodada humana NOT_RUN**: `evals/reviewers/registry.json` sem revisor |
| Holdout semântico independente | protocolo em `evals/semantic/INDEPENDENT_HOLDOUT.md` | **NOT_RUN**: precisa de outra pessoa |
| Benchmark de detectores com textos humanos consentidos | `docs/V07_EXTERNAL_BENCHMARK.md` | **LIVE_NOT_RUN** |

Nenhuma avaliação humana foi simulada por persona automatizada.

## Resultados por plataforma

Preenchido no CP15/CP16.
