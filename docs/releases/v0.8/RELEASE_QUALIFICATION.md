# Qualificação da v0.8.0.dev0

> Estado: registro do CP16–CP18, preenchido com os resultados reais à medida que rodam; um item que não rodou diz
> NOT_RUN. Três coisas diferentes, nunca somadas: **implementação** (código e testes que passaram),
> **qualificação local** (`scripts/qualify.py` numa revisão, em plataformas nomeadas) e **qualificação externa**
> (CI do GitHub conferida ao vivo por SHA, holdout de outra pessoa, revisão humana cega, provider real).

## Revisão candidata

Em andamento: a primeira candidata (`d4b0ed1`) falhou no Linux com Python 3.13 (abaixo); a correção está em
`9a847f9` e a matriz roda de novo sobre a revisão que vai para a `main`.

## Qualificação local por plataforma

`scripts/qualify.py --scope local` em árvore limpa. Linux: contêineres `python:3.x-slim` (Docker 28.5.1, kernel
WSL2) com um clone do repositório dentro do contêiner; Windows 10 com o CPython 3.12 da máquina (é o único
instalado: o 3.11 do Windows fica para a CI, V08-GAP-10).

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

- **Derivanta Engine** na revisão de código `d4b0ed1` contra o reteste do CP15 (`b2d106f`), mesma entrada de
  rastreabilidade: COMPARABLE, 0 novos, 1 ausente (a duplicação do teste novo, corrigida), 172 persistentes;
  rastreabilidade 28 com link, 2 sem link por desenho, 0 quebrados.
- **Assertiva**: pendente sobre a revisão candidata final.

## Externos

| Item | Estado |
|---|---|
| CI do GitHub na revisão da `main` | NOT_RUN (CP17) |
| Holdout independente | NOT_RUN: precisa de outra pessoa |
| Revisão humana cega | NOT_RUN: nenhum revisor registrado |
| Provider real (R1–R4 do CP9) | NOT_RUN: aguardando autorização de custo |
