# CP0 — baseline de assurance (2026-11-05, `4044cfc`)

Execuções reais, saídas brutas sanitizadas nesta pasta, comandos e exit codes em `MANIFEST.json`. O que cada ferramenta **observou** está separado do que o agente **concluiu** depois.

## Ambiente

- Windows 11, CPython 3.12.10; venv do projeto fora do repositório (PyYAML 6.0.3, coverage 7.17.2, build 1.6.1, cosmic-ray 8.7.0); nada instalado globalmente.
- Assertiva 0.10.1 instalada num venv próprio a partir da tag `v0.10.1` (`2618d95`). A instalação global pré-existente responde `assertiva 0.10.1`, mas o pip a registra como `0.5.5` (instalação editável antiga com metadados velhos): não foi usada.
- Derivanta Engine 0.1.0 (`0be2a38`) do venv do próprio repositório do Engine; Framework local `218761d`, aceito pelo Engine como revisão compatível.
- `derivanta-engine review` **não existe** nesta versão (comandos: `evaluate`, `compare`, `inspect`).

## Gates nativos (executados pelo agente)

| Gate | Exit | Resultado |
|---|---|---|
| `scripts/validate_package.py` | 0 | válido |
| `unittest discover -s evals` | 0 | 281 testes, OK, 0 skips |
| `voznativa eval` nas 7 suítes semânticas | 0 em 6; **1** em `holdout.jsonl` | 23/24 estrito (`ho-007`, divergência de classificação conhecida) |
| suíte de decisão (`run_decisions`) | — | 28/30 (`dc-021` wrong_scope, `dc-029` unnecessary_change) |

## Derivanta Engine

**Observado pelo Engine** (`inspect --maintainability`): inventário completo (216 arquivos), 88 lidos (fontes Python e manifests); documentação, CI e configuração só inventariadas por caminho. 57 candidatos INFO, todos `HYPOTHESIS`: 40 de complexidade, 15 de duplicação, 2 de definição não referenciada. Nenhuma execução de código do projeto.

**Observado pelo Engine** (`evaluate --repository`): workflow primário `ADAPTIVE_TEST_ASSURANCE`, risco HIGH (heurística experimental do Engine), revisão independente exigida; 12 campos materiais não declarados (RTO/RPO/disponibilidade não se aplicam a uma CLI local; residência e compliance foram declarados como nulos); `license: not observed`.

**Conclusões do agente** (lendo o código):

| Achado do Engine | Disposição | Motivo |
|---|---|---|
| `license: not observed` | **confirmado** | o repositório não tem LICENSE; a decisão está pendente em `docs/LICENSING.md` (decisão do mantenedor, não do agente) |
| `_NUMBER_WORD_ALT` em `spans.py` `LIKELY_DEAD` | a verificar no CP4 | |
| `RELATIONSHIPS` em `review.py` `UNKNOWN_DYNAMIC` | a verificar no CP4 | |
| duplicação `spans.py` x `ledger.py` (tabelas de tipos) | a verificar no CP4 | duas fontes do mesmo vocabulário podem divergir |
| duplicação `router.py` x `cli.py` (lista de gêneros) | a verificar no CP4 | idem |
| duplicações entre `scripts/experiments/*` e testes | contextual | experimentos congelados registram o que rodou; não são código de produção |
| 40 de complexidade | contextual | sinal de refatoração, não defeito; `planner.plan` (53) e `engine._rewrite` (44) são os maiores |
| `unittest` / `external LLM CLI` "not observed" | **falso positivo do contexto** | stdlib e CLI externos nunca aparecem em manifests; o Engine diz isso na explicação (ver dogfood) |

## Assertiva

**Observado pela Assertiva** (`audit --execute`, cópia descartável): unittest nativo, 281 invocações PASS (exit 0); cobertura medida 93,7% linhas / 84,0% ramos (produto sem testes: 91,0% / 84,5%); wheel: build, install sem índice, import e fechamento de dependências PASS; **testes contra o wheel NOT_RUN** ("no test runner adapter"); sdist e instalação a partir de índice NOT_RUN. 7 checks declarados no CI, 5 `UNKNOWN` (scripts do projeto). Mutação e controles negativos: não evidenciados.

**Conclusões do agente sobre `FALSE_GREEN_CANDIDATE` (4 testes, `CONDITIONAL_ASSERTION`)** — com controles negativos em `negative-controls.json`:

| Teste | Disposição | Evidência |
|---|---|---|
| `test_frozen_suites_were_not_edited` | **CONFIRMED** | NC1: renomear a chave `frozen` no manifesto deixa um holdout congelado ser editado com o teste verde |
| `test_independent_claims_need_the_protocol_fields` | CONTEXTUAL | hoje não afirma nada (nenhuma suíte é independente); NC2 mostra que falha quando a alegação aparece |
| `test_holdouts_never_report_false_green` | FALSE_POSITIVE | NC3/NC3b detectados; 34 de 52 casos chegam à asserção |
| `test_nothing_is_auto_accepted_without_identity` | FALSE_POSITIVE | NC4 detectado; a direção oposta (NC4b) é protegida por outros dois testes |

**Achados do agente que nenhuma ferramenta levantou:**

1. **Benchmark conta `provider_error` como sucesso de invariantes.** Na execução oficial do `ptbr-bench-v2`, `B5-voznativa-v040 / bv2-wa-03` terminou em `provider_error`, devolveu o original e o scorer registrou `invariants_ok: true`, `errors: 0`; o resumo diz `15/15`. O texto da `EVALUATION.md` explica o caso, mas a tabela e o scorer não separam a falha (H2).
2. **O runner de baseline lê o resultado do unittest pela última linha do stderr**, sem contar skips, erros de coleta ou testes inesperadamente aprovados (H1).
3. **Nenhum gate local reproduz o job `package` do CI** (sdist → wheel → venv limpo → `smoke_installed.py`); a qualificação da Assertiva cobre build e import do wheel, não os comandos.

## Gaps que ficam abertos neste ponto

CI remoto BLOCKED (cobrança); holdout independente e revisão humana NOT_RUN; mutação ainda não executada.
