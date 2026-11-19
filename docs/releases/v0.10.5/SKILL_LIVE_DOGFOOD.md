# A Skill usada por um agente real (R5)

> Host: **Claude Code 2.1.317**, modelo escritor **Haiku**, em um projeto novo para cada execução, com a Skill do VozNativa da versão sob teste instalada em `.claude/skills/voznativa/` (v0.10.5: `SKILL.md` sha256 `069d1e13…`, revisão `8f5ffc1`). O pedido **nunca nomeia a Skill**: o agente recebe o texto em `texto.txt` e um pedido comum ("Revise este resumo para clareza e concisão…") e grava a resposta em `final.txt`. Harness: `scripts/v0105_host_session.py`, chamado por `scripts/v0105_live_arms.py`. Cada ferramenta usada e cada comando do VozNativa ficam registrados; na página pública só entram os **nomes dos subcomandos**, porque os comandos brutos carregam caminhos locais.

## Ativação e uso do fluxo

| | v0.10.0 | v0.10.5 |
|---|---|---|
| Sessões (12 tarefas × 3 repetições) | 36 | 36 |
| Skill ativada sem ser nomeada | 13 | **28** |
| Algum comando do VozNativa **antes** de escrever (`plan`, `route`, `diagnose`, `context`, `rewrite-prompt`) | 3 | **16** |
| `compare` antes de entregar | 9 | **16** |
| Skill ativada, mas nenhum comando rodado | 3 | 10 |
| Turnos (mediana) | 6 | 11 |
| Tempo (mediana) | 20,0 s | 29,7 s |
| Custo total do braço | US$ 0,36 | US$ 0,42 |
| Holdout (6 tarefas, uma vez): Skill ativada | 1/6 | **6/6** |

Ativação observada no log de ferramentas do host (chamada à ferramenta `Skill`), não inferida. As sessões em que a Skill não foi ativada na v0.10.5 concentram-se em pedidos estreitos: T10 (adaptar para divulgação, 3/3), T04 (só ortografia, 2/3), T11 (só corrigir erros, 2/3), T05 (1/3).

Das sessões da v0.10.5 que chamaram o CLI, 16 passaram `--attr pedido=…` (o contexto aberto da v0.10 chegou ao agente, V105-GAP-02) e 2 não. Nenhuma chamou `rewrite-prompt`.

**Leitura.** A descrição nova da Skill (V105-GAP-09) e o fluxo mínimo `plan → candidata → compare` mudaram o comportamento de forma grande e consistente, também no holdout. Mas o fluxo **ainda é pulado em 20 de 36 sessões** (V105-GAP-01 fica PARTIAL), e em 10 sessões o agente ativa a Skill e não roda nada.

## Decisão de editar ou não

Expectativa congelada com cada tarefa no CP0 (`devolver igual`, `editar`; as tarefas "pode editar" não entram na conta).

| | v0.10.0 | v0.10.5 |
|---|---|---|
| Decisões certas | 14/21 | **19/21** |
| Editou texto que devia voltar igual | 7 | **2** |
| Devolveu igual quando devia editar | 0 | 0 |

Controle: o LLM direto, que não usa o VozNativa, foi de 9 para 10 edições indevidas no mesmo período. A melhora da Skill não é variação do modelo.

Os dois erros restantes: T02 rep. 1 (conto; o agente rodou só `compare`) e T12 rep. 1 (diálogo; nenhum comando).

## Qualidade pelo juiz cego

Juiz Sonnet, mesmo fornecedor (`same_vendor`, `MODEL_JUDGED`), cego a braço e versão, com o original entre as candidatas. Critério R6: uma tarefa conta como ganho ou perda só se aparecer em ≥ 2 das 3 repetições.

| Eixo | Ganho | Perda | Empate |
|---|---|---|---|
| Fidelidade | 3 | 0 | 9 |
| Atende ao pedido | 1 | **5** | 6 |
| Naturalidade | 1 | **4** | 7 |

**Não é ganho de qualidade; é uma troca** (V105-GAP-16). A Skill da v0.10.5 erra menos ao decidir não mexer e preserva mais, mas nas tarefas de edição entrega menos do que foi pedido. A causa observada nas sessões: o agente lê `review_required` como bloqueio e desfaz a edição. No T08 ele escreveu: "Mantive o verbo 'incluiu', porque o gate detectou que removê-lo perdia uma ação". O sinal do gate ali é correto ("revisão de literatura de artigos" apaga o verbo; "que incluiu" → "incluindo" passa limpo, conferido).

Risco observado (V105-GAP-17): no T05 a Skill entregou dizendo "mantive todas as ideias", e o juiz apontou erro crítico de sentido. O `compare` não achou nada determinístico, o que na Skill significa `unverified`; o agente não repassou isso.

## Casos em que a Skill não devia reescrever

| Caso | Resultado na v0.10.5 |
|---|---|
| Poema ("Melhore este poema", T03 e holdout H02) | T03: 0 de 3 edições (v0.10.0: 3 de 3); H02: devolveu igual |
| Diálogo literário ("Revise este diálogo", T12, H06) | 1 edição em 3 (v0.10.0: 3 de 3); H06: igual |
| Resumo acadêmico, "corrija apenas erros" (T11, H05) | T11: igual 3/3; H05: editou (erro) |
| Texto que não é português (READMEs em inglês) | `language: en`, `decision: no_change` nos três |

## Primeiro uso e falhas do host

- Projeto limpo, Skill copiada para `.claude/skills/`: descoberta automática funciona sem configuração global.
- Piloto da v0.10.0: o harness não dava a ferramenta `Edit` ao agente (V105-HARNESS-01, corrigido antes da campanha).
- Limite de 5 horas da conta atingido no meio da campanha: 83 execuções gravadas como resultado (V105-HARNESS-02). Campanha refeita do zero; nenhuma execução sem resposta do provider entrou nos números acima.

## O que não foi testado

Codex, Gemini CLI e outros hosts; modelo escritor diferente de Haiku; revisão humana das saídas. Tudo `NOT_RUN`.

## Continuação (19/11): causa dos pulos, `SKILL.md` revisada e holdout prospectivo

**Causa dos pulos (V105-GAP-01).** 12 sessões da campanha e 6 sondagens com o resultado de cada ferramenta registrado:
- **O host não é a causa principal.** As negações de permissão vieram de comandos compostos (`…; echo "exit=$?"`), e em 6/6 o agente refez o comando e seguiu.
- **"Erros" do Bash** eram o código de saída do `compare` (1, 2 ou 3, que é o protocolo).
- **Os pulos são decisão do modelo e variam entre execuções:** 6 decisões de não mudar tomadas só por leitura (poema, ortografia já atual, "corrija só erros"), 4 edições entregues sem gate e 2 com `compare` só depois de escrever. O mesmo T08 rodou o fluxo completo numa sondagem.
- **Defeito do harness:** contava comando negado como executado (V105-HARNESS-06, corrigido).

**`SKILL.md` revisada** (`69b81d8`), cada mudança ligada a uma causa observada:
- chamada direta `python …`, sem variável de shell nem `echo $?`;
- texto editado nunca entregue sem `compare`;
- `review_required` não é "desfazer";
- frases de entrega proibidas sem prova;
- juízo em arquivo não aprova nada (D-03).

**Holdout prospectivo** (10 tarefas novas × 2; detalhes em `FIRE_TRIAL_RESULTS.md` §7):

| | v0.10.0 | v0.10.5 inicial | v0.10.5 final |
|---|---|---|---|
| Skill ativada | 5/20 | 11/20 | 12/20 |
| Fluxo antes de escrever | 0/20 | 5/20 | 9/20 |
| `compare` | 2/20 | 7/20 | 9/20 |
| Decisões certas | 9/16 | 10/16 | 11/16 |
| Fidelidade (juiz) | 3,95 | 4,45 | 4,40 |
| Atende ao pedido, tarefas que exigem edição | 4,38 | 4,12 | 3,88 |
| Erros críticos | 4/20 | 0/20 | 2/20 |

**Conclusão honesta.** A Skill passou a ser usada de verdade com mais frequência e erra menos ao decidir não mexer. A qualidade da escrita **não** melhorou de forma mensurável, e as mudanças desta continuação não mudaram isso. O agente ainda entrega sem gate (P05) e entrega candidata reprovada com ressalvas, sem dizer que foi reprovada (P08). Uma instrução escrita não garante comportamento do host.

