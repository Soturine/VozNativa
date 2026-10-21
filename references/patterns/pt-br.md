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

## Biblioteca v2 (v0.4.0): como o detector decide

O catálogo executável está em `voznativa/data/patterns_pt_br.yml`; cada padrão traz `rationale` (por que soa a fórmula), `legitimate` (quando manter) e `sources`. Casos positivos e falsos positivos em `evals/patterns/cases.jsonl`; um teste exige os dois para todo padrão.

Ocorrência lexical isolada não é prova. O detector combina:

- **gênero e canal**: `exempt` (legítimo ali) e `weak_in` (comum ali);
- **posição**: abertura genérica só conta quando abre o parágrafo; fecho de efeito e "em suma" só no fim (e "em suma" só em texto curto);
- **função**: guardas que reconhecem o uso legítimo — gerúndio durativo ancorado num horário, tríade depois de dois-pontos (lista anunciada), "ecossistema" em biologia, "jornada de trabalho", claim promocional atribuído a uma fonte;
- **frequência**: padrões fracos que só viram fortes quando se repetem (tríades, gerúndio de consequência, pleonasmo, jargão);
- **decisão**: um achado forte, ou fracos em número que cresce com o tamanho do texto (mínimo 2; um a cada 150 palavras). Limiar sem calibração.

Famílias novas: ENEM-ismo fora da redação escolar (`enem_formula`), conectivo redundante (`connector_pleonasm`), gerúndio de consequência no fim da frase (`gerund_tail`), oficialês deslocado (`officialese`), fecho de efeito (`closing_formula`), tríade de abstratos (`formulaic_triad`), anáfora em série (`anaphora_run`), avaliativo repetido (`repeated_evaluation`), pleonasmo (`pleonasm`), jargão corporativo (`corporate_vague`) e decalque de construção do inglês (`calque_construction`).

Limitações conhecidas: a regex não vê aspas, então uma fórmula citada é capturada; listas de verbos e adjetivos foram montadas pelo desenvolvedor; nada foi calibrado em corpus.
