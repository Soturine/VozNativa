# Perfil de engenharia derivado (Derivanta Framework)

Interpretação da Constituição de Engenharia do Derivanta (`Derivanta/constitution/ENGINEERING_CONSTITUTION.md`, revisão `218761d`) para o VozNativa. É um artefato **derivado**: não redefine requisitos aprovados (README, SKILL.md, `docs/DESIGN_SPEC.md`, planos de versão) e é atualizado quando o contexto muda. Escrito em 2026-11-05 sobre `4044cfc`.

## Composição

```yaml
project:
  type: [python-library, cli, agent-skill, llm-using-system, nlp-pipeline, semantic-preservation-evaluator]
  lifecycle: pre-release (0.x .dev0), single maintainer
languages: [{name: python, versions: "3.11-3.13"}]
runtime_dependencies: [PyYAML]          # o núcleo semântico é stdlib
external_boundaries:
  - model provider command (claude -p, codex, gemini, Emulate API)   # não confiável, custo, latência
  - Agent Skill hosts (Claude Code, Codex, Gemini CLI)               # leem SKILL.md
  - corpora e skills de terceiros                                     # licença, privacidade
quality_priorities:
  critical: [semantic preservation, evidence honesty, privacy of user text]
  important: [portability Windows/Linux, reproducibility, bounded cost, no invented identity/region]
risk_domains: [untrusted text input, prompt injection, personal data in text and voice samples,
               provider credentials, licensing of corpora and third-party skills]
external_reference_profiles: [OWASP_GENAI_AGENT_SECURITY_PROFILE, NIST_AI_SECURE_DEVELOPMENT_PROFILE]
not_applicable: [persistence/transactions, multi-tenancy, availability SLOs, RTO/RPO (CLI local, sem serviço)]
```

## Requisitos e casos de uso

| Caso de uso | Comando | Contrato observável |
|---|---|---|
| verificar uma reescrita | `compare` | exit 0 idêntico, 1 fail, 2 revisão, 3 precisa de juiz; JSON `voznativa.comparison` |
| reescrever com verificação | `rewrite` | desfechos `accepted`, `needs_judgment`, `needs_review`, `no_change`, `returned_original`, `provider_error` |
| planejar sem modelo | `plan`, `patterns` | decisão `no_change` / `edit` / `transform`, escopo, frases a manter |
| contexto e voz | `route`, `refs`, `profile`, `contract`, `drift` | Context Contract, Voice Profile v2 sem texto bruto, Voice Contract com precedência de `references/VOICE_STACK.md` |
| texto criado a partir de fontes | `ground`, `judge-prompt --fact` | toda afirmação ligada a uma fonte autorizada |
| avaliação | `eval`, `benchmark`, `blind-*`, `review` | relatórios com proveniência; julgamento humano só assinado |
| regionalidade (v0.5) | `region`, `regional` | ativação só com pack de evidência compatível; abstenção caso contrário |

## Invariantes (fonte: README "Política conservadora", SKILL.md)

1. Só a identidade é aceita automaticamente; `no_deterministic_issues` mantém `semantic_equivalence: unverified`.
2. Nenhum julgamento sobrescreve `fail`; juiz LLM não resolve `review_required`; só revisão humana assinada resolve.
3. Sem candidata segura, devolve o original.
4. `provider_error` é um desfecho próprio e **nunca** conta como tarefa concluída (H2).
5. Holdouts e manifestos de benchmark congelados não são editados depois da primeira execução.
6. Regionalidade: força efetiva 0 sem pack de evidência; voz observada do autor vence marcadores regionais genéricos; o sistema nunca infere origem, identidade ou traços da pessoa.
7. Relatórios gravados com `--redact` não guardam texto, credenciais nem caminhos absolutos.

## Estados e transições do `rewrite` (`voznativa/engine.py`)

```text
start ─ plan.decision == no_change e sem --force ─────────────────────────▶ no_change (modelo não chamado)
  │
  ├─ ProviderError (depois dos retries do provider) ─────────────────────▶ provider_error (texto original)
  │
  └─ tentativa k (1..attempts)
        candidatas → validate_candidate (compare/ground + protocolo + região + drift + PT-BR)
        ├─ todas fail ─────────────── feedback da falha dominante ──▶ tentativa k+1
        ├─ NO_CHANGE e destino pedido difere, k < attempts ─────────▶ tentativa k+1
        ├─ limpa + juiz: fail, k < attempts ────────────────────────▶ tentativa k+1
        └─ escolhida ─▶ terminal
terminal:
  NO_CHANGE com destino pedido ─▶ needs_review
  NO_CHANGE sem destino        ─▶ no_change
  accepted_by_llm/human        ─▶ accepted
  no_deterministic_issues      ─▶ needs_judgment
  review_required/human_claimed─▶ needs_review
  fail (juiz)                  ─▶ returned_original
tentativas esgotadas sem candidata ─▶ returned_original
```

Estados terminais e o texto entregue: só `accepted`, `needs_judgment` e `needs_review` entregam a candidata; os demais entregam o original.

## Fronteiras de confiança

| Fronteira | Ameaça | Controle existente | Lacuna |
|---|---|---|---|
| texto do usuário → prompt | injeção de instrução | cercas com hash, tokens de protocolo reprovam a candidata, aviso `embedded_instruction` do planejador | depende do modelo não obedecer; o gate só pega efeitos detectáveis |
| saída do modelo → engine | candidata/juízo não confiável | `compare`, validação do juízo, hashes vinculados pelo engine | juiz é o mesmo modelo (viés) |
| engine → processo do provider | execução com o usuário | diretório temporário vazio, `--provider-env minimal`, árvore de processos, limite de saída | **não é sandbox**: rede, disco e credenciais herdadas |
| relatórios → repositório público | vazamento de texto/credencial/caminho | `--redact`, HMAC com chave não gravada, `assurance_record.py` sanitiza caminhos | revisão manual antes de publicar execuções reais |
| corpora/skills de terceiros | licença, dados pessoais | só metadados (Carolina), skills buscadas por hash no benchmark | licença do próprio repositório indefinida |

## Requisitos de teste e qualificação

- Todo comportamento corrigido entra com teste cujo oráculo é o comportamento (valor/estado observável), não a implementação.
- Suítes congeladas: hash conferido e conjunto de suítes congeladas fixado (falso verde NC1 do CP0).
- Gate local único: `scripts/qualify.py` (H1), exit codes preservados, estados PASS/FAIL/BLOCKED/NOT_RUN/SKIPPED/INCONCLUSIVE/WAIVED_BY_OWNER.
- Avaliação separa segurança semântica, sucesso da transformação, falha de provider, avaliação pendente e preferência humana (H2).
- Assurance independente: Assertiva (auditoria da suíte, mutação direcionada) e Derivanta Engine (inspeção e comparação entre checkpoints); nenhum dos dois é revisão humana independente.

## Desempenho, custo, compatibilidade

- Pipeline determinístico: latência medida em `evals/perf/`; `compare` domina (≈6–7 s em 8 mil palavras).
- Custo: só chamadas de modelo custam; benchmark v2 US$ 4,64. Nova execução paga exige justificativa de valor.
- Compatibilidade declarada: Python 3.11–3.13, Windows e Linux; matriz local em `evals/compat/`; CI remoto por disparo manual (último verde: run #123 em `40e19e4`).

## Achados estruturais do CP1 (insumo do CP4)

| Item | Fonte | Estado |
|---|---|---|
| `_NUMBER_WORD_ALT` sem uso (`spans.py`) | Engine `LIKELY_DEAD`, confirmado por busca | código morto: remover |
| `RELATIONSHIPS` definido e nunca usado (`review.py`) | Engine `UNKNOWN_DYNAMIC`; leitura | funcionalidade parcial: o registro de revisores não é validado contra os valores aceitos |
| `--task` do CLI repete `router.TASKS` | Engine duplicação | duas fontes da mesma lista: usar `TASKS` |
| `OPAQUE_TYPES` (ledger) x `HARD_TYPES` (spans) | Engine duplicação | contextual: conjuntos com semânticas diferentes que se sobrepõem por definição |
| sem ciclos de import em nível de módulo | análise AST | `cli` importa sob demanda; `ptbr→router→project` são imports tardios sem ciclo |
| `planner.plan` (53 caminhos), `engine._rewrite` (44) | Engine complexidade | candidatos de refatoração só com motivo de engenharia (H5) |
| benchmark conta `provider_error` como invariantes ok | leitura do scorer e da execução oficial | defeito de avaliação (H2) |
| baseline lê unittest pela última linha do stderr | leitura | defeito de evidência (H1) |

## Política de generalização e anti-overfitting (v0.7.0)

Regra central: **uma correção localizada não vira alegação de melhoria geral sem transferência para casos nunca usados para desenvolvê-la e sem controles negativos relevantes.**

1. **Corpus é evidência, não regra.** Nenhum código pode depender do nome de uma fonte, autor, editora ou edição (`if "Gutenberg"`, `if author == "Machado"`). Teste obrigatório: trocar a fonte/autor do caso mantém a decisão.
2. **Casos de desenvolvimento ≠ casos de aceitação.** O caso que revelou um defeito (ex.: G1 no Machado) entra como regressão; a alegação de melhoria exige casos novos escritos antes da execução e de outro gênero/época/estrutura, mais um controle negativo (o comportamento antigo correto continua correto).
3. **Suítes congeladas não são alvo.** Benchmarks e holdouts v1–v4 não são editados, reordenados nem reanotados; um oráculo errado vira suíte nova com justificativa.
4. **Métricas separadas.** Nenhum percentual único soma eixos incomparáveis; pior grupo e tamanho de amostra aparecem ao lado da média.
5. **Abstenção é resultado.** Sem evidência suficiente, `unknown` com proteções conservadoras; nunca um palpite confiante.
6. **Controles de falso positivo.** Todo detector novo ou ampliado tem casos que **não** devem disparar (ex.: "de boa qualidade" para G3; WhatsApp real para G1; artigos do mesmo tema para G2).
7. **Escopo da alegação.** Um resultado vale para os gêneros, épocas e variedades medidos; combinações não observadas ficam declaradas como não cobertas.

## ADRs

Nenhuma decisão desta rodada justificou ADR até aqui. O contrato de Regional Evidence Pack (CP5) é decisão material e terá registro próprio.
