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

## 6. O que não rodou

Revisão humana cega, holdout feito por terceiro, juiz de outro fornecedor, modelo local, Codex/Gemini, macOS, Word: `NOT_RUN`. Sem eles, nenhuma afirmação aqui é sobre "escrita melhor para pessoas".
