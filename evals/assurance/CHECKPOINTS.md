# Checkpoints da rodada "Continuous Assurance, v0.4 Hardening e v0.5.0 Regional Evidence"

Registro do que foi **implementado, validado, não validado e bloqueado** em cada checkpoint. Saídas das ferramentas em `runs/`.

## CP0 — baseline (2026-11-05) — concluído

- Estado confirmado: `main` = `0ba7bc2`, `origin/v0.4.0-dev` = `4044cfc` (44 commits à frente), árvores limpas.
- Executado: validador, 281 testes, 7 suítes semânticas (`holdout.jsonl` exit 1 por `ho-007`), decisão 28/30, Engine `inspect`/`evaluate`, Assertiva estática e `--execute`, 8 controles negativos.
- Baseline: `evals/baselines/v0.4.0-hardening-start.json`; análise: `runs/2026-11-05-cp0-baseline/ANALYSIS.md`.
- Divergências do pedido: `derivanta-engine review` não existe na 0.1.0; a Assertiva global tem metadados `0.5.5` (não usada).

## CP1 — perfil derivado — concluído

- `docs/ENGINEERING_PROFILE.md`: casos de uso, invariantes, máquina de estados do `rewrite`, fronteiras de confiança, requisitos de teste e achados estruturais.
- Sem ADR (nenhuma decisão material ainda).

## CP4/H1 — runner de qualificação — implementado e testado

- `scripts/qualify.py`: 13 gates, cada um em processo próprio com exit code preservado; estados PASS/FAIL/BLOCKED/NOT_RUN/SKIPPED/INCONCLUSIVE/WAIVED_BY_OWNER; relatório JSON UTF-8; sem pipelines de shell; reproduz o job `package` do CI (sdist → wheel → venv limpo → smoke).
- Falhas conhecidas explícitas em `evals/qualification/expectations.json`; evidência externa em `evals/qualification/external.json` (CI BLOCKED, holdout independente e revisão humana NOT_RUN).
- `evals/test_qualify.py` (10 testes): skip, nada coletado e erro de importação nunca viram PASS; falha nova não se esconde atrás de falhas conhecidas.
- Primeira execução (`--scope release`, Windows/3.12): o runner achou o próprio defeito de descoberta (crash classificado como FAIL, corrigido); `cli:exit-codes` **FAIL**: erro de uso sai com 2, o mesmo código de `review_required` do `compare` (defeito confirmado, ainda não corrigido).
- Não validado: Linux (gate `review:pty` só roda em POSIX), Python 3.11/3.13.

## Próximo (não iniciado)

H1 restante: corrigir exit 64 de uso no CLI; trocar a leitura de unittest do `baseline.py` pelo runner. Depois H2 (benchmark: `provider_error` não conta como invariantes ok), correção do falso verde NC1, H3–H6, CP5+.
