# CP6: mutantes aplicados à mão nas regras de eventos

Harness: `scripts/experiments/v08_cp6_mutants.py` (cópia completa da árvore por mutante, controle sem mutação primeiro, `python -B -m unittest evals.test_v08_events`). AGENT_OBSERVED, Windows 10, CPython 3.12.6, 2026-11-07.

| Mutante | Arquivo | Resultado |
|---|---|---|
| Controle (sem mutação) | — | OK |
| Artigo "a" solto sempre tratado como preposição | `events.py` | morto (4 falhas) |
| Palavras de tempo não puladas ("às 14h", "à noite") | `events.py` | morto (1) |
| "para" + infinitivo tratado como destinatário | `events.py` | morto (1) — **sobreviveu na primeira rodada**: o teste usava uma frase em que o infinitivo era o próprio verbo do quadro; ganhou o teste `test_purpose_after_a_transfer_verb_is_not_a_recipient` |
| Auxiliar tomado como agente ("vou mandar") | `events.py` | morto (1) |
| Sem tolerância à flexão do destinatário | `compare.py` | morto (1) |
| Converso sinalizado sem exigir o mesmo sujeito | `compare.py` | morto (1) |
| Checagem de destinatário desligada | `compare.py` | morto (3) |
| Sinais novos como críticos | `compare.py` | morto (2) |
| Checagem de troca dá/recebe removida | `compare.py` | morto (1) |

Escopo: só as regras novas do CP6. O resto de `compare.py` segue com a cobertura de mutação da v0.7 (faixa 429–583) e o restante como lacuna (V08-GAP-03, CP14).
