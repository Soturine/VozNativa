# Voice Stack, regionalidade e gírias

## Voice Stack

Precedência padrão:

1. amostras do próprio autor;
2. canal e contexto;
3. comunidade/socioleto;
4. regionalidade;
5. default PT-BR.

Amostras autorizadas têm precedência porque o objetivo é preservar idioleto, não aproximar todo mundo de uma média.

## Voice Profile

Campos iniciais:

```yaml
schema_version: 1
locale: pt-BR
source:
  type: samples
  sample_count: 0
register:
  formality: null
sentence:
  mean_words: null
  stdev_words: null
paragraph:
  mean_sentences: null
punctuation:
  em_dash_rate: null
  ellipsis_rate: null
  question_rate: null
lexicon:
  recurring: []
  avoided: []
  abbreviations: []
  foreign_terms: []
discourse:
  preferred_openers: []
  connectors: []
regional:
  target: null
  strength: 0.0
community:
  target: null
temporal:
  target_year: null
notes: []
```

O perfil registra observações linguísticas; não deve inferir atributos pessoais.

## Regionalidade

Regionalidade não é um dicionário de bordões. Um pack deve representar distribuição e contexto.

Dimensões possíveis:
- região;
- estado;
- cidade/área quando houver evidência suficiente;
- capital/interior;
- léxico;
- pronomes e formas de tratamento;
- construções morfossintáticas;
- marcadores discursivos;
- pragmática;
- temporalidade;
- fonte;
- confiança.

### Intensidade

```text
0.00 = neutro
0.25 = nuance leve
0.50 = perceptível
0.75 = forte, requer boa evidência/amostra
1.00 = transformação estilística explícita
```

### Regional Overfit Guard

Sinais:
- marcador regional repetido;
- densidade alta de marcadores;
- uso de marcador fora do registro esperado;
- combinação de vários estereótipos;
- regionalização maior que a solicitada.

A saída correta pode conter **zero gírias regionais**.

### Dialect Mixing Guard

Mistura regional não é automaticamente errada: pessoas migram, convivem online e misturam repertórios. O guard deve rejeitar mistura apenas quando ela parece adicionada pelo sistema sem apoio em amostra, pedido ou contexto.

## Community packs

Regionalidade não domina toda a voz. Comunidades podem explicar melhor parte do vocabulário:
- tech;
- gaming;
- academia;
- engenharia;
- jurídico;
- marketing;
- streaming;
- Discord/online;
- corporativo.

Um dev de São Paulo pode compartilhar mais vocabulário profissional com um dev de Recife do que com alguém de outra comunidade da mesma cidade.

## Temporal slang

Schema conceitual:

```yaml
term: "..."
type: slang
regions: []
communities: []
contexts: []
observed_from: null
observed_until: null
register:
  min: very_casual
  max: casual
confidence: 0.0
do_not_force: true
sources: []
```

Gírias devem ter temporalidade. Expressão comum em 2012 não deve ser tratada como default de 2026 sem evidência.

## Padrões PT-BR iniciais

Famílias a desenvolver:
- oficialês deslocado;
- abertura genérica estilo redação/ENEM;
- marcadores vazios de importância;
- gerundismo burocrático;
- gerúndio conclusivo mecânico;
- conectivos empilhados;
- paralelismo e trios artificiais;
- falsa profundidade;
- linguagem promocional sem suporte;
- fechamento otimista genérico;
- tradução literal do inglês;
- purismo artificial contra estrangeirismos consagrados.

Todos são sinais contextuais. Nenhum deve virar blacklist absoluta.
