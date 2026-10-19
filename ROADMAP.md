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
- [x] perfil por canal (`channels` no Voice Profile v2)
- [x] comparação de voice vectors normalizados (`voznativa drift --profile`)
- [~] Voice Drift por janelas (normalizado; limiar NÃO calibrado)
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

## Pesquisa/decisões pendentes
- [ ] licença do repositório (proposta Apache-2.0 em `docs/LICENSING.md`)
- [ ] resolver o conflito de licença do Corpus Carolina antes de qualquer ingestão
- [ ] holdout semântico escrito por outra pessoa
- [ ] execução real do benchmark (B0–B5) com manifesto e juízes
- [ ] calibração dos limiares do `compare` e do drift com reescritas reais

## v0.7 — Rewrite Engine Contract
- [x] contrato agnóstico de modelo
- [x] provider adapter interface (command, static, emulate)
- [x] Context Router executável
- [x] montagem dinâmica de referências (orçamento de palavras)
- [x] retries por falha dominante
- [x] compare original/candidate
- [x] saída JSON estável (`kind` + `schema_version` em cada relatório)

## v0.8 — Evaluation System
- [x] factual/semantic (dev + 2 holdouts)
- [ ] voice
- [ ] regional
- [~] false-positive (casos `false_red` e NO_CHANGE; sem detector de edição desnecessária)
- [ ] genre
- [~] adversarial (limitações conhecidas viram casos `known_limitation`)
- [ ] long-form drift
- [ ] temporal slang
- [ ] human review protocol
- [~] eval provenance (hashes congelados; corpus não ingerido)
- [~] benchmark skill-only: runner, casos e manifesto prontos; execução real não feita
- [ ] benchmark system-level reproduzível
- [ ] blind pairwise harness
- [x] frozen benchmark manifests (`cases_sha256`, `manifest.example.json`)

## v0.9 — Packaging & Integrations
- [x] manifests para hosts suportados (Claude Code plugin, Codex `openai.yaml`; Gemini via SKILL.md)
- [~] CLI (`voznativa`); estável só a partir da 1.0
- [ ] exemplos de integração
- [ ] documentação de extensão de packs
- [ ] política de contribuição de dados linguísticos
- [~] provider adapter para Emulate (não validado ao vivo)
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
