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
| REMOTE_CI | **PASS** em `9f44010`: run #124 (id 42260943492), `workflow_dispatch`, 8/8 jobs (Ubuntu e Windows × 3.11/3.12/3.13 + pacote nos dois), verificado ao vivo por `scripts/ci_evidence.py` | https://github.com/Soturine/VozNativa/actions/runs/42260943492 |
| INDEPENDENT_HOLDOUT | NOT_RUN | precisa de outra pessoa |
| BLIND_HUMAN_REVIEW | NOT_RUN | registro de revisores vazio |
| EXTERNAL_DETECTOR_BENCH | LIVE_NOT_RUN | sem chaves, sem textos humanos consentidos |
| RELEASE_READINESS | não pronto para release estável | 0.7.0.dev0; sem tag, sem PyPI |

## CI remota (CP16)

`main` avançou por fast-forward de `bf8e1a4` para `9f44010` (26 commits) sem disparar nenhuma Action. Um único `gh workflow run ci.yml --ref main` gerou o run #124: concluído com sucesso, 8/8 jobs, no SHA exato. Commits posteriores a `9f44010` mudam só arquivos de evidência (`evals/qualification/external.json`, `evals/assurance/runs/`, este arquivo e `docs/V07_EXECUTION_STATE.md`); o gate verifica isso por `git diff` e mantém PASS por equivalência só-evidência. Custo: um run de 8 jobs; nenhum outro run desta rodada no VozNativa. No repositório da Assertiva, dois runs foram disparados por engano por um push na PR #8 e cancelados (VN07-DISC-034).

## v0.7.0.dev1 (estabilização)

As seções acima são da dev0 e ficam como registro histórico. Esta seção qualifica a `0.7.0.dev1`. Plano e achados: `docs/PLAN_v0.7.0.dev1.md` e `docs/V07_DISCOVERY_REGISTER.md` (VN07-DISC-037..057).

### Qualificação local (CP6)

Revisão `f1f7446` (versão `0.7.0.dev1`), árvore limpa em todas as execuções, `scripts/qualify.py --scope release`. Registros: `evals/assurance/runs/2026-11-07-h07-cp6/`.

| Plataforma | Python | unittest | validator, semântica, holdouts, decisão, roteador, CLI, gatilhos de workflow | pacote (sdist → wheel → venv limpo → smoke fora do checkout) | `review:pty` | Veredito |
|---|---|---|---|---|---|---|
| Windows 10 | 3.12.6 | 726: 725 PASS, 1 skip (POSIX) | PASS | PASS | NOT_RUN (POSIX) | INCOMPLETE (exit 3, externos) |
| Windows 10 | 3.11.9 | 726: 725 PASS, 1 skip (POSIX) | PASS | PASS | NOT_RUN (POSIX) | INCOMPLETE (exit 3, externos) |
| Linux local (3.11, 3.12, 3.13) | — | — | — | — | — | **BLOCKED**: sem distro WSL nesta máquina; o engine Linux do Docker Desktop respondeu HTTP 500 durante toda a sessão |

- Nos dois runs do Windows, os gates externos ficaram NOT_RUN: `ci:github-actions` (ainda não havia run nesta revisão), `holdout:independent` e `review:blind-human`. Nenhum gate local falhou.
- A variável `PIP_NO_BUILD_ISOLATION=0` existia no ambiente do usuário e foi removida para os runs; a CI não a define.
- O Python 3.11.9 portátil vem do pacote NuGet, com SHA512 conferido contra o catálogo.

**Sem prova local no Linux nesta rodada.** A única evidência Linux da dev1 é a CI do CP7: `ubuntu-latest` com 3.11, 3.12 e 3.13, mais o job de pacote. O `review:pty` só roda em POSIX. Ele está no job Linux da CI, mas não foi executado localmente nesta rodada.

### Benchmarks e medições (árvore limpa, `f1f7446`)

| Instrumento | Resultado |
|---|---|
| `ptbr-bench-v4` | 22/22, exit 0 (`benchmarks/runs/ptbr-bench-v4-20261107T061937Z.json`) |
| `ptbr-bench-v5` | 36/36, exit 0 (`benchmarks/runs/ptbr-bench-v5-20261107T061937Z.json`) |
| Amostra de predicados (não independente, mesmo autor) | 16/20 riscos sinalizados, 1/18 falso alarme (`evals/predicates/runs/predicates-2026-11-07-dev1.json`). A linha de base em `e7506f5` era 7/20 e 4/18 |
| Mutação (`AGENT_OBSERVED`, Cosmic Ray 8.7.0 com `-B`) | `compare.py` nas linhas 76 e 429–583: 271/271, 201 mortos; oráculos novos matam 44 dos 70 sobreviventes (`evals/assurance/runs/2026-11-07-h07-cp5b/MUTATION.md`). `temporal.py`: 674/922. `document.py`: amostra de 120 de 454 |

### CI remota (CP7)

Pendente até o merge na `main`: um único `workflow_dispatch`, verificado ao vivo por `scripts/ci_evidence.py`.

### Veredito por dimensão (dev1, antes da CI)

| Dimensão | Estado | Base |
|---|---|---|
| IMPLEMENTATION | PASS no escopo da dev1 (H07-001..020) | `docs/PLAN_v0.7.0.dev1.md`, testes por requisito |
| LOCAL_QUALIFICATION | PASS (gates locais) em Windows 3.11/3.12; **Linux local BLOCKED** | tabela acima |
| REMOTE_CI | pendente (CP7) | — |
| INDEPENDENT_HOLDOUT | NOT_RUN | precisa de outra pessoa |
| BLIND_HUMAN_REVIEW | NOT_RUN | registro de revisores vazio |
| EXTERNAL_DETECTOR_BENCH | LIVE_NOT_RUN | sem chaves, sem textos humanos consentidos |
| RELEASE_READINESS | não pronto para release estável | 0.7.0.dev1; sem tag, sem PyPI |
