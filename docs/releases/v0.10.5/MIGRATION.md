# Migração para a v0.10.5

## D-03: juízo de modelo lido de arquivo não aprova mais nada

**O que muda.** `compare --judgment juizo.json`, `ground --judgment …` e `apply_judgment` chamado diretamente com um juízo `kind: "llm"` e `verdict: "equivalent"` **não** levam mais a `accepted_by_llm`, qualquer que seja a `generator_relation` escrita no arquivo (`different_model`, `different_provider`, `same_vendor`, `independence_verified`). O relatório fica no estado que tinha (`no_deterministic_issues`), com `safe_to_auto_accept: false`, `requires` contendo `independent_judgment` e um bloco novo:

```json
"declared_assessment": {
  "verdict": "equivalent",
  "judge_id": "…",
  "generator_relation": "different_model",
  "relation_evidence": "DECLARED",
  "note": "a judgment file declares who judged; …"
}
```

O código de saída do `compare` segue o estado (3 em vez de 0 nesse caso).

**O que não muda.**
- `voznativa rewrite --judge-cmd …` / `--judge-api-model …`: o engine executa o juiz e deriva a relação dos comandos que ele mesmo rodou (`relation_evidence: ENGINE_OBSERVED`). Aceita como antes, com os mesmos níveis (`partial` para `same_vendor` e `different_model`, `provider` para `different_provider`).
- Um `not_equivalent` lido de arquivo continua reprovando, e um `uncertain` continua pedindo revisão: rejeições só deixam o resultado mais seguro.
- Revisão humana assinada (`voznativa review`) continua resolvendo `review_required` como antes.
- `same_agent`, `same_model` e `unknown` continuam virando `agent_assessment`, como na v0.10.

**Por quê.** No fluxo da Skill, quem escreve a candidata também escreve o arquivo de juízo. Até a v0.10.5 inicial, o agente podia declarar `different_model` sobre a própria candidata e receber `accepted_by_llm` e `safe_to_auto_accept: true`. O relatório já marcava a relação como `DECLARED` (V105-GAP-11, achado na sessão real do Derivanta Framework), mas a aceitação continuava. Um arquivo sem autenticação não prova quem julgou; assinatura de integridade também não provaria identidade nem independência.

**Como adaptar.** Para aceitação automática por modelo, use o `rewrite` com juiz configurado. Para registrar a avaliação de um juiz externo que você executou fora do VozNativa, o arquivo continua aceito como evidência (fica em `evidence.judgments` e em `declared_assessment`), mas a decisão de aceitar passa a ser sua ou de uma revisão humana assinada.

Testes: `evals/test_v0105_relation_evidence.py` (vermelho antes da mudança); os testes de nível de independência (`test_v08_judge_relation`, `test_semantic_layer`, `test_v010_judge_independence`) passaram a usar juízo observado pelo engine, único caminho que ainda aceita.
