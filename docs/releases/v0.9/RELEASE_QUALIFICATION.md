# Qualificação da v0.9.0

> Critérios congelados no CP0 ([`PLAN.md`](PLAN.md)), antes de qualquer mudança de comportamento. Resultados preenchidos com o que de fato rodou; o que não rodou fica NOT_RUN. Três coisas nunca somadas: **implementação**, **qualificação local** e **qualificação externa** (CI conferida ao vivo, holdout de outra pessoa, revisão humana cega).

Revisão qualificada: **`39cc6d8`** (`main`, merge da release e da correção de caminhos curtos). Os commits seguintes mudam só documentação; a equivalência do código é conferida por `scripts/ci_evidence.py` e pela CI final registrada em [`EXECUTION_STATE.md`](EXECUTION_STATE.md).

## Resultados

| # | Critério | Resultado |
|---|---|---|
| R1 | `qualify.py --scope release`, Windows 10, CPython 3.12.6, árvore limpa | **PASS** em `39cc6d8`: validador, unittest (1.025: 1.023 PASS, 2 skips com motivo), semântica dev 77/77, holdouts safety e strict, decisão 28/30, roteador 15/16, códigos de saída, gatilhos da CI, pacote (sdist → wheel → venv limpo → smoke → suíte contra o wheel). Veredito INCOMPLETE só pelos externos (`review:pty` só POSIX, holdout independente, revisão humana cega), como na v0.8.1 |
| R2 | CPython 3.11 no Windows; Linux 3.11/3.12/3.13 | Windows 3.11.18: gates locais **PASS** em `4b9b198` (1.024 testes; o código de `39cc6d8` difere só pela correção de caminhos curtos, coberta pela CI). Linux local: **BLOCKED** (Docker sem resposta; não reiniciado). **Substituído** pela CI (R6), que roda unittest, validador, semântica e `pty` em Linux 3.11/3.12/3.13. Desvio: holdouts strict e regressões de decisão e roteador rodaram só no Windows |
| R3 | benches e predicados sem piora; congelados byte-idênticos | `ptbr-bench-v4` **22/22**, `ptbr-bench-v5` **36/36**, predicados **19/20** e **1/18** (v0.8.1: 17/20 e 1/18), em worktree de `4b9b198`; suítes congeladas sem diferença desde `17d1f10` |
| R4 | correções com teste que falha antes e passa depois | cada correção tem teste de defeito que falha em `17d1f10` (ou no código anterior à correção) e controles que passam nas duas: CP4 (11 testes de defeito, 5 controles), GAP-24 (relação do juiz), V09-DF-01 (houveram), leitor TEI, caminhos curtos; registros por CP em [`EXECUTION_STATE.md`](EXECUTION_STATE.md) |
| R5 | privacidade | **PASS**: gate em cada push (patch de cada commit) e no intervalo inteiro `17d1f10..4b9b198` (15 commits): nada em comum com os 4 documentos privados nem com os termos sensíveis. Com `--tree`, a árvore inteira só tem as fixtures falsas e os caminhos antigos já presentes na árvore da v0.8.1 (V08-GAP-29); nenhum novo |
| R6 | CI do GitHub no commit final da `main` | run #129 em `8cf27c8`: **FAIL** (3 jobs Windows: `TEMP` 8.3 do runner; um defeito real do gate de privacidade). Corrigido em `e645559`, reproduzido e verificado localmente. Run **#130** em `39cc6d8`: **8/8 PASS**, `workflow_dispatch`, conferido ao vivo (relação `same`). A CI final do commit da tag está em [`EXECUTION_STATE.md`](EXECUTION_STATE.md) |
| R7 | funcionalidade declarada testada; integração real só com execução real | estados por integração em [`INTEGRATIONS.md`](INTEGRATIONS.md): provider real e host agent-led real executados; adapter HTTP declarado como testado com servidor falso; Codex, Gemini, modelo local e Emulate não declarados como verificados |
| R8 | nenhum falso verde P1 conhecido sem correção ou risco aceito | V09-GAP-01..04 e GAP-24 corrigidos com conjuntos congelados e provas reais; o que resta (verbos e qualificadores fora das classes, correferência, V08-GAP-19) está no registro de gaps como PARTIAL ou ACCEPTED_RISK e nas notas |
| R9 | desempenho | `scripts/perf_compare.py` em `39cc6d8`: 17.600 palavras **5,48 s** de CPU (v0.8.1: 5,84 s), razão 800/100 blocos 11,7× (v0.8.1: 14,4×); teste de tempo com método novo e limite 19× inalterado |
| R10 | versão e artefatos | `0.9.0` em `voznativa/__init__.py`, `SKILL.md`, `.claude-plugin/plugin.json`, README (teste `test_readme`); smoke confere CLI, pacote e metadados iguais. Artefatos construídos da revisão exata da tag e conferidos depois do download: [`EXECUTION_STATE.md`](EXECUTION_STATE.md) |

## Complementares

- **Assertiva 0.10.1** `audit --execute`: três execuções em clones limpos; as duas primeiras acharam um defeito latente (leitura de 500 MB no leitor TEI) e dois erros do agente (commit sem o arquivo de que dependia; expectativa de exceção ampla), todos corrigidos; a terceira, em `bd62d60`: suíte PASS (1.398 invocações), 0 candidatos a falso verde. Detalhes: [`ASSURANCE.md`](ASSURANCE.md).
- **Derivanta Engine 0.1.0**: COMPARABLE com a v0.8.1; 25 novos INFO triados; duas duplicações reais corrigidas.

## Externos (não obrigatórios)

| Item | Estado |
|---|---|
| holdout independente | NOT_RUN: ninguém além do agente escreveu conjuntos |
| revisão humana cega | NOT_RUN: sem revisores cadastrados |
| juiz de outro fornecedor | NOT_RUN: um único fornecedor disponível |
| Codex, Gemini CLI | NOT_RUN: não instalados |
| modelo local real | NOT_RUN: execução do servidor baixado negada pelo controle de permissões da sessão |
| Emulate ao vivo | BLOCKED: sem chave |
| macOS | NOT_RUN: sem ambiente |
| renderização de DOCX no Word/LibreOffice | NOT_RUN: nenhum dos dois na máquina |

## Decisão

Os critérios obrigatórios R1–R10 foram atendidos, com R2 substituído pela CI para Linux (desvio registrado acima, mesma política da v0.8.1). Publicação: **`v0.9.0` como release estável no GitHub**, tag anotada no commit final da `main`. Sem PyPI.

O que os testes não dizem: nenhum resultado acima comprova equivalência semântica de reescritas. Os conjuntos e as regras foram escritos pelo mesmo agente; o juiz usado nos dogfoods era de outro modelo, mas do mesmo fornecedor.
