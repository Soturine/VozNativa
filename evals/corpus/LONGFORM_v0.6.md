# CP10 — textos longos, literatura e verso (2026-11-05)

Fonte: `machado-de-assis-corpus`, a 32ª fonte do registro.
- Hugging Face, CC0 sobre a compilação; os textos estão em domínio público, já que Machado de Assis morreu em 1908.
- É um prefixo explícito de 6 MB fixado no commit `7f63759`.
- Contém 309 registros: 12 obras completas do Project Gutenberg, na ortografia anterior a 1943, e 297 páginas do Wikisource, na ortografia atual. O último registro foi cortado e conta como 1 erro de leitura esperado.

Execução: `scripts/corpus_longform.py` → `evals/corpus/runs/longform-2026-11-05.json`. A coluna "antes da regra" vem de `longform-2026-11-05-before-literary-rule.json`, uma execução anterior à regra literária e às correções do mapa (cabeçalho e abertura). Só contagens; nada de texto foi exportado.

Os textos continuam fora do repositório, no cache local.

O Gutenberg não foi usado diretamente: a verificação TLS falhou neste ambiente e não foi desligada.

## Partição honesta

| subconjunto | registros | papel |
|---|---|---|
| Gutenberg (12 obras) | 12 | regras de segmentação e de verso **ajustadas aqui** |
| Wikisource, capítulos das mesmas 12 obras | 128 | **não independente**: mesmo texto, outra edição; separado depois que o agente notou a sobreposição pelos títulos (a deduplicação por registro não a vê, porque um capítulo é pequeno diante do romance inteiro) |
| Wikisource, outras obras | 169 | separado para a segmentação e o verso |

## Segmentação (M9)

O módulo `voznativa/longform.py` faz três coisas:
- monta um mapa de dependências entre parágrafos (abertura anafórica, referência para trás, anúncio do parágrafo seguinte, sigla definida antes, diálogo, lista, verso);
- corta só em fronteira segura;
- quando uma cadeia passa de duas vezes o limite, faz um corte forçado e **o relata**.

A junção dos segmentos sempre devolve o texto exato, e a execução verifica isso em todos os documentos.

| limite | subconjunto | cortes | cortes sobre dependência visível | forçados (relatados) | não relatados |
|---|---|---|---|---|---|
| 900 palavras | Gutenberg | 794 | 2 | 2 | 0 |
| 900 | outras obras (separado) | 184 | 0 | 0 | 0 |
| 400 | Gutenberg | 1.941 | 18 | 18 | 0 |
| 400 | outras obras (separado) | 550 | 1 | 1 | 0 |

**Limite:** "dependência visível" é o que a heurística de superfície enxerga, como aberturas, siglas e marcas. Uma dependência de sentido sem marca não entra na conta. Portanto, "0 cortes não relatados" não prova que nenhum corte separou ideias ligadas.

## Verso

Na primeira versão do classificador, um terço de cada romance do Gutenberg era lido como verso. A causa era a prosa com quebra de linha fixa, que preenche ~70 caracteres por linha e continua em minúscula. A regra foi corrigida nas obras do Gutenberg:

| obra | parcela classificada como verso |
|---|---|
| *Poesias Completas* | 92% |
| romances | 0–1% |

No subconjunto separado, 26 das 297 páginas são majoritariamente verso. Numa amostra de 24 páginas, o agente leu cada uma e as 24 concordaram com a classificação (3 poemas, 21 prosas). **Isto é observação do agente, não avaliação humana.**

## Literatura como controle de mudança desnecessária

Os segmentos de 900 palavras foram lidos pelo detector editorial:

| subconjunto | gênero `literary` antes da regra | `literary` depois | gênero `unknown` |
|---|---|---|---|
| Gutenberg | 437/798 = 55% | 2/804 = 0,25% [0,1–0,9] | 444/804 = 55% |
| mesmas obras, Wikisource | — | 0/162 [0–2,3] | 20/162 = 12% |
| outras obras | 80/501 = 16% (antes da separação) | 0/343 [0–1,1] | 60/343 = 17% |

- **Causa medida:** o gênero literário já isentava os padrões editoriais, mas não a camada PT-BR. Dois achados disparavam:
  - `pt_pt_variant` forte, na ortografia brasileira anterior a 1943 ("acção" 104 ocorrências, "facto" 70, "projecto" 42) e no uso do século XIX ("rapariga", "constipação", "estar a + infinitivo");
  - `treatment_mixed`, quando personagens diferentes usam formas de tratamento diferentes.
- **Regra adotada,** coerente com `references/genres/literary.md`: no gênero `literary`, a variante PT-PT é uma nota (`note_only`), que é relatada mas nunca conta para `edit` nem é tratada pelo planejador, e a mistura de tratamento não é achado. A primeira versão só rebaixava a variante para fraca. O `ptbr-bench-v4` (caso `bv4-lt-03`) mostrou que três notas num diálogo curto ainda passavam do limiar de fracos. A regra é categórica, por gênero, e não um limiar ajustado. Ela foi decidida **depois** de ver todos os subconjuntos, então a queda para 0–0,25% não é evidência separada: é o efeito mecânico da regra.
- **Risco que continua:**
  - com o gênero `unknown`, o texto literário histórico ainda recebe achados PT-PT em 12–55% dos segmentos;
  - o roteador inferiu `literary` em só 36 de 804 segmentos do Gutenberg e chamou 259 de `whatsapp`, provavelmente por causa do diálogo com "--";
  - nas outras obras, o roteador inferiu `literary` em 267 de 343 segmentos.
  - O roteador não foi alterado: tem suíte de regressão congelada.
  - **Recomendação:** ensinar o roteador a reconhecer o diálogo com "--" e a ortografia anterior a 1943, numa versão própria, com a suíte do roteador reavaliada.

## Política literária no planejador

`longform.literary_policy` decide até onde a reescrita pode ir:
- **verso** (≥ 50% das palavras): `no_change` sem pedido explícito; com pedido explícito, só mudanças locais;
- **prosa literária:** escopo local, sem reescrever parágrafo nem documento;
- **destino pedido** (alvo): conta como pedido explícito.

Esta política está coberta por testes. Nenhum modelo foi chamado para medi-la.
