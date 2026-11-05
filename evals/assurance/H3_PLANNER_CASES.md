# H3 — os dois casos restantes da suíte de decisão (2026-11-05)

Suíte `evals/decision/cases.jsonl` (congelada, escrita pelo desenvolvedor): 28/30 em `4af90ac`. Nenhum limiar foi mudado; nenhum caso foi editado.

## `dc-021` — `transform` (esperado `edit`)

- Texto: pedido curto em estilo de chat ("vc pode me mandar o relatório? a diretoria pediu pra hoje"), 11 palavras; dicas `channel=email`, `register=professional-natural`.
- O planejador detecta três destinos diferentes do texto (gênero e canal e-mail x WhatsApp inferido; registro `professional-natural` x registro de chat) e decide `transform`, escopo `document`, com uma troca pontual na frase 0 e a frase 1 mantida.
- O README define como mudança de destino "canal ou gênero diferente do texto, registro, público, perfil de voz". Pelo contrato documentado, `transform` é a decisão correta.
- **Determinação: erro de expectativa** (o caso contradiz o requisito escrito). Consequência prática nula para a chamada do modelo: o modelo é chamado nos dois casos; muda só o escopo declarado num texto de duas frases.
- Ambiguidade real registrada: `--genre` serve tanto para descrever o texto quanto para pedir um destino. Se o mantenedor decidir que "é um e-mail mal escrito" deve ser `edit`, a mudança é de contrato (um campo separado para o gênero de origem), não de limiar.

## `dc-029` — `edit` (esperado `no_change`)

- Texto corporativo de 209 palavras escrito como texto natural, com dois achados fracos legítimos pela definição dos padrões: `nominal_chain` ("implementação da validação", o exemplo da própria justificativa do padrão) e `pleonasm` ("repetir de novo").
- Regra: `weak_needed_for_edit = max(2, ceil(palavras / 150))` = 2; dois fracos → `edit`, escopo `local`: o modelo recebe 2 de 17 frases para mudar e 15 para manter.
- Nem a classificação (os dois achados correspondem aos padrões) nem a inferência estão erradas. O que o caso questiona é a **política**: dois achados fracos reais em ~200 palavras justificam chamar o modelo? O limiar `/150` não foi calibrado com dados; trocá-lo por `/100` deixaria o caso verde e seria ajuste ao caso.
- **Determinação: INCONCLUSIVE — limiar sem calibração.** Fica como falha conhecida em `evals/qualification/expectations.json`. O que decide: medir, com textos naturais de pessoas reais, a taxa de mudanças desnecessárias e se leitores preferem a versão editada (benchmark v3, CP7, e revisão humana cega).
