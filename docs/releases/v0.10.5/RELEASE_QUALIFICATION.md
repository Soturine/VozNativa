# Qualificação da v0.10.5

> Critérios R1–R18 congelados no CP0 ([`PLAN.md`](PLAN.md)), antes de qualquer mudança de produto. Regra de decisão: release estável só com R1–R3, R5, R7, R9 e R12–R18 em PASS; R6 pode terminar em `NO_MEASURABLE_GAIN` sem bloquear. Externos ficam `NOT_RUN` e restringem as afirmações.

| # | Resultado | Evidência |
|---|---|---|
| R1 | **PASS** (CP0): baseline `v0.10.0` reproduzida | `qualify --scope release --offline` na worktree da tag, todos os gates locais PASS |
| R2 | **PASS**: nenhuma regressão P0/P1 conhecida; cada correção tem teste vermelho na v0.10.0, controle e replay em texto real | `GAP_REGISTER.md`; suíte completa OK (1.167 testes, 2 pulados) |
| R3 | **PASS**: congelados históricos sem piora (semântico dev, holdouts de segurança e estrito, regressão de decisão e de roteador) | `qualify --scope release --offline` em `95522c9`, árvore limpa: todos os gates locais PASS; veredito `INCOMPLETE` só pelos externos (`review:pty`, `holdout:independent`, `review:blind-human` NOT_RUN; `ci:github-actions` INCONCLUSIVE offline) |
| R4 | **PASS**: 427 itens reais, 28 rótulos, 5 faixas; lacunas de família declaradas e refletidas nas afirmações | `CORPUS_AND_LICENSES.md`, `evals/v0105/corpus_manifest.json` |
| R5 | **PASS**: Skill num host real (Claude Code 2.1.317), 12 tarefas × 3 repetições por versão + holdout, pedido sem nomear a Skill; ativação observada no log do host | `SKILL_LIVE_DOGFOOD.md` |
| R6 | **PASS** como protocolo; resultado: **engine com ganho** (juiz: atende ao pedido +6 tarefas, naturalidade +4, nenhuma perda; acima do ruído medido no braço de controle); **Skill `NO_MEASURABLE_GAIN`** em qualidade (troca: fidelidade +3, pedido −5, naturalidade −4); contexto e conhecimento sem ganho isolado | `FIRE_TRIAL_RESULTS.md` §2 |
| R7 | **PASS**: 11 gaps de produto corrigidos com vermelho→verde, controle e replay (GAP-02, 04–09, 11, 13–15) e 5 de harness; abertos declarados: GAP-01 (PARTIAL), GAP-16, 17, 18 | `GAP_REGISTER.md` |
| R8 | **PASS**: 3 fluxos completos (lei de 12.259 palavras, romance, DOCX/PDF), oráculo independente, nenhuma falha de provider; limites declarados (PDF não é editado; Word `NOT_RUN`) | `FIRE_TRIAL_RESULTS.md` §3 |
| R9 | **PASS**: no mesmo corpus, `ERROR_CONFIRMED` 2 → 2 e planos `edit` 18 → 18; falsos alarmes metamórficos 10 → 1 | `FIRE_TRIAL_RESULTS.md` §1 |
| R10 | **PASS**: quatro trilhas com estados separados (`REAL_HOST_EXECUTED`, `CLI_EXECUTED_STATIC`, `AUDIT_EXECUTED`) | `ASSURANCE_RECIPROCAL.md` |
| R11 | **PASS** (revisão) / merges **BLOCKED**: PR #6 (Engine, `a9eb371`) e PR #11 (Assertiva, `4325936`, CI do PR verde) revisados com controles novos; falha herdada da Assertiva com causa provada. O merge do PR #6 foi negado pelo controle de permissões do agente; nenhum merge foi alegado nem contornado; os dois PRs seguem abertos e prontos | `ASSURANCE_RECIPROCAL.md` |
| R12 | **PASS**: nenhuma remoção sem prova; ciclos só dentro de funções e travados por teste; Engine base × candidato comparável e triado; defeitos de harness corrigidos | `MAINTAINABILITY.md` |
| R13 | **PASS**: `compare` em 17.600 palavras 1,04× a v0.10.0 (teto 1,15×), melhor de 2 medições intercaladas no código final | `FIRE_TRIAL_RESULTS.md` §1 |
| R14 | **PASS com desvio de processo registrado**: gate em cada push (último intervalo: PASS, 1 commit, 7.873 linhas); nenhum texto `local_only`, caminho privado ou conteúdo de documento privado publicado. Varredura da árvore inteira (883 arquivos): caminhos e e-mails revisados e aceitos (fixtures inventados); 21 "credenciais" são nomes de variável e anotações de tipo no código (`numerals.py`, `redact.py`, `providers.py`, `spans.py`), fixtures falsos de teste (`test_privacy.py`, `test_v08_doc_validator.py`, `test_v08_dx.py`) e registros de auditoria da v0.8 que citam esses testes, revisados um a um; o gate não permite aceitar credencial por desenho e não foi alterado. Desvio: no push do CP12a, 4 commits anteriores foram enviados com o gate rodado só sobre o último; o gate do intervalo completo rodou depois e deu PASS | `EXECUTION_STATE.md` |
| R15 | **PARTIAL**: local PASS (sdist → wheel → venv limpo → smoke fora do checkout → suíte contra o wheel instalado, `95522c9`); CI final 8/8 **NOT_RUN**: a CI é manual e roda na `main` integrada, e a integração está bloqueada | `qualify` |
| R16 | **PASS**: links e comandos da documentação validados por `test_readme` e `test_v08_doc_validator`; estados REAL/NOT_RUN explícitos | suíte |
| R17 | **BLOCKED**: sem merge na `main` não há tag nem release estável; PR #4 aberto e pronto. Nenhuma tag, release ou pre-release foi criada | PR #4 |
| R18 | **PASS**: gerador reprodutível, página autocontida, QA no Edge com 55 verificações (conteúdo de cada seção igual aos dados, filtros, mesa de revisão, exportações analisadas, dados ausentes e hostis, 320/390/768 px, teclado, movimento reduzido) e capturas reais em `docs/observatory/screenshots/` | `scripts/v0105_observatory_qa.py` |

## Externos (`NOT_RUN`)

Revisão humana cega, holdout feito por terceiro, juiz de outro fornecedor, modelo local, Codex/Gemini CLI, macOS, renderização no Word. Consequência: nenhuma afirmação sobre "escrita melhor para pessoas"; os ganhos acima são de decisão de editar, de detecção pelo gate e de juízo de modelo do mesmo fornecedor.

## Decisão

**Release estável: não publicada.** R15 (CI final) e R17 (publicação) dependem da integração na `main`, que exige uma ação de merge que o controle de permissões do agente negou no PR #6; pela regra da rodada, a integração não foi tentada por outro caminho. Os demais critérios obrigatórios estão em PASS. Entrega: PR #4 (`dev/v0.10.5` → `main`) pronto para merge com `--no-ff`; depois do merge, faltam a CI manual de 8 jobs na `main`, a tag anotada `v0.10.5`, wheel e sdist da revisão da tag, `SHA256SUMS.txt` conferido após download e a GitHub Release.
