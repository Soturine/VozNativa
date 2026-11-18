# Avaliação da v0.10 (CP10 e CP12)

Eixos separados, nunca somados. Todos os conjuntos foram escritos pelo mesmo agente que escreveu as regras; nada aqui é revisão humana ou avaliação independente.

## CP10 — braços com modelo real (ablação)

**Método.** `scripts/v010_arms.py`, modelo `claude -p --model haiku --tools ""` (o mesmo em todos os braços), `--provider-env minimal`, 2 tentativas, sem juiz. Textos: `evals/v010/arms/texts.jsonl` (10 textos congelados no manifesto **antes** da execução: gêneros que o router não mapeia — roteiro de podcast, legenda de vídeo, bilhete escolar, ata, e-mail/post misto, relatório curto, poema, mensagem, anúncio, redação escolar; 4 não precisam de mudança). Braços: A0 original; A1 LLM direto; B3 engine `v0.9.0`; B4 v0.10 sem atributos e sem bloco de conhecimento (removido no próprio script, sem chave no produto); B5 v0.10 completo (`--attr` do texto + conhecimento). Registro: [`evals/v010/runs/arms-haiku-2026-11-18.json`](../../../evals/v010/runs/arms-haiku-2026-11-18.json).

| Braço | Edições desnecessárias (4 bons) | Mudou quando precisava (6) | Textos com sinal major/crítico | Checagens específicas (poema, condição, contraste, informalidade, exceção) | Chamadas |
|---|---|---|---|---|---|
| A1 LLM direto | **3/4** | 6/6 | 4 | 4/5 (perdeu a exceção do anúncio) | 10 |
| B3 v0.9.0 | 0/4 | 4/6 | 0 | 5/5 | 4 |
| B4 v0.10 sem contexto/conhecimento | 0/4 | 4/6 | 0 | 5/5 | 4 |
| B5 v0.10 completo | 0/4 | 4/6 | 0 | 5/5 | 4 |

**Leitura honesta.**
- O LLM direto alterou 3 de 4 textos bons (inclusive a mensagem informal e a ata) e perdeu a exceção "exceto para produtos já em promoção"; os engines não tocaram textos bons.
- **Contexto aberto e conhecimento: nenhum ganho demonstrado.** B4 e B5 deram saídas idênticas em 3 dos 4 textos reescritos; no quarto (redação escolar) B5 tirou o "Além disso" triplo mas repetiu "Ela também" duas vezes, B4 juntou as frases. n = 1 execução por braço: não é evidência de efeito, nem positivo nem negativo. O conhecimento selecionado em B5 foi pertinente (`kn-contraste-consequencia` no relatório com "Entretanto", `kn-concessao` na redação), e a relação "Entretanto" foi preservada em todos os braços.
- **Lacuna real achada**: dois textos que pediam mudança (e-mail/post com "venho por meio deste comunicar"; anúncio com "É com grande satisfação que anunciamos") saíram `no_change` em **todos** os engines, porque o detector não tinha essas fórmulas e o planner não chama o modelo sem achado. Corrigido em `patterns_pt_br.yml` (`formulaic_courtesy`), com controle ("Foi com grande alegria que recebi" não dispara). Esses 10 textos passam a ser **desenvolvimento**.
- Custo: 22 chamadas de Haiku (o `claude -p` em texto puro não informa custo; estimativa abaixo de US$ 0,20).

**Limites.** `compare` é o instrumento do próprio engine; as checagens específicas são testes de string escritos antes da execução; sem juiz e sem leitores.
