# False Positive Guard

## Objetivo

Impedir que o VozNativa destrua escrita legítima apenas porque ela se parece com um padrão catalogado.

## Evidência insuficiente por si só

- gramática correta;
- vocabulário formal;
- um conectivo;
- um travessão;
- frase longa;
- frase curta;
- lista de três itens;
- voz passiva;
- repetição de termo técnico;
- heading padronizado;
- texto sem gíria;
- conclusão explícita.

## Contextos com proteção elevada

### Acadêmico
Hedging, repetição terminológica, citações e estrutura formal podem ser obrigatórios.

### Jurídico/regulatório
Nominalizações e fórmulas institucionais podem carregar precisão normativa.

### Técnico
Repetição de identificadores e nomenclatura é frequentemente desejável.

### Literário
Repetição, paralelismo, fragmento e pontuação marcada podem ser estilo.

### Chat pessoal
Erros, abreviações e inconsistências podem ser idioleto.

## Teste de intenção

Antes de editar, perguntar:
1. o padrão atrapalha compreensão?
2. repete algo sem informação?
3. conflita com gênero?
4. conflita com amostra do autor?
5. sua remoção perde nuance?
6. existe evidência além de uma palavra isolada?

## Do-nothing evals

O conjunto de evals precisa conter casos em que a resposta correta é:
```text
NO_CHANGE
```

Sem esses casos, o sistema aprende a editar por obrigação.

## Regra de confiança

Detecção de baixa confiança nunca deve disparar transformação forte sem validação contextual.
