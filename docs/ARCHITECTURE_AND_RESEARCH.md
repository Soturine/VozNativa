# Arquitetura e pesquisa

## Arquitetura

Fluxo-base:

```text
Context Router
  -> Semantic Ledger / Fact Lock
  -> Deterministic Analyzer
  -> Voice Stack
  -> Rewrite Engine
  -> Validation Gates
```

### Context Router
Classifica gênero, canal, objetivo, público, formalidade e restrições.

### Semantic Ledger
Fonte de verdade do conteúdo protegido. Deve evoluir de extração lexical para claims estruturados, modalidade, negação, temporalidade, causalidade e relações entre entidades.

### Deterministic Analyzer
Mede o que não precisa ser "estimado" pelo LLM: tamanho de frase, parágrafos, pontuação, conectivos, números, datas, URLs, repetições e padrões simples.

### Voice Stack
Composição em camadas, com precedência:
1. amostra do próprio autor;
2. canal/contexto;
3. comunidade/socioleto;
4. regionalidade;
5. default PT-BR.

### Rewrite Engine
Camada generativa, agnóstica de provedor. Recebe contexto, Semantic Ledger, Voice Profile e referências necessárias.

### Validation Gates
- Semantic Guard;
- False Positive Guard;
- Regional Overfit Guard;
- Dialect Mixing Guard;
- Voice Drift Guard.

## Regionalidade

Regionalidade é distribuição, não decoração.

"Sotaque escrito" é um atalho coloquial. Sotaque estrito é fenômeno fonético/fonológico; na escrita, VozNativa modela sobretudo léxico, morfossintaxe, pragmática, discurso, marcadores conversacionais e grafia estilizada.

Um pack regional pode descrever:
- léxico observado;
- formas de tratamento;
- marcadores discursivos;
- construções morfossintáticas;
- contrações;
- diferenças capital/interior quando houver evidência;
- período temporal;
- contexto;
- confiança e fonte.

Nunca deve exigir bordões. "Mineiro" não significa inserir "uai"; "gaúcho" não significa inserir "bah".

## Temporalidade e gírias

Gíria envelhece. Cada item deve poder registrar:
- regiões;
- comunidades;
- contextos;
- início/fim de observação;
- formalidade;
- confiança;
- regra `do_not_force`.

Isso permite distinguir escrita contemporânea de imitações datadas e evita slang stuffing.

## Idioleto

O objetivo central não é descobrir "como humanos escrevem", mas como **esta pessoa** escreve em determinado contexto.

Voice Profile pode observar:
- comprimento e variação de frases;
- tamanho de parágrafo;
- pontuação;
- conectores;
- abreviações;
- contrações;
- estrangeirismos;
- léxico recorrente;
- palavras evitadas;
- emojis;
- capitalização;
- autocorreções;
- ritmo.

Observação linguística não autoriza inferência de identidade.

## Métricas operacionais

Não usar "AI probability". Preferir:
- mechanicality;
- formulaicity;
- voice_drift;
- regional_overfit;
- register_mismatch;
- semantic_loss.

Essas métricas descrevem o comportamento do framework; não provam autoria.

## Pesquisa comparativa

Projetos estudados como referência conceitual:
- blader/humanizer;
- mackswendhell/humanizer-pt-br;
- opaulomarcondes/humanizador-pt;
- gabrielkashimarki/humanizer-ptbr;
- fabricioctelles/skills (humanizar).

Ideias úteis observadas:
- catálogo de padrões e packaging;
- adaptação PT-BR;
- contexto de voz separado;
- padrões retóricos brasileiros;
- trava factual;
- false-positive guard;
- perfis e regressão.

VozNativa deve manter taxonomia e implementação próprias. Antes de copiar qualquer material externo, revisar licença e atribuição.

## Pesquisa linguística brasileira

Bases relevantes para orientar futuros packs e evals:
- Projeto Atlas Linguístico do Brasil (ALiB);
- Projeto NURC;
- Corpus Carolina / USP;
- outros corpora brasileiros com licença compatível.

A inclusão de corpus exige revisão individual de licença. A meta não é copiar grandes blocos, e sim usar evidência para calibrar comportamento, exemplos próprios e evals.

## Princípio de implementação

Código para o determinístico. LLM para semântica, pragmática, ironia, tom e reescrita.

Sempre que possível, análise e validação devem limitar a autoavaliação do mesmo modelo que gerou a candidata.
