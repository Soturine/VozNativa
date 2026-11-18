# Robustez semântica, diagnóstico e termos técnicos (v0.9 CP4)

Continuação de [`../v0.8/SEMANTICS.md`](../v0.8/SEMANTICS.md). Objetivo: diminuir falsos verdes com números e nomes intactos sem criar falsos vermelhos em excesso, e diagnosticar erros gramaticais de alta confiança que o planner não via.

## Método

1. **Conjuntos congelados antes das regras** (`e5b134c`, publicado antes de qualquer regra): `evals/v09/semantic/{development,holdout}.jsonl` (pares original × candidata: qualificador, cenário, classe de evento, estado do fato, aspecto, 1ª pessoa, e controles de paráfrase) e `evals/v09/diagnose/{development,holdout}.jsonl` (erros e controles), com sha256 em `evals/v09/MANIFEST.json`. `scripts/v09_prospective_eval.py` recusa rodar se um arquivo mudar.
2. **O development** foi lido enquanto as regras eram escritas; **o holdout** foi rodado uma vez, depois das regras fixadas, e o resultado é registrado como saiu.
3. **Limite declarado:** o mesmo agente escreveu os conjuntos e as regras, na mesma sessão; o holdout não é independente e mede conformidade com a especificação, não qualidade em textos reais.

## Resultados

| Conjunto | `v0.8.1` (`17d1f10`) | v0.9 (regras fixadas) |
|---|---|---|
| semântico development: riscos sinalizados | 4/31 | **31/31** |
| semântico development: falsos alarmes | 7/20 | **4/20** |
| semântico holdout: riscos sinalizados | 4/18 | **18/18** |
| semântico holdout: falsos alarmes | 1/10 | **2/10** (oficial); 1/10 após correção pós-holdout |
| diagnóstico development: erros / falsos alarmes | 0/11 / 0/11 | **11/11** / 0/11 |
| diagnóstico holdout: erros / falsos alarmes | 0/6 / 0/6 | **6/6** / 0/6 |
| amostra de predicados (`evals/predicates`, congelada na v0.7) | 17/20, 1/18 | **19/20**, 1/18 |
| `ptbr-bench-v4` / `ptbr-bench-v5` | 22/22 / 36/36 | ver `EXECUTION_STATE.md` |

Correções feitas **depois** do holdout (o holdout deixa de ser prospectivo para elas):

- o padrão de atribuição na passiva incluía "avisados pelo", mas "avisou" não é marcador de atribuição na ativa; a assimetria criou um falso alarme (`h-c09`). A passiva agora só conta para verbos cuja ativa conta;
- as perífrases aspectuais deixaram de ser listas de frases e passaram a exigir infinitivo, porque "voltou **ao** depósito" casava com "voltou a" (achado pelo conjunto congelado de eventos da v0.8, `ed-26`, não pelo holdout).

Os quatro falsos alarmes restantes no development são anteriores à v0.9: modalidade conservadora ("é obrigatório" → "precisam", "passou a permitir" → "passou a ser possível"), "o total de pedidos" → "os pedidos" (omissão de "total"), e troca de papéis em nominalização (V08-GAP-19).

## O que mudou no `compare`

Todos os sinais novos são `major` (revisão humana), nunca `critical`; nenhum deles aparecer não prova equivalência.

| Código | Quando | Dados |
|---|---|---|
| `qualifier_dropped` / `qualifier_changed` / `qualifier_added` | um qualificador operacional some, vira o contraste ou aparece: automático/manual, obrigatório/opcional, parcial/total, provisório/definitivo, preliminar/final, estimado/confirmado, presencial/online, gratuito, interno/externo, oficial, exclusivo, frequência (diário … anual), cenário (físico/em campo × simulado/emulado/virtual/teórico/offline) | `voznativa/data/semantic_classes.json` (`qualifier_sets`); "manual", "final", "total", "oficial" depois de determinante, preposição ou número são lidos como substantivo |
| `event_changed` | a classe de evento do verbo some e a candidata traz outra (assinar × receber, aprovar × analisar, identificar × tratar, executar × planejar, instalar × verificar…) | `event_classes`; sinônimo da mesma classe não muda nada, verbo fora das classes se abstém |
| `fact_status_changed` | a candidata acrescenta um verbo de intenção, tentativa, pedido ou proposta que o original não tinha ("concluiu" → "pretende concluir", "pagou" → "solicitou o pagamento") | `status_governors` |
| `aspect_changed` | "passou a", "começou a", "voltou a" + infinitivo aparecem ou somem | padrões em `markers_pt_br.json` |
| negação cessativa | "deixou de"/"parou de" + infinitivo contam como negação: "deixou de enviar" = "não envia mais"; "deixou de enviar" → "envia" é negação removida (crítico) | padrões; "não deixe de", "não podemos deixar de" são expressões fixas |
| atribuição na passiva com agente | "informou os clientes" = "os clientes foram informados pela gerente" (V08-GAP-20); sem o agente continua atribuição perdida | padrão |
| `predicate_missing` / `_replaced` | um verbo da mesma classe ("solicitou" → "pediu") não é mais ação perdida | classes |

Também: formas irregulares que a morfologia por regras não analisa (*ver, ler, obter, propor, requerer, querer*); e, quando os dois textos têm o mesmo número de frases, o par na mesma posição é comparado a partir de similaridade 0,25 (frases com a maioria das palavras trocadas eram puladas).

Retiradas antes do holdout por falsos vermelhos nas suítes congeladas: "real"/"reais" (moeda depois de numeral por extenso: `fr-008`, `num-103`, `h3-num-003`) e "em produção" ("para produção", caso de saída 3 da CLI).

## Diagnóstico gramatical

`diagnose` reporta, como `formal_error` de alta confiança, com controles:

| Tipo | Exemplo | Correção | Controles que não disparam |
|---|---|---|---|
| `plural_agreement` | "os resultado", "algumas calçada" | sugestão (o plural não é gerado por regra) | pronome oblíquo ("ele os viu", "a diretora as recebeu"), invariáveis em -s/-x ("os ônibus"), numerais, anglicismos, rótulos de uma letra (DF-06) |
| `impersonal_fazer` | "Fazem dois anos que…" | `auto_fix` → "Faz" | "fazem dois trabalhos" |
| `existential_haver` | "Houveram muitas…", "haviam vários…" | `auto_fix` → "Houve", "havia" | "haviam chegado" (auxiliar) |
| `crase` | "à partir", "à pé", "à organizar" | `auto_fix` → "a" | "à mulher", "à vista", "à feira" |

Em texto informal viram `possible_contextual_error` (sugestão); em texto literário, `literary_license`. O **planner** passa a tratar esses erros como edição pontual da frase: antes, um texto sem achado de `patterns` ficava `no_change` e o modelo nem era chamado (segundo dogfood). Regência ("assistiu o jogo") ficou fora: "assistir o paciente" é correto e a regra não separa os sentidos com alta confiança.

## Termos técnicos e siglas

- **V09-GAP-10:** um texto que usa três ou mais termos distintos do domínio técnico passa a ser desse domínio, qualquer que seja o gênero; os termos deixam de virar sugestão de troca (antes, num parágrafo acadêmico de computação: 4 sugestões e decisão `edit`; agora nenhuma). Um termo isolado continua sugerido; jargão de negócio em texto acadêmico continua sugerido (suíte `pt-206`).
- **V09-GAP-11:** sigla com letras internas ("Radio Detection And Ranging (RADAR)", "Sound Navigation And Ranging (SONAR)") é reconhecida como definição, lendo a sigla como prefixos das palavras em ordem; sem soletração possível continua sem definição.

## Limites (CP4.7)

Correferência, causalidade entre frases distantes, troca de papéis sem relação lexical (V08-GAP-19) e evento diferente fora das classes listadas continuam fora do alcance das regras. Os conjuntos de classes são autorais (E0), pequenos e sem calibração externa; um verbo fora deles se abstém. Nenhum resultado desta página certifica uma reescrita: o melhor estado sem juiz continua `no_deterministic_issues`, e a revisão humana dos dogfoods já rejeitou candidatas que passaram nos gates.
