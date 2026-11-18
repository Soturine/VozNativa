# Estado de execução da v0.10.5

## Ponto de partida (CP0, conferido ao vivo)

| Item | Valor |
|---|---|
| VozNativa | `main` = `origin/main` = `e274379`; tag `v0.10.0` anotada (`7c8c141`); release Latest; CI #132 8/8 em `e612a43`; branch `dev/v0.10.5` |
| Derivanta Engine | PR #6 **aberto**; release v0.1.0 Latest |
| Assertiva | PR #11 **aberto**; release v1.0.1 Latest |
| Derivanta Framework | `Soturine/Derivanta`, release v0.1.0 Latest |
| Baseline | `qualify --scope release --offline` na worktree de `v0.10.0`: todos os gates locais PASS (INCOMPLETE só pelos externos) |
| Disco | 98% ocupado (13 GB livres); temporários da rodada v0.10 apagados com autorização do mantenedor |

## Checkpoints

| CP | Estado | Commit | Evidência |
|---|---|---|---|
| CP0 + CP1 | concluído | (este commit) | plano e R1–R18 congelados; corpus real de 427 itens com direitos por operação; 18 tarefas live congeladas; piloto de host real (Skill ativada sem ser nomeada) |
