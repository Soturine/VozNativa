# Estado de execução da v0.10

> Fonte única do estado da rodada. Cada CP registra commit, gate e evidência; retomar a partir da última linha concluída.

## Ponto de partida (CP0)

| Item | Valor |
|---|---|
| Base | tag `v0.9.0` (objeto `e83eb0c`, tipo `tag`) → `main` `6b487f7`; local = `origin/main`; árvore limpa |
| GitHub | release `v0.9.0` Latest; PR #2 MERGED; sem issues abertas; CI #131 8/8 em `118b0e7` |
| Branch | `dev/v0.10.0` criada de `6b487f7` |
| Worktree da base | `../v010-work/base-v090` (destacada em `v0.9.0`) |
| Identidade Git | local do repositório (noreply Soturine); global não alterado |

## Baseline reproduzida (R1)

| Medição | Resultado em `v0.9.0` |
|---|---|
| `qualify.py --scope release --offline` | todos os gates locais **PASS** (validador, unittest, semântica dev, holdouts safety/strict, decisão, roteador, códigos de saída, gatilhos da CI, pacote sdist→wheel→venv→smoke→suíte); INCOMPLETE só por `review:pty` (POSIX), CI (offline), holdout independente e revisão humana; 5 min 14 s |
| `perf_compare.py` (5 repetições, CPU) | 17.600 palavras: **5,52 s** mín. (mediana 5,64 s); razão 800/100 blocos 12,6× → teto R11 = 6,35 s |
| `v010_prospective_eval.py --split development` | semântica: riscos **16/21**, falsos alarmes **5/13**; diagnóstico: erros **3/7**, falsos alarmes **0/9**; contexto: não aplicável (módulo não existe) |
| Holdouts v0.10 | **não rodados** (regra: uma execução, no fim, para base e candidato juntos) |

## Conjuntos congelados

`evals/v010/MANIFEST.json` (sha256 por arquivo), escritos antes de qualquer regra da v0.10. Mesmo autor das regras; `independent: false`. Os conjuntos das v0.7–v0.9 seguem byte-idênticos.

## Checkpoints

| CP | Estado | Commit | Evidência |
|---|---|---|---|
| CP0 | concluído | `74880ad` | plano, critérios R1–R15, conjuntos congelados, baseline |
| CP1 | concluído | `7bf35bd` | [`RESEARCH_REGISTER.md`](RESEARCH_REGISTER.md): 13 fontes com licença literal e decisão; OpenAlex sem conector ativo (chave e custo) |
| CP2 | concluído | `800fcc1` | TaskContext aberto (`task_context.py`, subcomando `context`, `--attr`/`--attrs-file`/`--context-proposal`); 15 testes; conjunto `context` dev 6/6; gate local PASS (1.040 testes) |
| CP3 | concluído | `441d201` | registro de conhecimento (15 entradas, 7 fontes com natureza/licença/acesso), seleção por necessidade com orçamento e motivo, variante em registro informal, recusa de entradas com cara de instrução; `knowledge list/select`; 11 testes |
| CP4 | concluído | `ed8c92e` | status de diagnóstico (`ERROR_CONFIRMED`…`UNCERTAIN`, `recommend_edit`), 6 regras novas com variantes por contexto; diagnose dev 3/7 → 7/7, FA 0/9; 11 testes (8 vermelhos em v0.9.0) |
| CP5 + CP6a | concluído | `ca1646c` | relações discursivas por família, ação coordenada perdida, 4 falsos alarmes do CP7 calibrados com controles, futuro → passado com "foi"; semantic dev 16/21 → 21/21, FA 5/13 → 0/13; instrumentos v0.8/v0.9 idênticos; 18 testes (12 vermelhos em v0.9.0) |
| CP6b | concluído | `ba50b5c` | relação do juiz: 7 relações, `unknown`/`same_model` não aprovam, `same_vendor` aprova com independência parcial registrada; testes antigos que dependiam de `unknown` aprovar adaptados e o contrato antigo invertido explicitamente; [`MIGRATION.md`](MIGRATION.md) |
| CP7 | concluído | `d74a376` | matriz de elegibilidade; UD-GSD lido localmente (2.404 sentenças): defeito real de `plural_agreement` achado e corrigido (test 11 → 1 alarme; dev retido 16 → 11 na rodada única, 6 reais); ENEM como perfil; 4 testes (3 vermelhos em v0.9.0) |
| CP8 | concluído | `7b34d7f` | Knowledge Watcher report/propose (7 fontes, OpenAlex desligada), fetch com GET condicional e bloqueio de endereço privado; execução real em 6 fontes (304 na segunda); 19 testes; `SCHEDULER_READY` |
| CP9 | concluído | `7a3185d` | Derivanta antes × depois `COMPARABLE`; 4 duplicações/candidatos meus corrigidos, 3 aceitos com motivo; ciclo novo `compare`↔`judge` desfeito e herdado `diagnose`↔`planner` desfeito (5 → 4); 2 defeitos do Derivanta achados para o CP11 |
| CP11a | concluído | `1ffa346` | VozNativa lia inglês como português (achado no dogfood B1): guarda de idioma |
| CP10 | concluído | (este commit) | braços com Haiku em 10 textos de gêneros não mapeados: LLM direto alterou 3/4 bons e perdeu uma exceção; engines 0/4; contexto/conhecimento sem ganho demonstrado (n = 1); lacuna de fórmulas corrigida; aviso de credenciais com `--provider-env inherit` (V08-GAP-23); script de mutação v0.10 |
