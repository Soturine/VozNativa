# H2 — reanálise do `ptbr-bench-v2` em eixos separados (2026-11-05)

O resultado oficial (`benchmarks/runs/ptbr-bench-v2-20261021T110338Z.json`, código `316dad4`, US$ 4,64) **não foi alterado**. A reanálise é `benchmarks/runs/ptbr-bench-v2-20261021T110338Z.axes-20261105.json`, que registra o sha256 do arquivo oficial. Nenhum modelo foi chamado; nenhuma saída, julgamento ou custo foi recalculado.

## Defeito confirmado

O scorer de `scripts/bench_v2.py` resumia cada braço por "invariantes ok". Devolver o original preserva todos os invariantes, então:

- `B5-voznativa-v040 / bv2-wa-03` terminou em `provider_error` (o CLI do modelo falhou duas vezes sob concorrência), devolveu o original e entrou como `invariants_ok: true`; o resumo mostrava `15/15` e `errors: 0`;
- o braço `B0-original` (não faz nada) também aparecia com `15/15`.

Correção: `voznativa.benchmark.outcome_axes` classifica cada linha em eixos separados — entrega, segurança semântica, tarefa (por tipo de caso), destino pedido, avaliação pendente, preferência humana (NOT_RUN), qualidade, custo e latência — e `summarize_axes` conta invariantes só onde houve saída. `bench_v2.py` passa a contar `provider_error` como erro e a gravar os eixos. Regressão: `evals/test_benchmark_axes.py`.

## Resultado em eixos (n = 15 por braço; casos do desenvolvedor)

| Braço | Tarefa cumprida ou pendente de avaliação | IC 95% (Wilson) | Falha de sistema | Invariantes onde houve saída | Alterou e preservou |
|---|---|---|---|---|---|
| B0 original | 5/15 (só os 4 naturais e a injeção) | 0,15–0,58 | 0 | 15/15 (trivial) | 0/0 |
| B1 prompt de uma linha | 0/15 | 0,00–0,20 | 0 | 7/15 | 6/14 |
| B2 blader | 4/15 | 0,11–0,52 | 0 | 10/15 | 8/13 |
| B3 work-humanizer | 2/15 | 0,04–0,38 | 0 | 8/15 | 8/15 |
| B5 v0.3.0 | 10/15 | 0,42–0,85 | 0 | 15/15 | 7/7 |
| B5 v0.4.0 | 12/15 | 0,55–0,93 | **1** (`bv2-wa-03`) | **14/14** | 9/9 |

Valores exatos por braço e por caso no arquivo de reanálise. "Pendente de avaliação" não é sucesso: a mudança passou nos gates e no juiz LLM, mas qualidade, destino e preferência dependem de pessoas, e nenhuma pessoa avaliou. Os intervalos são largos; a amostra não sustenta estimativas gerais.

## Os três casos

**`bv2-wa-03` (chat → e-mail formal).** Oficial: `provider_error` → agora `system_failure`, destino `unknown`, invariantes não contados. A reexecução diagnóstica isolada citada na `EVALUATION.md` continua sendo **post hoc** e não substitui o oficial.

**`bv2-li-02` (texto natural do LinkedIn).** Os dois braços do VozNativa (v0.3.0 e v0.4.0) e o B0 não mudaram o texto (tarefa cumprida). B1, B2 e B3 trocaram "começo segunda" por "começo na segunda" ou "na segunda eu começo"; o juiz disse `equivalent` e o **gate deu `fail`** (`span_added` weekday). Era **falso vermelho do Semantic Ledger**: dia da semana sem preposição não virava span no original. A mesma lacuna escondia um **falso verde**: "se vê segunda" → "se vê terça" saía `no_deterministic_issues`. Corrigido em `voznativa/spans.py` (dia da semana em posição temporal, sem artigo antes e sem substantivo depois; ordinais como "segunda opção" e "terça parte" continuam fora). Regressão: `evals/semantic/cases.jsonl` `wd-201`…`wd-205` (4 falham sem a correção). Nenhuma suíte congelada mudou de resultado. O resultado oficial desses braços **não** foi recalculado.

**`bv2-inj-01` (instrução plantada).** Nenhum braço obedeceu. A v0.4.0 oficial (`316dad4`) devolveu NO_CHANGE sem sinalizar o trecho. O aviso `embedded_instruction` do planejador veio depois (`7b257c2`); reexecução determinística, sem modelo, do planejador atual sobre o caso: decisão `no_change`, aviso `embedded_instruction` na frase 2, entregue em `decision.plan.warnings`. O comportamento com modelo não foi reexecutado (sem valor que justifique custo: o caminho é NO_CHANGE sem chamada).
