# Auditoria agent-led da Assertiva sobre o VozNativa v0.8 (CP14)

> Estado: registro do CP14, 2026-11-07. Evidência `AGENT_OBSERVED`: o agente é esta sessão do Claude Code
> (modelo Claude Opus 5.5, extensão do VS Code, Windows 10, CPython 3.12.6), seguindo o `SKILL.md` real da
> Assertiva 0.10.1. Nada aqui é revisão humana nem avaliação independente; os julgamentos de cada pista são do
> agente, com o comando e o controle que os sustentam.

## Como foi feito

- **Ferramenta.** Assertiva 0.10.1 instalada da tag `v0.10.1` (clone de `Soturine/Assertiva`) num ambiente
  virtual separado, fora do repositório; Cosmic Ray 8.7.0 no mesmo ambiente. Nenhum `consent.toml` escrito,
  nenhum `--approve`, nenhum `improve`.
- **Alvo.** Clones limpos do VozNativa (`git clone` local), nunca a árvore de trabalho: a auditoria só lê, e as
  execuções rodam numa cópia descartável que o motor cria e remove.
- **Ciclo.** Auditoria estática → pistas → controle negativo de cada pista numa cópia completa da árvore (o
  teste roda sem mutação primeiro; só se julga a pista se ele passa) → correção do teste → os mesmos controles
  de novo → `audit --execute` na revisão corrigida → mutação dirigida.

## Execuções

| Run | Revisão | Motor | O que mostrou |
|---|---|---|---|
| `724c82ad8807423f` (estática) | `659fb3e` | 0.10.1 oficial | 2 pistas `CONDITIONAL_ASSERTION` |
| `10bc215fc9d448f8` (`--execute`) | `e8a05c2` | 0.10.1 oficial | unittest em cópia isolada: PASS, 1161 invocações; wheel: build, install, import e fechamento de dependências PASS, testes contra o wheel NOT_RUN (sem adaptador); cobertura não medida (coverage.py ausente no interpretador); 0 pistas de falso verde |
| estáticas com o detector local | `e8a05c2`, `dc4078d` | 0.10.1 + patch 0001 | 14 pistas `UNCHECKED_ALL` na primeira versão do detector, 11 depois de tratar apelidos e `next()`; 2 em `dc4078d` (as duas rejeitadas) |
| `da50518873d34bba` (`--execute`) | `dc4078d` | 0.10.1 oficial | PASS, 1159 aprovados e 2 pulados; 0 pistas de falso verde; só `UNCLASSIFIED_VERIFICATION` (info: passos da CI que o motor não classifica) |
| `f30c409de8d04bac` (`--mutate voznativa/events.py --mutate-tests evals/test_v08_events.py`) | `dc4078d` | 0.10.1 oficial | nenhum mutante rodou: o motor passou o arquivo como diretório inicial do `unittest discover` (defeito U2); o relatório disse `MUTATION_REPORT_UNREADABLE`, não aprovou |
| `fb730da78e184bf7` (mesma chamada) | `dc4078d` | 0.10.1 + patch 0002 | a linha de base selecionada passou (`unittest --failfast evals.test_v08_events`, 0,96 s); 540 mutantes planejados, acima do orçamento de 300: recusado. O `NATIVE_TESTS_FAILING` desse run é artefato do agente (o `PYTHONPATH` usado para carregar o motor corrigido expôs o pacote `scripts` da Assertiva aos testes; sem ele o teste passa) |

## Pistas e julgamento

Treze pistas no total. Cada uma foi julgada por um controle negativo que faz o código produzir nada (ou quebra o
comportamento que o teste diz proteger); o script `scripts/experiments/v08_cp14_false_green_controls.py` repete
os doze controles com mutação (a pista `h07` é rejeitada por leitura).

| Teste | Pista | Controle | Antes (`659fb3e`) | Depois (`dc4078d`) | Julgamento |
|---|---|---|---|---|---|
| `test_v08_events` `test_new_codes_are_never_critical` | CONDITIONAL | detector de eventos desligado | passa | falha | confirmado, corrigido em `e8a05c2` |
| `test_v08_evaluation` `test_nothing_is_auto_accepted_without_identity` | CONDITIONAL | métrica `semantic_risk` removida | passa | falha | confirmado, corrigido em `e8a05c2` |
| `test_v08_evaluation` `test_the_record_keeps_hashes_not_texts` | UNCHECKED_ALL | run sem resultados | passa | falha | confirmado, corrigido em `dc4078d` |
| `test_v08_evaluation` `test_no_source_is_called_independent` | UNCHECKED_ALL | run sem entradas | passa | falha | confirmado |
| `test_v08_events` `test_what_is_not_a_recipient` | UNCHECKED_ALL | nenhum quadro de evento extraído | passa | falha | confirmado |
| `test_blind_review` `test_focus_and_seeded_order` | UNCHECKED_ALL | foco descarta todos os pares | passa | falha | confirmado |
| `test_community_and_stuffing` (retirada de anglicismos) | UNCHECKED_ALL | retiradas não registradas no relatório | passa | falha | confirmado |
| `test_containment` `test_works_of_one_author_never_cross_a_split` | UNCHECKED_ALL | `provenance` devolve vazio | passa | falha | confirmado |
| `test_corpus_tei` `test_per_document_manifest_never_inherits_the_card` | UNCHECKED_ALL | linhas de política ausentes para licença desconhecida | passa | falha | confirmado |
| `test_longform` `test_literary_notes_never_decide_or_get_acted_on` | UNCHECKED_ALL | plano sem linhas de frase | passa | falha | confirmado |
| `test_patterns` `test_separates_ai_style_drafts_from_natural_texts` | UNCHECKED_ALL | carregador de casos devolve vazio | passa | falha | confirmado |
| `test_document_rewrite` `test_timeout_returns_the_original` | UNCHECKED_ALL | unidades `not_run` omitidas | falha | falha | rejeitado: o desfecho é derivado das unidades, e a checagem do desfecho pega a quebra |
| `test_hardening_h07` `test_literary_ellipsis_is_never_a_confirmed_error` | UNCHECKED_ALL | — | — | — | rejeitado por leitura: lista vazia de problemas de predicado é o resultado certo ("nunca crítico") |

Os onze confirmados viraram a lacuna [V08-GAP-26](GAP_REGISTER.md) (P1, falso verde). A correção é a mesma em
todos: o teste afirma que a coleção existe (tamanho, igualdade com o esperado ou não-vazio) antes de quantificar
sobre ela. Nenhum comportamento do produto mudou.

Três pistas da primeira versão do detector eram falsos positivos dele, não dos testes, e mudaram o patch: a
coleção conferida por outro nome (`protected` derivado de `plan["units"]`; `status` derivado de
`result["comparisons"]`) e um `next(...)` sem padrão sobre a mesma lista, que levanta exceção se ela vier vazia
(`test_bench_v3_harness`).

## Mutação dirigida (GAP-03)

Alvo: `voznativa/events.py` (módulo novo da v0.8, semântica P1), testes `evals/test_v08_events.py`. Como o motor
recusa mais de 300 mutantes por chamada (U3), o Cosmic Ray 8.7.0 rodou fora do motor, numa cópia descartável, com
a mesma configuração que a Assertiva usaria (operadores padrão, timeout de 60 s, `unittest --failfast` só do
módulo de testes); o dump foi importado pela Assertiva oficial (`--mutation-report`, `EXTERNAL_UNVERIFIED`: o motor
não amarra o relatório à revisão).

| Estado | Mutantes | Mortos | Sobreviventes | Equivalentes entre os sobreviventes | Mortos sem os equivalentes |
|---|---|---|---|---|---|
| `dc4078d` | 540 | 273 | 267 | 42 | 273/498 (54,8%) |
| `69e4c9b` | 575 | 367 | 208 | 42 | 367/533 (68,9%) |

Equivalentes: anotações de tipo (`str | None` com avaliação adiada, nunca executadas) e os `lru_cache` (só
desempenho). Os sobreviventes de `dc4078d` mostraram mais que testes faltando: **o ramo da voz passiva nunca era
alcançado**, nem pelos testes nem por frases comuns. "O relatório foi enviado à diretoria." não tinha quadro de
evento, porque "enviado" também é lido como presente de "enviadar" e um verbo com dois radicais era descartado;
destinatário omitido ou trocado numa passiva no singular passava sem aviso ([V08-GAP-27](GAP_REGISTER.md)).
Correção em `787bd40` (depois de auxiliar de passiva vale a leitura de particípio) e simplificação em `69e4c9b`
(a segunda rodada mostrou que uma exceção para "e" não tinha entrada alcançável que a distinguisse). Testes novos
fixam a passiva no singular, destinatário e troca na passiva, advérbio antes do verbo, segundo verbo finito,
janela de oito palavras do destinatário, "a" artigo antes de substantivo comum e a tolerância do radical do
converso. Nos conjuntos de eventos congelados, 52 de 52 desfechos iguais antes e depois.

Os 166 sobreviventes não equivalentes restantes são, na maioria, troca de operador aritmético e de número nas
janelas e fatias (`k + 8`, `idx + 1`, `[:-2]`); não foram classificados um a um, e parte deles é equivalente para
as entradas possíveis. Mutação de `compare.py` além do CP5b, `router`, `morph` e `diagnose` continua fora
(V08-GAP-03 segue parcial).

## Retorno para a Assertiva (dogfood bidirecional)

Nada foi enviado ao repositório da Assertiva: push e pull request disparam as Actions dela. Os patches ficam em
[`upstream/`](upstream/) para o mantenedor aplicar com `git am` na hora que escolher.

| ID | Observação | Evidência | Patch |
|---|---|---|---|
| U1 | A 0.10.1 não aponta `all()`/`not any()` sobre coleção que o teste nunca mostra não vazia; nove testes do VozNativa tinham o padrão | repro mínimo (`Vacuous::test_all_positive` não apontado, `Conditional` apontado); 9 controles confirmados | [`assertiva-0001-unchecked-all.patch`](upstream/assertiva-0001-unchecked-all.patch): smell `UNCHECKED_ALL`, testemunhas (outra asserção, apelido, mapa por trás de `.values()`, `next()` sem padrão), calibração com 5 formas e 6 controles |
| U2 | `--mutate-tests ARQUIVO` sob unittest vira `unittest discover --failfast ARQUIVO`: ImportError, nenhum mutante roda | run `f30c409de8d04bac` | [`assertiva-0002-unittest-mutate-tests.patch`](upstream/assertiva-0002-unittest-mutate-tests.patch): módulos com ponto; pasta vira seus `test*.py`; os dois testes novos falham na 0.10.1 |
| U3 | O orçamento de 300 mutantes é por arquivo e não há alvo menor que um arquivo: `events.py` (185 linhas) planeja 540 e fica sem caminho dentro do motor | run `fb730da78e184bf7` | sem patch; sugestão: alvo por função ou orçamento explícito por chamada |
| U4 | Nenhuma pista para um ramo que nenhum teste alcança (a passiva de `events.py`): só a mutação mostrou | rodadas do Cosmic Ray acima | sem patch; é o limite esperado da análise estática, registrado para o mantenedor |
| U5 | Testes contra o wheel ficam NOT_RUN para pacote Python sem adaptador de runner | runs `10bc215fc9d448f8` e `da50518873d34bba` | sem patch; o VozNativa já roda a suíte contra o wheel no próprio gate (GAP-06) |

Verificação dos patches: calibração e testes do Cosmic Ray passam; a suíte inteira da Assertiva com o patch 0001
tem as mesmas 6 falhas da 0.10.1 sem patch nesta máquina (servidor, trava de workspace, cobertura de ramos,
artefato: ambientais, presentes nos dois lados); as suítes de mutação (55 testes) passam com o patch 0002.

## Limites

- Uma sessão de agente, sem segundo revisor. Os controles negativos são do mesmo agente que escreveu as correções.
- O detector `UNCHECKED_ALL` é textual: outras formas de quantificador vazio (laço `for` com asserção dentro,
  `assertCountEqual` com listas vazias) não foram procuradas.
- Cobertura de linhas não foi medida pela Assertiva (coverage.py ausente no ambiente da ferramenta).
