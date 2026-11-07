# Estado de execução da v0.8.0 (retomada de sessão)

Retome por este arquivo **e** pelo Git (`git fetch --prune; git log --oneline origin/dev/v0.8.0 -20`). Se divergirem, o Git vence e este arquivo é corrigido.

- Branch: `dev/v0.8.0`, criada de `main` = `c2708de` em 2026-11-07.
- Plano: [`PLAN.md`](PLAN.md). Gaps: [`GAP_REGISTER.md`](GAP_REGISTER.md). Rastreabilidade: [`TRACEABILITY.md`](TRACEABILITY.md).
- Política: push da branch por CP com `scripts/checkpoint.py push`; nenhuma Action até o CP17; tag e pre-release só no CP18.

## Checkpoints

| CP | Título | Estado | Commit | Verificação |
|---|---|---|---|---|
| CP0 | Discovery, AS-IS, baseline | concluído | (este commit) | `qualify --scope release` em `c2708de`, árvore limpa, Windows 10 + CPython 3.12.6: 726 testes (725 + 1 skip POSIX), gates locais PASS, `ci:github-actions` PASS, exit 3 só por `review:pty`, holdout e revisão humana. v4 22/22, v5 36/36, predicados 16/20 e 1/18. GAP-01 e GAP-09 reproduzidos. `evals/assurance/runs/2026-11-07-v08-cp0/` |

| CP1 | Integridade: autorização do chamador, `resume` sem autoridade | concluído | (este commit) | GAP-01 e GAP-09 corrigidos. `evals/test_v08_integrity.py` (14 testes): em `2ced479` 7 falham ou dão erro por método, 4 controles passam, 1 passa sem provar. 7 mutantes à mão, todos mortos, depois de um controle sem mutação (`scripts/experiments/v08_cp1_mutants.py`, `evals/assurance/runs/2026-11-07-v08-cp1/MUTANTS.md`). Mudança de API anotada no CHANGELOG |

| CP2 | Desempenho de spans e morfologia | concluído | (este commit) | `spans.extract` 40 mil palavras 18,6 s → 1,6 s, 80 mil 30,1 s → 3,0 s, saída idêntica; `build_plan` 40 mil 9,1 s → 0,73 s; ordem de `morph` estável. Aberto e medido: `compare` quadrático (GAP-12) e falso vermelho em documento longo (GAP-13), ambos para o CP7. [`PERFORMANCE.md`](PERFORMANCE.md) |
| CP3 | DX I: doctor, demo, erros, suíte contra o wheel | concluído | (este commit) | `voznativa doctor` e `voznativa demo` (29 subcomandos); erros de arquivo/encoding/pasta em PT-BR com exit 64; gate de pacote roda a suíte inteira contra o wheel (748, 746 PASS, 2 skips com motivo; origem do import conferida). `evals/test_v08_dx.py` 13 testes |
| CP4 | Evaluation Core | concluído | (este commit) | `voznativa evaluate` sobre 9 suítes existentes, lidas no lugar: development 109 casos (sensibilidade 61/61, falso alarme 0/17), frozen_regression 176 (85/89, 1/33; decisão exata 28/30); nada independente. `evals/test_v08_evaluation.py` 18 testes. Registro em `evals/v08/runs/`. [`EVAL_PROTOCOL.md`](EVAL_PROTOCOL.md) |

## Regras desta rodada

- **Commits:** sem `Co-authored-by` nem trailer de IA; identidade local (`git config --local`): Rafael Souza, noreply Soturine. Sem force push, sem `reset --hard`. Tag e release só no CP18, nas condições do plano. Sem PyPI.
- **Gate antes do commit:** `python scripts/qualify.py --scope local --only validator,unittest,semantic:dev,semantic:holdouts:safety,semantic:holdouts:strict,decision:regression,router:regression,cli:exit-codes,ci:workflow-triggers --out <scratch>/q.json`, exit 0, encadeado com `&&`.
- **Não escrever na árvore durante um gate** (registros de bench vão depois ou para o scratchpad). `scripts/bench_v4.py` não aceita `--help`: ele roda o bench e grava em `benchmarks/runs/`.
- **Edição de arquivos:** nada de heredoc com barra invertida; usar a ferramenta de edição ou script em arquivo.
- **Upstream:** Assertiva (push e pull_request disparam Actions) e Framework (pull_request): não fazer push. Engine: só `push` na `main` dispara; a branch da PR #3 pode receber push.

## Bloqueios conhecidos

- Python 3.11 não instalado nesta máquina (GAP-10).
- Holdout independente, revisão humana cega, provider real e detectores live: NOT_RUN até haver pessoas e autorização de custo.

## Próximo passo

CP5: splits, contenção entre conjuntos (GAP-08), congelados byte-idênticos, braços B0–B6 numa API comum.
