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
| CP9D | Erros do original e modos editoriais (adendo 2) | concluído | `1469b8b` + `d2eb53e` | `voznativa/diagnose.py`, CLI `diagnose` e `rewrite --mode`; `evals/test_diagnose.py` (12); FP em texto humano medido; variante do gatilho de subjuntivo medida e rejeitada como padrão |
| CP10 | ptbr-bench-v5 OOD | concluído | `36dd20c` (congelamento), `e634a3b` (runner), `f5cacd6`/`0233670` | 1ª execução oficial 34/36 em `e634a3b` (roteamento 14/16); correções gerais; rodada pós-correção registrada a seguir; `docs/V07_OOD_BENCHMARK.md` |
| CP11 | Detectores externos | concluído (infra) | `5c2377a` | adapters Copyleaks (contrato verificado), GPTZero (parcial), Originality (UNSUPPORTED), mock/replay rotulados; protocolo H0/H1/A0/A1; 9 testes; live **LIVE_NOT_RUN** |
| CP12 | Unicode/proveniência/browser | concluído | `a5570a2` | `voznativa/integrity.py`, `voznativa integrity`, `provenance` no `rewrite`; 8 testes; navegador UNSUPPORTED (sem alvo autorizado); Art. 50 registrado |
| CP13 | Avaliação humana e evidência | concluído (estado honesto) | `7d2382b` | instrumento cego testado; rodada humana, holdout independente e detectores live NOT_RUN; `docs/V07_RELEASE_QUALIFICATION.md` diz o que a CI valida |
| CP14S | Linha futura de Standards (adendo 3, só docs) | concluído | (este commit) | `docs/V08_STANDARDS_VISION.md`, ADR-0003 (proposto); nada implementado |
| CP14 | Dogfood e mutação | concluído | `3fb4163`, `a4426e4`, `7d2382b`, este commit | Engine: 5 corrigidos → ABSENT; Assertiva `--execute` PASS; AXF-VN-01 corrigido upstream (Assertiva PR #8 `3415828`); Engine PR #3 `7e8e9ee`; mutação de `temporal.py`: 613 → 633 mortos de 875, 44 executáveis triados (`evals/assurance/runs/2026-11-06-v07-cp14/MUTATION.md`); incidente: 2 runs de Actions da Assertiva disparados e cancelados |
| CP15 | Pacote, docs, compatibilidade | concluído | `7d2382b`, `cc0a00b`, `37e8d6e`, este commit | README novo testado; versão 0.7.0.dev0; qualificação local de `37e8d6e` PASS (gates locais) em Windows 3.11/3.12 e WSL 3.11/3.12/3.13; pacote PASS fora do checkout; auditoria da abstenção do roteador |
| CP16 | Merge na main + CI manual | concluído | `9f44010` (main), este commit (evidência) | fast-forward `bf8e1a4` → `9f44010` sem Action automática; run #124 (42260943492) `workflow_dispatch` success 8/8, verificado ao vivo; VN07-DISC-003 resolvido: Actions executou normalmente (sem bloqueio de cobrança) |

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

Rodada v0.7.0 fechada como 0.7.0.dev0 (sem tag, sem PyPI). Abertos: braços com modelo, revisão humana cega, holdout independente, detectores live, backlogs B-L*, B-D2, B-R1, B-R2, linha de normas (V08).

## v0.7.0.dev1 (estabilização)

Plano: `docs/PLAN_v0.7.0.dev1.md`. Branch `dev/v0.7.0-hardening`, criada de `main` = `e7506f5`. Retomada: `git fetch --prune; git log --oneline origin/dev/v0.7.0-hardening -20`; o Git vence este arquivo.

| CP | Título | Estado | Commit | Verificação |
|---|---|---|---|---|
| CP0 | Inventário, baseline, reproduções | concluído | `bc6f4fd` | baseline `qualify --scope release` em `e7506f5`, Windows 3.12.10: 635 testes (634 PASS + 1 skip POSIX), gates locais PASS, exit 3 INCOMPLETE (externos; `ci:github-actions` NOT_RUN porque a árvore ficou suja durante a execução); 8 achados reproduzidos (H07-F1..F8); `evals/test_hardening_h07.py` (4 xfail); amostra de predicados congelada (sha256 `b08827c5…`), linha de base 7/20 riscos, 4/18 falsos alarmes |
| CP1 | Retriagem dos mutantes de identidade | concluído | (este commit) | 12 mutantes aplicados à mão em `git archive` de `bc6f4fd` sem bytecode: suíte da rodada 2 → 12 sobrevivem; + `test_hardening_h07` → 5 mortos (91, 109, 235, 262, 303), 7 equivalentes argumentados; produção sem mudança; 2 achados de método (bytecode velho, `group(0)` de casamento total) |
