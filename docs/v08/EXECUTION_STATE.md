# Estado de execução da v0.8.0 (retomada de sessão)

Retome por este arquivo **e** pelo Git (`git fetch --prune; git log --oneline origin/dev/v0.8.0 -20`). Se divergirem, o Git vence e este arquivo é corrigido.

- Branch: `dev/v0.8.0`, criada de `main` = `c2708de` em 2026-11-07.
- Plano: [`PLAN.md`](PLAN.md). Gaps: [`GAP_REGISTER.md`](GAP_REGISTER.md). Rastreabilidade: [`TRACEABILITY.md`](TRACEABILITY.md).
- Política: push da branch por CP com `scripts/checkpoint.py push`; nenhuma Action até o CP17; tag e pre-release só no CP18.

## Checkpoints

| CP | Título | Estado | Commit | Verificação |
|---|---|---|---|---|
| CP0 | Discovery, AS-IS, baseline | concluído | (este commit) | `qualify --scope release` em `c2708de`, árvore limpa, Windows 10 + CPython 3.12.6: 726 testes (725 + 1 skip POSIX), gates locais PASS, `ci:github-actions` PASS, exit 3 só por `review:pty`, holdout e revisão humana. v4 22/22, v5 36/36, predicados 16/20 e 1/18. GAP-01 e GAP-09 reproduzidos. `evals/assurance/runs/2026-11-07-v08-cp0/` |

| CP1 | Integridade: autorização do chamador, `resume` sem autoridade | concluído | (este commit) | GAP-01 e GAP-09 corrigidos. `evals/test_v08_integrity.py` (14 testes): em `2ced479` 7 falham ou dão erro por método, 4 controles passam, 1 passa sem provar. 7 mutantes à mão, todos mortos, depois de um controle sem mutação (`scripts/experiments/v08_cp1_mutants.py`, `evals/assurance/runs/2026-11-07-v08-cp1/MUTANTS.md`). Mudança de API anotada no CHANGELOG |

| CP2 | Desempenho de spans e morfologia | concluído | (este commit) | `spans.extract` 40 mil palavras 18,6 s → 1,6 s, 80 mil 30,1 s → 3,0 s, saída idêntica; `build_plan` 40 mil 9,1 s → 0,73 s; ordem de `morph` estável. Aberto e medido: `compare` quadrático (GAP-12) e falso vermelho em documento longo (GAP-13), ambos para o CP7. [`PERFORMANCE.md`](PERFORMANCE.md) |
| CP3 | DX I: doctor, demo, erros, suíte contra o wheel | concluído | (este commit) | `voznativa doctor` e `voznativa demo` (29 subcomandos); erros de arquivo/encoding/pasta em PT-BR com exit 64; gate de pacote roda a suíte inteira contra o wheel (748, 746 PASS, 2 skips com motivo; origem do import conferida). `evals/test_v08_dx.py` 13 testes |
| CP4 | Evaluation Core | concluído | (este commit) | `voznativa evaluate` sobre 9 suítes existentes, lidas no lugar: development 109 casos (sensibilidade 61/61, falso alarme 0/17), frozen_regression 176 (85/89, 1/33; decisão exata 28/30); nada independente. `evals/test_v08_evaluation.py` 18 testes. Registro em `evals/v08/runs/`. [`EVAL_PROTOCOL.md`](EVAL_PROTOCOL.md) |
| CP5 | Integridade × autenticidade, independência, vazamento, braços | concluído | (este commit) | `--replay` na revisão; `independence_evidence` exigida; links fora da raiz recusados; vazamento: `ho-022` = `rel-agent-001`, 1 caso do v5 repete texto de desenvolvimento; v1–v5 byte-idênticos; braços B0–B6 numa interface (B0/B2 offline, demais NOT_RUN sem provider). Testes: `test_v08_eval_integrity` (14), `test_v08_arms` (8). [`INDEPENDENCE_AND_LEAKAGE.md`](INDEPENDENCE_AND_LEAKAGE.md). **Erratum:** o commit `dee69e2` diz "replay REPRODUCED", mas o run gravado nele (`gate-and-planner-3b91fb6`) veio de árvore suja (a auditoria de vazamento foi gravada antes) e o replay deu `NOT_REPLAYABLE`. O run válido é `gate-and-planner-dee69e2` (árvore limpa), com `replay-dee69e2.json` = REPRODUCED |
| CP6 | Eventos, papéis e destinatário (GAP-04) | concluído | (este commit) | conjuntos `evals/events/` congelados antes do código (`53d48fc`), linha de base registrada (`ea84db3`); depois: desenvolvimento 14/15 riscos e 2/13 falsos alarmes, holdout (uma execução) 11/12 e 3/12; predicados 17/20 e 1/18; semânticas, decisão, roteador, v4 22/22, v5 36/36 sem mudança; 10 mutantes mortos. [`SEMANTICS.md`](SEMANTICS.md) |
| CP7a | GAP-13: falso vermelho em documento longo | concluído | (este commit) | causa: desempate do alinhamento entre frases que diferem só por "não"; reproduzido em documento bem formado e em 9 parágrafos; corrigido por posição, sem tocar nos guards; 0/309 relatórios das suítes mudaram; v4 22/22, v5 36/36, predicados 17/20 |
| CP7b | GAP-12: custo do `compare` e limite de tempo da validação global | concluído | (este commit) | 30 mil palavras 24,7 s → 8,5 s, 41 mil 12,4 s, saída idêntica (0/309); `timeout_s` cobre a validação global e devolve o original; resíduo `contains_word` documentado |
| CP7 | Long-form e arquitetura | concluído | (este commit) | `test_v08_longform`: reescrita limpa com gêmeas não é mais revertida (em `c353058` revertia [1, 4]); documento misto com todos os blocos. [`ARCHITECTURE.md`](ARCHITECTURE.md) com os três modos e Agent-Led Runtime; lacuna V08-GAP-16 (autoavaliação do agente sem rótulo próprio) para o CP12 |
| CP8 | Eixos de qualidade e curva do Router | concluído | (este commit) | `voznativa/axes.py` (proxies rotulados); auditoria do Router reproduzida igual à v0.7; curva de limiares: ponto atual no joelho, limiar não muda, falta de pistas em notícia/blog. [`EVAL_MATRIX.md`](EVAL_MATRIX.md). Corpora rematerializados no scratchpad (só datas de verificação mudaram no registro) |

## Regras desta rodada

- **Commits:** sem `Co-authored-by` nem trailer de IA; identidade local (`git config --local`): Rafael Souza, noreply Soturine. Sem force push, sem `reset --hard`. Tag e release só no CP18, nas condições do plano. Sem PyPI.
- **Gate antes do commit:** `python scripts/qualify.py --scope local --only validator,unittest,semantic:dev,semantic:holdouts:safety,semantic:holdouts:strict,decision:regression,router:regression,cli:exit-codes,ci:workflow-triggers --out <scratch>/q.json`, exit 0, encadeado com `&&`.
- **Não escrever na árvore durante um gate** (registros de bench vão depois ou para o scratchpad). `scripts/bench_v4.py` não aceita `--help`: ele roda o bench e grava em `benchmarks/runs/`.
- **Edição de arquivos:** nada de heredoc com barra invertida; usar a ferramenta de edição ou script em arquivo.
- **Upstream:** Assertiva (push e pull_request disparam Actions) e Framework (pull_request): não fazer push. Engine: só `push` na `main` dispara; a branch da PR #3 pode receber push.

## Bloqueios conhecidos

- Python 3.11 não instalado nesta máquina (GAP-10).
- Holdout independente, revisão humana cega, provider real e detectores live: NOT_RUN até haver pessoas e autorização de custo.

## Próximo passo

CP9: apresentar ao mantenedor as opções de execução real (provider, Agent Skill com agente real, juiz) com estimativa de consumo e aguardar autorização; preparar cenários, instrumentos e limites; sem autorização, tudo que precisa de modelo fica NOT_RUN.
