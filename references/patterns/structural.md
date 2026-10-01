# Padrões estruturais

## Princípio

Estrutura regular não é defeito. Ela vira sinal quando a regularidade parece **independer do conteúdo**.

## Famílias

### Paragraph templating
Vários parágrafos seguem exatamente:
1. tópico;
2. explicação;
3. exemplo;
4. mini-conclusão.

Detecção:
- similaridade de número de sentenças;
- aberturas repetidas;
- fechamentos semanticamente redundantes.

### Uniformidade excessiva
Sentenças/parágrafos com comprimentos quase idênticos durante texto longo.

False positive:
- manual, ficha, especificação ou template institucional.

### Forced triads
Sequências recorrentes de três itens sem necessidade conceitual.

### Contrast formula
Uso repetido de:
- "não X, mas Y";
- "não se trata de X, e sim de Y";
- "mais do que X, Y".

Manter quando a negação corrige uma expectativa real.

### One-line closer
Frase isolada após parágrafo que apenas nomeia a conclusão já evidente.

### Listification
Conteúdo vira bullets automaticamente apesar de relações causais/argumentativas que pediriam prosa.

### Symmetry by rule
Seções com mesmo número de bullets, mesma extensão e mesmo padrão retórico sem razão semântica.

## Análise determinística futura

Métricas candidatas:
- coeficiente de variação do tamanho das sentenças;
- distribuição de sentenças por parágrafo;
- similaridade de sentence openers;
- repeated closing patterns;
- lista/prosa ratio;
- frequência de estruturas coordenadas;
- repetição posicional de conectivos.

Essas métricas são descritivas. O LLM/context router decide se a regularidade é funcional.
