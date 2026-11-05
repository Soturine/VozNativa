# Dogfood cruzado — VozNativa ↔ Assertiva ↔ Derivanta Engine (rodada de 2026-11-05)

Registro canônico. Cada item diz o que a **ferramenta observou** e o que o **agente concluiu** depois, com reprodução, reteste e estado de encaminhamento. O mesmo agente (mesma família de modelo) construiu o VozNativa, rodou as ferramentas e julgou os resultados: autoavaliação com evidência de ferramenta, não qualificação independente.

Instrumentos: Assertiva 0.10.1 (wheel construído da tag `v0.10.1`, `2618d95`, venv próprio); Derivanta Engine 0.1.0 (`0be2a38`) com o Framework `218761d`; Cosmic Ray 8.7.0; Windows 11, CPython 3.12.10. Saídas: `evals/assurance/runs/`.

## 1. VozNativa — defeitos achados nesta rodada

| ID | Quem achou | Hipótese → reprodução | Antes → depois | Teste que detecta | Commit |
|---|---|---|---|---|---|
| VN-D01 | `scripts/qualify.py` (gate de exit codes) | erro de uso sai 2 = `review_required` do `compare` | `--no-such-flag` exit 2 → 64 | `test_argument_errors_never_exit_with_a_gate_status` (falha sem a correção: `2 != 64`) | `8b103e7` |
| VN-D02 | Assertiva `FALSE_GREEN_CANDIDATE` + controle negativo NC1 | renomear `frozen` no manifesto deixa editar holdout | teste verde → falha | `test_frozen_suites_were_not_edited` (NC1 refeito: falha) | `ada5aa6` |
| VN-D03 | leitura do agente (scorer do benchmark) | `provider_error` devolve o original e conta como invariantes ok | v0.4.0 "15/15" → 14/14 onde houve saída + 1 falha de sistema | `evals/test_benchmark_axes.py` | `286dfc8` |
| VN-D04 | reanálise H2 de `bv2-li-02` | dia da semana sem preposição: falso vermelho e, no mesmo mecanismo, falso verde | `wd-201`…`wd-205`: 4 falham sem a correção | casos dev | `4af90ac` |
| VN-D05 | probe H4 | "2 da tarde" ≠ "14h"; "triplicar" não era valor (`ho-007`) | probe 19/29 → 25/29; `ho-007` 24/24 estrito | `tm-*`, `mul-*` | `78502c1` |
| VN-D06 | probe H4 | troca de papéis entre substantivos comuns e de ordem temporal passava | idem | `role-*`, `ord-201` | `c341967` |
| VN-D07 | perfil (cProfile) | `signals.markers` O(frases × tokens) | compare 8k palavras 10,4 s → 0,96 s | teste diferencial contra o algoritmo anterior | `eb8ea99` |
| VN-D08 | perfil do loop sem modelo | `adherence` quadrático | 48,6 s → 1,1 s | `BestRatioEquivalence` (2 mutantes de folga mortos) | `a8c9d41` |
| VN-D09 | mutante sobrevivente do teste diferencial | contração no 1º termo ("na função de" = causal) | marcador falso → nenhum | `FirstSlotContractions` | `df42939` |
| VN-D10 | revisão H6 | chave HMAC criada legível e só depois `chmod 600` | criação atômica 0600 | `ReviewKeyCreation` (POSIX) | `218e912` |
| VN-D11 | gate de pacote | falha do smoke escondida por `PermissionError` no Windows | erro real visível | smoke no gate `package` | `e0944a1` |
| VN-D12 | testes metamórficos (CP7) | NFD e NBSP mudavam veredito (20/216 com NFD, incluindo falsos verdes) | 0/216 | `evals/test_metamorphic.py` (3 falham sem a correção) | `1191080` |
| VN-D13 | mutação dirigida (Cosmic Ray) | oráculos fracos nos eixos do benchmark | sobreviventes 263 → 212 → 204; 17 dos 19 restantes no trecho são equivalentes | `MutationFindings` | `8a530f8`, `4c228f3`, `b6a61b2` |
| VN-D14 | Engine `ENG-MAINT-UNREFERENCED` / duplicação | `_NUMBER_WORD_ALT` morto; `RELATIONSHIPS` nunca validado; `--task` duplicado | Engine compare: 3 achados **ABSENT** | `ReviewerRegistry` | `ed13559` |
| VN-D15 | Engine compare (achado NEW) | `outcome_axes` com 37 caminhos | uma função por eixo; reanálise byte a byte igual | testes de eixos | `db2dff3` |

## 2. Assertiva 0.10.1

**O que ela acertou (verdadeiros positivos):** executou de fato a suíte unittest (281, depois 316 invocações, exit 0) numa cópia descartável, com cobertura medida; apontou o falso verde real NC1 (1 de 4 candidatos); construiu e instalou o wheel; manteve como UNKNOWN os scripts do projeto no CI; no reprodutor, apontou corretamente uma tautologia e um mutante sobrevivente real.

| ID | Classificação | Revisão auditada | Hipótese | Reprodução | Esperado | Observado | Impacto | Correção proposta | Reteste | Encaminhamento |
|---|---|---|---|---|---|---|---|---|---|---|
| AXF-VN-01 | defeito (unittest + mutação) | VozNativa `66b918e`; reprodutor sintético | `--mutate-tests ARQUIVO` não funciona com unittest | projeto `calc/` + `tests/test_calc.py` + CI com `unittest discover`; `--mutate calc/__init__.py --mutate-tests tests/test_calc.py` | rodar só esse arquivo de teste (o `--help` diz "files or folders") | `discover -s tests/test_calc.py` → `ImportError: Start directory is not importable`; 0 mutantes; achado rotulado `MUTATION_REPORT_UNREADABLE` | mutação dirigida impossível em projetos unittest com suíte lenta (VozNativa: 70 s × 825 mutantes) | mapear arquivo para `discover -s <pasta> -p <arquivo>` ou id de módulo; rotular como falha de seleção, não de relatório | controle positivo: `--mutate-tests tests` → 18 mutantes, 17 mortos | intake no repositório Assertiva (ver §4) |
| AXF-VN-02 | precisão / recomendação | VozNativa `4044cfc` | `CONDITIONAL_ASSERTION` trata filtro dentro de laço sobre dados fixos como asserção que pode não rodar e recomenda "torne incondicional" | teste `for value, expected in CASES: if expected: assertTrue(...)` | lead com recomendação de asserção de não vacuidade (contar casos alcançados) | `FALSE_GREEN_CANDIDATE` "make the check unconditional"; quebrar a função faz o teste falhar | 2 de 4 candidatos no VozNativa eram falso positivo prático; 1 era real (NC1) | sub-padrão `FILTERED_LOOP_ASSERTION` com `resolve_with` de não vacuidade | controle negativo: o teste detecta a quebra | intake |
| AXF-VN-03 | lacuna de evidência | VozNativa e reprodutor | execuções unittest não registram `source_identity`, `interpreter`, `temp_root` (o pytest registra) | qualquer `--execute` em projeto unittest | os mesmos campos do pytest | `null` nos três | um verde não prova qual cópia do código foi importada | registrar origem dos módulos importados no adaptador unittest | — | intake |
| AXF-VN-04 | lacuna | VozNativa `4044cfc` | testes contra o wheel instalado ficam NOT_RUN em projeto unittest | `--execute` no VozNativa | rodar a suíte contra o wheel, como no pytest | `tests NOT_RUN: "no test runner adapter for this project"` embora o adaptador unittest tenha rodado a fonte | qualificação do artefato sem testes | reutilizar o adaptador unittest na qualificação do artefato | — | intake |
| AXF-VN-05 | observação de design | reprodutor sem CI | sem CI nem configuração, projeto só com unittest é tratado como pytest | `audit --execute` no reprodutor sem `.github` | tentar descoberta unittest da stdlib ou dizer que o runner é desconhecido | `pytest-native BLOCKED`, `ENVIRONMENT_NOT_PREPARED` | falso BLOCKED em projetos stdlib | fallback para `unittest discover` quando não há pytest e há `unittest.TestCase` | — | intake (observação) |
| AXF-VN-ENV | ambiente local, não defeito | — | instalação global editável antiga | `pip show assertiva` | — | `assertiva --version` 0.10.1, metadados pip 0.5.5 | risco de rodar código diferente do pensado | usar venv próprio (feito) | — | não encaminhado |

## 3. Derivanta Engine 0.1.0 e Framework

**O que ele acertou:** com o Engine atual (`17fa564`), o `compare` entre um relatório do Engine antigo e um do novo foi `COMPARABLE` e apontou duas duplicações reais introduzidas nesta rodada (corrigidas: uma lista com um só dono em `voznativa/regional.py`); `license: not observed` (o repositório não tem LICENSE); três candidatos de manutenção confirmados e corrigidos (VN-D14), e o `compare` registrou os três como **ABSENT** em escopo comparável (reteste derivado pelo próprio Engine); a nova complexidade em `outcome_axes` apareceu como **NEW** e foi tratada (VN-D15).

| ID | Classificação | Observado pelo Engine | Conclusão do agente | Correção proposta | Encaminhamento |
|---|---|---|---|---|---|
| DEF-VN-01 | falso positivo de contexto (INFO); reproduzido também em `17fa564` | `evaluate`: tecnologia declarada `unittest` e "external LLM CLI" "not observed in the inspected scope" | o Engine lê só manifests no `evaluate`; runner da stdlib e CLI externo nunca aparecem em manifest; o workflow de CI que roda `python -m unittest` foi inventariado, não lido | ler os comandos dos workflows de CI como evidência de runner, ou classificar tecnologias da stdlib/CLI como "não observáveis por manifest" | intake no repositório Engine |
| DEF-VN-02 | proporcionalidade | 12 campos materiais faltando em profundidade DEEP, incluindo RTO, RPO e disponibilidade para uma CLI offline | os campos aceitam texto; falta um jeito estruturado de dizer "não se aplica" | valor estruturado `not_applicable` com motivo nos campos de operação | intake |
| DEF-VN-03 | **hipótese corrigida** | — | registrei primeiro que `derivanta-engine review` não existia; era verdade só para o checkout local `0be2a38`, 7 commits atrás de `origin/main`. O Engine atual (`17fa564`) tem `review` e foi usado (`runs/2026-11-05-cp8-engine-m3`): 3 propostas fundamentadas → CANDIDATE (INFERRED), contagem falsa → REJECTED `CONTRADICTED`, pedido de RETESTED → REJECTED `STATUS_NOT_REQUESTABLE` | nenhuma | não encaminhado (erro do agente) |
| DEF-VN-05 | identidade de versão | `--version` responde `derivanta-engine 0.1.0` em `0be2a38` (M2) e em `17fa564` (M3, com `review`, MCP e camada de aplicação) | a versão não distingue builds com superfícies diferentes; um relatório não diz qual Engine o produziu além de "0.1.0" | incluir revisão ou versão de desenvolvimento (`0.1.0.devN+g<sha>`) no `--version` e no campo `engine` dos relatórios | intake |
| DEF-VN-04 | contextual | complexidade em `reference_markers` (oráculo copiado de propósito no teste diferencial) | o Engine não distingue oráculo de referência de código de produção | nenhuma; a disposição é do projeto | não encaminhado |

Framework: o perfil derivado (`docs/ENGINEERING_PROFILE.md`) usou a Constituição, Authority & Exceptions, Continuous Assurance e DoR/DoD sem precisar de regra específica do VozNativa no núcleo; nada foi proposto para a Constituição.

## 4. Estado de encaminhamento

Atualizado quando os registros forem publicados nos repositórios responsáveis; "encaminhado" não significa corrigido.
