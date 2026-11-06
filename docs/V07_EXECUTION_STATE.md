# Estado de execução da v0.7.0 (retomada de sessão)

Retome por este arquivo **e** pela realidade do Git (`git fetch --prune; git log --oneline origin/dev/v0.7.0 -20`), nunca pela memória de uma conversa. Se divergirem, o Git vence e este arquivo é corrigido.

- Branch: `dev/v0.7.0` (criada de `bf8e1a4` = `origin/main` em 2026-11-06)
- Política: push por CP verificado com `git ls-remote`; nenhuma Action até o CP16.
- Cache de corpora: fora do Git, em `VOZNATIVA_CORPUS_CACHE` (scratchpad da sessão). `voznativa corpus prepare <id>` refaz.

## Checkpoints

| CP | Título | Estado | Commit | Verificação |
|---|---|---|---|---|
| CP0 | Baseline, plano, riscos | concluído | (este commit) | `qualify.py` local em `bf8e1a4`: 460 testes (457 PASS + 3 xfail), gates PASS, veredito INCOMPLETE (pty/CI/humanos); Engine 97 candidatos INFO; Assertiva 1 INFO (`evals/assurance/runs/2026-11-06-v07-cp0/`) |
| CP1 | Harness e integridade de CI | pendente | | |
| CP2 | Ingestão v2 (TEI) e governança | pendente | | |
| CP3 | Expansão de corpora | pendente | | |
| CP4 | Contenção e splits (G2) | pendente | | |
| CP5 | Router v3 (G1) | pendente | | |
| CP6 | Gíria/contexto (G3) | pendente | | |
| CP7 | Contrato long-form | pendente | | |
| CP8 | Rewrite por segmentos (G4) | pendente | | |
| CP9 | Guards globais | pendente | | |
| CP10 | ptbr-bench-v5 OOD | pendente | | |
| CP11 | Detectores externos | pendente | | |
| CP12 | Unicode/proveniência/browser | pendente | | |
| CP13 | Avaliação humana e evidência | pendente | | |
| CP14 | Dogfood e mutação | contínuo | | |
| CP15 | Pacote, docs, compatibilidade | pendente | | |
| CP16 | Merge na main + CI manual | pendente | | |

## Bloqueios conhecidos

- Holdout independente e revisão humana cega: dependem de pessoas (NOT_RUN).
- Detectores de IA live: sem chave/autorização de upload nesta sessão (LIVE_NOT_RUN até haver).
- Gutenberg e ALiB falharam TLS na v0.6 (não desativar verificação).

## Próximo passo

CP1.
