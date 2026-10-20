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
- [ ] ledger estruturado de claims (extração automática; hoje só via juiz) → pesquisa em v0.3.0 M1
- [~] entidades/relações: presença; troca de valores, de agentes e de atribuições (troca mútua); NÃO detecta pronomes, inversão ativa/passiva com a mesma ordem, fontes em minúscula
- [x] modalidade e negação (léxico E1, concordância negativa, compostos im+possível)
- [x] temporalidade: datas, horas, dias, relativos; antes/depois
- [x] causalidade: causal x correlacional; direção invertida dentro da frase (orientação dos conectores, causativas fazer/levar); entre frases NÃO detectada
- [~] antônimos: 13 pares do léxico de polaridade; antônimos fora do léxico NÃO detectados
- [x] julgamentos vinculados ao sha256 dos textos; revisão humana assinada (`voznativa review`)
- [ ] spans protegidos configuráveis pelo usuário → v0.3.0 M1
- [x] semantic-loss report (`voznativa compare`) com política conservadora
- [x] contrato de juiz LLM/humano
- [ ] modelo NLI PT-BR opcional (pesquisa: ASSIN2 + BERTimbau/Albertina) → v0.3.0 M1
- [ ] holdout escrito por terceiros (os atuais foram escritos pelo mesmo autor do motor) → v0.3.0 M4

## v0.3.0 — Semantic Intelligence & Author Voice (em andamento)

Plano, work packages e critérios obrigatórios: `docs/PLAN_v0.3.0.md`. Não será marcada como concluída enquanto houver critério obrigatório pendente (holdout independente, revisão humana cega e CI dependem de terceiros).

### M1 — Semantic Intelligence
- [ ] holdout prospectivo v0.3 congelado antes das correções
- [ ] adições dentro da frase (novidade por oração; regressão ho-007)
- [ ] números por extenso compostos e equivalências
- [ ] causalidade entre frases adjacentes
- [ ] papéis agente/paciente em voz ativa/passiva
- [ ] spans protegidos configuráveis pelo usuário (de v0.2)
- [ ] experimento de sintaxe opcional (spaCy) — adotar só com ganho medido
- [ ] experimento de NLI PT-BR opcional (de v0.2) — relatório de viabilidade

### M2 — PT-BR Writing Quality
- [ ] detector de padrões operacional com isenções por gênero (absorve v0.4)
- [ ] decisão de NO_CHANGE e reescrita dirigida aos achados, validada em execução real
- [ ] planejamento por documento — só com ganho medido

### M3 — Author Voice
- [x] perfil por canal (`channels` no Voice Profile v2)
- [x] comparação de voice vectors normalizados (`voznativa drift --profile`)
- [~] Voice Drift por janelas (normalizado; limiar NÃO calibrado)
- [ ] voice match mensurável no relatório do engine
- [ ] estabilidade em textos longos
- [ ] calibração com amostras consentidas (bloqueado: depende de amostras reais)

### M4 — Evidence & Benchmarks
- [ ] dataset de benchmark congelado antes da execução
- [ ] benchmark skill-only com o mesmo LLM (raw, prompt simples, blader, work-humanizer, VozNativa) (de v0.8)
- [ ] benchmark system-level com Emulate (bloqueado: chave de API) (de v0.8)
- [ ] instrumento de revisão humana cega (de v0.8)
- [ ] rodada de revisão humana registrada (depende de pessoas)
- [ ] holdout independente executado (depende de outra pessoa)

### M5 — Corpus Pilot
- [ ] ingestão metadata-only de um recorte do Corpus Carolina

### M6 — Release Qualification
- [ ] retries e erros de provider sem derrubar o engine
- [ ] privacidade em relatórios de integração
- [ ] exemplos reais antes/depois
- [ ] matriz de compatibilidade final
- [ ] CI verde (bloqueado: cobrança do GitHub Actions)

## v0.4 — PT-BR Pattern Library
- [ ] expandir oficialês deslocado → v0.3.0 M2
- [ ] expandir ENEM-ismo → v0.3.0 M2
- [ ] expandir gerundismo → v0.3.0 M2
- [ ] expandir gerúndio conclusivo
- [ ] expandir conectivos empilhados → v0.3.0 M2
- [ ] expandir trios/paralelismos formulaicos
- [ ] expandir linguagem promocional vaga → v0.3.0 M2
- [ ] expandir conclusão genérica → v0.3.0 M2
- [ ] tradução literal / PT-BR x PT-PT
- [ ] falsos positivos por gênero → v0.3.0 M2
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
- [ ] resolver o conflito de licença do Corpus Carolina antes de qualquer ingestão (o piloto metadata-only da v0.3.0 M5 não ingere texto)
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
- [ ] voice → v0.3.0 M3
- [ ] regional
- [~] false-positive (casos `false_red` e NO_CHANGE; sem detector de edição desnecessária)
- [ ] genre
- [~] adversarial (limitações conhecidas viram casos `known_limitation`)
- [ ] long-form drift → v0.3.0 M3
- [ ] temporal slang
- [ ] human review protocol → v0.3.0 M4
- [~] eval provenance (hashes congelados; corpus não ingerido)
- [~] benchmark skill-only: runner, casos e manifesto prontos; execução real não feita → v0.3.0 M4
- [ ] benchmark system-level reproduzível → v0.3.0 M4
- [ ] blind pairwise harness → v0.3.0 M4
- [x] frozen benchmark manifests (`cases_sha256`, `manifest.example.json`)

## v0.9 — Packaging & Integrations
- [x] manifests para hosts suportados (Claude Code plugin, Codex `openai.yaml`; Gemini via SKILL.md)
- [~] CLI (`voznativa`); estável só a partir da 1.0
- [ ] exemplos de integração → v0.3.0 M6
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
