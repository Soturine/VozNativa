# Regionalidade e packs regionais

## Princípio

Regionalidade é **distribuição de variantes em contexto**, não uma lista de bordões.

Um pack regional existe para modular escolhas quando há evidência suficiente. Ele não deve transformar localização em caricatura nem tentar identificar a origem do usuário.

## Dimensões possíveis

Um pack pode registrar:
- região macro;
- estado;
- cidade/localidade;
- capital/interior;
- zona urbana quando a fonte tiver essa granularidade;
- período de coleta;
- modalidade: fala/escrita;
- gênero/canal;
- léxico;
- formas de tratamento;
- pronomes;
- construções morfossintáticas;
- marcadores discursivos;
- pragmática;
- contrações;
- grafia estilizada;
- força e confiança;
- fonte e evidência.

## Requisito de evidência

Uma feature regional não entra como regra operacional sem:
1. fonte identificada;
2. recorte geográfico;
3. período;
4. modalidade;
5. população/amostra;
6. contraste com outra região ou baseline;
7. false-positive case;
8. nível E0–E4 conforme `docs/CORPUS_AND_EVIDENCE_STRATEGY.md`.

## Fontes iniciais

- ALiB: cobertura nacional e variação diatópica;
- NURC: fala urbana culta em capitais selecionadas;
- Projeto SP2010: fala paulistana estratificada;
- CORAA: família de corpora de fala/transcrição;
- C-ORAL-BRASIL: fala espontânea, especialmente útil para oralidade;
- Corpus Carolina: útil para escrita/gêneros, mas não deve ser usado sozinho como atlas regional.

## Intensidade

```text
0.00 = sem regionalização deliberada
0.10–0.25 = nuance leve
0.25–0.50 = perceptível, requer evidência
0.50–0.75 = forte, preferencialmente com amostra/autorização
0.75–1.00 = estilização explícita, não default
```

A intensidade não significa "quantidade de gírias".

## Regional Overfit Guard

Sinais:
- repetição do mesmo marcador;
- muitos marcadores em pouco texto;
- feature regional mais forte que a amostra;
- mistura de estereótipos;
- marcador incompatível com canal/registro;
- densidade artificialmente constante.

Exemplo ruim:
```text
uai ... trem ... sô ... uai ... trem ...
```

O problema não é cada termo individualmente; é a distribuição artificial.

## Dialect Mixing Guard

Mistura real existe por:
- migração;
- família;
- internet;
- trabalho;
- comunidade;
- convivência entre regiões.

O guard não deve "purificar" a voz. Ele só sinaliza quando o próprio sistema parece ter adicionado sinais incompatíveis sem suporte.

## Capital x interior

Nunca assumir:
```text
São Paulo capital = estado de São Paulo
Recife = Pernambuco inteiro
Salvador = Bahia inteira
Porto Alegre = Rio Grande do Sul inteiro
Rio capital = estado do Rio
```

Se a fonte não sustenta granularidade local, o pack também não sustenta.

## Estrutura futura de pack

```yaml
pack_id: br-sp-capital
version: 0.1
status: experimental
scope:
  country: BR
  state: SP
  locality: sao-paulo
  modality: spoken
  period: 2011-2013
features:
  - id: ...
    level: discourse
    description: ...
    contexts: [...]
    evidence:
      sources: [...]
      level: E2
      confidence: 0.61
    generation:
      default_strength: low
      mandatory: false
      do_not_force: true
```

## Não objetivos

- classificar origem do usuário;
- imitar grupo social sem consentimento;
- escrever foneticamente por padrão;
- inserir sotaque como decoração;
- usar uma palavra isolada como prova regional.
