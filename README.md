# VozNativa

> Motor de voz escrita para português brasileiro: reescrita contextual, preservação semântica verificável, voz do autor por canal e regionalidade só com evidência.

VozNativa não tenta responder "como um humano escreve?". A pergunta é:

> **Como esta pessoa escreveria este conteúdo, neste canal, para este público, sem perder fatos, intenção ou registro?**

É uma Agent Skill (Claude Code, Codex, Gemini CLI e outros hosts compatíveis com `SKILL.md`) e um pacote Python com CLI que verifica cada reescrita antes de ela ser entregue.

## Princípios

1. **Significado antes de estilo.**
2. **Voz antes de "humanidade".**
3. **Contexto antes de regra.**
4. **Regionalidade sem caricatura.**
5. **Observação linguística não vira inferência de identidade.**
6. **Código para o determinístico.**
7. **LLM para semântica, pragmática, tom e reescrita.**
8. **Sem promessa de evasão de detectores.**
9. **Progressive disclosure.**
10. **Mudanças precisam de regressão/evidência.**

## Como funciona

```text
texto ─▶ route ─▶ Context Contract (gênero, canal, registro, fontes de fato x amostras de voz)
            │
            ├─▶ refs ─────▶ referências selecionadas sob orçamento de palavras
            ├─▶ profile ──▶ Voice Profile v2 (estatísticas, sem texto bruto)
            └─▶ contract ─▶ Voice Contract (precedência de references/VOICE_STACK.md)
                              │
patterns + ptbr + ledger ─▶ plan (o que mudar, por quê, quanto) ──┴─▶ rewrite-prompt / rewrite ─▶ candidata
                                                               │
                          compare / ground ◀───────────────────┘
                               │
             identical · fail · review_required · no_deterministic_issues
                               │
                      juiz LLM ou humano (judge-prompt, --judgment)
```

**Política conservadora:** só a identidade é aceita automaticamente. Passar nos gates determinísticos dá `no_deterministic_issues` com `semantic_equivalence: "unverified"`; equivalência só é registrada com um julgamento vinculado ao sha256 dos dois textos, e um juiz LLM não resolve um `review_required`. Só uma revisão humana **assinada** (`voznativa review`, que exige terminal interativo) resolve; um JSON com `"kind": "human"` sem assinatura válida fica como `human_review_claimed`. O relatório separa o que a assinatura mostra: **integridade** (aqueles bytes foram assinados), **posse da chave** (a chave HMAC padrão em `~/.voznativa/` é um segredo da máquina: o desenvolvedor ou um agente rodando como o mesmo usuário também assina; com `--ssh-key` a chave privada é do revisor), **identidade declarada** (nome digitado, nunca comprovado) e **independência** (no máximo declarada no registro `evals/reviewers/`; revisão HMAC nunca conta como independente). Ninguém sobrescreve um `fail`. Se nenhuma candidata for segura, o engine devolve o original.

## Estado (0.5.0.dev0, em desenvolvimento)

Versão de desenvolvimento, **não qualificada**. Os critérios externos herdados da v0.3.0 continuam abertos: holdout escrito por outra pessoa e rodada de revisão humana cega. O CI (GitHub Actions) voltou a rodar em 2026-11-05: run #123 verde em `40e19e4` (8/8 jobs); desde a v0.6.0 ele só roda por disparo manual no fechamento de cada rodada, e a evidência vale só para a revisão testada (`evals/qualification/external.json`). Plano e situação da v0.5.0 (inclui o hardening da v0.4.0): `docs/PLAN_v0.5.0.md`; anteriores: `docs/PLAN_v0.4.0.md`, `docs/PLAN_v0.3.0.md`. Qualificação local: `python scripts/qualify.py`.

| Componente | Estado |
|---|---|
| Semantic Ledger + `compare` | implementado: valores PT-BR normalizados (números por extenso, durações, "2 da tarde", verbos multiplicadores, dia da semana sem preposição), negação, modalidade, quantificadores, condições, antes/depois, causalidade (também entre frases vizinhas), troca de papéis entre entidades nomeadas (ativa/passiva) e entre substantivos comuns, inversão de ordem temporal, antônimos do léxico, atribuição, orações inventadas, termos protegidos, troca regional que muda o referente; análise sobre cópia canônica (NFC, espaços). Não detecta pronomes nem trocas entre frases |
| Juiz LLM/humano | contrato implementado; votos concordantes (padrão 2); revisão humana assinada; nenhum modelo embarcado |
| Detector de padrões (`patterns`) | biblioteca v2: 27 padrões decididos por gênero, canal, posição, função e frequência, cada um com casos positivos e falsos positivos; descritivo, não é detector de autoria |
| Camada PT-BR | marcas de PT-PT (falsos amigos não são trocados às cegas), estrangeirismos por domínio, tratamento, oralidade x registro |
| Planejador (`plan`) | decide por frase manter, trocar o trecho, cortar a fórmula ou reescrever; lista o que preservar; mede edições fora do plano |
| Context Router + Reference Selector | implementado; gênero `unknown` quando a evidência é fraca |
| Repositório como fonte de fatos (`project`, `ground`) | implementado: rejeita caminho, subcomando e flag inventados |
| Voice Profile v2 + Voice Contract | implementado; distância ao perfil medida no engine; limiares sem calibração com amostras reais |
| Rewrite Engine + providers | implementado: NO_CHANGE sem chamar o modelo quando não há achado, reescrita dirigida aos achados, nova tentativa após recusa do juiz, retries de provider; executado com claude-sonnet-5-5 (`docs/EVALUATION.md`, `examples/`) |
| Benchmark | `ptbr-bench-v1` e `-v2` executados (v2 reanalisado em eixos: tarefa, segurança, falha de sistema); `ptbr-bench-v3` congelado, **NOT_RUN**; Emulate não executado (falta chave) |
| Revisão humana cega | instrumento pronto (`blind-*`); **nenhum resultado humano** |
| Regional Evidence Packs | implementado (v0.5.0): contrato versionado, abstenção por padrão, voz do autor vence; **um** pack piloto (`br-norte-lex-mandioca`, ALiB, confiança baixa, sem revisão humana). Fora dele, força efetiva 0 |
| Gíria temporal, community packs | **não calibrados**: força efetiva 0 |
| Corpus | piloto só de metadados do Corpus Carolina; nenhum texto ingerido |
| Adapters/LoRA | não implementados |

Números e limitações: `docs/EVALUATION.md`. Rastreabilidade: `docs/TRACEABILITY.md`.

## Instalar

Requer Python 3.11+. O núcleo semântico (`compare`, `ledger`, `judge-prompt`, `ground`) usa só a biblioteca padrão; roteamento, contrato e perfil usam PyYAML.

```bash
pip install -e .            # instala a CLI `voznativa` e o PyYAML
# ou, sem instalar: python scripts/voznativa_cli.py <comando>
```

O wheel inclui `references/` e `assets/` (em `voznativa/_bundled`), então todos os comandos funcionam sem checkout. `VOZNATIVA_HOME` só serve para apontar para outro checkout, por exemplo com referências editadas.

Como skill:

| Host | Instalação |
|---|---|
| Claude Code | plugin pela marketplace deste repositório (`.claude-plugin/`), ou copie a pasta para `~/.claude/skills/voznativa` |
| Codex | coloque a pasta em `.agents/skills/voznativa` (repositório) ou `~/.agents/skills/voznativa` |
| Gemini CLI | `gemini skills install <url-do-repositório> --consent` ou copie para `.gemini/skills/voznativa` |
| Outros | qualquer host que leia `SKILL.md`; os comandos usam `python <skill>/scripts/voznativa_cli.py` |

O diretório instalado deve se chamar `voznativa` (a spec exige que o nome bata com o `name` do `SKILL.md`).

## Usar a CLI

```bash
voznativa compare original.txt candidata.txt      # gate: exit 0 ok, 1 fail, 2 revisão, 3 precisa de juiz
voznativa ledger texto.txt                         # inventário de valores e marcadores
voznativa route texto.txt --channel email          # Context Contract
voznativa refs texto.txt --budget 4000             # referências a carregar
voznativa profile a1.txt a2.txt --channel whatsapp > perfil.json
voznativa contract texto.txt --profile perfil.json --compact
voznativa rewrite-prompt texto.txt --profile perfil.json   # prompt para o agente responder
voznativa rewrite texto.txt --cmd '["claude", "-p", "--tools", ""]'   # loop completo; ferramentas do agente desligadas
voznativa rewrite texto.txt --cmd '["claude", "-p", "--tools", ""]' --judge-cmd '["claude", "-p", "--tools", ""]' \
  --protect "Projeto Aurora" --judge-votes 2 --provider-env minimal --provider-env-allow ANTHROPIC_API_KEY
voznativa rewrite email.txt --channel whatsapp --cmd ...   # destino explícito: o engine não devolve NO_CHANGE sem tentar
voznativa patterns texto.txt --genre corporate     # achados editoriais; decide edit ou no_change_candidate
voznativa plan texto.txt --genre corporate         # plano de reescrita por frase, sem chamar modelo
voznativa regional packs                           # Regional Evidence Packs disponíveis
voznativa regional check texto.txt --region norte  # o que a região pedida permite, ou por que o sistema se abstém
voznativa judge-prompt original.txt candidata.txt  # prompt do juiz semântico
voznativa review original.txt candidata.txt --reviewer ana --out revisao.json   # revisão humana assinada (só em terminal; nome declarado)
voznativa review original.txt candidata.txt --reviewer ana --ssh-key ~/.ssh/revisao --principal ana@exemplo.org --out revisao.json
voznativa blind-tasks benchmarks/runs/<execução>.json --out tarefas.json   # pares cegos para revisão humana
voznativa blind-review tarefas.json --reviewer ana --out respostas.json
voznativa blind-summary tarefas.json respostas.json   # uma resposta válida por tarefa e chave; lista participantes
voznativa ground doc.md --repo .                   # todo valor/caminho/comando tem fonte?
voznativa judge-prompt pedido.txt doc.md --fact notas.md        # juiz de fundamentação (modo create)
voznativa ground doc.md --request pedido.txt --fact notas.md --judgment juizo.json
voznativa eval evals/semantic/cases.jsonl
voznativa benchmark benchmarks/cases/ptbr-v1.jsonl benchmarks/outputs --manifest m.json
```

`rewrite` termina com um destes desfechos: `accepted`, `needs_judgment`, `needs_review`, `no_change`, `returned_original` (nenhuma candidata segura) ou `provider_error` (o comando do modelo falhou depois dos retries; exit 1). `decision.no_change_reason` distingue os NO_CHANGE: `no_editorial_findings` (sem achado e sem destino pedido; o modelo não é chamado, `--force` chama mesmo assim), `model_found_nothing_to_change` e `model_claims_target_met`. Se o pedido muda o destino (canal ou gênero diferente do texto, registro, público, perfil de voz) e o modelo responde NO_CHANGE, o engine pede de novo e, persistindo, devolve `needs_review`.

**Isolamento do provider.** `--cmd` roda cada chamada num diretório temporário vazio. Isso **não é sandbox**: o processo roda com o seu usuário, lê e escreve qualquer caminho absoluto, acessa a rede e recebe o ambiente (com `--provider-env inherit`, o padrão, todas as credenciais). Para um CLI de agente, desligue as ferramentas (`claude -p --tools ""`, `codex exec --sandbox read-only`, `gemini --sandbox`); o engine avisa quando não estão desligadas. Isolamento de verdade exige contêiner ou sandbox do sistema. O texto do usuário é tratado como material não confiável: cada bloco do prompt fecha com uma marca que carrega o hash do conteúdo, e candidatas que acrescentam marcas do protocolo (`<final>`, veredito) falham.

No Windows, passe arquivos em vez de usar pipe no PowerShell 5.1: ele troca acentos por `?` antes de o texto chegar ao programa. Os scripts de `scripts/*.py` da versão 0.1.0 continuam funcionando com os mesmos argumentos.

## Regionalidade e voz

"Sotaque escrito" é um atalho coloquial: sotaque é fonético. Na escrita, VozNativa trabalha com léxico, morfossintaxe, pragmática, discurso e formas de tratamento. Regionalidade é **distribuição, não decoração**: um pedido "mineiro informal" não autoriza inserir `uai` em toda frase. Regionalidade só entra por um Regional Evidence Pack (`docs/REGIONAL_EVIDENCE.md`) e por uma região que a pessoa pede (`--region`); o sistema nunca deduz a região do texto ou do autor. Sem pack que cubra a região, o gênero e o referente, a força é 0 e o relatório diz por quê. A forma que o autor usa vence a do pack; uma troca que pode mudar o referente (macaxeira → mandioca no Norte) pede revisão; uma forma regional que ninguém pediu é sinalizada.

O Voice Profile observa ritmo, pontuação, abreviações, contrações, termos de comunidade e aberturas, com confiança limitada pelo número de amostras. Ele não guarda o texto nem palavras de tópico e não infere identidade.

## Desenvolvimento

```bash
python scripts/qualify.py                 # todos os gates locais; exit 0 PASS, 1 FAIL, 3 incompleto
python scripts/validate_package.py
python -m unittest discover -s evals -p "test_*.py"
```

Toda correção de comportamento entra com um caso de regressão. Casos novos de eval vão para `evals/semantic/cases.jsonl`; os holdouts são congelados e não são editados depois de rodar.

## Pesquisa e licenças

Projetos e corpora estudados, com versões e decisões: `docs/RESEARCH_LOG.md`. Licenças de terceiros: `docs/LICENSING.md`.

**Licença do VozNativa: ainda não definida** (proposta: Apache-2.0, ver `docs/LICENSING.md`). Até a decisão, não há permissão de reutilização.
