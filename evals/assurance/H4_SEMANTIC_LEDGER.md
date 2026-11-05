# H4 — reavaliação do Semantic Ledger (2026-11-05)

Instrumento: `scripts/experiments/ledger_probe_h4.py`, 29 pares escritos pelo desenvolvedor por categoria (não é holdout nem evidência independente). Resultados: `evals/experiments/ledger_probe_h4.before.json` (código `bbdc5d6`) e `.after.json`.

**Antes: 19/29** (o arquivo `before` registra 18/29 porque a expectativa de "cresceu duas vezes" estava errada no probe: "duas vezes" também é "em duas ocasiões", e bloquear é a leitura segura; corrigida antes do `after`). **Depois: 25/29.**

## Corrigido (com regressão em `evals/semantic/cases.jsonl`)

| Categoria | Defeito | Correção | Casos |
|---|---|---|---|
| dias da semana | "começo segunda" → "começo na segunda" era `fail` (falso vermelho, `bv2-li-02`); "segunda" → "terça" sem preposição passava (falso verde) | dia da semana em posição temporal, sem artigo antes nem substantivo depois | `wd-201`…`wd-205` |
| equivalência temporal | "14h" → "2 da tarde" era `fail` | "N da manhã/tarde/noite/madrugada" vira hora (tarde/noite +12) | `tm-201`, `tm-202` |
| `ho-007` / valores | "triplicar a receita" inserido só aparecia como marcador | verbos multiplicadores são valor (`x2`/`x3`/`x4`); "dobrar" só sem objeto logo depois ("dobrou a esquina" fica fora) | `mul-201`…`mul-203`; `ho-007` passa estrito (24/24), caso congelado intacto |
| troca de papéis com substantivos comuns | "o cliente processou a empresa" → "a empresa processou o cliente" passava | `role_or_order_swapped` (major): mesmas palavras de conteúdo trocando de lado em torno de uma palavra única; mudança de voz (passiva com "pelo") fica com a verificação de papéis existente | `role-201`…`role-203` |
| ordem temporal | "primeiro a Ana revisa, depois o Caio aprova" invertido passava | mesma verificação, com `antes`/`depois`/`primeiro`/`até`/`desde` como pivôs | `ord-201` |

Controle de falso vermelho da verificação nova: dispara em 14 casos das suítes, **todos** com bloqueio esperado, e em **nenhuma** das 90 saídas reais de modelo do `ptbr-bench-v2`.

## Limitações que ficam (casos `known_limitation`)

- **Pronomes / correferência** (`lim-201`): "porque ela estava atrasada" → "porque estava atrasada" muda quem se atrasou; sem resolução de correferência não há sinal determinístico confiável.
- **Troca entre frases** (`lim-202`): predicados trocados entre duas frases alinhadas por entidade; o alinhamento por sobreposição de radicais pareia as frases erradas.
- **Inflexão diferente** (`lim-203`): "teste antes de publicar" → "publique antes de testar"; o radical grosseiro separa "publique" de "publicar". Afrouxar o radical para pegar isso aumentaria colisões em todo o `compare`.
- Já cobertos e confirmados pelo probe: causalidade (direção, correlação → causa), adições, omissões de condição e exceção, mudanças pragmáticas de modalidade e compromisso.

## Extração estruturada de claims

Não implementada. As três limitações acima são exatamente o que extração de claims (sujeito, predicado, objeto, tempo, condição) resolveria, mas com modelo, custo e não determinismo. Proposta para experimento controlado (fora do gate): rodar um extrator nas 29 pares deste probe e nas saídas do benchmark v2, comparar com o `compare` atual e medir detecções novas x falsos vermelhos, como foi feito com NLI e spaCy (`evals/experiments/`). Não é requisito da v0.5.
