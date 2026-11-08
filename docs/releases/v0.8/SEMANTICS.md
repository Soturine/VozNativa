# Semântica de eventos na v0.8 (CP6, V08-GAP-04)

O que o gate passou a ver, como foi medido e o que continua invisível.

## O que mudou

| Sinal | Severidade | O que detecta | Onde |
|---|---|---|---|
| `recipient_dropped` | major | o destinatário de um verbo de transferência ("ao cliente", "para a diretoria") sumiu da frase alinhada e das vizinhas | `compare._event_issues`, `voznativa/events.py` |
| `recipient_changed` | major | o destinatário virou outro | idem |
| `agent_recipient_swapped` | major | quem dá e quem recebe trocaram, com o mesmo verbo | idem |
| `event_converted` | major | o verbo virou o inverso com o **mesmo sujeito** ("A rede comprou" → "A rede vendeu"); com os papéis trocados ("A comprou de B" → "B vendeu para A") nada é sinalizado | idem, pares em `voznativa/data/verb_relations.json` |
| `polarity_flipped` (existente) | critical | novas classes de antônimos: contratar/demitir, exportar/importar, ligar/desligar, deferir/indeferir em formas finitas | `voznativa/data/markers_pt_br.json` |

Decisões:

- **Nada novo é crítico** além das classes de antônimos, que usam o mecanismo crítico já existente. Os quadros vêm de regras e se abstêm no que é ambíguo; a decisão final é do juiz ou de uma pessoa.
- **Conversos não são antônimos.** comprar/vender, enviar/receber, emprestar/tomar trocam papéis; tratá-los como antônimos reprovaria a paráfrase legítima com papéis trocados (controle `ed-27` e `eh-22`).
- **Prefixo só quando seguro.** `contrat*` pegaria "contrato" e `import*` pegaria "importante": essas classes usam formas explícitas (testado).
- **O que não é destinatário:** hora ("às 14h", "à noite"), finalidade ("para avaliar"), locuções ("a partir", "ao longo"), e o artigo do objeto ("entregou **a** planilha"; "a" só é preposição depois do objeto e antes de nome próprio).
- **Agente:** o núcleo antes do verbo, nunca um auxiliar ("vou mandar"), clítico ou preposição; voz passiva lê o agente de "por/pelo/pela".

## Medição

Conjuntos escritos e congelados (hash em `evals/events/MANIFEST.json`) **antes** de qualquer código do CP6, pelo mesmo autor do engine: não são independentes. Registros: `evals/v08/runs/events-before-53d48fc.*` e o run depois da regra.

| Conjunto | Antes (`53d48fc`) | Depois |
|---|---|---|
| desenvolvimento (28: 15 riscos, 13 controles) | riscos 7/15, falso alarme 2/13 | riscos 14/15, falso alarme 2/13 |
| holdout prospectivo (24: 12 riscos, 12 controles), **uma execução** | riscos 5/12, falso alarme 3/12 | riscos 11/12 (IC95% 64,6%–98,5%), falso alarme 3/12 |
| amostra de predicados da v0.7 (congelada) | 16/20, falso alarme 1/18 | 17/20 (`pr-17`, destinatário omitido), falso alarme 1/18 |
| suítes semânticas, decisão, roteador, `ptbr-bench-v4`/`-v5` | PASS, 22/22, 36/36 | sem mudança |

Os falsos alarmes restantes (2 no desenvolvimento, 3 no holdout) vêm de checagens anteriores (`role_or_order_swapped` com complemento deslocado, `attribution_changed` na passiva com "pela escola"), não das regras novas. Não foram afrouxadas.

Mutação: 10 mutantes aplicados à mão nas regras novas (cópia completa da árvore, controle sem mutação), todos mortos por `evals/test_v08_events.py`; um sobreviveu na primeira rodada (finalidade "para" + infinitivo) e ganhou teste. Registro: `evals/assurance/runs/2026-11-07-v08-cp6/MUTANTS.md`.

## Limites conhecidos

- **"assinou" → "recebeu"** (`ed-12`): verbos que não são antônimos nem conversos, só eventos diferentes. Regras não separam isso de um sinônimo; continua `predicate_replaced` (info). Exige léxico semântico medido ou juiz.
- **`eh-03`** ("Transferi R$ 500,00 para o meu irmão" → sem o irmão): perdido no holdout. Não ajustei a regra depois de ver o holdout; uma correção precisa de conjunto novo congelado antes.
- Correferência, elipse do destinatário ("entreguei-lhe"), sujeito oculto: sem quadro, sem sinal.
- Os quadros cobrem só verbos de transferência e pares conversos listados; outros eventos continuam nas checagens anteriores.

## Causas dos erros restantes (diagnóstico, sem ajuste retroativo)

Investigação feita depois da execução única do holdout, a pedido do mantenedor. **Nenhum caso dos conjuntos congelados foi usado para mudar regra ou léxico.** Cada causa vira gap pendente; corrigir exige um conjunto novo, congelado antes do código.

| Caso | Sintoma | Camada | Causa comprovada | O que resolveria | Gap |
|---|---|---|---|---|---|
| `eh-03` ("Transferi R$ 500,00 para o meu irmão" → sem o irmão) | recipient não detectado | **extração** (morfologia) | `morph.verbs` não devolve "Transferi": no início de frase, terminação fraca (-i) exige sujeito antes ou artigo depois, e o próximo token é "R$"; sem verbo não há quadro. Além disso, "para" é lido como o verbo *parar* | aceitar 1ª pessoa do pretérito com terminação forte quando o lema é de transferência, medido contra o ouro UD (falso positivo de verbo) | V08-GAP-18 |
| `ed-12` ("assinou" → "recebeu") | evento diferente não detectado | **conhecimento lexical** | não são antônimos nem conversos; regras não separam evento diferente de sinônimo | recurso lexical de relações entre verbos com licença clara, ou juiz | V08-GAP-04 (aberto) |
| `ed-19`, `eh-16` (destinatário deslocado na frase) | falso alarme `role_or_order_swapped` | **correspondência** (checagem anterior à v0.8) | `_crossing_issues` compara a ordem das palavras dos dois lados de um pivô; mover o complemento ("entregou aos fornecedores o cronograma") parece troca | consultar os quadros de evento: mesmo agente, mesmo destinatário e mesmo objeto → não é troca | V08-GAP-19 |
| `ed-27`, `eh-22` (converso com papéis trocados) | falso alarme `role_or_order_swapped` | **representação de papéis** | a mesma checagem por ordem não sabe que "A comprou de B" = "B vendeu para A"; as regras do CP6 já não sinalizam | idem, com os pares conversos de `verb_relations.json` | V08-GAP-19 |
| `eh-17` ("A escola informou… aos pais" → "Os pais foram informados pela escola…") | falso alarme `attribution_changed` | **léxico de marcadores** | "informou" conta como marcador de atribuição; a passiva "informados pela" não é reconhecida como a mesma atribuição | marcador de atribuição na passiva com agente da passiva, medido nas suítes de atribuição | V08-GAP-20 |

Nada disso é crítico: os falsos alarmes acima pedem revisão (`major`) e não reprovam.
