# Mutação de `voznativa/temporal.py` — v0.7.0 (CP14)

Ferramenta: Cosmic Ray 8.7.0 (venv próprio), executado diretamente, numa cópia de `git archive` da revisão (o arquivo mutado é byte a byte o mesmo nas duas rodadas). Comando de teste: `evals.test_temporal evals.test_community_and_stuffing evals.test_mutation_gaps_v06 evals.test_slang_v07 evals.test_known_gaps_v06` (+ `evals.test_mutation_gaps_v07` na 2ª rodada). Windows 11, CPython 3.12.

| Rodada | Revisão | Mutantes | Mortos | Sobreviventes | Em assinaturas/anotações | Executáveis |
|---|---|---|---|---|---|---|
| 1 | `a4426e4` (temporal.py após o CP6) | 875 | 613 | 262 | 198 | 64 |
| 2 | `7d2382b` (+ 13 testes de `test_mutation_gaps_v07`) | 875 | **633** | **242** | 198 | **44** |

Mesmo conjunto de chaves (operador, ocorrência, linha) nas duas rodadas; 20 mutantes passaram de sobrevivente a morto e nenhum no sentido inverso.

## Assinaturas e anotações (198)

Mutações em anotações de tipo (`str | None` → `str + None` etc.). Sob `from __future__ import annotations` elas não são avaliadas no caminho executável. Isso só é equivalência **para o caminho executável**: nada no repositório chama `typing.get_type_hints` nem `inspect.signature` sobre `temporal` (verificado por busca), mas uma ferramenta externa que avalie as anotações veria uma anotação inválida. Classificação: equivalente no contrato atual; não equivalente para introspecção.

## Executáveis restantes (44), um a um por classe

| Classe | Mutantes (linha × n) | Argumento | Estado |
|---|---|---|---|
| Identidade em vez de igualdade (`==`/`!=` → `is`/`is not`) | 71, 91, 109, 149, 226, 229, 235, 243, 249, 262, 303 (12) | os operandos são literais de string/int pequenos internados pelo CPython no mesmo módulo, ou valores vindos desses literais; o resultado é igual **no CPython**. Equivalência dependente de implementação, não da linguagem | equivalente (CPython) |
| Ordem em vez de igualdade sobre conjunto fechado | 103 (`level != "E0"` → `>`: níveis E0–E4), 109 e 303 (`status != "active"` → `>`: active, dated, fading, obsolete — todos ≥ "active", só "active" é igual), 226 `>=` (sense ∈ {slang, other_sense}: só "slang" ≥ "slang"), 229 `<=` ({unknown, pre_reform_orthography}), 232 `>=` ({context, form}), 249 `>=` (4 sentidos: só "slang" ≥ "slang") (7) | o conjunto de valores possíveis é fechado e validado (`validate_lexicon`, `observe`); para cada valor o resultado coincide | equivalente (conjunto fechado) |
| Tamanho do cache | 142 (2) | `lru_cache(maxsize)` muda desempenho, não resultado | equivalente |
| Ordem de alternação das formas | 121 (1) | o padrão de cada entrada é `(?<!\w)(?:f1|f2…)(?!\w)`; com as duas guardas de fronteira, a ordem das alternativas não muda o que casa | equivalente |
| Sinal da chave de ordenação | 339 `-x` → `~x` (1) | `~x = -x-1`: mesma ordem | equivalente |
| Contagem padrão e `> 0` → `!= 0` | 99 (2), 275 (4), 359 (4) | só diferem com atestação sem `count` (a validação exige o campo) ou com contagem **negativa**, que a validação **não** proíbe | lacuna aceita: invariante de dados não imposto (backlog: validar `count >= 0`) |
| Fronteira não testada | 48 (2): `STALE_AFTER_DAYS` 548 → 547/549; 188 (8): a 2ª ocorrência de `end + 1` em `_hyphen_compound` (`plain[end + 1]`), que só difere com hífen seguido de não-letra ("de boa- valeu"); 267 (1): grupo da regex de época; 339 `not x` (1): ordem das razões agregadas quando não ordenadas por contagem | comportamento real sem oráculo | **lacuna real, risco baixo**, não corrigida nesta rodada |

Resumo dos 44: 22 equivalentes com argumento (12 dependentes do CPython), 10 dependentes de um invariante de dados não imposto, 12 lacunas reais de baixo risco. Nenhum foi declarado equivalente pelo número da linha: o sobrevivente da linha 188 que parecia morto pelo teste `"tá de boa-"` era a outra ocorrência de `+` na mesma linha (verificado aplicando o mutante à mão: a 1ª ocorrência levanta `IndexError` com esse teste e morre).

## Outros módulos

Não houve mutação de `router.py`, `processing.py`, `morph.py`, `diagnose.py`, `document.py` e `engine.rewrite_document` nesta rodada (custo: cada módulo tem centenas de mutantes e a suíte relevante leva segundos por mutante). Estado: NOT_RUN, com prioridade para `document.py` e `compare._moved_signal_issues` na próxima rodada.
