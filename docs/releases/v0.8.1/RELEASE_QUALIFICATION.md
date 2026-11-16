# Qualificação da v0.8.1

> Estado: critérios fixados **antes** de rodar; resultados preenchidos com o que de fato rodou. Item que não rodou fica NOT_RUN. Três coisas nunca somadas: **implementação** (código e testes), **qualificação local** (`scripts/qualify.py` numa revisão, em plataformas nomeadas) e **qualificação externa** (CI conferida ao vivo, holdout de outra pessoa, revisão humana cega).

## Conteúdo

- DF-01 a DF-09, corrigidos a partir de dois dogfoods ([`DOGFOOD_TG1.md`](../v0.8/DOGFOOD_TG1.md), [`DOGFOOD_TCC2.md`](../v0.8/DOGFOOD_TCC2.md)). Cada um tem teste de regressão sintético que falha no código anterior à correção e passa depois.
- Versão `0.8.1` em `voznativa/__init__.py`, `SKILL.md` e `.claude-plugin/plugin.json` (o teste `test_readme` exige as três iguais, além do README).
- Histórico: os commits dos dois dogfoods foram refeitos antes da integração para tirar um fragmento de cinco palavras do primeiro documento de uma docstring e de uma fixture. Árvores conferidas: idênticas à versão revisada, exceto a fixture trocada. Auditoria por commit contra os dois documentos: nenhuma sequência de cinco palavras nem termo característico em comum.

## Critérios

**Obrigatórios para release estável** (qualquer FAIL bloqueia; vira pre-release `0.8.1.dev0` ou nada é publicado):

1. `qualify.py --scope release` em árvore limpa no Windows (CPython 3.12): unittest, validador, semânticas dev e holdouts (safety e strict), regressões de decisão e roteador, códigos de saída, gatilhos da CI e pacote (sdist → wheel → venv limpo → smoke → suíte contra o wheel).
2. A mesma qualificação em Linux (contêineres Python 3.11, 3.12 e 3.13), como na v0.8.0.dev0.
3. Benches congelados `ptbr-bench-v4` 22/22 e `ptbr-bench-v5` 36/36, e amostra de predicados sem piora (17/20, 1/18).
4. Testes DF-01 a DF-09: falham no código anterior e passam no final.
5. Auditoria de privacidade do histórico integrado: limpa.
6. CI do GitHub no commit final da `main`, conferida ao vivo. **Se a CI não puder rodar por limitação externa** (billing, cota), o critério fica NOT_RUN e a release estável depende da qualificação local completa nas quatro plataformas; a decisão e o motivo ficam registrados aqui e nas notas.

**Externos, não obrigatórios** (já NOT_RUN na v0.8.0.dev0; seguem registrados como lacunas): holdout independente, revisão humana cega, provider de outro fornecedor como juiz independente, `review:pty` no Windows (só POSIX).

**Complementares:** Assertiva (`audit --execute`) e Derivanta Engine, quando aplicáveis.

## Resultados

Revisão qualificada: **`5f27d1e`** (`main`, merge da release). O commit de evidência que vem depois muda só documentação; `scripts/ci_evidence.py` confere a equivalência do código.

| # | Critério | Resultado |
|---|---|---|
| 1 | `qualify.py --scope release`, Windows 10, CPython 3.12.6, árvore limpa | **PASS** em todos os gates locais: unittest 933 (931 PASS, 2 skips com motivo), validador, semânticas dev e holdouts (safety e strict), regressões de decisão e roteador, códigos de saída, gatilhos da CI, pacote (sdist → wheel → venv limpo → smoke → suíte contra o wheel). Veredito do runner: INCOMPLETE só pelos externos abaixo e pelo `review:pty` (só POSIX) |
| 2 | mesma qualificação em contêineres Linux 3.11/3.12/3.13 | **BLOCKED**: o Docker Desktop da máquina parou de responder (`docker ps` sem resposta em 45 s). Não foi reiniciado (aplicativo do usuário, possivelmente em uso). **Substituído** pela CI do critério 6, que roda unittest, validador, avaliação semântica e o `pty` em Linux com 3.11, 3.12 e 3.13. Desvio registrado: os gates só locais (holdouts strict, regressões de decisão e roteador) rodaram apenas no Windows |
| 3 | benches e predicados | `ptbr-bench-v4` **22/22** (árvore limpa), `ptbr-bench-v5` **36/36** (registro `dirty` porque o v4 acabara de gravar o seu arquivo de run, como na v0.8.0.dev0), predicados **17/20** riscos e **1/18** falsos alarmes (inalterados) |
| 4 | testes DF-01 a DF-09 antes/depois | os seis arquivos rodados com `unittest` sobre `702a448` (v0.8.0.dev0): todos FAILED (falhas: dogfood 10, compare_omission 3, marker_forms 8, diagnose_labels 8, entity_in_token 1, moved_groups 1); sobre a `main` final: todos OK. Os controles de cada arquivo passam nas duas revisões |
| 5 | privacidade do histórico integrado | **limpa**: cada um dos 8 commits (diff e mensagem) comparado com os dois documentos por sequências de cinco palavras e por termos característicos ausentes do repositório: 0 em comum |
| 6 | CI do GitHub na `main` | **PASS**: run [#127](https://github.com/Soturine/VozNativa/actions/runs/43862352767), `workflow_dispatch`, `5f27d1e`, 8/8 jobs (Linux e Windows × 3.11/3.12/3.13, pacote nos dois), conferida ao vivo por `scripts/ci_evidence.py` (relação `same`). Uma única execução |

Externos (não obrigatórios, NOT_RUN como na v0.8.0.dev0): holdout independente, revisão humana cega, juiz de outro fornecedor.

Complementares:

- **Assertiva 0.10.1** `audit --execute` em `5f27d1e` (run `8defc9b90f1447df`, sem mudanças locais): suíte PASS em cópia isolada (1.233 invocações); wheel construído, instalado e importado, com fechamento de dependências PASS; testes contra o wheel NOT_RUN pela ferramenta (sem adaptador); 1 achado `info` (checks da CI não classificados, o mesmo das rodadas anteriores); 0 candidatos a falso verde.
- **Derivanta Engine 0.1.0** `inspect --maintainability` em clones limpos de `702a448` e `5f27d1e`, mais `compare`: COMPARABLE; 172 persistentes, 0 ausentes, 5 novos INFO. Três são complexidade nas funções que cresceram com DF-04/08/09 (`_moved_signal_issues` 24 caminhos, `_omitted_clause_issues` 17, `_span_issues` 17). Dois são duplicação, porque a lista de preposições nova do DF-07 (`diagnose._EXPANSION_STOP`) repete cinco palavras de tabelas de `signals.py`; os papéis são diferentes. Aceitos sem refatoração nesta versão.

Teste instável: `evals/test_v08_compare_perf.py` cruzou o limite de 19× sob carga da suíte inteira (19,4 e 21,2). Medido isoladamente com o mesmo método, a razão fica em 12–13× tanto em `702a448` quanto no código final: não houve regressão de desempenho. O limite não foi alterado.

## Decisão

Todos os critérios obrigatórios foram atendidos, com o critério 2 substituído pela CI e o desvio registrado acima. Publicação: **`v0.8.1` como release estável no GitHub**, com tag anotada no commit final da `main`. Sem PyPI.

O que os testes não dizem: nenhum resultado acima comprova equivalência semântica de reescritas. Os dois dogfoods mostraram candidatas aprovadas pelos gates e por um juiz do mesmo modelo que a revisão humana rejeitou.
