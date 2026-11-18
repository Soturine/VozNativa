# Manutenção: duplicação, código morto e ciclos (v0.10, CP9)

**Método.** Derivanta Engine 0.1.0 (`inspect --maintainability`, clone isolado do `origin/main` `37ba01a`) sobre o **mesmo caminho** em duas revisões (a `compare` exige o mesmo alvo: com diretórios diferentes deu `DIFFERENT_TARGET`). Cada candidato tratado como hipótese, conferido por busca, grafo de imports e testes. Grafo de imports próprio (todos os `from . import`, inclusive dentro de funções), porque o Engine não analisa ciclos.

## Antes × depois

| Medida | `v0.9.0` | v0.10 (CP9) |
|---|---|---|
| Linhas de `voznativa/*.py` | 15.933 | 17.296 (4 módulos novos: `task_context`, `knowledge`, `discourse`, `watcher` e dados) |
| Candidatos Derivanta (complexidade / duplicação / não referenciado) | 122 / 73 / 4 | 132 / 77 / 4 |
| Comparação Derivanta | — | `COMPARABLE`: 15 novos, 198 persistentes, 1 ausente |
| Ciclos de import entre pares de módulos | 5 | **4** |
| Dependências obrigatórias | PyYAML | PyYAML (nenhuma nova) |

## Triagem dos candidatos novos

| Candidato | Decisão | Motivo |
|---|---|---|
| `task_context.ROUTER_DIMENSIONS` repete `router.DIMENSIONS` | **corrigido**: derivado do router (um dono) | mesma lista em dois lugares divergiria |
| `task_context` repete fatia de `SOURCES` no bloco do prompt | **corrigido**: `SHOWN_SOURCES = SOURCES[:4]` | idem |
| `watcher.PIPELINE` "não referenciado" + trilha repetida | **corrigido**: a trilha das propostas vem de `PIPELINE` | a constante era a fonte e não era usada |
| ciclo `compare` ↔ `judge` criado no CP6 | **corrigido**: política de relação mora em `compare` (ao lado de `JUDGE_KINDS`); `judge` reexporta | ciclo novo é dívida nova |
| `judge.ACCEPTING_RELATIONS` repete strings de `GENERATOR_RELATIONS` | **aceito** | lista de permissão explícita: uma relação nova não deve aprovar por omissão |
| `task_context.RESERVED` repete chaves de configuração do CLI | **aceito** | contratos diferentes (o que um atributo não pode ser × o que a configuração define) |
| `planner._GRAMMAR_TYPES` repetido em teste | **aceito** | teste é oráculo independente |
| complexidade nova (`watcher.check`, `knowledge.validate/select`, `compare._tense_issues`, avaliador) | `watcher.check` **reduzida** (extraídos `_fetch_with_retry` e `_evaluate`); demais aceitas | funções de decisão com casos enumerados e testados |

## Dívidas herdadas resolvidas

- **V08-GAP-28 (parcial → 4 de 5 ciclos restam)**: `diagnose` ↔ `planner` desfeito movendo `weekday_conflicts` para `ledger` (a única coisa que `diagnose` usava do `planner`); `planner._weekday_conflicts` continua como alias. Restam `community`↔`packs`, `corpus.connectors`↔`corpus.tei`, `ptbr`↔`router`, `router`↔`temporal`: resolvidos por import dentro de função e cobertos por testes em qualquer ordem de carga; desfazê-los exige mover código entre módulos públicos (fica para a 0.11, ACCEPTED_RISK).

## Código "morto" que não é

Os 4 "não referenciados" da base são classes de teste que herdam de outra classe de teste do mesmo arquivo (`CountContract(LexiconFile)`, `TextBridge(Fixture)`…): o unittest as descobre por herança. **Não removidas.** É falso positivo do Derivanta (só reconhece subclasse direta de `TestCase`): corrigido no próprio Derivanta no CP11 ([`BIDIRECTIONAL_DOGFOOD.md`](BIDIRECTIONAL_DOGFOOD.md)).

Nenhuma API pública foi removida. Nenhum código foi apagado só por não ter referência textual.
