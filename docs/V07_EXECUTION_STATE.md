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
| CP1 | Retriagem dos mutantes de identidade | concluído | `80f3da3` | 12 mutantes aplicados à mão em `git archive` de `bc6f4fd` sem bytecode: suíte da rodada 2 → 12 sobrevivem; + `test_hardening_h07` → 5 mortos (91, 109, 235, 262, 303), 7 equivalentes argumentados; produção sem mudança; 2 achados de método (bytecode velho, `group(0)` de casamento total) |
| CP2 | Contrato das atestações do léxico | concluído | `e371fb4` | `temporal.validate_lexicon`: `count`/`words` inteiros >= 0 (bool, float e string recusados), anos inteiros com `from <= to`, `last_verified_at` ISO, `schema_version` inteiro; zero válido e sem atestar nada em `attested_in`/`entry_status`/`epoch_notes`; `CountContract` 9 testes; suítes de gíria 79 testes PASS; contrato em `references/slang/schema.yml` |
| CP3 | Predicados, eventos e compromissos | concluído (regra experimental) | `abad76b` | `compare._predicate_issues`/`_event_anchors` sobre `voznativa.morph`; amostra congelada não independente: antes 7/20 riscos e 4/18 FA, 1ª versão 14/20 e 1/18, versão final 16/20 e 1/18 (`evals/predicates/README.md`); `tense_changed` sem falso alarme de futuro; H07-007..010 em `test_hardening_h07.py` (oráculo do documento longo falha com a regra desligada); semântica dev/holdouts, decisão e roteador PASS; `ptbr-bench-v4` 22/22 e `-v5` 36/36 na árvore de trabalho; README e quickstart com três candidatas (boa, negação removida, ação perdida) |
| CP4 | README, SKILL, exemplos, alegações | concluído | `c909f1d` | abertura do README sem "prova"; limites com a regra de predicado; SKILL orienta `predicate_missing`/`predicate_replaced`; CHANGELOG `Unreleased (0.7.0.dev1)`; índice de docs; linha da amostra de predicados na tabela de evidência; `evals/test_readme.py` + `test_skill_contract` PASS (14); quickstart executado pela suíte; versão continua 0.7.0.dev0 até o CP6 |
| CP5 | Mutação e dogfood (agent-led) | concluído (mutação de `compare` parcial, por decisão do mantenedor) | (este commit) | Cosmic Ray com `-B`, todas as rodadas em cópias limpas. A (módulo da v0.7): 633 → 638 de 875 no mesmo conjunto, sem morte falsa por bytecode. B (`temporal.py` atual): 674/922. C (`compare.py`, faixa da regra): 132/271 executados, interrompida. D (`document.py`, amostra de 120): 68 mortos. 8 testes novos matam 17 dos 20 sobreviventes visados da regra; 3 equivalentes. Engine: DEF-VN-07 corrigido upstream (PR #3 `acd6ca3`), reteste com 2 ABSENT. Assertiva `--execute` PASS (755 invocações) e `--assessment` anexado. `evals/assurance/runs/2026-11-06-h07-cp5/MUTATION.md` |
| CP5B | Auditoria de fechamento (H07-017..020), rodada C completa, oráculos, dogfood | concluído | `ecf3dd2` + (este commit) | 3 hipóteses reproduzidas e corrigidas (DISC-052..054) e 1 quebra extra (DISC-055); em `d8aa669` os testes novos davam 20 falhas e 7 erros. Rodada C: 271/271, 201 mortos, 70 sobreviventes, nenhum morto do CP5 voltou a sobreviver; `test_compare_signal_oracles` mata 44 no replay, 22 equivalentes, 4 em B-M2 (DISC-057, com a hipótese da linha 467). Replay D: `test_document_plan_oracles` mata 25 de 52. Engine `inspect`/`compare` (5 novos, todos INFERRED, nenhum defeito) e rastreabilidade H07-017..020. Assertiva `--execute` em clone limpo: 815 invocações (814 + 1 skip), 90,27% linhas / 81,36% ramos; `--assessment` anexado ao run `6f5ee4fc6a1743b1`. `evals/assurance/runs/2026-11-07-h07-cp5b/MUTATION.md` |

## Handoff para a próxima sessão (outra máquina)

Escrito no fim do CP5, em 2026-11-06. A memória local do Claude **não** vai junto: tudo o que importa está aqui, no `docs/PLAN_v0.7.0.dev1.md`, no `docs/V07_DISCOVERY_REGISTER.md` (VN07-DISC-037..050) e em `evals/assurance/runs/2026-11-06-h07-cp*/`.

### Onde está

- Branch `dev/v0.7.0-hardening`. O último commit é o deste CP5; confira com `git fetch --prune` e `git log --oneline origin/dev/v0.7.0-hardening -8`.
- `main` = `dev/v0.7.0` = `e7506f5`, intocadas desde o início desta rodada.
- CI: o último run verde é o #124, em `9f44010`. Nenhum run nesta rodada.
- Versão ainda `0.7.0.dev0` no código. O CHANGELOG já tem a seção `Unreleased (0.7.0.dev1)`.

### Regras desta rodada (valem também na outra máquina)

- **Commits:** sem `Co-authored-by` nem trailer de IA. Identidade só local ao repositório (`git config --local`, autor Rafael Souza). Sem force push, sem `reset --hard`, sem tag, sem release, sem PyPI.
- **Commit só depois de exit 0 do gate.** No Windows, o `review:pty` (POSIX) fica de fora do gate local e é coberto no WSL no CP6:
  `python scripts/qualify.py --scope local --only validator,unittest,semantic:dev,semantic:holdouts:safety,semantic:holdouts:strict,decision:regression,router:regression,cli:exit-codes,ci:workflow-triggers --out <scratch>/q.json && git commit ... && python scripts/checkpoint.py push dev/v0.7.0-hardening --out <scratch>/push.json`
  Encadeie com `&&`, nunca com `;`, e nunca julgue por pipe (`| tail`).
- **GitHub Actions:** o workflow do VozNativa é só `workflow_dispatch`. Exatamente **um** dispatch, na `main`, no CP7.
- **Upstream:**
  - Assertiva PR #8: os gatilhos `push` e `pull_request` disparam Actions. **Não faça push** (BLOCKED_BY_CI_POLICY).
  - Derivanta Engine PR #3: só `push` na `main` dispara, então a branch da PR pode receber push.
  - Framework: tem `pull_request`, então não faça push.
- **Edição de arquivos:** não use heredoc com barra invertida (já gravou `\x08` e quebrou linhas de tabela duas vezes). Para regex e escapes, use a ferramenta de edição ou um script em arquivo. O validator agora recusa linha de tabela Markdown partida e caracteres de controle.
- **Mutação:** sempre `python -B` (ou `PYTHONDONTWRITEBYTECODE=1`) numa cópia `git archive`, nunca na árvore.
- **Assertiva `--execute`:** rode num clone limpo, nunca na árvore em edição (READ-ONLY VIOLATION).

### O que falta

1. **CP6: versão e qualificação.**
   - Troque para `0.7.0.dev1` em `voznativa/__init__.py`, `SKILL.md` (`version:`), `.claude-plugin/plugin.json`, README (linha **Estado**), cabeçalho da v0.7 no `ROADMAP.md` e `docs/README.md` (linha da qualificação). Conferido por `evals/test_readme.py::test_version_matches`.
   - Rode e registre, com a árvore limpa: `scripts/bench_v4.py` (esperado 22/22), `scripts/bench_v5.py` (36/36) e `scripts/predicate_eval.py --out evals/predicates/runs/predicates-<data>-dev1.json` (esperado 16/20 riscos e 1/18 falso alarme).
   - Rode `scripts/qualify.py --scope release` no Windows com 3.11 e 3.12 e no Linux com 3.11, 3.12 e 3.13. No WSL use `export PATH=$HOME/.local/bin:$PATH` e `uv venv --seed`; sem `--seed` o gate de pacote fica BLOCKED por falta de pip. Na máquina da retomada de 2026-11-07 não há distro WSL: o Linux local é Docker (imagens oficiais `python:3.11/3.12/3.13` sobre `git archive`), rotulado "Docker Linux (não WSL)". Se o ambiente tiver `PIP_NO_BUILD_ISOLATION=0`, remova a variável para o gate de pacote (a CI não a define). Esperado: gates locais PASS e exit 3 INCOMPLETE apenas pelos gates externos (CI antes do merge, holdout, revisão humana).
   - Registre em `evals/assurance/runs/<data>-h07-cp6/` com `scripts/assurance_record.py` e preencha a seção dev1 em `docs/V07_RELEASE_QUALIFICATION.md`.
2. **CP7: integração e CI.**
   - `git fetch --prune`. Confira que `origin/main` ainda é `e7506f5` e ancestral da branch.
   - Fast-forward da `main` para o último commit de código: `git checkout main && git merge --ff-only dev/v0.7.0-hardening && git push origin main`. Confira com `git ls-remote`.
   - Um único `gh workflow run ci.yml --ref main`. Espere terminar e confira run, SHA, evento `workflow_dispatch` e 8/8 jobs com `scripts/ci_evidence.py`.
   - Registre em `evals/qualification/external.json` e nesta seção, num commit só de evidência (`EVIDENCE_PATHS` de `scripts/ci_evidence.py`, sem alargar). Envie para a `main` e para a branch.
   - Se a CI falhar: não repita. Reproduza localmente e peça aprovação antes de outro run.
3. **Relatório final ao mantenedor:** commits por CP, achados, mutação antes e depois, Windows e WSL, CI, upstream, adiados e prontidão (não pronto para stable).

### Gaps e riscos conhecidos (não esconder no relatório)

- A regra de predicado é **experimental**. A amostra (`evals/predicates/`) é do mesmo autor e não é independente. `predicate_replaced` só informa, e "assinou" → "recebeu" passa como `no_deterministic_issues`. Destinatário omitido (`pr-17`) e radical curto (`pr-13`) não são detectados.
- A mutação de `compare.py` cobre só a faixa selecionada (linhas 76 e 429–583, completa no CP5B); o resto do módulo não foi mutado. `document.py` só tem a amostra D (120 de 454). Lacunas restantes em B-M2..M4 no plano. `router`, `morph` e `diagnose` não foram mutados.
- Testes contra o wheel: NOT_RUN pela Assertiva (AXF-VN-04). O smoke do VozNativa fora do checkout é a evidência.
- Holdout independente, revisão humana cega, provider real e detectores live continuam **NOT_RUN**.
- `condition.temporal` em "durante" → "no" é risco aceito (VN07-DISC-042).

### Ferramentas fora do repositório (recriar na outra máquina, se precisar)

- **Cosmic Ray 8.7.0:** num venv próprio com o projeto instalado (`pip install cosmic-ray==8.7.0 pyyaml`). Os harnesses estão versionados em `evals/assurance/runs/2026-11-06-h07-cp1/identity_mutants.py` e em `evals/assurance/runs/2026-11-06-h07-cp5/{cr_select.py,replay_survivors.py}`.
- **Assertiva 0.10.1:** wheel da tag `v0.10.1` num venv próprio.
- **Derivanta Engine:** `.venv` do clone com `pip install -e ".[dev]"` (inclui `mcp`). O gate é `python tools/verify.py`.
- **Cache de corpora:** `VOZNATIVA_CORPUS_CACHE` fora do repositório; recrie com `python scripts/corpus_prepare.py <ids>`. Só é necessário para as avaliações de corpora, não para os gates.

