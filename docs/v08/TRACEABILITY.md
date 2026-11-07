# Rastreabilidade da v0.8

Requisito → código → teste → evidência. "Teste definido" não é "teste executado", e "executado" não é "mata o defeito": a coluna Prova diz qual dos três foi demonstrado. A matriz da v0.7 continua em [`../TRACEABILITY.md`](../TRACEABILITY.md).

| ID | Requisito | Código | Teste | Prova | CP | Estado |
|---|---|---|---|---|---|---|
| V08-001 | Um plano serializado não concede permissão para reescrever verso; a autorização vem do chamador | `voznativa/document.py` | `evals/test_v08_integrity.py` | a definir no CP1 (falha antes, passa depois) | CP1 | aberto |
| V08-002 | Um registro de `resume` não é autoridade: candidato revalidado, estrutura checada, sem veredito de juiz herdado, registro refeito do plano | `voznativa/engine.py` | `evals/test_v08_integrity.py` | a definir no CP1 | CP1 | aberto |
| V08-003 | `spans.extract` subquadrático com saída idêntica | `voznativa/spans.py` | a definir | a definir | CP2 | aberto |
