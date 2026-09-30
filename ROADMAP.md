# Roadmap

## v0.1 — Foundation
- [x] visão e arquitetura
- [x] SKILL.md roteador
- [x] pesquisa comparativa
- [x] regras de regionalidade, gírias e idioleto
- [x] analisador determinístico
- [x] Semantic Guard lexical inicial
- [x] controle de spans sobrepostos e multiplicidade
- [x] Voice Profile estatístico inicial
- [x] Regional Overfit/Dialect Mixing baseline guard
- [x] schemas versionados iniciais
- [x] suíte de regressão
- [x] validador de pacote
- [x] CI

## v0.2 — Semantic Ledger
- [ ] ledger estruturado de claims
- [ ] entidades/relações
- [ ] modalidade e negação
- [ ] temporalidade
- [ ] causalidade
- [ ] spans protegidos configuráveis
- [ ] semantic-loss report

## v0.3 — Voice Model
- [ ] perfil por canal
- [ ] comparação de voice vectors
- [ ] Voice Drift por janelas
- [ ] estabilidade em textos longos
- [ ] calibração com amostras consentidas

## v0.4 — PT-BR Pattern Library
- [ ] oficialês deslocado
- [ ] ENEM-ismo
- [ ] gerundismo
- [ ] gerúndio conclusivo
- [ ] conectivos empilhados
- [ ] trios/paralelismos formulaicos
- [ ] linguagem promocional vaga
- [ ] conclusão genérica
- [ ] tradução literal
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
- [ ] community packs: tech, gaming, academia, engenharia, jurídico, corporativo etc.
- [ ] slang stuffing guard
- [ ] interação comunidade x região x canal

## v0.7 — Rewrite Engine Contract
- [ ] contrato agnóstico de modelo
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

## v0.9 — Packaging & Integrations
- [ ] manifests para hosts suportados
- [ ] CLI estável
- [ ] exemplos de integração
- [ ] documentação de extensão de packs
- [ ] política de contribuição de dados linguísticos

## v1.0 gate

1. Preservação semântica avaliada separadamente da naturalidade.
2. Voice consistency validada em múltiplos gêneros/canais.
3. Regionalidade calibrada com evidência e revisão humana.
4. Falsos positivos medidos.
5. Packs têm proveniência/licença.
6. Regressões bloqueiam release.
7. Nenhuma dependência de "AI detector score".
