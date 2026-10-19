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
ledger (spans + marcadores) ──┴─▶ rewrite-prompt / rewrite ─▶ candidata
                                                               │
                          compare / ground ◀───────────────────┘
                               │
             identical · fail · review_required · no_deterministic_issues
                               │
                      juiz LLM ou humano (judge-prompt, --judgment)
```

**Política conservadora:** só a identidade é aceita automaticamente. Passar nos gates determinísticos dá `no_deterministic_issues` com `semantic_equivalence: "unverified"`; equivalência só é registrada com um julgamento, e um juiz LLM não resolve um `review_required` (só um humano resolve). Ninguém sobrescreve um `fail`. Se nenhuma candidata for segura, o engine devolve o original.

## Estado (0.2.0.dev0)

| Componente | Estado |
|---|---|
| Semantic Ledger + `compare` | implementado: valores PT-BR normalizados, negação (com concordância negativa), modalidade, quantificadores, condições, antes/depois, causalidade, compromissos, atribuição |
| Juiz LLM/humano | contrato implementado; nenhum modelo embarcado |
| Context Router + Reference Selector | implementado; gênero `unknown` quando a evidência é fraca |
| Repositório como fonte de fatos (`project`, `ground`) | implementado: rejeita caminho, subcomando e flag inventados |
| Voice Profile v2 + Voice Contract | implementado; limiares heurísticos, sem calibração |
| Rewrite Engine + providers | implementado (`command`, `static`, `emulate` opcional); não testado com modelo real neste ambiente |
| Benchmark | tier determinístico + julgamentos por tipo; nenhuma execução real publicada |
| Packs regionais, gíria temporal, community packs | **não calibrados**: força efetiva 0 |
| Avaliação humana, corpus ingerido, adapters/LoRA | não implementados |

Números e limitações: `docs/EVALUATION.md`. Rastreabilidade: `docs/TRACEABILITY.md`.

## Instalar

Requer Python 3.11+. O núcleo semântico (`compare`, `ledger`, `judge-prompt`, `ground`) usa só a biblioteca padrão; roteamento, contrato e perfil usam PyYAML.

```bash
pip install -e .            # instala a CLI `voznativa` e o PyYAML
# ou, sem instalar: python scripts/voznativa.py <comando>
```

Com `pip install .` (não editável), `refs`, `contract`, `profile` e `rewrite` precisam de `VOZNATIVA_HOME` apontando para um checkout, porque `references/` não vai dentro do pacote.

Como skill:

| Host | Instalação |
|---|---|
| Claude Code | plugin pela marketplace deste repositório (`.claude-plugin/`), ou copie a pasta para `~/.claude/skills/voznativa` |
| Codex | coloque a pasta em `.agents/skills/voznativa` (repositório) ou `~/.agents/skills/voznativa` |
| Gemini CLI | `gemini skills install <url-do-repositório> --consent` ou copie para `.gemini/skills/voznativa` |
| Outros | qualquer host que leia `SKILL.md`; os comandos usam `python <skill>/scripts/voznativa.py` |

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
voznativa rewrite texto.txt --cmd "claude -p"      # loop completo com qualquer CLI de modelo
voznativa judge-prompt original.txt candidata.txt  # prompt do juiz semântico
voznativa ground doc.md --repo .                   # todo valor/caminho/comando tem fonte?
voznativa eval evals/semantic/cases.jsonl
voznativa benchmark benchmarks/cases/ptbr-v1.jsonl benchmarks/outputs --manifest m.json
```

No Windows, passe arquivos em vez de usar pipe no PowerShell 5.1: ele troca acentos por `?` antes de o texto chegar ao programa. Os scripts de `scripts/*.py` da versão 0.1.0 continuam funcionando com os mesmos argumentos.

## Regionalidade e voz

"Sotaque escrito" é um atalho coloquial: sotaque é fonético. Na escrita, VozNativa trabalha com léxico, morfossintaxe, pragmática, discurso e formas de tratamento. Regionalidade é **distribuição, não decoração**: um pedido "mineiro informal" não autoriza inserir `uai` em toda frase. Enquanto não houver pack com proveniência e revisão humana, a força regional efetiva é 0 e o guard regional só detecta exagero.

O Voice Profile observa ritmo, pontuação, abreviações, contrações, termos de comunidade e aberturas, com confiança limitada pelo número de amostras. Ele não guarda o texto nem palavras de tópico e não infere identidade.

## Desenvolvimento

```bash
python scripts/validate_package.py
python -m unittest discover -s evals -p "test_*.py"
```

Toda correção de comportamento entra com um caso de regressão. Casos novos de eval vão para `evals/semantic/cases.jsonl`; os holdouts são congelados e não são editados depois de rodar.

## Pesquisa e licenças

Projetos e corpora estudados, com versões e decisões: `docs/RESEARCH_LOG.md`. Licenças de terceiros: `docs/LICENSING.md`.

**Licença do VozNativa: ainda não definida** (proposta: Apache-2.0, ver `docs/LICENSING.md`). Até a decisão, não há permissão de reutilização.
