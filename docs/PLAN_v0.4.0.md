# Plano v0.4.0 — PT-BR Writing Intelligence & Hardening

Une três fontes: os gaps da auditoria da v0.3.0 (M0), o escopo original da v0.4 no `ROADMAP.md` (biblioteca de padrões PT-BR, PT-BR x PT-PT, estrangeirismos) e o planejamento por documento que a v0.3.0 deixou pendente (M2.3, agora M3).

Baseline: `evals/baselines/v0.4.0-start.json` (commit `0ba7bc2`, checkout limpo, 199 testes, validador ok, suítes como na v0.3.0: holdout 23/24).

Versão durante o desenvolvimento: `0.4.0.dev0`. **Código implementado não é versão qualificada.**

## A v0.3.0 continua aberta

Nada nesta fase fecha os critérios externos da v0.3.0: holdout escrito por outra pessoa, rodada de revisão humana cega e CI verde. A v0.4.0 constrói sobre a v0.3.0 sem declará-la concluída.

## Critérios para qualificar a v0.4.0

1. Todo WP obrigatório *validado* (código, testes e evidência registrada).
2. Nenhuma regressão: suítes de dev passam; holdouts congelados inalterados e sem falso verde.
3. Benchmark prospectivo novo congelado antes da primeira execução, com resultado registrado por sistema e comparação com a baseline anterior.
4. Os critérios externos herdados da v0.3.0 (holdout independente, revisão humana cega, CI verde em Linux e Windows 3.11–3.13) cumpridos, ou dispensados explicitamente pelo mantenedor.

Os itens do critério 4 dependem de pessoas e da conta do GitHub.

## M0 — Hardening obrigatório da v0.3

| WP | Defeito confirmado | Correção | Regressão |
|---|---|---|---|
| M0.1 | `ho-007` contava como falha sem dizer que foi detectado | `failure_kind` e `status_passed` nos relatórios; caso congelado intacto, nota em `MANIFEST.json` | `evals/test_hardening_v040.py` |
| M0.2 | modo create julgava a saída contra o pedido, não contra as fontes | juiz de fundamentação com fontes rotuladas, evidência literal obrigatória; valores do pedido contam como fonte; lacunas `[DADO NECESSÁRIO]` pedem revisão | `evals/test_hardening_v040.py` |
| M0.3 | NO_CHANGE ignorava mudança explícita de destino | `transformation_targets`, bloco DESTINO PEDIDO, NO_CHANGE do modelo refeito e depois revisão, `no_change_reason` | `evals/test_hardening_v040.py` |
| M0.4 | `blind-summary` inflava contagens e aceitava mapeamento de braços adulterado | `task_sha256`, todos os hashes conferidos, uma resposta por tarefa e chave, participantes por chave | `evals/test_review_assurance.py` |
| M0.5 | "verified" misturava integridade, posse, identidade e independência | `review.assess`; assinatura SSH do revisor; registro `evals/reviewers/` | `evals/test_review_assurance.py` |
| M0.6 | `--redact` guardava credenciais do comando, erros com texto, caminho e sha256 adivinhável | `voznativa/redact.py`; HMAC com chave não gravada | `evals/test_privacy.py` |
| M0.7 | timeout matava só o filho; saída sem limite; erros do Emulate derrubavam o engine; diretório temporário descrito como isolamento; delimitador do prompt quebrável | árvore de processos, limite, erros embrulhados, avisos para CLIs de agente, `--provider-env minimal`, cercas com hash, tokens de protocolo | `evals/test_providers_hardening.py` |
| M0.8 | `claim_added` no CHANGELOG (o código é `possible_addition`); exemplos `--cmd "claude -p"` com ferramentas ligadas; "CI job" citado como verificação | documentação corrigida; teste do README ignora flags dentro de valores entre aspas | `evals/test_skill_contract.py` |

Achado durante o M0: `quinta às 10h` sem preposição não era dia da semana (falso vermelho em reescrita para chat). Corrigido. Limitação que fica: `é sexta` sem preposição nem horário continua sem span, então "O prazo é sexta." → "O prazo termina na sexta." dá `span_added` (falso vermelho conhecido).

## M1–M5

Status e evidência por WP são registrados nas seções abaixo à medida que cada um termina.
