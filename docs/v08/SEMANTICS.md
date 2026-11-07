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
