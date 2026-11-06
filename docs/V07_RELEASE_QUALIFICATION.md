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

## Resultados por plataforma (qualificação local)

Revisão `37e8d6e` (código idêntico ao que vai para a `main`; commits posteriores mudam só arquivos de evidência e documentação de estado), árvore limpa em todas as execuções, `scripts/qualify.py --scope release`. Registros: `evals/assurance/runs/2026-11-06-v07-cp15/`.

| Plataforma | Python | unittest | validator, semântica, holdouts, decisão, roteador, CLI, gatilhos de workflow | pacote (sdist → wheel → venv limpo → smoke fora do checkout) | `review:pty` | Veredito |
|---|---|---|---|---|---|---|
| WSL Ubuntu 24.04 | 3.11.16 | 635/635 PASS | PASS | PASS | PASS | INCOMPLETE (externos) |
| WSL Ubuntu 24.04 | 3.12.14 | 635/635 PASS | PASS | PASS | PASS | INCOMPLETE (externos) |
| WSL Ubuntu 24.04 | 3.13.15 | 635/635 PASS | PASS | PASS | PASS | INCOMPLETE (externos) |
| Windows 11 | 3.12.10 | 634 PASS, 1 skip (teste de pipeline POSIX) | PASS | PASS | NOT_RUN (POSIX) | INCOMPLETE |
| Windows | 3.11.18 | 634 PASS, 1 skip | PASS | PASS | NOT_RUN (POSIX) | INCOMPLETE |

Nenhum `expectedFailure` restante: G1–G4 viraram testes de regressão. Primeira rodada no WSL (`cc0a00b`) marcou o gate de pacote como FAIL porque o venv do `uv` não tinha pip; o gate passou a classificar isso como BLOCKED (VN07-DISC-036) e a rodada foi repetida com pip.

Gate `ci:github-actions` antes do merge: NOT_RUN no Windows (a consulta ao vivo não achou run nessa revisão, como esperado) e INCONCLUSIVE no WSL (sem `gh` instalado lá: consulta indisponível nunca vira PASS).

## Benchmarks e medições

| Instrumento | Resultado |
|---|---|
| `ptbr-bench-v4` (congelado na v0.6) | 22/22 (era 21/22; o caso que passou a passar originou o G3: não independente) |
| `ptbr-bench-v5` (congelado antes do runner) | 1ª execução 34/36; após duas correções de recall 36/36 (não independente para esses 2 casos) |
| Semântica dev + 5 holdouts | 77/77; holdouts sem detecção perdida, modo estrito sem divergência nova |
| Roteador nos 7 corpora | precisão das decisões emitidas 93,8% (Wilson 91,8–95,4), cobertura útil 8,8%, erradas 0,58% |
| Morfologia contra ouro UD (4 treebanks) | 93–97% de acerto nas análises únicas; 64–69% das análises cobertas são únicas |

## Veredito por dimensão

| Dimensão | Estado | Base |
|---|---|---|
| IMPLEMENTATION | PASS para o escopo marcado `[x]` no `ROADMAP.md`; PARTIAL onde marcado `[~]` | testes por requisito em `docs/V07_VERIFICATION_MATRIX.md` |
| LOCAL_QUALIFICATION | PASS (gates locais) em Windows 3.11/3.12 e Linux 3.11/3.12/3.13; INCOMPLETE como veredito por causa dos gates externos | tabela acima |
| REMOTE_CI | registrado no fechamento (CP16) | `scripts/ci_evidence.py` |
| INDEPENDENT_HOLDOUT | NOT_RUN | precisa de outra pessoa |
| BLIND_HUMAN_REVIEW | NOT_RUN | registro de revisores vazio |
| EXTERNAL_DETECTOR_BENCH | LIVE_NOT_RUN | sem chaves, sem textos humanos consentidos |
| RELEASE_READINESS | não pronto para release estável | 0.7.0.dev0; sem tag, sem PyPI |
