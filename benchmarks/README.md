# VozNativa Benchmarks

Protocolo completo: `docs/evaluation/COMPETITIVE_BENCHMARK.md`. Esta pasta guarda os casos congelados e a convenção de saídas.

## Layout

```text
benchmarks/
  cases/smoke.jsonl          # 2 casos curtos (sanidade do runner)
  cases/ptbr-v1.jsonl        # 8 casos PT-BR, 47-58 palavras (Emulate exige >= 40)
  manifest.example.json      # versões, modelo-base e juízes de uma execução
  outputs/<sistema>/<id>.txt                 # candidata (ignorado pelo git)
  outputs/<sistema>/<id>.judgment-N.json     # julgamento LLM ou humano (opcional)
```

Um julgamento segue o contrato de `voznativa judge-prompt` (`kind`, `judge_id`, `verdict`, `claims`, `added_claims`). Arquivos são aplicados em ordem de nome; um juiz LLM só aprova resultados determinísticos limpos, um humano também resolve revisões, e ninguém sobrescreve `fail`.

## Rodar

```bash
voznativa benchmark benchmarks/cases/ptbr-v1.jsonl benchmarks/outputs --manifest benchmarks/manifest.json --json benchmarks/results/run.json
```

O relatório separa, por sistema:

- `deterministic_status` (tier 0: spans, marcadores, invariantes `must_preserve` com fronteira de palavra e polaridade);
- `status` final depois dos julgamentos e `judgments_by_kind` (`llm`, `human`);
- `hard_pass_rate` com **todos** os casos no denominador (saída ausente conta como falha).

O runner não chama modelo nem detector. `cases_sha256` identifica a versão dos casos.

## O que ainda não existe

- execuções reais publicadas (nenhuma saída de sistema foi gerada neste repositório);
- painel de juízes, ordem aleatória e cegamento automatizados;
- intervalos de confiança.
