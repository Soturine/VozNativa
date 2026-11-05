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

## CP4 — hardening da v0.4.0 — implementado e testado (2026-11-05)

| Item | Resultado | Evidência |
|---|---|---|
| H1 | runner `scripts/qualify.py`; exit 64 para erro de uso em todo comando (antes 2 = `review_required`); `baseline.py` conta todos os desfechos do unittest; falso verde NC1 corrigido (conjunto congelado fixo, decisão e benchmark com hash); registro de revisores validado; código morto e lista duplicada removidos | `8b103e7`…`9793d0d` |
| H2 | eixos de desfecho separados; `provider_error` nunca conta como sucesso; reanálise do oficial sem alterá-lo (v0.4.0: 12/15 tarefa cumprida ou pendente, 1 falha de sistema, invariantes 14/14 onde houve saída) | `286dfc8`, `H2_BENCHMARK_REANALYSIS.md` |
| H3 | `dc-021` erro de expectativa (contradiz o contrato do README); `dc-029` INCONCLUSIVE (limiar sem calibração); nada ajustado | `bbdc5d6`, `H3_PLANNER_CASES.md` |
| H4 | dia da semana sem preposição (falso vermelho de `bv2-li-02` e um falso verde), "2 da tarde", verbos multiplicadores (`ho-007` passa estrito), troca de papéis/ordem com substantivos comuns; probe 19/29 → 25/29; pronomes, troca entre frases e inflexão diferente ficam como limitação | `4af90ac`, `78502c1`, `c341967`, `24ba7e2`, `H4_SEMANTIC_LEDGER.md` |
| H5 | `signals.markers` indexado (compare 8k palavras 10,4 s → 0,96 s); `adherence` com poda por limite superior (loop sem modelo 48,6 s → 1,1 s); cache de ledger medido e rejeitado; testes diferenciais com mutantes mortos | `eb8ea99`, `a8c9d41`, `evals/perf/v0.4.0-dev-h5-*.json` |
| H5 (achado) | contração no primeiro termo de uma frase marcadora ("na função de" lido como causal) | `df42939` |
| H6 | chave de revisão criada com 0600 em uma chamada; testes do sanitizador de relatórios; varredura de caminhos/nomes nos arquivos versionados: limpa | `218e912` |

Não validado neste ponto: Linux (WSL disponível; vai no CP10), Python 3.11/3.13, comportamento com modelo depois das correções (nenhuma chamada paga feita no CP4).
