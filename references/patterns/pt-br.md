# Famílias de padrões PT-BR

Os padrões abaixo são **hipóteses contextuais**, nunca blacklist.

## 1. Oficialês deslocado

Sinais:
- excesso de substantivos abstratos;
- verbos-suporte: realizar, efetuar, proceder;
- fórmulas protocolares em contexto simples;
- passivas sem função clara.

False positive:
- texto jurídico, regulatório ou institucional pode exigir esse registro.

## 2. Abertura genérica / redação escolar

Sinais:
- "No cenário atual...";
- "Em um mundo cada vez mais...";
- contexto amplo antes de qualquer afirmação concreta;
- tese atrasada por frases de preparação.

Não editar se a contextualização for necessária para o argumento.

## 3. Marcadores vazios de importância

Exemplos:
- "é importante destacar";
- "vale ressaltar";
- "cabe mencionar".

Pergunta operacional:
**a frase seguinte perde alguma informação se o marcador for removido?**
Se não, é candidato a simplificação.

## 4. Gerundismo burocrático

Exemplos:
- "estaremos realizando";
- "iremos estar verificando".

Distinguir de gerúndio legítimo que expressa processo simultâneo ou durativo.

## 5. Conectivos empilhados

Sinais:
- parágrafos iniciados em sequência por "nesse sentido", "além disso", "por outro lado", "dessa forma";
- conectivo sem relação lógica real.

Métrica futura: posição/frequência por gênero, calibrada em corpus.

## 6. Nominalização excessiva

Exemplo:
"realização da implementação da validação"

Pode virar:
"implementar e validar"

Somente quando a mudança não altera agência, escopo ou tecnicidade.

## 7. Paralelismo e tríades formulaicas

Exemplo:
"robusto, eficiente e escalável"

Não é erro por si só. Sinal cresce quando:
- ocorre repetidamente;
- os itens são vagos;
- não há evidência;
- o texto usa sempre três elementos.

## 8. Falsa profundidade

Sinais:
- contraste dramático sem correção real;
- frase curta que apenas repete;
- "isso muda tudo";
- conclusão grandiosa a partir de fato banal.

## 9. Linguagem promocional sem suporte

Termos:
- revolucionário;
- inovador;
- poderoso;
- transformador;
- de última geração.

Manter quando forem citação, branding ou claim sustentado e atribuído.

## 10. Fechamento genérico

Sinais:
- repete a tese;
- prevê futuro otimista sem base;
- chama o tópico de essencial/importante sem acrescentar consequência.

## 11. Tradução literal / interferência do inglês

Investigar construções que parecem calque, mas nunca "corrigir" automaticamente estrangeirismo técnico estabelecido.

## 12. Purismo artificial

Termos como deploy, backend, feedback ou bug podem ser naturais em certas comunidades. Traduzir tudo pode soar menos brasileiro no domínio técnico.

## Score de evidência do padrão

Cada detecção deveria registrar:
- pattern_id;
- span;
- força;
- frequência;
- função discursiva;
- gênero;
- suporte da amostra do autor;
- false-positive candidate;
- fonte/evidência.

O sistema não deve produzir "AI score".
