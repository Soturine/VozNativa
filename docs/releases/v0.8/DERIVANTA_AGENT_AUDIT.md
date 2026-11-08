# Auditoria agent-led com o Derivanta sobre o VozNativa v0.8 (CP15)

> Estado: registro do CP15, 2026-11-08. Evidência `AGENT_OBSERVED`: o agente é esta sessão do Claude Code (modelo
> Claude Opus 5.5, extensão do VS Code, Windows 10, CPython 3.12.6), seguindo o `SKILL.md` real do Derivanta Engine
> e o workflow `skill/workflows/AUDIT.md` do Framework na revisão fixada. O mesmo agente construiu, inspecionou e
> julgou: nada aqui é revisão independente.

## Ferramentas e escopo

- **Engine:** `Soturine/Derivanta-Engine`, branch da PR #3 (`acd6ca3`, que contém a `main` `17fa564` e a correção
  DEF-VN-07 da rodada anterior), mais a correção DEF-VN-08 feita nesta rodada. Gate próprio (`tools/verify.py`:
  lint, format, types, tests, conformance) com exit 0 nesta máquina antes do uso e depois da correção.
- **Framework:** `Soturine/Derivanta` em `218761d` (a revisão fixada pelo Engine), clonado só para leitura; o
  `evaluate` confirmou as fontes fixadas como `UNCHANGED`.
- **Alvo:** clones limpos do VozNativa em `98094ac` (início do CP15) e `b2d106f` (depois das correções). A
  inspeção é estática: o Engine não executa nada do repositório.
- **Entrada de rastreabilidade:** gerada da matriz da v0.8 por
  `scripts/experiments/v08_cp15_traceability_input.py` (classes de teste viram um link por método; arquivo sem
  classe vira link de presença).

## O que o Engine viu e o que foi feito

Em `98094ac`: 174 candidatos (102 complexidade, 68 duplicação, 2 definições sem referência, 2 requisitos sem
link); 35 novos desde `ecf3dd2` (última inspeção registrada, h07). Rastreabilidade: 25 requisitos com link
estático, 0 quebrados, 2 sem link por desenho (V08-019 é medido por execução registrada; V08-020 é NOT_RUN).

| Achado | Julgamento | Ação | Reteste |
|---|---|---|---|
| `standards.DECISIONS` e `evaluation.AXES` nomeados só na definição | verdadeiro: vocabulário declarado que nada impõe; um nome errado passaria calado | testes exigem igualdade com o que `resolve()` emite (as 7 decisões alcançadas, a partir de `standards.VERIFICATION`) e com o que um run mede; renomear uma decisão ou um eixo faz os testes falharem (controle negativo) | `compare` com o mesmo escopo: ABSENT |
| Campos do plano escritos duas vezes nos dois retornos de `rewrite_document` | verdadeiro: risco de o registro do caminho de timeout divergir | um dono (`_PLAN_IN_RECORD`), conferido nos dois caminhos no teste que alcança o timeout da validação global | ABSENT |
| Dois arquivos de teste da v0.8 sem requisito (`test_v08_doc_validator`, `test_v08_evidence_paths`) | verdadeiro: o trabalho do CP12 não tinha linha na matriz | linhas V08-028 e V08-029; V08-030 registra esta rodada | 0 arquivos da v0.8 sem requisito |
| Duplicação entre a projeção de campos do `standards list` na CLI e a lista `REQUIRED` | contextual: mesmas palavras, papéis diferentes | nenhuma | — |
| Listas de contrações iguais em `events`, `signals` e `features` | contextual: cada uma serve a uma regra; unificar acoplaria `events` a uma tabela privada de `signals` | nenhuma | — |
| Complexidade alta em funções novas (`standards.validate_entry` 49 caminhos, `events.frames` e `compare._event_issues` 34, `standards.resolve` 32) | motor de refatoração, não defeito; as funções de eventos acabaram de ser mutadas no CP14 | backlog v0.9 | — |

`compare` de `98094ac` contra `b2d106f` com a mesma entrada: COMPARABLE, 3 ABSENT (os corrigidos), 171
PERSISTING, 2 NEW: complexidade do script de conversão (aceita: ferramenta de experimento) e uma duplicação do
próprio teste novo, que repetia a tupla `VERIFICATION`; o teste passou a iterar `standards.VERIFICATION`.

## O que o agente conferiu além do Engine (workflow AUDIT, passos 8 a 13)

- **Documentos ↔ código:** todo caminho do repositório escrito como código nos documentos vigentes existe (7
  ocorrências conferidas uma a uma: cache ignorado, referência `arquivo:linha`, registro pendente do CP16, padrões e
  histórico). O validador do CP12 só confere links Markdown; esta checagem não virou teste (lista curta, revisada).
- **Requisitos ↔ implementação:** todo caminho de código da matriz da v0.8 existe, e todo módulo novo da v0.8
  (`arms`, `axes`, `evaluation`, `events`, `onboarding`, `rubric`, `standards` e os dados) é dono de um requisito.
- **Ciclos de import:** nenhum ciclo entre imports de topo; contando os imports dentro de funções, há dois ciclos,
  ambos anteriores à v0.8 e resolvidos por import tardio (`ptbr`/`router`/`temporal`; `corpus.connectors`/
  `corpus.tei`, com comentário no código). Registrado como dívida de arquitetura (V08-GAP-28).
- **Determinismo:** a suíte inteira com `PYTHONHASHSEED=1` e `4242` deu os mesmos 903 desfechos, teste a teste.
- **Release (`evaluate`):** a tarefa declarada (publicar a v0.8.0.dev0 como pre-release) foi roteada para
  `skill/workflows/RELEASE.md`, com segurança e revisão independente como secundários, e a alegação "qualidade
  semântica validada de forma independente" saiu `ENG-F-UNSUPPORTED-CLAIM`, como deve: a v0.8 não faz essa
  alegação. O checklist de `RELEASE.md` orienta o CP16–CP18.

## Erro do próprio dogfood

O commit de evidência do CP14 (`98094ac`) foi enviado sem rodar o gate depois de gravar os dumps do Cosmic Ray
(`.jsonl` sob `evals/`); o validador e um teste os liam como casos e falhavam. Achado no início do CP15, corrigido
em `5b8a678` (registros de ferramentas em `evals/assurance/runs/` são evidência, não casos), com os bytes e hashes
dos registros intactos.

## Retorno para o Derivanta

- **Engine (PR #3, `docs/voznativa-v05-dogfood-intake-20261105`):** DEF-VN-08 corrigido em `32b89ec` (erro de
  entrada de rastreabilidade e de triagem sem local nem motivo; mensagem enganosa para `/` no fim), três testes que
  falham em `acd6ca3`, `tools/verify.py` exit 0; rodada registrada em `0cc48b3`
  (`docs/audits/external/VOZNATIVA_V05_FEEDBACK.md`). Push só na branch da PR, cujo push não dispara a CI do
  Engine (só `push` na `main`); nenhum run novo apareceu.
- **Sugestões sem patch:** passe de grafo de imports com ciclos como candidatos; dica de `--basetemp` no
  `verify.py` quando o diretório temporário padrão não é gravável.
- **Framework:** nada proposto. O Framework não recebe push (pull request dispara a CI dele). Um desencontro de
  hash que o agente leu no `OWNER_MAP.md` era erro do agente: o mapa já diz que os hashes são normalizados de CRLF.

## Limites

- Uma sessão de agente; o "desafio independente" do passo 13 do workflow AUDIT não existiu: os controles
  negativos e as releituras são do mesmo agente.
- A inspeção é estática; o que roda foi coberto pelos gates do VozNativa e pela Assertiva no CP14.
- As 102 marcas de complexidade e 66 de duplicação restantes não foram julgadas uma a uma.
