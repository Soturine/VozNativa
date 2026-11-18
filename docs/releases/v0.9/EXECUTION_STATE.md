# Estado de execução da v0.9.0 (retomada de sessão)

Retome por este arquivo **e** pelo Git (`git fetch --prune; git log --oneline origin/dev/v0.9.0 -20`). Se divergirem, o Git vence e este arquivo é corrigido.

- Branch: `dev/v0.9.0`, criada de `main` = `17d1f10` (tag `v0.8.1`) em 2026-11-18.
- Plano e critérios de release: [`PLAN.md`](PLAN.md). Gaps: [`GAP_REGISTER.md`](GAP_REGISTER.md). Rastreabilidade: [`TRACEABILITY.md`](TRACEABILITY.md).
- Política: commit por CP; antes de cada push, `scripts/privacy_gate.py` sobre os commits não publicados, lido como comando separado; nenhuma Action até o CP9.

## Checkpoints

| CP | Título | Estado | Commit | Verificação |
|---|---|---|---|---|
| CP0 | Estado, baseline, gate de privacidade, plano | concluído | ver `git log` | baseline abaixo; gate de privacidade com 7 testes; critérios R1–R10 congelados |

## Baseline (CP0)

Revisão `17d1f10` (tag `v0.8.1`), worktree limpa separada, Windows 10, CPython 3.12.6, 2026-11-18.

| Instrumento | Resultado |
|---|---|
| `qualify.py --scope release` (324 s) | validador, unittest (933: 931 PASS, 2 skips com motivo; 138 s), semântica dev 77/77, holdouts safety e strict, decisão 28/30, roteador 15/16, códigos de saída, gatilhos da CI, pacote (sdist → wheel → venv → smoke → suíte contra o wheel): **PASS**. `ci:github-actions` PASS ao vivo: run #128 (43893178929), `workflow_dispatch`, `17d1f10`, 8/8, relação `same`. Veredito INCOMPLETE (exit 3) só por `review:pty` (POSIX), holdout independente e revisão cega humana (NOT_RUN) |
| `ptbr-bench-v4` | 22/22 |
| `ptbr-bench-v5` | 36/36 (Wilson 95%: 0,904–1,0) |
| amostra de predicados | 17/20 riscos, 1/18 falsos alarmes |
| `scripts/perf_compare.py` (5 repetições) | 2.200 palavras: CPU mín. 0,41 s; 8.800: 2,09 s; 17.600: 5,84 s; razão 800/100 blocos = 14,4× |
| Reprodução sintética de gaps | ver [`GAP_REGISTER.md`](GAP_REGISTER.md) (V09-GAP-01 a 08) |

Ambiente disponível: CPython 3.12.6 e 3.11.18 (gerenciado pelo uv, fora do `py`), Docker 28.5.1 respondendo, Claude Code 2.1.317, PyMuPDF e pypdf instalados no Python do usuário (não são dependências do pacote). Ausentes: Codex, Gemini CLI, Ollama, `EMULATE_API_KEY`. Assertiva 0.10.1 e Derivanta Engine 0.1.0 em clones locais.

## Regras desta rodada

- **Commits:** sem `Co-authored-by` nem trailer de IA; identidade local (`git config --local`): Rafael Souza, noreply Soturine. Sem force push, sem `reset --hard`.
- **Gate antes do commit:** `python scripts/qualify.py --scope local --only validator,unittest,semantic:dev,semantic:holdouts:safety,semantic:holdouts:strict,decision:regression,router:regression,cli:exit-codes,ci:workflow-triggers --out <scratch>/q.json`.
- **Gate antes do push:** `python scripts/privacy_gate.py --base origin/<branch> --private <doc> ... --terms-file <fora do repo>`; ler o veredito; só então `git push` em comando separado.
- **Dados privados:** documentos e saídas dos dogfoods ficam fora do repositório; fixtures sintéticas de outro domínio.
- **Edição de arquivos:** nada de heredoc com barra invertida; usar a ferramenta de edição.

## Próximo passo

CP1.
