# Rastreabilidade da v0.10

> Objetivo → requisito → módulo/contrato → teste → execução → evidência. Linhas são preenchidas quando o teste existe e rodou; antes disso, ficam como planejadas.

| Objetivo | Requisito | Módulo | Teste | Execução / evidência | Estado |
|---|---|---|---|---|---|
| Baseline | R1 | — | `qualify.py --scope release --offline` em `v0.9.0` | [`EXECUTION_STATE.md`](EXECUTION_STATE.md) | PASS (local) |
| Conjuntos prospectivos | R6 | `evals/v010` | `scripts/v010_prospective_eval.py` | `evals/v010/runs/dev-base-v090.json` | baseline medida |
