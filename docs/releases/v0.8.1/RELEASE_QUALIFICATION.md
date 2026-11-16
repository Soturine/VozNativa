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

Preenchidos no commit de evidência que segue a qualificação.
