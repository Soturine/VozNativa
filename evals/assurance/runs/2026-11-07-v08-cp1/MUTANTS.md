# CP1: mutantes aplicados à mão na correção de GAP-01 e GAP-09

Harness: cópia completa da árvore (`git ls-files -co --exclude-standard`) num diretório temporário, um mutante por cópia, `python -B -m unittest` de `test_v08_integrity`, `test_hardening_cp5b`, `test_document_rewrite`, `test_document_plan_oracles`. Ferramenta: script do agente (AGENT_OBSERVED, não ENGINE_EXECUTED), Windows 10, CPython 3.12.6, 2026-11-07.

**Incidente de método:** a primeira rodada copiou só `voznativa/`, `evals/`, `references/` e `scripts/`. O módulo `test_hardening_cp5b` lê `.github/workflows/ci.yml` na importação e quebrou, então os sete mutantes "morreram" por erro de importação, não pelos testes. A rodada válida copia a árvore inteira e começa por um controle sem mutação, que precisa passar.

| Mutante | Arquivo | Resultado |
|---|---|---|
| Controle (sem mutação) | — | OK (precisa passar) |
| A autorização volta a vir do campo do plano | `document.py` | morto (7 falhas) |
| Sem a checagem "plano declara ≠ chamador autorizou" | `document.py` | morto (1 falha) |
| `reassemble` ignora o chamador e usa o plano | `document.py` | morto (3 falhas) |
| Retomada sem checagem de estrutura | `engine.py` | morto (1 falha) |
| Retomada sem o gate da unidade (sempre `needs_judgment`) | `engine.py` | morto (1 falha) só depois do teste `test_resumed_unit_outcome_follows_the_gate`; na primeira rodada sobreviveu, porque o caso de valor trocado era mascarado pelo `compare` global |
| `max` invertido (o desfecho mais leve vence) | `engine.py` | morto (2 falhas) |
| Registro reconstruído a partir do dado retomado, não do plano | `engine.py` | morto (1 erro) |

Equivalente argumentado e removido: a primeira versão tinha `claimed = prior["outcome"] if prior["outcome"] in {"needs_judgment", "needs_review"} else gate`. Trocar por `claimed = prior["outcome"]` não muda nada, porque `max` por `OUTCOME_RANK` já faz `accepted` (1) perder para qualquer desfecho de gate (≥ 2). A condição foi retirada do código.
