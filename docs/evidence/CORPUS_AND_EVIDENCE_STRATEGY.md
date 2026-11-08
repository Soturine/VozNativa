# Corpus and Evidence Strategy

## Objetivo

VozNativa não deve transformar listas de exemplos em "verdades sobre o português brasileiro". Toda regra linguística que afete geração, auditoria, regionalidade, registro ou gíria precisa declarar **de onde veio, para qual população/contexto vale e quão forte é a evidência**.

O objetivo dos corpora não é copiar frases para o repositório. É produzir evidência agregada para:

- frequência e distribuição de construções;
- contraste entre gêneros e canais;
- variação temporal;
- variação regional quando a fonte permite;
- falsos positivos;
- exemplos sintéticos de eval;
- limites de aplicação de cada regra.

## Regra central

```text
observação no corpus
    !=
regra de geração
    !=
identidade do autor
```

Uma frequência alta em um corpus não significa que toda pessoa daquele grupo escreve daquela forma.

## Camadas de evidência

### E0 — hipótese
Ideia de produto, observação informal ou padrão ainda sem validação.

Uso permitido: backlog e experimento.

### E1 — referência secundária
Artigo, gramática, estudo ou documentação descreve o fenômeno.

Uso permitido: criar hipótese operacional e eval exploratório.

### E2 — corpus com proveniência
Fenômeno observado em corpus com metadados suficientes para recortar gênero, época, região ou outra dimensão pertinente.

Uso permitido: regra experimental com escopo explícito.

### E3 — replicação
Fenômeno aparece em mais de uma fonte independente ou em diferentes amostras adequadas.

Uso permitido: regra default de análise, ainda com false-positive guard.

### E4 — validação humana
Revisores adequados ao fenômeno confirmam naturalidade, escopo e limites.

Uso permitido: pack calibrado.

Nenhuma regra deve esconder seu nível de evidência.

## Source Ledger

Cada fonte deve registrar:

- id;
- nome e versão;
- mantenedor;
- URL oficial;
- data de acesso;
- período coberto pelos dados;
- modalidade: escrita, fala, áudio/transcrição;
- gêneros/tipologias;
- população/amostragem;
- metadados disponíveis;
- licença do corpus;
- licenças dos documentos individuais, quando aplicável;
- usos permitidos pelo VozNativa;
- usos proibidos;
- limitações e vieses conhecidos;
- versão do pipeline que derivou métricas.

## Pipeline de derivação

```text
fonte
  -> licença/proveniência
  -> seleção por metadados
  -> limpeza
  -> métricas agregadas
  -> comparação com baseline
  -> revisão de viés
  -> hipótese linguística
  -> eval contrastivo
  -> regra/peso experimental
  -> validação humana
  -> pack versionado
```

O corpus bruto não entra automaticamente no pacote distribuído.

## Métricas úteis

Por gênero/recorte, quando a fonte suportar:

- comprimento de sentença e parágrafo;
- distribuição de pontuação;
- conectores por mil palavras;
- frequência de marcadores discursivos;
- densidade de nominalizações;
- padrões de gerúndio;
- pessoa/pronomes e formas de tratamento;
- abreviações e grafias informais;
- estrangeirismos;
- repetição lexical;
- razão pergunta/afirmação;
- posição de conectores;
- diversidade de aberturas de sentença;
- n-gramas apenas para análise agregada, não para copiar estilo individual.

## Regionalidade

Para regionalidade, priorizar fontes que realmente tenham desenho geográfico/sociolinguístico. Um corpus grande da web não substitui ALiB, NURC, SP2010 ou corpora regionais.

Não usar "local de hospedagem do site" ou domínio como proxy de origem linguística.

## Temporalidade

Toda análise temporal precisa distinguir:

- data do documento;
- data de coleta;
- data de publicação;
- versão do corpus.

"Contemporâneo" nunca deve significar automaticamente "2026".

## Licença e redistribuição

Metadados e estatísticas derivadas devem ser separados do texto-fonte.

Antes de versionar exemplos reais:
1. verificar a licença daquele documento;
2. verificar se redistribuição é permitida;
3. preferir exemplos sintéticos quando o objetivo for apenas testar o fenômeno;
4. armazenar atribuição quando necessária.

## Privacidade

Amostras pessoais de voz têm política diferente de corpora públicos:
- consentimento explícito;
- minimização;
- não inferir atributos sensíveis;
- não publicar amostras por padrão;
- permitir perfil derivado sem reter texto bruto quando o fluxo suportar.

## Critério de admissão de uma nova referência

Uma referência só entra como base operacional se responder:
1. Qual fenômeno ela sustenta?
2. Qual população/texto foi observado?
3. Qual período?
4. Qual modalidade?
5. Qual licença?
6. Quais metadados existem?
7. Qual viés conhecido?
8. Como isso muda uma decisão do VozNativa?
9. Qual eval demonstra ganho?
10. Em que caso a regra deve ficar desligada?

Sem essas respostas, a fonte pode ficar no inventário de pesquisa, mas não deve alimentar um pack.
