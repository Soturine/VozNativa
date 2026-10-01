# Arquitetura e pesquisa

## Arquitetura

```text
Input
  -> Context Router
  -> Semantic Ledger / Fact Lock
  -> Deterministic Analyzer
  -> Evidence-aware Pattern Analysis
  -> Voice Stack
  -> Rewrite Engine
  -> Validation Gates
  -> Output + optional audit
```

## 1. Context Router

Classifica:
- gênero;
- canal;
- público;
- objetivo;
- formalidade;
- tecnicidade;
- restrições;
- temporalidade;
- fontes de voz/contexto disponíveis.

A classificação não precisa ser perfeita; ela precisa impedir que referências irrelevantes contaminem a tarefa.

## 2. Semantic Ledger

Fonte de verdade do conteúdo.

### Baseline atual
Protege lexicalmente:
- números;
- datas;
- URLs;
- moeda;
- percentuais;
- identificadores.

### Evolução planejada
Claims estruturados com:
- entidades;
- predicados;
- negadores;
- modalidade;
- quantidade;
- unidade;
- condição;
- causalidade;
- temporalidade;
- escopo;
- atribuição.

Exemplo:
```text
"o problema pode causar perda de dados quando duas requisições..."
```

deve preservar:
- possibilidade, não certeza;
- condição concorrente;
- objeto da perda;
- direção causal.

## 3. Deterministic Analyzer

Responsável por medidas reproduzíveis:
- tamanho de sentenças/parágrafos;
- pontuação;
- conectores;
- gerúndios;
- advérbios;
- repetições;
- aberturas;
- perguntas;
- spans protegidos.

Não decide autoria nem "humanidade".

## 4. Evidence-aware Pattern Analysis

Padrões vêm de:
- análise linguística;
- corpora;
- referências secundárias;
- evals;
- observações de amostras.

Cada regra futura deve carregar nível de evidência E0–E4.

Ver:
- `docs/CORPUS_AND_EVIDENCE_STRATEGY.md`;
- `references/corpora/`;
- `references/patterns/`.

## 5. Voice Stack

Precedência:

```text
semântica
> instrução explícita
> autor no mesmo canal
> autor geral
> gênero/canal/público
> registro
> comunidade
> região
> default pt-BR
```

Ver `references/VOICE_STACK.md`.

## 6. Rewrite Engine

Camada generativa agnóstica de provedor.

Inputs futuros:
- original;
- context contract;
- semantic ledger;
- resolved voice contract;
- selected references;
- current findings.

Outputs:
- candidate text;
- transformation trace opcional;
- unresolved risks.

O modelo não deve receber todo o repositório de referências indiscriminadamente. Progressive disclosure é requisito arquitetural.

## 7. Validation Gates

### Semantic Guard
Invariantes lexicais hoje; claims futuramente.

### False Positive Guard
Evita editar escolhas legítimas.

### Regional Overfit Guard
Evita caricatura e slang stuffing.

### Dialect Mixing Guard
Sinaliza mistura adicionada sem suporte.

### Voice Drift Guard
Compara janelas de texto; baseline atual ainda não calibrado.

## Pesquisa comparativa de humanizers

Projetos analisados:
- blader/humanizer;
- mackswendhell/humanizer-pt-br;
- opaulomarcondes/humanizador-pt;
- gabrielkashimarki/humanizer-ptbr;
- fabricioctelles/skills/humanizar.

Contribuições conceituais estudadas:
- padrões estruturais;
- context/voice profile;
- retórica PT-BR;
- factual lock;
- false-positive thinking;
- progressive disclosure;
- packaging/evals.

VozNativa mantém taxonomia e implementação próprias.

## Pesquisa linguística brasileira

### Corpus Carolina
Principal fonte inicial para escrita contemporânea/gêneros/proveniência.

Uso:
- baselines por tipologia;
- falsos positivos;
- conectores;
- pontuação;
- nominalização;
- distribuição estrutural.

Limite:
não é atlas regional representativo.

### ALiB
Principal referência inicial para variação diatópica nacional.

Uso:
- léxico;
- morfossintaxe;
- pragmática;
- capital/interior quando sustentado.

### NURC
Fala urbana culta em capitais selecionadas, com valor histórico e estilístico.

### Projeto SP2010
Fala paulistana estratificada, útil para granularidade dentro da cidade de São Paulo.

### CORAA
Família de recursos de fala/transcrição, útil para modo spoken/conversational e comparação entre fala espontânea/preparada.

### C-ORAL-BRASIL
Importante para fala espontânea e estrutura informacional.

## Corpus não vira regra diretamente

```text
corpus
-> recorte
-> métrica
-> comparação
-> hipótese
-> false-positive test
-> eval
-> revisão humana
-> pack
```

## Licença

Fontes podem ter:
- licença do corpus;
- licença do cabeçalho/metadados;
- licenças individuais por documento;
- restrição acadêmica/não comercial;
- termos diferentes por versão.

A pipeline deve guardar tudo isso no Source Ledger.

## Princípio

**Código para o determinístico; LLM para interpretação e reescrita; corpus para evidência; humanos para calibração.**

Nenhum componente sozinho deve ser considerado árbitro de naturalidade.
