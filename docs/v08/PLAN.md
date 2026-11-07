# Plano da v0.8.0.dev0: Evaluation System & Contextual Intelligence

Plano de execução da rodada v0.8, ajustado ao AS-IS ([`AS_IS.md`](AS_IS.md)) e ao registro de gaps ([`GAP_REGISTER.md`](GAP_REGISTER.md)). Estado e retomada: [`EXECUTION_STATE.md`](EXECUTION_STATE.md); o Git vence este arquivo.

- **Partida:** `main` = `c2708de` (0.7.0.dev1), conferido com `git fetch --prune` em 2026-11-07.
- **Branch:** `dev/v0.8.0`, criada de `main` em `c2708de`.
- **Commits:** por CP, identidade local do repositório (Rafael Souza, noreply Soturine), sem trailers de coautoria. Push da branch ao fim de cada CP com `scripts/checkpoint.py push`, conferido no remoto.
- **CI:** o workflow continua só `workflow_dispatch`. Nenhum run durante os CPs. Um único dispatch na `main` no CP17.
- **Tag e pre-release:** só no CP18 (adendo do mantenedor, 2026-11-07), depois da CI final verde. Sem PyPI, sem release estável.

## Escopo por faixa

| Faixa | Conteúdo nesta rodada |
|---|---|
| MUST | integridade de documento (GAP-01/09), desempenho de spans (GAP-02), instalação e primeiro uso (`doctor`, `demo`, paridade com o wheel), Evaluation Core (schema de caso/run, runner, braços, relatório), splits e contenção, EventFrame mínimo, dogfood Assertiva/Derivanta agent-led, documentação |
| SHOULD | discurso e long-form, avaliadores por eixo e curva do Router, Standards Registry + Applicability Resolver, Rubric Engine com critérios objetivos |
| CONDITIONAL | pilotos ENEM/acadêmico em nível de metadados e critérios objetivos com fontes oficiais verificadas; braços com provider real e revisão humana só com autorização e pessoas reais (senão NOT_RUN com protocolo) |
| FUTURE | LoRA, interface web, scraping, notas oficiais simuladas, geração de trabalhos acadêmicos |

## Checkpoints

| CP | Conteúdo | Gate |
|---|---|---|
| CP0 | AS-IS, gaps, pesquisa, plano, baseline em `c2708de` | baseline registrado; nada de algoritmo muda |
| CP1 | GAP-01 e GAP-09: autorização vem do chamador; `resume` não é autoridade | contrafactuais falham antes e passam depois; plano legítimo, JSON, CRLF, retomada legítima sem regressão; v4/v5 |
| CP2 | GAP-02: perfil, curva, correção com saída idêntica, limites | igualdade exata da saída em corpus congelado e adversarial; curva antes/depois |
| CP3 | DX I: `doctor`, `demo`, mensagens de erro, paridade wheel × checkout (GAP-06) | smoke sdist → wheel → venv fora do checkout, sem `PYTHONPATH` |
| CP4 | Evaluation Core: schema de caso, run, eixos, evidência, relatório | run offline reproduzível; NOT_RUN nunca vira PASS; dados inválidos recusados |
| CP5 | Splits, contenção (GAP-08), congelados byte-idênticos, braços B0–B6 numa API | contenção negativa; congelamento antes de tuning; denominadores e ICs |
| CP6 | EventFrame mínimo, destinatário, troca de evento (GAP-04) | pares contrastivos; nenhum bloqueio crítico novo por sinônimo; v4/v5/predicados sem regressão |
| CP7 | Discurso e long-form | documento misto sem corrupção; guard global pega o que cada unidade não pega |
| CP8 | Avaliadores por eixo; curva do Router (GAP-05) | estratificado; proxies rotulados como proxies |
| CP9 | Benchmark system-level, providers, revisão cega | relatório por braço com NOT_RUN explícito |
| CP10 | Standards Registry + Applicability Resolver (ST-01..ST-04) | regra de 2025 não substitui a de 2023; fonte desconhecida abstém |
| CP11 | Rubric Engine (ST-05) e pilotos | critério sem fonte verificada não vira regra; nenhuma nota oficial |
| CP12 | DX II: CLI, Skill, docs públicas | snippets do README testados; SKILL, README e `--help` coerentes |
| CP13 | Segurança, licenças, threat model | recusa provada nos casos negativos |
| CP14 | Assertiva agent-led (GAP-03) | findings com disposição e contrafactual; mutação dirigida |
| CP15 | Derivanta Engine/Framework agent-led | nenhum `NOT_OBSERVED` tratado como ausência |
| CP16 | Versão `0.8.0.dev0`, qualificação multiplataforma, `EVIDENCE_PATHS` da v0.8 (GAP-11) | gates locais PASS; pendências externas nomeadas |
| CP17 | Fast-forward da `main`, um `workflow_dispatch`, evidência | run verde verificado ao vivo no SHA do código |
| CP18 | Tag anotada `v0.8.0.dev0` e GitHub pre-release (adendo) | ver abaixo |

### CP18 — Tag e GitHub pre-release (adendo de 2026-11-07)

Pré-condições, todas conferidas e registradas antes de qualquer escrita remota:

1. CP0–CP17 concluídos; qualificação final aprovada, com as limitações externas nomeadas.
2. `main` local = `origin/main`, contendo código, docs e evidência.
3. O run único do CP17 está verde e o commit a publicar é equivalente ao testado (`scripts/ci_evidence.py` = `same` ou só evidência depois). Nenhuma CI nova para publicar.
4. Gatilhos de todos os workflows conferidos: nenhum reage a `push` de tag nem a `release`. Se algum reagir, parar e registrar.
5. Nenhuma tag `v0.8.0.dev0` existente (local ou remota). Sem sobrescrever, sem force push.

Passos: tag anotada `v0.8.0.dev0` no commit qualificado; sdist e wheel construídos a partir de `git archive` dessa revisão; smoke de instalação fora do checkout; `SHA256SUMS`; release com `--prerelease --latest=false` e notas em inglês; conferência pela API (tag → commit, `prerelease: true`, ativos e checksums baixados e recalculados); registro em `CHANGELOG.md` e no estado, num commit só de evidência. Se houver bloqueio de segurança, empacotamento ou qualificação: registrar e não publicar.

## Decisões de escopo tomadas no CP0

- **GAP-09 entra no CP1** junto com o GAP-01: mesma classe (dado serializado concedendo autoridade), achado durante a reprodução.
- **Ordem preservada** em relação ao prompt. Nenhum CP fundido; se o tempo apertar, os CONDITIONAL viram backlog qualificado com caminho de execução, nunca alegação.
- **Sem dependência pesada nova** no núcleo. spaCy/Stanza só como adapter opcional se uma medição mostrar ganho (ver [`RESEARCH_LANDSCAPE.md`](RESEARCH_LANDSCAPE.md)).

## Riscos

| Risco | Mitigação |
|---|---|
| Escopo muito maior que uma sessão | CPs pequenos, push por CP, `EXECUTION_STATE.md` atualizado a cada CP para retomada sem contexto oculto |
| Dados escritos na árvore durante gates sujam a qualificação | registros de bench e qualificação gravados depois dos gates, ou no scratchpad |
| Mudança de contrato público (assinaturas de `reassemble`, desfechos) | parâmetro novo com default seguro; mudança anotada no CHANGELOG |
| Tag ou release disparar Actions | gatilhos conferidos no CP18 antes de escrever no remoto |
