# ALiB — Atlas Linguístico do Brasil

## Papel no VozNativa

O ALiB é uma fonte central para **variação linguística brasileira**, especialmente quando a pergunta envolve diferenças diatópicas e sua interação com dimensões sociais e estilísticas.

A metodologia do projeto contempla dados:
- fonético-fonológicos;
- semântico-lexicais;
- morfossintáticos;
- prosódicos;
- pragmáticos;
- metalinguísticos;
- discursos semidirigidos;
- leitura de texto.

O projeto usa uma perspectiva de Dialetologia Pluridimensional e uma rede nacional de pontos, com capitais e localidades do interior.

Referências:
- https://alib.ufba.br/
- https://www.scielo.br/j/alfa/a/v3JHS56nn7zfC4RHRK6GYgD/

## Como usar

### Regional lexicon
Uma variante lexical pode entrar como evidência regional somente quando:
- o referente está claro;
- a distribuição geográfica está documentada;
- o período da coleta é registrado;
- a frequência/alternância é conhecida ou a incerteza é mantida.

### Morfossintaxe e pragmática
Preferir regras probabilísticas/condicionais:
```text
observado em região/contexto X
-> candidato de baixa/média força
-> nunca marcador obrigatório
```

### Capital x interior
Não reduzir um estado à capital. Quando a evidência distinguir capital/interior, o pack também deve distinguir.

## Limitações para o produto

- grande parte dos dados é de fala, não de escrita digital;
- coleta dirigida altera o grau de espontaneidade;
- faixas etárias/escolaridade e desenho amostral precisam acompanhar qualquer conclusão;
- cartas e estudos representam recortes, não um "dicionário de sotaques";
- um fenômeno geográfico não deve virar inferência sobre origem de um usuário.

## Conversão para packs

Cada feature derivada deve carregar:

```yaml
feature_id: ...
level: lexical|morphosyntactic|pragmatic|discourse
scope:
  region: ...
  locality: ...
  capital_interior: ...
source:
  corpus: ALiB
  publication: ...
  question_or_map: ...
  period: ...
evidence:
  level: E1|E2|E3|E4
  confidence: ...
generation:
  default_strength: low
  mandatory: false
  do_not_force: true
```

O objetivo é evitar o modelo "estado -> bordão".
