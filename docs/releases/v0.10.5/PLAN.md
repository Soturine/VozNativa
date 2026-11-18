# Plano da v0.10.5 — prova de fogo PT-BR

> CP0, 18/11/2026, **antes de qualquer mudança de produto**. Base: `v0.10.0` (tag anotada `7c8c141` → `main` `e274379`, conferido ao vivo; CI #132 8/8). Branch `dev/v0.10.5`. Critérios R1–R18 congelados aqui; podem ganhar gates, nunca perder piso.

## O que esta rodada responde

1. A **Skill usada por um agente real** (Claude Code com a Skill instalada no projeto) ajuda ou atrapalha, em textos reais PT-BR de gêneros diferentes, frente ao LLM direto e ao engine?
2. Contexto aberto e conhecimento (v0.10) mudam alguma coisa quando medidos com repetição?
3. O que quebra em textos reais que ninguém escreveu para o motor?

## Corpus (CP1; detalhes em [`CORPUS_AND_LICENSES.md`](CORPUS_AND_LICENSES.md))

427 itens PT-BR reais, 28 rótulos de gênero, 5 faixas de tamanho (micro 44, curto 145, médio 122, longo 108, documento 8). Direitos: domínio público 254 (Machado de Assis, leis federais), CC BY 84 (resumos acadêmicos), **só análise local** 89 (UD-GSD, UD-Bosque CETENFolha, UD-PetroGold, UD-DANTEStocks, B2W). Texto fora do Git; manifesto com hash em `evals/v0105/corpus_manifest.json`.

**Lacunas declaradas** (sem fonte lícita disponível nesta rodada; nada inventado no lugar): mensagens cotidianas e WhatsApp reais, correspondência/e-mail, redes sociais gerais (só tweets de mercado, uso local), documentação técnica PT-BR escrita por pessoas, saúde/orientação, criativo/comercial além de avaliações de produto, fala transcrita regional. **Consequência:** nenhuma afirmação de qualidade vale para essas famílias; a campanha live cobre literário, institucional/jurídico e acadêmico.

## Campanhas

| Nível | O quê | Tamanho |
|---|---|---|
| 1 offline | `route`, idioma, `diagnose`, `plan`, `compare` em todos os 427 itens; metamórficos com oráculo conhecido (perturbações em cópias) | 427 itens, v0.10.0 × v0.10.5 |
| 2–3 live | 12 tarefas de desenvolvimento × 3 repetições × braços A1 (LLM direto), A2 (Skill em host real), A3 (engine) e A3-bare (engine sem contexto/conhecimento); juiz de outro modelo do mesmo fornecedor, cego ao braço | `evals/v0105/live_tasks.json` (congelado, sha256 `f89f96ab…`) |
| holdout | 6 tarefas congeladas agora, rodadas **uma vez** no fim, v0.10.0 × v0.10.5 (A2 e A3) | idem |
| 4 documentos | 3 fluxos completos: LGPD (12 mil palavras, institucional), capítulos de romance (literário), PDF/DOCX gerado de texto em domínio público | — |

Modelo escritor: Haiku (`claude -p --model haiku`); juiz: Sonnet. Relação `same_vendor`: o juízo é `MODEL_JUDGED`, dependente, nunca revisão humana.

## Orçamento

O `claude` CLI usa o login da conta (sem chave de API no ambiente); custo registrado pelo `total_cost_usd` que o CLI devolve (preço de API equivalente). Teto da campanha: **US$ 10**; subtetos: braços live US$ 3, juiz US$ 4, documentos US$ 1,5, reserva de replay US$ 1,5.

## Critérios de release (congelados)

| # | Critério | Piso |
|---|---|---|
| R1 | baseline v0.10.0 reprodutível | `qualify --scope release --offline` sem FAIL local na worktree da tag (**PASS no CP0**) |
| R2 | sem regressão P0/P1 conhecida | testes de defeito + controles; replay |
| R3 | congelados históricos sem piora | v4 22/22, v5 36/36, predicados 19/20 e 1/18, regressão 88/89 e 1/33, conjuntos v0.9 e v0.10 (dev e holdout) iguais ou melhores |
| R4 | corpus real multigênero | ≥ 200 itens, ≥ 25 rótulos, 5 faixas (**atingido**); lacunas de família declaradas e refletidas nas afirmações |
| R5 | Skill real em host | ≥ 12 tarefas × 3 repetições em sessão real com a Skill instalada; descoberta registrada (automática × explícita) |
| R6 | comparação justa com modelo real | mesmo modelo nos braços; juiz cego; custo e chamadas por braço; ganho só afirmado se aparecer em ≥ 2 de 3 repetições **e** no juiz; senão `NO_MEASURABLE_GAIN` |
| R7 | gaps reais corrigidos | teste vermelho→verde + controle + replay real |
| R8 | documentos longos reais | 3 fluxos completos com integridade conferida; limites DOCX/PDF declarados |
| R9 | falso alarme em texto real | no mesmo corpus, `ERROR_CONFIRMED` e planos `edit` em texto publicado **não pioram** frente à v0.10.0 |
| R10 | dogfood em 4 trilhas | VozNativa, Assertiva (`audit --execute`), Derivanta Engine (CLI), Derivanta Framework (sessão real de agente) com estados separados |
| R11 | PRs #6 e #11 e falhas da Assertiva | revisados com controles novos; estado real dos PRs; nenhum merge alegado sem ter ocorrido |
| R12 | manutenção | remoção só com prova; ciclos tratados ou justificados; harness confiável |
| R13 | desempenho | `compare` 17.600 palavras ≤ 1,15 × v0.10.0, medido intercalado na mesma sessão |
| R14 | privacidade | gate em todo push; intervalo + árvore no fechamento; nenhum texto `local_only` publicado |
| R15 | instalação e pacote | sdist → wheel → venv → smoke → suíte; CI final 8/8 |
| R16 | docs coerentes | links válidos; estados REAL/STUB/NOT_RUN; nenhuma afirmação sem evidência |
| R17 | publicação | tag anotada, artefatos da tag, `SHA256SUMS` conferido após download |
| R18 | site **VozNativa Observatory** | gerador reprodutível, diff interativo, filtros, matriz, gaps, 4 trilhas, acessibilidade e movimento reduzido; QA em navegador real com screenshots; senão `BROWSER_NOT_RUN` e **sem** release estável |

**Regra de decisão.** Release estável só com R1–R3, R5, R7, R9, R12–R18 PASS. R6 pode terminar em `NO_MEASURABLE_GAIN` sem bloquear (é resultado, não falha). Externos (revisão humana cega, holdout de terceiro, juiz de outro fornecedor, modelo local, Codex/Gemini, macOS, Word) ficam `NOT_RUN` e restringem as afirmações, sem virar PASS.
