# Roadmap

Legenda: `[x]` implementado e testado · `[~]` parcial · `[ ]` não implementado.

## v0.1 — Foundation
- [x] visão e arquitetura
- [x] SKILL.md roteador
- [x] pesquisa comparativa
- [x] design spec completo
- [x] matriz de rastreabilidade
- [x] agent metadata inicial
- [x] assets/templates iniciais
- [x] regras de regionalidade, gírias e idioleto
- [x] biblioteca inicial de padrões PT-BR
- [x] referências por gênero e registro
- [x] community-pack scaffolds
- [x] analisador determinístico
- [x] Semantic Guard lexical inicial
- [x] wrappers protect_spans/fact_guard
- [x] controle de spans sobrepostos e multiplicidade
- [x] Voice Profile estatístico inicial
- [x] Regional Overfit/Dialect Mixing baseline guard
- [x] Voice Drift baseline
- [x] Audit baseline
- [x] schemas versionados iniciais
- [x] suíte de regressão foundation
- [x] scaffolds de eval por domínio
- [x] corpus/evidence strategy
- [x] competitive benchmark protocol
- [x] benchmark runner determinístico inicial
- [x] model/adapter research track
- [x] validador de pacote
- [x] CI

## v0.2 — Semantic Ledger
- [x] ledger determinístico por sentença (spans + marcadores)
- [ ] ledger estruturado de claims (extração automática; hoje só via juiz)
- [~] entidades/relações: presença de entidades; troca de valores entre entidades; troca de agentes NÃO detectada
- [x] modalidade e negação (léxico E1, concordância negativa, compostos im+possível)
- [x] temporalidade: datas, horas, dias, relativos; antes/depois
- [x] causalidade: causal x correlacional; direção causal invertida NÃO detectada
- [ ] spans protegidos configuráveis pelo usuário
- [x] semantic-loss report (`voznativa compare`) com política conservadora
- [x] contrato de juiz LLM/humano
- [ ] modelo NLI PT-BR opcional (pesquisa: ASSIN2 + BERTimbau/Albertina)
- [ ] holdout escrito por terceiros (os atuais foram escritos pelo mesmo autor do motor)

## v0.3 — Voice Model
- [ ] perfil por canal
- [ ] comparação de voice vectors
- [ ] Voice Drift calibrado por janelas
- [ ] estabilidade em textos longos
- [ ] calibração com amostras consentidas

## v0.4 — PT-BR Pattern Library
- [ ] expandir oficialês deslocado
- [ ] expandir ENEM-ismo
- [ ] expandir gerundismo
- [ ] expandir gerúndio conclusivo
- [ ] expandir conectivos empilhados
- [ ] expandir trios/paralelismos formulaicos
- [ ] expandir linguagem promocional vaga
- [ ] expandir conclusão genérica
- [ ] tradução literal / PT-BR x PT-PT
- [ ] falsos positivos por gênero
- [ ] estrangeirismos por domínio

## v0.5 — Regional Layer
- [ ] taxonomia região/estado/localidade quando houver evidência
- [ ] distinções capital/interior quando sustentadas por dados
- [ ] packs com fonte, período e confiança
- [ ] calibração do Regional Overfit Guard
- [ ] Dialect Mixing contextual
- [ ] avaliação humana regional

## v0.6 — Temporal Slang & Communities
- [ ] léxico temporal real
- [ ] aging/deprecation
- [ ] community packs validados: tech, gaming, academia, engenharia, jurídico, corporativo etc.
- [ ] slang stuffing guard
- [ ] interação comunidade x região x canal

## v0.7 — Rewrite Engine Contract
- [ ] contrato agnóstico de modelo
- [ ] provider adapter interface
- [ ] Context Router executável
- [ ] montagem dinâmica de referências
- [ ] retries por falha dominante
- [ ] compare original/candidate
- [ ] saída JSON/YAML estável

## v0.8 — Evaluation System
- [ ] factual/semantic
- [ ] voice
- [ ] regional
- [ ] false-positive
- [ ] genre
- [ ] adversarial
- [ ] long-form drift
- [ ] temporal slang
- [ ] human review protocol
- [ ] corpus/eval provenance
- [ ] benchmark skill-only reproduzível
- [ ] benchmark system-level reproduzível
- [ ] blind pairwise harness
- [ ] frozen benchmark manifests

## v0.9 — Packaging & Integrations
- [ ] manifests para hosts suportados
- [ ] CLI estável
- [ ] exemplos de integração
- [ ] documentação de extensão de packs
- [ ] política de contribuição de dados linguísticos
- [ ] provider adapter para Emulate/API externa
- [ ] adapters para modelos locais/custom

## Research track — Optional Model / Adapter
- [x] arquitetura e gates documentados
- [ ] candidate generation + reranking
- [ ] dataset contract para adapters pessoais
- [ ] LoRA/PEFT experiment
- [ ] channel holdout
- [ ] domain adapter experiment
- [ ] specialized PT-BR model feasibility study

Essa trilha é opcional e nunca substitui Semantic Ledger, Fact Guard ou evals.

## v1.0 gate

1. Preservação semântica avaliada separadamente da naturalidade.
2. Voice consistency validada em múltiplos gêneros/canais.
3. Regionalidade calibrada com evidência e revisão humana.
4. Falsos positivos medidos.
5. Packs têm proveniência/licença.
6. Regressões bloqueiam release.
7. Nenhuma dependência de "AI detector score".
8. Benchmark competitivo diferencia skill-only de system-level.
9. Qualquer adapter/modelo especializado precisa passar pelos mesmos semantic gates.
