# Resultados da prova de fogo (v0.10.5)

> Protocolo, critérios e congelamentos: [`PLAN.md`](PLAN.md) (CP0, antes de qualquer mudança de produto). Corpus e direitos: [`CORPUS_AND_LICENSES.md`](CORPUS_AND_LICENSES.md). Tudo isto pode ser explorado no [VozNativa Observatory](../../observatory/index.html), gerado a partir de `evals/v0105/observatory_data.json`.
>
> **O que vale e o que não vale.** Textos reais em PT-BR, sem textos sintéticos no lugar de famílias ausentes. Escritor Haiku; juiz Sonnet do mesmo fornecedor (`MODEL_JUDGED`, dependente). **Nenhum revisor humano** (`NOT_HUMAN_VALIDATED`). Famílias sem fonte lícita (mensagens, e-mail, documentação técnica, saúde, criativo, fala regional): nenhuma afirmação vale para elas.

## 1. Campanha offline: 427 textos, 1.632 perturbações com resposta conhecida

Cada item real recebeu cópias alteradas de propósito, e o oráculo é a própria transformação, não o engine. Mesma máquina, mesmo corpus, v0.10.0 (`e274379`) × v0.10.5 (código final, com GAP-13/14/15). A primeira execução da v0.10.5 (18/11, 18:56) era de antes dessas correções e foi refeita.

| Perturbação | Esperado | v0.10.0 | v0.10.5 |
|---|---|---|---|
| Negação acrescentada | sinalizar | 307/311 | **311/311** |
| Negação removida | sinalizar | 221/239 | **236/239** |
| Frase do meio apagada | sinalizar | 212/231 | **228/231** |
| Contraste virou consequência | sinalizar | 186/186 | 186/186 |
| Número trocado | sinalizar | 155/160 | **159/160** |
| Exceção apagada | sinalizar | 53/53 | 53/53 |
| Linhas reunidas | **não** sinalizar | 37/47 | **46/47** |
| Unicode decomposto (NFD) | **não** sinalizar | 405/405 | 405/405 |

Mudanças de sentido que passaram sem sinal: **46 → 7**. Falsos alarmes em mudança benigna: **10 → 1**. Nenhum tipo piorou. "Número trocado" caiu de 5 para 1 sem sinal com a correção de dígitos colados a letras (V105-GAP-13), achada nesses mesmos casos.

Por família (acertos/casos, v0.10.0 → v0.10.5): literário 997 → 1033 de 1040; acadêmico 305 → 311 de 311; institucional e jurídico 98 → 99 de 99; jornalístico 54 → 57 de 57; jornalístico (blog) 35 → 36 de 36; redes sociais 36 → 37 de 38; avaliações de consumidor 51 de 51 nas duas.

**Falso alarme em texto publicado (R9).** Itens com `ERROR_CONFIRMED`: 2 → 2 (os mesmos dois, `plural_agreement`). Planos `edit`: 18 → 18. Não piorou.

**Roteamento (achado, sem correção nesta rodada; V105-GAP-18).** O `route` devolve `unknown` em 260 dos 427 textos, nas duas versões; das 35 leis, 3 saem `legal`; dos 90 acadêmicos, 4 saem `academic`. `unknown` é abstenção conservadora, não erro, mas o roteamento automático quase não reconhece gênero em texto real. O contexto declarado pelo usuário (`--attr genre=…`) continua sendo o caminho confiável.

**Desempenho (R13).** `compare` em 17.600 palavras, melhor de 2 medições intercaladas na mesma sessão (base, candidato, base, candidato), código final: 5,45 s → 5,66 s de CPU (**1,04×**; teto 1,15×). A medição de 18/11 (0,98×) era de antes do GAP-15, que mexe em `spans`, e foi refeita. O CPU total das duas campanhas offline não é comparável: rodaram em sessões e cargas diferentes.

## 2. Braços live: 12 tarefas × 3 repetições × 4 braços × 2 versões

288 execuções, mesmo modelo escritor, ordem dos braços sorteada por repetição, **zero** execuções sem resposta do provider nos números (as 83 contaminadas pelo limite de cota foram descartadas e a campanha refeita; V105-HARNESS-02).

### Decisão de editar ou não (expectativa congelada no CP0)

| Braço | Decisão certa | Edição indevida | Faltou editar | Custo |
|---|---|---|---|---|
| LLM direto (controle, sem VozNativa) | 12 → 11 de 21 | 9 → 10 | 0 → 0 | US$ 0,06 → 0,04 |
| Skill no host | 14 → **19** de 21 | 7 → **2** | 0 → 0 | US$ 0,36 → 0,42 |
| Engine | 12 → **17** de 21 | 0 → 0 | 9 → **4** | US$ 0,00 → 0,10 |
| Engine sem contexto (ablação) | 12 → 12 | 0 → 0 | 9 → 9 | US$ 0,00 → 0,04 |

Na v0.10.0 o engine **nunca chamou o modelo** nas 12 tarefas (`no_change` em 36/36): o modo pedido era ignorado sem achado do detector (V105-GAP-08). Os 4 "faltou editar" restantes do engine são T06/T07 (lei em linguagem simples): os gates reprovaram as candidatas e o engine devolveu o original, o comportamento seguro. Parte desses vermelhos era falsa (V105-GAP-15, corrigido depois da campanha; ver §4), parte era real ("só podem ser aplicadas", "sem possibilidade de recurso").

**A ablação não mede conhecimento.** "Engine sem contexto" remove os atributos **e o pedido do usuário**; sem saber o que fazer, o modelo responde `NO_CHANGE` em 36/36. O efeito medido é o do pedido. O conhecimento foi selecionado em 18 das 36 execuções do engine (`kn-contraste-consequencia` em 18, `kn-concessao` em 3), mas nenhum experimento desta rodada isola o efeito dele. **TaskContext e conhecimento: capacidade funcional, ganho não demonstrado.**

### Juiz cego (R6: ganho só se aparecer em ≥ 2 de 3 repetições)

| Braço | Fidelidade (+/−/=) | Atende ao pedido | Naturalidade |
|---|---|---|---|
| LLM direto (controle) | +2 −4 =6 | +1 −3 =8 | +1 −1 =10 |
| Skill no host | +3 −0 =9 | +1 **−5** =6 | +1 **−4** =7 |
| Engine | +0 −0 =12 | **+6** −0 =6 | **+4** −0 =8 |
| Engine sem contexto | =12 | =12 | =12 |

O controle mostra o ruído do próprio critério: só por variação do modelo, o LLM direto teve 6 tarefas fora do empate em fidelidade.

- **Engine: ganho**, acima do ruído e sem nenhuma perda: atende ao pedido em 6 tarefas e naturalidade em 4, com fidelidade estável. Um erro crítico apontado pelo juiz (T05 rep. 3), numa saída que o engine **não** aceitou sozinho (`needs_judgment`).
- **Skill: troca, não ganho** (`NO_MEASURABLE_GAIN` em qualidade; V105-GAP-16). Mais fidelidade e menos edições indevidas, menos atendimento ao pedido nas tarefas de edição. Detalhes em [`SKILL_LIVE_DOGFOOD.md`](SKILL_LIVE_DOGFOOD.md).

### Holdout interno (6 tarefas congeladas no CP0, rodadas uma vez no fim)

| | Skill v0.10.0 | Skill v0.10.5 | Engine v0.10.0 | Engine v0.10.5 |
|---|---|---|---|---|
| Decisões certas | 1/4 | 3/4 | 3/4 | 4/4 |
| Skill ativada | 1/6 | 6/6 | — | — |

n = 1 por célula: direção igual à do desenvolvimento, `INCONCLUSIVE` como prova isolada.

## 3. Documentos inteiros (R8)

| Fluxo | Texto | Resultado | Oráculo independente |
|---|---|---|---|
| Lei inteira (LGPD, 12.259 palavras, `POLISH`) | 28 unidades (V105-GAP-14: antes, 1) | 20 sem mudança, 2 pedem julgamento, 1 devolvida ao original; 23 chamadas, US$ 0,07, 170 s | 80 artigos na mesma sequência; 0 número perdido ou acrescentado; proporção de palavras 1,00 |
| Capítulos de romance (Machado, 3.116 palavras, `ADAPT`) | 6 unidades | 2 para revisão humana, 4 devolvidas ao original | 0 número perdido; proporção 1,00 |
| DOCX e PDF (gerados de texto em domínio público) | DOCX 20 parágrafos; PDF 4 páginas | DOCX: só o parágrafo pedido mudou, tabela mantida, `docx_check` PASS, original intocado. PDF: recall de palavras 100%, anotação gravada (o PDF não é editado), original intocado | — |

Limites: PDF é extração e anotação, não edição; DOCX renderizado no Word: `NOT_RUN`.

## 4. Correção feita depois da campanha (V105-GAP-15)

Achada na leitura dos vermelhos do engine em T06/T07: depois de `§ 3°` ou de um inciso sem ponto (`I -`), a primeira palavra do dispositivo era lida como nome próprio. Teste vermelho na v0.10.0, controle verde, replay em todas as 144 reescritas reais da campanha: 21 mudam, todas em T06/T07, todas pela retirada do falso `span_*`. A campanha live **não** foi refeita com essa correção; os números da §2 são da revisão `8f5ffc1`.

## 5. Custo

US$ 3,26 medidos (preço de API equivalente informado pelo `claude` CLI; a conta usa login, sem chave de API), de um teto de US$ 10: braços live US$ 1,23 (US$ 0,20 perdidos na campanha abortada), holdout US$ 0,13, juiz US$ 1,04, documentos US$ 0,19, sessões do Derivanta Framework (Sonnet) US$ 0,65, piloto US$ 0,01.

**Continuação (19/11):** US$ 1,74 a mais: holdout prospectivo (180 execuções) US$ 0,94, juiz US$ 0,72, sondagens de permissão US$ 0,08, sessão do Framework instalado US$ 0,01. **Total da rodada: US$ 5,01** de US$ 10.

## 6. O que não rodou

Revisão humana cega, holdout feito por terceiro, juiz de outro fornecedor, modelo local, Codex/Gemini, macOS, Word: `NOT_RUN`. Sem eles, nenhuma afirmação aqui é sobre "escrita melhor para pessoas".

## 7. Continuação: holdout prospectivo e ablação válida (19/11)

**Por que existe.** As 12 tarefas live, as 6 do holdout interno e os casos T05/T06/T07/T08 orientaram correções e viraram desenvolvimento e regressão. A correção do GAP-15 e as mudanças da continuação (D-03, `SKILL.md` revisada) vieram depois da campanha de §2. Antes de medir o código final, congelei um **holdout prospectivo** novo (commit `69b81d8`, `evals/v0105/prospective_tasks.json`): 10 tarefas, 2 repetições, autores, obras e fontes disjuntos do desenvolvimento. São crônicas de Lima Barreto, conto de João do Rio, telegrama de 1897 de Euclides da Cunha e ensaio de Júlia Lopes de Almeida (domínio público, Wikisource), documentação do Python em PT-BR (PSF License; não publicada aqui) e notícia e título da Agência Brasil (termos da EBC: reprodução com fonte, sem fim comercial; não publicados aqui). Preparado pelo mesmo agente: **interno, não independente**. O hash do manifesto aparece como `2585d43c…` no registro de congelamento, calculado sobre os bytes com CRLF, e como `3094ca64…` no Observatory, calculado com fim de linha normalizado. O conteúdo é o mesmo; a prova é o commit.

**Fontes que não deram.** planalto.gov.br recusou a conexão (nenhuma lei nova no holdout; não contornado). Gutenberg em manutenção. Sem fonte lícita: WhatsApp e e-mail reais, redação escolar, publicidade, descrição de produto. `NOT_RUN` para essas famílias.

**Execução.** 180 execuções, nenhuma falha de provider, US$ 0,94; juiz cego Sonnet (mesmo fornecedor), 20/20 linhas, US$ 0,72.

### Decisão de editar e qualidade (16 decisões com expectativa fixa; juiz em 20 execuções por linha)

| Braço | Decisão certa | Edição indevida | Faltou editar | Fidelidade | Pedido (só tarefas que exigem edição, n = 8) | Naturalidade | Erro crítico |
|---|---|---|---|---|---|---|---|
| LLM direto (controle) | 8/16 | 8 | 0 | 3,25 | 3,88 | 4,10 | **7**/20 |
| Skill v0.10.0 | 9/16 | 7 | 0 | 3,95 | 4,38 | 4,05 | 4/20 |
| Skill v0.10.5 inicial (`8f5ffc1`) | 10/16 | 6 | 0 | 4,45 | 4,12 | 4,20 | 0/20 |
| Skill v0.10.5 final (`69b81d8`) | 11/16 | 5 | 0 | 4,40 | 3,88 | 3,95 | 2/20 |
| Engine v0.10.0 | 6/16 | 2 | 8 | 4,85 | 1,00 | 3,40 | 1/20 |
| Engine v0.10.5 final | **10/16** | 2 | **4** | 4,85 | 1,88 | 3,50 | 0/20 |

Uso do fluxo pela Skill: ativada em 5 → 11 → 12 de 20; algum passo antes de escrever em 0 → 5 → 9; `compare` em 2 → 7 → 9.

**Por que o pedido só nas tarefas que exigem edição.** O juiz lê "revise" como "mude": nas tarefas cuja expectativa congelada é devolver igual, a Skill que devolve o original leva 1–2 em "atende ao pedido". Comparar esse eixo em todas as tarefas favorece quem edita.

**Leitura.**
- **Engine: ganho confirmado num conjunto novo.** Mais decisões certas, metade das edições faltantes, atendimento ao pedido maior, fidelidade igual e nenhum erro crítico. Continua conservador demais nas tarefas de edição (V105-GAP-23).
- **Skill: sem ganho mensurável de qualidade** (`NO_MEASURABLE_GAIN`). A fidelidade melhora frente à v0.10.0 nos dois conjuntos (+0,41 e +0,45, acima do ruído do controle). O atendimento ao pedido e a naturalidade não melhoram: as quedas cabem no ruído do controle, que varia 0,56 sozinho entre rodadas. As mudanças da continuação aumentaram o uso do fluxo e não melhoraram a escrita. Os 2 críticos da final: P05 (troca "criam" → "criavam" sem rodar nenhum gate; o gate também não pegaria, V105-GAP-22) e P08 (aviso para o WhatsApp que estendeu uma condição e inventou um mês; o `compare` reprovou e o agente entregou com ressalvas, V105-GAP-17).
- **LLM direto:** editou todas as 8 oportunidades de não mexer e teve 7 erros críticos em 20 saídas. É a referência do que acontece sem nenhum controle.

### Ablação válida (mesmo pedido em todas as variantes; diferença pareada contra o engine completo, n = 20 pares)

| Variante | Δ fidelidade | Δ pedido | Δ naturalidade | Textos alterados (completo / variante) |
|---|---|---|---|---|
| Sem atributos (só o pedido), com conhecimento | −0,15 (1 melhor, 3 piores) | +0,05 (2 / 1) | +0,10 (2 / 1) | 8 / 8 |
| Com atributos, sem conhecimento | 0,00 (1 / 2) | +0,05 (2 / 1) | +0,15 (3 / 0) | 8 / 8 |
| Sem atributos nem conhecimento | −0,30 (0 / 3) | −0,15 (2 / 4) | 0,00 (2 / 1) | 8 / 8 |

**Atributos e conhecimento: `NO_MEASURABLE_GAIN`** isoladamente. Tirar os dois juntos tende a piorar a fidelidade (0 melhores, 3 piores), mas com n = 20 pares e diferenças pequenas é `INCONCLUSIVE`. As variantes alteraram exatamente os mesmos 8 textos: o que decide se o engine edita é o pedido e o modo, não os atributos nem o conhecimento.

