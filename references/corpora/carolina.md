# Corpus Carolina

## Identidade da fonte

**Nome:** Corpus Geral do Português Brasileiro Contemporâneo — Carolina  
**Instituições:** LaViHD / C4AI / USP  
**Metodologia:** WaC-wiPT — Web as Corpus with Provenance and Typology  
**Cobertura declarada:** português brasileiro contemporâneo; o portal descreve material de 1970–2021 nas versões publicamente documentadas.

O site oficial de download lista a **versão 1.3 Ada**, com atualização em **26/11/2024**, em Portulan e Hugging Face. A página institucional principal ainda apresenta estatísticas da 1.2: aproximadamente 823 milhões de tokens, mais de dois milhões de textos e mais de 11 GB. O VozNativa deve preservar essa distinção; não atribuir automaticamente as estatísticas da 1.2 à 1.3.

Fontes oficiais:
- https://sites.usp.br/corpuscarolina/
- https://sites.usp.br/corpuscarolina/corpus/
- https://sites.usp.br/corpuscarolina/documenta/
- https://huggingface.co/datasets/carolina-c4ai/corpus-carolina

## Por que é útil

O diferencial do Carolina para o VozNativa não é apenas escala. É a presença de **proveniência, tipologia e metadados**, permitindo comparar escrita de origens e gêneros diferentes sem tratar toda a web brasileira como uma massa homogênea.

Usos planejados:

### 1. Baselines por tipologia/gênero
Medir distribuições de:
- tamanho de sentença;
- tamanho de parágrafo;
- pontuação;
- conectores;
- nominalizações;
- repetições;
- posição de marcadores discursivos;
- densidade de listas/títulos quando recuperável;
- estrangeirismos por domínio.

### 2. False-positive guard
Uma construção não deve ser penalizada apenas porque aparece em listas de "AI tells". Se for frequente e funcional em um gênero humano real, isso é evidência contra regra absoluta.

### 3. Registro
Comparar famílias de textos — jurídico, jornalístico, social, acadêmico/literário quando disponíveis — para evitar que um único padrão de naturalidade seja aplicado a tudo.

### 4. Temporalidade
Quando os metadados permitirem, observar mudança de frequência ao longo do tempo. O período do Carolina não deve ser extrapolado automaticamente para "linguagem de 2026".

## O que o Carolina NÃO resolve

- não é um atlas dialetológico;
- não prova origem regional individual;
- não oferece, sozinho, um modelo confiável de sotaque/regionalidade;
- não deve ser usado para inferir identidade;
- corpus web tem vieses de disponibilidade, publicação e representação;
- a própria documentação da v1 afirma que a coleção não é balanceada em procedência e tipologia.

## Licenciamento

O Carolina reúne documentos de múltiplas origens e **cada documento mantém sua própria licença**, registrada nos metadados. O portal da USP declara o cabeçalho como CC BY-NC-SA 4.0; o card do Hugging Face (`carolina-c4ai/corpus-carolina`, consultado em 2026-10-19) declara `cc-by-4.0`. Esse conflito entre fontes oficiais não está resolvido (ver `docs/policy/LICENSING.md`). Portanto:

- não copiar textos do corpus para o repo sem verificar a licença individual;
- métricas agregadas devem guardar a versão e o recorte da fonte;
- exemplos de eval devem preferir material sintético quando não houver necessidade de trecho real;
- qualquer dataset derivado redistribuído precisa de revisão jurídica/licença específica.

## Plano de ingestão

Fase A — metadata-only:
1. ler taxonomias e proveniência;
2. mapear categorias para gêneros internos do VozNativa;
3. produzir relatório de cobertura e desbalanceamento.

Fase B — estatísticas:
1. processar texto por lote;
2. normalizar sem apagar marcas relevantes;
3. calcular métricas agregadas;
4. salvar apenas agregados + hash/versionamento do recorte.

Fase C — hipóteses:
1. comparar gêneros;
2. encontrar padrões candidatos;
3. testar contra false positives;
4. transformar apenas padrões robustos em evals.

Fase D — calibração:
1. revisão humana;
2. limites por gênero;
3. versionar baseline.

## Artefatos derivados esperados

```text
data-derived/carolina/
  manifest.json
  taxonomy-map.yml
  genre-baselines.json
  connector-distributions.json
  punctuation-distributions.json
  temporal-slices.json
  provenance-report.md
```

Esses artefatos devem conter estatísticas e metadados, não uma cópia indiscriminada do corpus.
