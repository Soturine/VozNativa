# Piloto agent-led (v0.8, CP9): a Agent Skill operada por um agente real

**Evidência:** AGENT_OBSERVED. Não é avaliação humana, não é avaliação independente, não é execução com provider externo. Nenhuma API, chave ou serviço pago foi usado.

- **Agente hospedeiro:** a própria sessão do Claude Code que desenvolve a v0.8 (modelo `claude-opus-5-5`), usando só suas ferramentas locais (shell e leitura/escrita de arquivos). O agente é o "modelo" da Skill: lê o `SKILL.md`, roda a CLI, escreve a candidata e o juízo.
- **Revisão do código:** `103414d` (`dev/v0.8.0`), com a correção V08-GAP-16 já aplicada. Windows 10, CPython 3.12.6. Data: 2026-11-07.
- **Procedimento:** o `SKILL.md` dessa revisão, seção "Rewrite (padrão)", seguido ao pé da letra; `VN="python -B scripts/voznativa_cli.py"`.
- **Textos:** três textos autorais do repositório, já publicados sob MIT: `examples/quickstart/original.txt`, `email.txt`, `erros.txt`.
- **Limite principal:** o mesmo agente escreveu a Skill, os detectores e este piloto. O piloto mostra que o procedimento é executável e como se comporta; não mede qualidade editorial.

Artefatos (saídas reais das ferramentas, sem caminhos locais): este diretório.

## P1 — rascunho com fórmulas vazias (`original.txt`)

| Passo | Comando | Saída | Decisão do agente |
|---|---|---|---|
| 1 | `route` | exit 0; gênero `unknown`, canal `unknown` | sem pedido de destino; segue |
| 1 | `patterns` | exit 0; `edit`: 2× `empty_metadiscourse` | há o que mudar |
| 3 | `rewrite-prompt` | exit 0; plano: cortar as duas fórmulas; preservar 14/11/2025, sexta-feira, R$ 12.000,00, "pode", "não" | li as 4 referências listadas (`false-positives`, `pt-br`, `structural`, `rhetorical`); "não reescreva o resto por gosto": só as fórmulas saem |
| 4 | candidata `p1-candidata.txt` | "O relatório trimestral será enviado até sexta-feira, 14/11/2025. O orçamento não pode ultrapassar R$ 12.000,00." | — |
| 5 | `compare` | exit 3, `no_deterministic_issues`, `unverified`; só `metadiscourse_changed` (info) | vai ao juiz |
| 6 | `judge-prompt`, `p1-juizo.json`, `compare --judgment` | exit 3; `agent_assessment` com `AGENT_OBSERVED`; `requires: independent_judgment` | autoavaliação registrada sem aprovar (GAP-16) |
| 7 | entrega | a candidata + "verificada pelos gates e avaliada por mim, não por juiz independente" | — |

**P1b (variante exploratória).** Considerei uma versão mais idiomática: "O orçamento tem teto de R$ 12.000,00". `compare` deu exit 1 (`fail`: `negation_changed` e `modality_changed` críticos). Pela leitura do agente, "tem teto de" equivale a "não pode ultrapassar"; o gate não consegue verificar essa paráfrase e reprova por conservadorismo. O `SKILL.md` manda corrigir os itens críticos e repetir: a tentativa 2 restaurou "não pode ultrapassar", deu exit 3 e ficou idêntica à candidata de P1. **O ciclo de rejeição e correção funcionou como descrito.** Custo observado: um falso vermelho em paráfrase legítima que troca negação por noção de limite (registrado em limitações, não corrigido afrouxando o gate).

## P2 — e-mail que já serve (`email.txt`)

| Passo | Comando | Saída | Decisão |
|---|---|---|---|
| 1 | `route` | exit 0; gênero `email`, canal `email`, registro `professional-natural` | — |
| 1 | `patterns --genre email` | exit 0; `no_change_candidate`, nenhum achado | teste de intenção do `false-positives.md`: nada atrapalha a leitura, nada sem informação, adequado ao gênero; sem pedido de mudança |
| — | — | — | **NO_CHANGE**, sem candidata e sem chamar modelo, com o motivo |

## P3 — erro formal e contradição (`erros.txt`), pedido "revise este texto"

| Passo | Comando | Saída | Decisão |
|---|---|---|---|
| 1 | `route`, `patterns` | exit 0; `no_change_candidate`, nenhum achado | **seguindo só a seção "Rewrite (padrão)", a resposta seria NO_CHANGE** |
| — | `plan` | exit 0; `no_change` | idem |
| — | leitura do agente | "o o" repetido; terça-feira × 13/11/2026 | os detectores do fluxo padrão não veem nenhum dos dois |
| — | `diagnose` (seção "Erros do original", fora do fluxo padrão) | exit 0; `formal_error`/`repeated_word` (`auto_fix`), `internal_contradiction`/`weekday_date_mismatch` (`suggest`) | corrigir só o formal; a contradição é do autor |
| — | `rewrite --mode PROOFREAD` | exit 3, `needs_judgment`; aplicou "o o" → "o" | candidata `p3-candidata.txt` |
| 5 | `compare` | exit 3, nenhum issue | juiz |
| 6 | `p3-juizo.json`, `compare --judgment` | exit 3; `agent_assessment` | sem aprovação |
| 7 | entrega | texto corrigido + "13/11/2026 é sexta-feira, não terça; mantive como está: confirme qual dos dois vale" | — |

## O que o piloto mostrou

| Requisito do mantenedor | Resultado |
|---|---|
| Ler e seguir o `SKILL.md` real | feito, com os comandos reais e as referências que o prompt listou |
| Analisar contexto, gênero, intenção, voz e significado | feito pelo agente; o Router abstém em P1 e acerta em P2 |
| Executar os comandos | 18 execuções da CLI (P1: 6, P1b: 2, P2: 2, P3: 8), com exit codes registrados acima |
| NO_CHANGE quando apropriado | P2 |
| Gerar candidata com justificativa | P1, P3 |
| `compare`, achados e correção de candidata rejeitada | P1b: `fail` → correção → exit 3 |
| Juízo com vínculo original/candidata/versão/avaliador | `p1-juizo.json`, `p3-juizo.json`: hashes do BINDING, `judge_id`, `generator_relation: same_agent` |
| Autoavaliação nunca como juízo independente | as duas viraram `agent_assessment`, exit 3 |
| Casos não previstos pelos detectores | **lacuna encontrada (V08-GAP-17):** o fluxo padrão da Skill decide NO_CHANGE sem rodar `diagnose`, então erro formal e contradição passam calados se o agente seguir só o procedimento |

## Limitações

- Um agente, uma sessão, três textos curtos escritos pelo mesmo autor do engine. Nada aqui é estatística.
- O agente conhecia os textos e os detectores; um agente sem esse contexto pode errar de outro jeito. A validação com outro agente (Codex, Gemini CLI) e com pessoas continua NOT_RUN.
- Falso vermelho observado em P1b é custo conhecido do gate conservador.
