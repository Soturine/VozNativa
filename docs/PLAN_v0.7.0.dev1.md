# Plano da v0.7.0.dev1: estabilização

Rodada corretiva sobre a v0.7.0.dev0. Não é a v0.8 e não reabre a v0.7: fecha lacunas de confiabilidade encontradas na auditoria posterior e qualifica a revisão sem regressão.

- **Partida:** `main` = `dev/v0.7.0` = `e7506f5` (conferido com `git ls-remote` em 2026-11-06). Código testado pela CI: `9f44010`, run #124, `workflow_dispatch`, 8/8. `e7506f5` só acrescenta evidência.
- **Branch:** `dev/v0.7.0-hardening`, criada de `main` em `e7506f5` com a árvore limpa.
- **Política de CI:** `.github/workflows/ci.yml` tem só `workflow_dispatch` (gate `ci:workflow-triggers`). Nenhum run durante os CPs. Um único dispatch na `main` no CP7.
- **Estado e retomada:** `docs/V07_EXECUTION_STATE.md`, seção "v0.7.0.dev1". Achados: `docs/V07_DISCOVERY_REGISTER.md` (VN07-DISC-037 em diante). Verificação: `docs/V07_VERIFICATION_MATRIX.md`. Qualificação: `docs/V07_RELEASE_QUALIFICATION.md`. Atualizo esses arquivos em vez de criar cópias `V07_HARDENING_*`: os dois primeiros e os registros em `evals/assurance/runs/` já estão na lista de caminhos só de evidência do `scripts/ci_evidence.py`, que não precisa crescer.

## Baseline (CP0)

`scripts/qualify.py --scope release` em `e7506f5`, Windows 11, CPython 3.12.10 (Python do sistema, não venv). Exit 3, veredito INCOMPLETE.

- **Unittest:** 635 rodaram, 634 PASS, 1 skip (pipeline POSIX).
- **Gates locais:** validator, semantic (dev e holdouts), decisão, roteador, CLI, pacote e gatilhos de workflow, todos PASS.
- **NOT_RUN:** `review:pty` (POSIX), `holdout:independent`, `review:blind-human` e `ci:github-actions`. O último ficou NOT_RUN porque a árvore estava suja: criei os arquivos da amostra de predicados durante a execução. A falha é de processo, não de código. Fica registrada e não é tratada como PASS.

## Achados reproduzidos antes de qualquer correção

| ID | Achado | Classificação | Severidade | Impacto | Reprodução |
|---|---|---|---|---|---|
| H07-F1 | A triagem da v0.7 chamou de "equivalentes no CPython" 12 mutantes `==`/`!=` → `is`/`is not` por internamento de literais. Cinco deles comparam valores vindos de YAML, regex ou argumento, que são iguais mas não são o mesmo objeto. | CONFIRMED (triagem) | P2 | testes; a semântica de produção está correta | `evals/test_hardening_h07.py::DynamicStringsReachTheComparisons` |
| H07-F2 | O `MUTATION.md` lista 11 linhas para "12" mutantes de identidade. Falta a linha 188 (`plain[end] == "-"`). | CONFIRMED (documentação) | P3 | rastreabilidade | consulta ao `temporal.sqlite` da rodada 2 |
| H07-F3 | O validador do léxico não impõe o contrato de `count`: aceita valor negativo, booleano, float e string. Também não valida `from <= to`, `words` nem a data de verificação. | CONFIRMED | P2 | dados: um negativo some de `attested_in` sem erro | `CountContract` (xfail até o CP2) |
| H07-F4 | O par do README "será enviado até…" → "vai até…" sai `no_deterministic_issues`: a ação de enviar some sem nenhum issue. | CONFIRMED | P1 | semântica: falso verde em compromisso | `PredicateLoss` (xfail até o CP3) e amostra prospectiva |
| H07-F5 | `tense_changed` trata futuro perifrástico ("vai depositar") e sintético ("depositará") como tempos diferentes: 3 dos 18 controles legítimos da amostra viraram `review_required`. | CONFIRMED | P2 | UX: falso alarme | `FutureForms` (xfail até o CP3) |
| H07-F6 | `condition.temporal` acusa "durante o fim de semana" → "no fim de semana". | ACCEPTED_RISK | P3 | UX: falso alarme pontual | amostra `pc-09`. Não corrijo: é o comportamento documentado do marcador, e a única evidência é um caso da própria amostra. |
| H07-F7 | O README diz que VozNativa "prova com gates determinísticos" que compromissos continuam lá. Os gates verificam só invariantes, e o próprio exemplo do README perde a ação. | CONFIRMED | P1 | documentação: alegação inflada | leitura do README, linha 5 |
| H07-F8 | As linhas VN07-DISC-016 e VN07-DISC-030 do registro de descobertas têm texto corrompido por heredoc: newline literal dentro da tabela e `\x08` repetido. | CONFIRMED | P3 | documentação | `cat -A docs/V07_DISCOVERY_REGISTER.md` |

## Requisitos

| ID | Requisito | Aceite | Teste ou evidência | CP |
|---|---|---|---|---|
| H07-001 | Comparações contra `"active"` e outros enums do léxico funcionam por valor quando os dados vêm de YAML. | Os mutantes de identidade nas linhas 109 e 303 morrem. | `test_status_active_from_yaml_is_active` | CP1 |
| H07-002 | Enum, sentido e época vindos de YAML, CLI ou regex são comparados por conteúdo. | Os mutantes 91, 235 e 262 morrem. Os demais são classificados um a um, com origem do operando e restrição declarada. | `DynamicStringsReachTheComparisons` e nova rodada de mutação | CP1 |
| H07-003 | `count` negativo é rejeitado com motivo explícito. | Mensagem com "count" e "negative". | `test_negative_count_is_refused_with_a_reason` | CP2 |
| H07-004 | `count == 0` é válido, mas não atesta nada. | `attested_in` não usa o zero; evidência acima de E0 com só zeros é rejeitada. | `test_zero_count_is_valid_but_attests_nothing` | CP2 |
| H07-005 | `count` booleano, float ou string é rejeitado, sem conversão silenciosa. | Uma mensagem por campo. | `test_boolean_float_and_string_counts_are_refused` | CP2 |
| H07-006 | Ação ou compromisso trocado por verbo leve, ou removido, gera sinal de risco estruturado. | O par do README fica `review_required` com issue própria, nunca `fail` sem evidência. | `PredicateLoss` e amostra | CP3 |
| H07-007 | A mesma ação dita com outro verbo pleno, em voz passiva ou nominalizada não é bloqueada. | Os controles da amostra não pioram. | amostra `pc-*` | CP3 |
| H07-008 | A inversão agente/paciente continua detectada. | Os testes `role_reversed` existentes seguem PASS. | suíte | CP3 |
| H07-009 | Elipse e inversão literária não viram erro confirmado. | No máximo `review_required`, nunca `fail` pela regra nova. | `pc-10`, `pc-12`, `pc-17`, `pc-18` e teste dedicado | CP3 |
| H07-010 | Em documento longo, a omissão de uma ação noutro segmento não dá falso verde global. | O `compare` global de `rewrite_document` sinaliza. | teste em `test_document_rewrite` | CP3 |
| H07-011 | README, quickstart, CLI e wheel funcionam e não alegam mais do que verificam. | `test_readme`, smoke do pacote, exemplos com o significado preservado. | `evals/test_readme.py`, gate de pacote | CP4 |
| H07-012 | Mutantes de `temporal.py` reclassificados por evidência, numa rodada reproduzível. | Mesmo conjunto de chaves da rodada 2, ou a diferença explicada. | `evals/assurance/runs/2026-11-06-h07-cp5/` | CP1/CP5 |
| H07-013 | Nenhum workflow com `push` ou `pull_request`. | Gate `ci:workflow-triggers` PASS. | `scripts/qualify.py` | todos |
| H07-014 | Mudança de código depois da CI invalida o PASS; commit só de evidência mantém a equivalência. | Testes existentes de `ci_evidence` e um novo para um arquivo de código em `docs/`. | `evals/test_ci_evidence.py` | CP6 |
| H07-015 | Futuro perifrástico e sintético da mesma referência temporal não são "mudança de tempo". | `FutureForms` | `FutureForms` | CP3 |
| H07-016 | O registro de descobertas sem caracteres de controle nem linhas partidas. | Varredura no validator. | `scripts/validate_package.py` ou teste | CP0 |
| H07-017 | Um plano de documento serializado não concede permissão: editar `action`, `kinds`, `blocks` ou offsets (mesmo com hash recalculado) não desprotege código, tabela, separador ou citação. | `validate_plan` aponta o problema e `reassemble` recusa; planos válidos (JSON, CRLF, verso autorizado) seguem iguais. | `PlanIsDataNotAuthority` | CP5B |
| H07-018 | Depois de uma CI verde, só registros não executáveis mantêm a equivalência de código. | Harness `.py`, `conftest.py`, `pyproject.toml` ou código movido para `evals/assurance/runs/` invalidam o PASS. | `EvidencePathsAreRecordsOnly` (com git real) | CP5B |
| H07-019 | A CI que qualifica é manual e completa por identidade. | Evento ≠ `workflow_dispatch`, job ausente, duplicado ou trocado → INCONCLUSIVE. | `ManualRunAndExactMatrix` | CP5B |
| H07-020 | Documento vazio ou só com espaços não quebra a reescrita longa. | Volta intacto com `no_change`. | `test_whitespace_only_document_is_returned_unchanged` | CP5B |

## Hipóteses e decisões de escopo

- **CP1 não muda produção.** O código usa `==`, que é o certo. Muda a triagem e os oráculos. Mutantes cujo operando só vem de literais do próprio pacote continuam "equivalentes sob CPython". Essa é uma restrição declarada, não uma prova.
- **CP3 começa pela opção mais barata que mede algo:** âncoras de predicado com a morfologia por regras que já existe (`voznativa.morph`) e radicais. Verbo pleno da fonte ausente na frase alinhada da candidata:
  - quando a candidata só tem verbo leve (`ser`, `estar`, `ir`, `ter`, `haver`, `ficar`) ou nenhum verbo, gera issue `major`;
  - quando o verbo pleno foi trocado por outro, gera só `info`, porque sinônimo não se decide sem léxico semântico.

  Alternativas comparadas e não adotadas nesta rodada:
  - parser de dependências (dependência nova e pesada);
  - NLI ou LLM judge (não determinístico, já existe como `--judge-cmd`);
  - lista de pares de verbos (seria decorar exemplos).
- **A amostra de predicados** (`evals/predicates/cases-h07.jsonl`, sha256 em `evals/predicates/MANIFEST.json`) foi congelada antes de qualquer código da regra. É conjunto de desenvolvimento do mesmo autor: os números antes e depois são regressão, não benchmark cego. A linha de base pré-regra (`evals/predicates/runs/predicates-2026-11-06-before.json`) deu 7/20 riscos sinalizados e 4/18 falsos alarmes. Três desses falsos alarmes motivaram o H07-F5, o que os torna não prospectivos.
- **Versão:** `0.7.0.dev1` no CP6, nunca `0.7.1`, porque não houve v0.7.0 estável.

## Checkpoints

| CP | Conteúdo | Gate |
|---|---|---|
| CP0 | Plano, baseline, reproduções (xfail), amostra congelada, correção do registro corrompido | `qualify --scope local` exit 0 |
| CP1 | Reclassificação dos 12 mutantes de identidade com mutantes aplicados um a um | idem |
| CP2 | Contrato de `count`, `from`/`to`, `words` e data de verificação no validador canônico | idem |
| CP3 | Âncoras de predicado e equivalência de futuro | idem, mais suítes semânticas congeladas sem regressão |
| CP4 | README, SKILL, exemplos e alegações | idem, mais `test_readme` |
| CP5 | Mutação: `temporal.py` completo, amostra dirigida em `compare` (regra nova e `_moved_signal_issues`) e `document.py`; dogfood Engine/Assertiva | idem |
| CP5B | Auditoria de fechamento: integridade do plano (H07-017), allowlist de evidência (H07-018), evento e matriz da CI (H07-019), rodada C completa (271), oráculos de `document.py`, dogfood agent-led | idem, mais v4 22/22 e v5 36/36 |
| CP6 | `0.7.0.dev1`, qualificação Windows 3.11/3.12 e WSL 3.11–3.13 | `qualify --scope release` (INCOMPLETE só por gates externos) |
| CP7 | Fast-forward da `main`, dispatch único, registro | run verificado ao vivo |

## Riscos

| Risco | Mitigação |
|---|---|
| A regra de predicado gera falso alarme em paráfrase legítima. | Severidade `major` (revisão), nunca `critical`. Controles positivos na amostra e nas suítes congeladas. Se o ganho não superar o custo, a regra fica experimental. |
| A morfologia por regras inventa verbos ("prazo" → "prazar"). | Só âncoras fortes: construção com auxiliar, ou forma finita com terminação forte e análise única. Na dúvida, abstém. |
| A amostra de predicados está enviesada pelo autor. | Rotulada como não independente. Um holdout de outra pessoa é pré-requisito v0.8. |
| Novo dispatch acidental de Actions. | Gatilhos conferidos antes de cada push; upstream bloqueado se o push disparar Actions. |

## Backlog para a v0.8 (não implementado aqui)

- Holdout independente de predicados e compromissos, escrito por outra pessoa antes da regra.
- Relações semânticas de verbo (sinônimo × evento diferente: "assinou" × "recebeu") com recurso lexical licenciado e medido.
- Destinatário e papéis temáticos além de agente/paciente (`pr-17`).
- Mutação completa de `router`, `morph`, `diagnose`.
- **B-M1:** oráculos para `count == 1` dentro da época e para o ramo de valor ausente em `_attestation_problems`.
- **B-M2:** mutação de `compare.py`. **Feito no CP5B:** rodada C completa nas linhas 76 e 429–583 (271 de 271: 201 mortos, 70 sobreviventes) e oráculos em `evals/test_compare_signal_oracles.py` (44 dos 70 mortos só por esse arquivo; 22 equivalentes argumentados em `evals/assurance/runs/2026-11-07-h07-cp5b/MUTATION.md`). **Falta:** decidir se construção com auxiliar no infinitivo (`progressive@inf`) abstém em `_time_reference` (linha 467, VN07-DISC-057) e só então escrever o oráculo; ficha determinística para token com dois radicais (520) e para token de construção reanalisado (529); mutação do resto de `compare.py`.
- **B-M3:** oráculos de fronteira em `document.py`. **Feito no CP5B:** corte de segmentos, recuo, corte forçado, aparas do núcleo, recusa campo a campo, `structure_of` (`evals/test_document_plan_oracles.py`; replay da amostra D: 25 de 52 sobreviventes mortos só por esse arquivo). **Falta:** padrões de `Limits` (linhas 44/46/49), `frozen` (42), limite de 80 valores (134), `carry` com token que é nome e sigla (126). Baixo risco: padrões e dicas ao modelo, não guardas.
- **B-M4:** `spans.extract` quadrático (VN07-DISC-056): ~90 s em 193 mil palavras. Índice de intervalos, com teste de equivalência da saída antes de otimizar.
- **Refatorar `compare._predicate_issues`** (21 caminhos) depois da mutação completa, para não invalidar a evidência atual.

