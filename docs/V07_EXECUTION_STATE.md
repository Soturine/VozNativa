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
| CP5 | Router v3 (G1) | concluído | `f7c10f1` | G1 fechado; Context Contract v3 (14 dimensões, `protections`); `evals/test_router_v3.py` + 14 oráculos congelados (14/14 na 1ª execução); suítes congeladas sem mudança; corpora: 0 `whatsapp` errado |
| CP6 | Gíria/contexto (G3) | concluído | `2e88a46` | G3 fechado; amostras congeladas `cases-v07` 18/18 (1ª: 17/18 por contagem de ids) e `cases-v07b` 6/12 → 12/12; `evals/test_slang_v07.py`; gíria em fontes formais → 0; mutantes de `temporal.py`: reexecução no CP14 (módulo mudou) |
| CP7 | Contrato long-form | concluído | `60f14b4` (com CP8) | `voznativa/document.py` (plano v1: unidades sem perda, núcleo/bordas, protegidos, inventário, carry, dependências, limites, validação fail-closed); testes `Contract` (7) |
| CP8 | Rewrite por segmentos (G4) | concluído | `60f14b4` (com CP7) | `engine.rewrite_document` + CLI `rewrite --long-form`; E2E com stub determinístico, NO_CHANGE, falha, malicioso/injeção, timeout, limites, orçamento + retomada, estrutura, falha global com reversão, documento grande, CLI com provedor de comando real; G4 fechado; chamadas com modelo externo: NOT_RUN (sem autorização de custo) |
| CP9 | Guards globais | concluído | `2a21c7e` | 3 falsos verdes do `compare` corrigidos (negação deslocada, parágrafo dependente movido, frase curta nova); 6 variações metamórficas estáveis; guards do documento; `evals/test_global_guards.py`; suítes congeladas inalteradas; `ptbr-bench-v4` 22/22 (rodada limpa após o commit) |
| CP9L | Camada linguística (adendo 1) | concluído | `d51e110` | `voznativa/morph.py` + sinal `tense_changed`; ADR-0002; medição contra ouro UD em 4 treebanks; `evals/test_morph.py`; inventário e backlog em `docs/V07_LINGUISTICS.md`; `ptbr-bench-v4` 22/22 em `2a21c7e` (evidência deste commit) |
| CP9D | Erros do original e modos editoriais (adendo 2) | concluído | (este commit) | `voznativa/diagnose.py`, CLI `diagnose` e `rewrite --mode`; `evals/test_diagnose.py` (12); FP em texto humano medido; variante do gatilho de subjuntivo medida e rejeitada como padrão |
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

- README, DX & documentation UX → CP15 (RF-21).

## Próximo passo

CP10.
