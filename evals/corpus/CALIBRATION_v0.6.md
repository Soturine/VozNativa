# CP6 — calibração dos detectores com corpora (2026-11-05)

Execução: `scripts/corpus_calibrate.py` → `evals/corpus/runs/calibration-2026-11-05.json` (21 s, só contagens agregadas; política: `PROCESS_LOCAL` e `EXPORT_STATISTICS` exigidos antes da leitura).
Fontes: UD Portuguese-Bosque (CF = Folha, PT-BR; CP = Público, PT-PT, 1994–95) e um prefixo de 8 MB da B2W-Reviews01 (avaliações de produtos, 2018).
Divisões: as mesmas da execução de integridade (unidade = documento ou revisor unido ao cluster de duplicatas; sem vazamento). Os números de `calibration` e `evaluation` aparecem lado a lado. **Nenhum limiar, lista ou padrão foi alterado neste checkpoint.**

## 1. Marcadores PT-PT (`ptbr.variant_markers`)

| unidade | divisão | recall PT-PT | falsos positivos em PT-BR | precisão |
|---|---|---|---|---|
| frase | calibration | 326/2717 = 12,0% [10,8–13,3] | 0/2091 [0–0,2%] | 326/326 |
| frase | evaluation | 302/2433 = 12,4% [11,2–13,8] | 0/2116 [0–0,2%] | 302/302 |
| documento | calibration | 226/514 = 44,0% [39,7–48,3] | 0/484 [0–0,8%] | 226/226 |
| documento | evaluation | 189/464 = 40,7% [36,4–45,3] | 0/499 [0–0,8%] | 189/189 |

Intervalos de Wilson a 95%.
- **Medido:** a precisão é perfeita nas duas divisões, porque nenhum marcador disparou em 4.207 frases brasileiras. O recall é baixo, e isso é esperado: a lista contém apenas formas exclusivas, e a maioria das frases europeias não tem nenhuma delas. Os acertos se distribuem assim: ortografia 208, léxico 112 e sintaxe 51 (calibração).
- **Limite:** o PT-BR medido é jornalismo da Folha de 1994–95. Gírias, oralidade e textos posteriores ao Acordo Ortográfico não foram medidos. Os números não valem para "qualquer PT-BR".
- **Decisão:** nenhuma ampliação da lista neste CP. Aumentar o recall exige formas que também aparecem no Brasil, o que trocaria uma precisão demonstrada por um ganho não demonstrado. Fica registrado como oportunidade com custo conhecido.

## 2. Mudança desnecessária em texto humano (controle de texto natural)

Os textos foram escritos e publicados por pessoas. Qualquer `edit` aqui é candidato a mudança desnecessária. É apenas candidato: alguns achados podem ser legítimos, e ninguém revisou os casos.

| fonte (gênero do roteador) | divisão | documentos | `edit` | achados / 1000 palavras |
|---|---|---|---|---|
| Bosque CF (journalistic) | calibration | 484 | 1 (0,2%) [0–1,2] | 0,83 |
| Bosque CF (journalistic) | evaluation | 499 | 1 (0,2%) [0–1,1] | 0,79 |
| B2W (social) | calibration | 9.663 | 30 (0,31%) [0,2–0,4] | 0,83 |
| B2W (social) | evaluation | 10.220 | 18 (0,18%) [0,1–0,3] | 0,78 |

- Na B2W, quase todos os `edit` vêm de achados **fortes**: `officialese`, `empty_metadiscourse`, `dramatic_punchline`, `pt_pt_variant`, `gerundismo`. O acúmulo de fracos causou 4 casos em 9.663 e 5 em 10.220. No Bosque, cada divisão tem um único `edit`, e esse caso vem de acúmulo de fracos.
- Os padrões mais frequentes em texto humano são `promotional`, `formulaic_triad`, `anaphora_run`, `nominal_chain` e `stacked_connector`. Por documento, em `documents_with_pattern`. A maioria é fraca e não leva a `edit` sozinha.
- Ainda não medido: a taxa de `edit` do **planejador completo** (perfil, destino, registro), por gênero e canal além dos dois listados, e o resultado de uma reescrita. Esta medição usa o detector, que é a entrada do planejador.

## 3. `dc-029` — limiar `max(2, ceil(palavras/150))`

Varredura do divisor (75, 100, 150, 200, 300) sem mudar a regra:
- **Em todo o conjunto:** trocar o divisor move no máximo 1 documento em ~21 mil. Texto humano quase nunca tem dois achados fracos. Na B2W, o histograma de fracos por documento fica em 0: 9.503 · 1: 156 · 2: 3 · 3: 1 (calibração).
- **Na faixa do `dc-029` (150–299 palavras):** a amostra é pequena (Bosque 17 + 18; B2W 40 + 34). Só um documento da avaliação B2W muda de decisão entre `/100` e `/150`.
- **Determinação: continua INCONCLUSIVE.** A medição não mostra que o limiar `/150` cause mudanças desnecessárias em texto humano: a taxa de `edit` por acúmulo de fracos fica abaixo de 0,1% nas duas fontes. Também não mostra que `/100` seja melhor. A faixa de 150–300 palavras está sub-representada, porque os documentos do Bosque são trechos curtos e as avaliações também são curtas. Mudar o limiar com base nisso seria ajuste ao caso. O `dc-029` fica como falha conhecida.
- **O que decidiria:** um corpus de textos longos (300+ palavras) de gêneros profissionais e revisão humana cega dos `edit` (CP10/M9). Não executada.

## 4. Confusões declaradas

- Gênero e época estão confundidos: o Bosque é jornalismo de 1994–95, e a B2W reúne avaliações de 2018.
- A B2W foi lida pelo gênero `social`. O roteador não tem um gênero "avaliação de produto".
- O prefixo B2W corta o arquivo e não é uma amostra aleatória.
- **Não verificado:** a sobreposição entre essas fontes e os exemplos usados para desenvolver os padrões. A deduplicação da execução de integridade só comparou as duas fontes entre si e encontrou 0 clusters entre fontes. Ela não comparou as fontes com `evals/`. O dado é E2 (medição automática), não E3.
