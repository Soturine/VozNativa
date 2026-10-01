# Voice Stack

## Objetivo

Voice Stack resolve conflitos entre voz pessoal, canal, gênero, comunidade, regionalidade e default PT-BR sem transformar nenhuma dessas camadas em identidade fixa.

## Ordem de precedência

```text
1. preservação semântica
2. instrução explícita da tarefa
3. amostras do autor no mesmo canal
4. perfil geral do autor
5. gênero + canal + público
6. registro
7. comunidade/socioleto
8. regionalidade
9. default PT-BR
```

A ordem pode ser ajustada apenas quando a tarefa exigir explicitamente outra coisa.

## Por que canal fica alto

Uma pessoa pode escrever:
- "nn sei agr" no WhatsApp;
- "não tenho certeza neste momento" em e-mail;
- "o comportamento ainda não foi validado" em documentação técnica.

Todos podem pertencer ao mesmo idioleto.

## Merge de features

Cada camada fornece preferências, não texto pronto.

Exemplo:
```yaml
sentence_length:
  author: short-mixed
  channel: short
  genre: unconstrained
  resolved: short-mixed

slang:
  author: low
  channel: medium
  region: medium
  resolved: low

technical_terms:
  community: preserve
  genre: preserve
  resolved: preserve
```

## Conflitos

### Autor x região
Amostra do autor vence. Não regionalizar à força.

### Canal x formalidade
Se o usuário pediu formalidade alta em WhatsApp, cumprir o pedido sem transformar a mensagem em ofício.

### Comunidade x português "puro"
Terminologia comunitária estabelecida pode vencer substituição purista.

### Gênero x idioleto
Termos, citações e convenções obrigatórias do gênero não devem ser destruídos para copiar hábitos pessoais.

## Strength

Cada layer futura pode produzir:
- value;
- confidence;
- strength;
- provenance;
- scope.

Exemplo:
```yaml
feature: em_dash
value: occasional
source: author_samples
confidence: 0.78
strength: medium
scope: github_docs
```

## Temporalidade

Voice Profile também precisa de tempo. Uma amostra antiga pode não representar escrita atual.

Campos futuros:
- observed_from;
- observed_until;
- sample_date;
- decay policy;
- profile version.

## Regionalidade

Regionalidade entra como nuance. Ver `references/regions/README.md`.

Não usar região como proxy para:
- idade;
- classe;
- escolaridade;
- personalidade;
- comunidade.

## Communities

Community packs descrevem práticas discursivas e terminologia de um domínio. Ver `references/communities/README.md`.

Eles não devem "gamificar" ou "corporativizar" um texto apenas porque o usuário pertence a uma comunidade.

## Gíria

Gíria é uma feature temporal e contextual:
- termo;
- comunidade;
- região;
- canal;
- período;
- intensidade;
- confidence;
- do_not_force.

## Resolver ou não resolver

Se as camadas entram em conflito e a confiança é baixa, a decisão preferida é **não estilizar**.

```text
low evidence + high stylistic impact
-> preserve source style
```

## Relação com Rewrite Engine

O Rewrite Engine não recebe "escreva brasileiro". Recebe um contrato resolvido, por exemplo:

```yaml
voice_contract:
  locale: pt-BR
  register: professional-natural
  sentence_rhythm: mixed
  contractions: low
  technical_english: preserve
  em_dash: occasional
  regional_strength: 0.0
  slang_strength: 0.0
  first_person: allowed
  protected_patterns:
    - terminology
    - numbers
    - modality
```

Isso reduz improvisação do modelo e torna evals reproduzíveis.
