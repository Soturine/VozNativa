# Manutenção na v0.10.5 (R12)

> Instrumento: **Derivanta Engine** (inspeção estática, nunca executa o projeto), versão da branch do PR #6 (`a9eb371`, editável). Comandos: `derivanta-engine inspect <pasta> --maintainability --format json` e `derivanta-engine compare`. Saídas fora do repositório.

## Base × candidato, comparável

A primeira comparação inspecionou duas worktrees com nomes diferentes (`base`, `cand2`) e o Engine respondeu `DIFFERENT_TARGET` com **zero** achados em todas as categorias. Isso não é "nada mudou": o Engine identifica o alvo pelo caminho e se recusou a comparar. Refeita do jeito comparável, **a mesma pasta** inspecionada em `v0.10.0` (`e274379`) e depois em `8f5ffc1`:

| | Complexidade | Duplicação | Total |
|---|---|---|---|
| v0.10.0 | 134 | 79 | 213 |
| v0.10.5 (`8f5ffc1`) | 142 | 85 | 227 |
| `compare` | 8 NEW | 7 NEW, 1 ABSENT | 212 PERSISTING, `COMPARABLE` |

Achados do Engine são candidatos (`HYPOTHESIS`, `INFERRED`), não defeitos. Triagem dos 15 novos:

| Achado | Onde | Decisão |
|---|---|---|
| 6 duplicações `DUPLICATE_TABLE` | `scripts/v0105_*.py`, `scripts/experiments/claude_cost_provider.py`, `scripts/v010_arms.py`, `scripts/ci_evidence.py` | **Aceito.** São listas curtas de literais: argumentos de `rewrite` (`--provider-env minimal …`) e o prefixo das variáveis do host (`CLAUDE_CODE_`). Os testes repetem os comandos de propósito, como oráculo independente do harness; unificar acoplaria teste e harness. |
| 1 duplicação em `scripts/ci_evidence.py` (NEW) e 1 (ABSENT) | lista `EVIDENCE_PATHS` | **Aceito.** É o registro dos caminhos de evidência (V105-GAP-03); o teste `test_v08_evidence_paths.py` lista os mesmos caminhos para conferir o verificador. |
| 7 complexidades no harness | `scripts/v0105_*.py` | **Aceito.** Scripts de campanha, executados poucas vezes; os defeitos achados neles (falha de cota gravada como resultado) foram corrigidos com teste de comportamento, não com refatoração. |
| 1 complexidade em `voznativa/compare.py` | detecção de negação e de frase apagada (V105-GAP-05/06) | **Risco aceito nesta rodada.** A função cresceu com as duas correções; cada caminho novo tem teste de defeito e controle. Refatorar no fim da rodada, sem ganho comportamental, arriscaria as próprias correções. Fica para a v0.11. |

Ausência de candidato não é prova de ausência de código morto: o Engine lê 265 arquivos-fonte e teste, mas não resolve imports dinâmicos, entrypoints nem reflexão.

## Código morto

Nenhuma remoção nesta rodada. O replay da v0.10 já tinha zerado os falsos "não referenciados" do VozNativa (PR #6 do Engine, classes de teste herdadas); nenhum candidato novo de código não referenciado apareceu.

## Ciclos de import

Os quatro ciclos herdados (`community↔packs`, `ptbr↔router`, `router↔temporal` e `compare→patterns→project→router→ptbr`) fecham **só** por imports dentro de funções; nenhum ciclo em nível de módulo. Remover exigiria mover funções públicas entre módulos sem defeito observado. Decisão: manter e travar. `evals/test_v0105_import_graph.py` falha se um ciclo de nível de módulo aparecer e importa cada membro sozinho num interpretador novo (commit `1082b07`).

## Harness

| Defeito | Achado por | Correção |
|---|---|---|
| Falha de cota/provider gravada como resultado; a retomada pulava o arquivo | campanha live do candidato (83 execuções de T05–T12 contaminadas pelo limite de 5 h da conta) | `provider_failed()` no `v0105_live_arms.py`: a execução vai para `failed/`, nunca vira resultado, e o harness para após 3 falhas seguidas; campanha refeita do zero na mesma revisão |
| Juiz sem resposta virava linha com notas vazias | revisão do juiz após o defeito acima | `JudgeUnavailable` no `v0105_judge.py`: nada é gravado e a retomada repete |
| QA do Observatory aprovava página com seções vazias | o mantenedor abriu a página | QA reescrito: cada seção precisa ter tantos itens quanto os dados (53 verificações) |
| Oráculo "linhas reunidas" contava lei e diálogo como benignos | revisão do harness (V105-GAP-10) | corrigido e remedido |

## Continuação (19/11)

Derivanta Engine na mesma pasta, v0.10.0 × `69b81d8`: `COMPARABLE`, 212 persistentes, 20 novos, 1 ausente. Os 5 novos em relação à triagem anterior estão nos scripts do Observatory: 4 de complexidade (aceitos, scripts de campanha) e 1 de duplicação **real e com divergência**. A lista de braços estava copiada do harness e não conhecia a ablação nova; o gerador passou a importá-la do harness (V105-GAP-20).

Caminhos frágeis revistos: o fluxo de documentos resolvia `--work` relativo ao `cwd` do CLI (V105-HARNESS-04, corrigido com `resolve()`); `PIP_NO_BUILD_ISOLATION=0` e a pasta temporária do pytest são do ambiente desta máquina e estão documentados em `ASSURANCE_RECIPROCAL.md`; nenhum código do VozNativa depende deles.
