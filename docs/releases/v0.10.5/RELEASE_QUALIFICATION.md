# Qualificação da v0.10.5

> Critérios R1–R18 congelados no CP0 ([`PLAN.md`](PLAN.md)), antes de qualquer mudança de produto. Regra de decisão: release estável só com R1–R3, R5, R7, R9 e R12–R18 em PASS; R6 pode terminar em `NO_MEASURABLE_GAIN` sem bloquear. Externos ficam `NOT_RUN` e restringem as afirmações.

| # | Resultado | Evidência |
|---|---|---|
| R1 | **PASS** (CP0): baseline `v0.10.0` reproduzida | `qualify --scope release --offline` na worktree da tag, todos os gates locais PASS |
| R2 | **PASS**: nenhuma regressão P0/P1 conhecida; cada correção tem teste vermelho na v0.10.0, controle e replay em texto real | `GAP_REGISTER.md`; suíte completa OK (1.167 testes, 2 pulados) |
| R3 | **PASS**: congelados históricos sem piora (semântico dev, holdouts de segurança e estrito, regressão de decisão e de roteador iguais) | `qualify --scope release --offline` na revisão final (linha da execução abaixo) |
| R4 | **PASS**: 427 itens reais, 28 rótulos, 5 faixas; lacunas de família declaradas e refletidas nas afirmações | `CORPUS_AND_LICENSES.md`, `evals/v0105/corpus_manifest.json` |
| R5 | **PASS**: Skill num host real (Claude Code 2.1.317), 12 tarefas × 3 repetições por versão + holdout, pedido sem nomear a Skill; ativação observada no log do host | `SKILL_LIVE_DOGFOOD.md` |
| R6 | **PASS** como protocolo; resultado: **engine com ganho** (juiz: atende ao pedido +6 tarefas, naturalidade +4, nenhuma perda; acima do ruído medido no braço de controle); **Skill `NO_MEASURABLE_GAIN`** em qualidade (troca: fidelidade +3, pedido −5, naturalidade −4); contexto e conhecimento sem ganho isolado | `FIRE_TRIAL_RESULTS.md` §2 |
| R7 | **PASS**: 11 gaps de produto corrigidos com vermelho→verde, controle e replay (GAP-02, 04–09, 11, 13–15) e 5 de harness; abertos declarados: GAP-01 (PARTIAL), GAP-16, 17, 18 | `GAP_REGISTER.md` |
| R8 | **PASS**: 3 fluxos completos (lei de 12.259 palavras, romance, DOCX/PDF), oráculo independente, nenhuma falha de provider; limites declarados (PDF não é editado; Word `NOT_RUN`) | `FIRE_TRIAL_RESULTS.md` §3 |
| R9 | **PASS**: no mesmo corpus, `ERROR_CONFIRMED` 2 → 2 e planos `edit` 18 → 18; falsos alarmes metamórficos 10 → 1 | `FIRE_TRIAL_RESULTS.md` §1 |
| R10 | **PASS**: quatro trilhas com estados separados (`REAL_HOST_EXECUTED`, `CLI_EXECUTED_STATIC`, `AUDIT_EXECUTED`) | `ASSURANCE_RECIPROCAL.md` |
| R11 | **PASS**: PR #6 (Engine) e PR #11 (Assertiva) revisados com controles novos e enviados; falha herdada da Assertiva com causa provada; estado dos merges no fechamento abaixo | `ASSURANCE_RECIPROCAL.md` |
| R12 | **PASS**: nenhuma remoção sem prova; ciclos só dentro de funções e travados por teste; Engine base × candidato comparável e triado; defeitos de harness corrigidos | `MAINTAINABILITY.md` |
| R13 | **PASS**: `compare` em 17.600 palavras 1,04× a v0.10.0 (teto 1,15×), melhor de 2 medições intercaladas no código final | `FIRE_TRIAL_RESULTS.md` §1 |
| R14 | **PASS com desvio de processo registrado**: nenhum texto `local_only`, caminho privado ou conteúdo de documento privado publicado (gate no intervalo inteiro e na árvore no fechamento). Desvio: no push do CP12a, 4 commits anteriores foram enviados com o gate rodado só sobre o último; o gate do intervalo completo rodou depois do envio e deu PASS | `EXECUTION_STATE.md` |
| R15 | pendente: sdist → wheel → venv → smoke → suíte contra o wheel no `qualify`; CI final 8/8 | preenchido no fechamento |
| R16 | **PASS**: links e comandos da documentação validados por `test_readme` e `test_v08_doc_validator`; estados REAL/NOT_RUN explícitos | suíte |
| R17 | pendente: tag anotada, artefatos da tag, `SHA256SUMS` conferido após download | preenchido no fechamento |
| R18 | **PASS**: gerador reprodutível, página autocontida, QA no Edge com 55 verificações (conteúdo de cada seção igual aos dados, filtros, mesa de revisão, exportações analisadas, dados ausentes e hostis, 320/390/768 px, teclado, movimento reduzido) e capturas reais em `docs/observatory/screenshots/` | `scripts/v0105_observatory_qa.py` |

## Externos (`NOT_RUN`)

Revisão humana cega, holdout feito por terceiro, juiz de outro fornecedor, modelo local, Codex/Gemini CLI, macOS, renderização no Word. Consequência: nenhuma afirmação sobre "escrita melhor para pessoas"; os ganhos acima são de decisão de editar, de detecção pelo gate e de juízo de modelo do mesmo fornecedor.
