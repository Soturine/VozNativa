# Estado de execução da v0.7.0 (retomada de sessão)

Retome por este arquivo **e** pela realidade do Git (`git fetch --prune; git log --oneline origin/dev/v0.7.0 -20`), nunca pela memória de uma conversa. Se divergirem, o Git vence e este arquivo é corrigido.

- Branch: `dev/v0.7.0` (criada de `bf8e1a4` = `origin/main` em 2026-11-06)
- Política: push por CP verificado com `git ls-remote`; nenhuma Action até o CP16.
- Cache de corpora: fora do Git, em `VOZNATIVA_CORPUS_CACHE` (scratchpad da sessão). `voznativa corpus prepare <id>` refaz.

## Checkpoints

| CP | Título | Estado | Commit | Verificação |
|---|---|---|---|---|
| CP0 | Baseline, plano, riscos | concluído | `a59ad68` | `qualify.py` local em `bf8e1a4`: 460 testes (457 PASS + 3 xfail), gates PASS, veredito INCOMPLETE (pty/CI/humanos); Engine 97 candidatos INFO; Assertiva 1 INFO (`evals/assurance/runs/2026-11-06-v07-cp0/`) |
| CP1 | Harness e integridade de CI | concluído | `9eea718` | `evals/test_ci_evidence.py` 20 testes (1 skip POSIX no Windows); gates validator, unittest, decision, router, cli, workflow-triggers PASS via `scripts/checkpoint.py`; consulta live real: HEAD NOT_RUN, run #123 confere com o registro |
| CP2 | Ingestão v2 (TEI) e governança | concluído | `9cbaf0f` | `evals/test_corpus_tei.py` 17 testes (XXE/bomba recusados, licença por documento fail-closed, CoNLL-U com documento, cache dentro de repo recusado); suíte unittest PASS |
| CP3 | Expansão de corpora | concluído | `4d4587c` | 3 → 7 fontes EVALUATION_INTEGRATED (GSD, PetroGold, PUD, DANTEStocks); integridade sem vazamento; `scripts/corpus_crossgenre.py`; `evals/test_corpus_v07.py`; suíte PASS. Ver `docs/V07_CORPUS_INTEGRATION.md` |
| CP4 | Contenção e splits (G2) | concluído | `b19e92a` | G2 fechado (xfail → teste normal); `evals/test_containment.py` 11 testes; 184 vínculos reais, 0 entre fontes; 52 pares vazavam no split do CP3; reexecução sem vazamento; suíte PASS |
| CP5 | Router v3 (G1) | concluído | (este commit) | G1 fechado; Context Contract v3 (14 dimensões, `protections`); `evals/test_router_v3.py` + 14 oráculos congelados (14/14 na 1ª execução); suítes congeladas sem mudança; corpora: 0 `whatsapp` errado |
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

## Adendos recebidos durante o CP3

- Linguistic Intelligence & Morphosyntactic Assurance → CP9L (`docs/PLAN_v0.7.0.md`, RF-18).
- Document Understanding & Editorial Intelligence → CP7/CP9/CP9L/CP9D (RF-19).

- Versioned Standards & Evaluation Framework → linha futura; docs na v0.7 (CP14S, RF-20).

## Próximo passo

CP6.
