# Qualificação da v0.8.0.dev0

> Estado: registro do CP16–CP18, preenchido com os resultados reais à medida que rodam; um item que não rodou diz
> NOT_RUN. Três coisas diferentes, nunca somadas: **implementação** (código e testes que passaram),
> **qualificação local** (`scripts/qualify.py` numa revisão, em plataformas nomeadas) e **qualificação externa**
> (CI do GitHub conferida ao vivo por SHA, holdout de outra pessoa, revisão humana cega, provider real).

## Revisão candidata

**`8db60ea`** (`dev/v0.8.0`). A primeira candidata (`d4b0ed1`) falhou no Linux com Python 3.13 (abaixo); a
correção está em `9a847f9`. Os commits depois de `8db60ea` mudam só registros de evidência e documentos de estado;
a CI do CP17 roda na `main` que os contém, e `scripts/ci_evidence.py` confere a equivalência de código.

## Qualificação local por plataforma

`scripts/qualify.py --scope local` em árvore limpa. Linux: contêineres `python:3.x-slim` (Docker 28.5.1, kernel
WSL2) com um clone do repositório dentro do contêiner; Windows 10 com o CPython 3.12 da máquina (é o único
instalado: o 3.11 do Windows fica para a CI, V08-GAP-10).

### `8db60ea` (candidata)

| Plataforma | Python | unittest | demais gates locais | pacote (sdist → wheel → venv → smoke → suíte contra o wheel) | `review:pty` | Veredito |
|---|---|---|---|---|---|---|
| Windows 10 | 3.12.6 | 904: 902 PASS, 2 skips | PASS | PASS (900 PASS, 4 skips contra o wheel) | NOT_RUN (POSIX) | INCOMPLETE (só o `pty`) |
| Linux (contêiner) | 3.11.17 | 904: 903 PASS, 1 skip | PASS | PASS (901 PASS, 3 skips) | PASS | PASS |
| Linux (contêiner) | 3.12.15 | 904: 903 PASS, 1 skip | PASS | PASS (901 PASS, 3 skips) | PASS | PASS |
| Linux (contêiner) | 3.13.16 | 904: 903 PASS, 1 skip | PASS | PASS (901 PASS, 3 skips) | PASS | PASS |

Skips, todos com motivo registrado: pipeline POSIX e link simbólico sem privilégio (Windows), junção de diretório
(só Windows), o teste de ponta a ponta do `bench_v3` e a checagem de links da documentação contra o wheel (a árvore
do wheel não tem o pacote-fonte).

### `d4b0ed1` (primeira candidata, substituída)

| Plataforma | Python | unittest | demais gates locais | pacote (sdist → wheel → venv → smoke → suíte contra o wheel) | `review:pty` | Veredito |
|---|---|---|---|---|---|---|
| Windows 10 | 3.12.6 | 903: 901 PASS, 2 skips | PASS | PASS | NOT_RUN (POSIX) | INCOMPLETE |
| Linux (contêiner) | 3.11.17 | PASS | PASS | PASS | PASS | PASS |
| Linux (contêiner) | 3.12.15 | PASS | PASS | PASS | PASS | PASS |
| Linux (contêiner) | 3.13.16 | 1 FAIL (`test_cli_reference_matches_the_parser`) | PASS | FAIL (o mesmo teste contra o wheel) | PASS | **FAIL** |

Causa da falha no 3.13: a partir dele o `argparse` quebra a linha de `usage:` e o `...` da lista de subcomandos em
outros pontos; `docs/guide/CLI.md`, gerado no 3.12, divergia só em quebra de linha. A CI roda 3.13 no Linux e no
Windows: a única execução final teria falhado. Corrigido em `9a847f9` (o gerador junta essas quebras; teste
alimenta as duas formas e exige o mesmo resultado; a referência confere em 3.11, 3.12 e 3.13).

## Reconciliação das auditorias com o código final

- **Derivanta Engine** na candidata `8db60ea` (e antes em `d4b0ed1`, mesmo resultado) contra o reteste do CP15 (`b2d106f`), mesma entrada de
  rastreabilidade: COMPARABLE, 0 novos, 1 ausente (a duplicação do teste novo, corrigida), 172 persistentes;
  rastreabilidade 28 com link, 2 sem link por desenho, 0 quebrados.
- **Assertiva 0.10.1** (`audit --execute`, run `9844f785e7714a50`) em clone limpo de `8db60ea`: suíte PASS numa
  cópia isolada (1.177 aprovados, 2 pulados); 0 pistas de falso verde; wheel `voznativa-0.8.0.dev0`: build,
  install, import e fechamento de dependências PASS, testes contra o wheel NOT_RUN pela ferramenta (sem adaptador;
  o gate de pacote acima roda a suíte contra o wheel). O detector local `UNCHECKED_ALL` (patch 0001) aponta só as 2
  pistas rejeitadas no CP14.
- Mutação: a do CP14 (`events.py`, 367 de 575 mortos) foi feita em `69e4c9b`; `events.py` não mudou depois
  (conferido com `git diff 69e4c9b 8db60ea -- voznativa/events.py`, vazio).

## Benchmarks e amostras (revisão `8db60ea`)

| Instrumento | Resultado |
|---|---|
| `ptbr-bench-v4` (congelado na v0.6) | 22/22 (igual à v0.7) |
| `ptbr-bench-v5` (congelado na v0.7) | 36/36 (igual à v0.7); o registro diz `dirty` porque o `bench_v4` tinha acabado de gravar o seu arquivo de run no clone |
| Amostra de predicados (`scripts/predicate_eval.py`) | 17/20 riscos sinalizados, 1/18 falso alarme (v0.7: 16/20 e 1/18) |
| Semântica dev + holdouts | PASS nos gates `semantic:*` de todas as plataformas |
| Conjuntos de eventos congelados | desenvolvimento 14/15 riscos, 2/13 falso alarme; holdout prospectivo 11/12, 3/12 (sem mudança desde o CP6) |

Todos escritos pelo lado do desenvolvimento: nenhum é evidência independente.

## Externos

| Item | Estado |
|---|---|
| CI do GitHub na revisão da `main` | NOT_RUN (CP17) |
| Holdout independente | NOT_RUN: precisa de outra pessoa |
| Revisão humana cega | NOT_RUN: nenhum revisor registrado |
| Provider real (R1–R4 do CP9) | NOT_RUN: aguardando autorização de custo |
