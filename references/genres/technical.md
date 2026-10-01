# Gênero técnico

## Objetivo

Tornar documentação técnica clara e natural sem alterar comportamento, contratos ou precisão.

## Conteúdo protegido

- código;
- comandos;
- paths;
- nomes de arquivo;
- identificadores;
- versões;
- APIs;
- endpoints;
- status codes;
- thresholds;
- unidades;
- termos de domínio;
- pré-condições e pós-condições.

## Problemas frequentes

- introduções genéricas antes de instruções simples;
- excesso de adjetivos como robusto, poderoso, eficiente;
- enumeração artificial de benefícios;
- repetição do nome da tecnologia;
- explicar o óbvio antes de dizer o procedimento;
- abstração excessiva em vez de exemplo concreto.

## Não humanizar

Nunca transformar:
`HTTP 409` em "um erro de conflito";
`PostgreSQL 17` em "PostgreSQL";
`timeout de 30 s` em "alguns segundos".

## Estilo recomendado

- frases diretas;
- sujeito técnico claro;
- verbos operacionais;
- exemplos concretos;
- listas apenas quando realmente enumerativas;
- evitar metáforas quando podem gerar ambiguidade.

## Evals

- command preservation;
- code/path preservation;
- version preservation;
- causal relationship preservation;
- precondition preservation;
- no invented implementation detail.
