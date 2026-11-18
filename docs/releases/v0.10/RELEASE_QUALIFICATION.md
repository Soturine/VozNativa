# Qualificação da v0.10.0

> Critérios R1–R15 congelados no CP0 ([`PLAN.md`](PLAN.md)). Preenchido com o que de fato rodou; o que não rodou fica NOT_RUN. Em preenchimento até o CP14.

| # | Critério | Resultado |
|---|---|---|
| R1 | baseline v0.9.0 reproduzida | **PASS** (CP0): todos os gates locais em worktree da tag |
| R4 | benches, predicados, regressões ≥ v0.9 | **PASS** (CP12): v4 22/22, v5 36/36, predicados 19/20 e 1/18, regressão 88/89 e 1/33, conjuntos da v0.9 iguais |
| R6 | semântica, diagnóstico, edição desnecessária | **PASS** (CP12): dev 21/21 e 0/13, holdout 12/12 e 0/10 (base 10/12, 5/10); diagnóstico dev 7/7 e 0/9, holdout 5/5 e 0/5 (base 1/5); braços: engine 0/4 edições desnecessárias |
| R10 | mutação | **PASS**: 24/25 mortos (96%); sobrevivente equivalente documentado |
| R11 | desempenho | **PASS** pelo método intercalado (razão ≈ 1,015); a primeira medição isolada deu 1,30 por deriva da máquina entre sessões, registrada em `evals/v010/runs/perf-2026-11-18.json` |
