# Rastreabilidade da v0.8

Requisito → código → teste → evidência. "Teste definido" não é "teste executado", e "executado" não é "mata o defeito": a coluna Prova diz qual dos três foi demonstrado. A matriz da v0.7 continua em [`../TRACEABILITY.md`](../TRACEABILITY.md).

| ID | Requisito | Código | Teste | Prova | CP | Estado |
|---|---|---|---|---|---|---|
| V08-001 | Um plano serializado não concede permissão para reescrever verso; a autorização vem do chamador | `voznativa/document.py` | `evals/test_v08_integrity.py::PlanCannotAuthoriseVerse` | falha em `2ced479` (3 FAIL + 12 ERROR), passa depois; 3 mutantes de `document.py` mortos. `test_non_boolean_caller_grant_is_refused` passava em `2ced479` por outro motivo (`TypeError` do argumento desconhecido): não conta como prova | CP1 | IMPLEMENTED_AND_TESTED |
| V08-002 | Um registro de `resume` não é autoridade: candidato revalidado, estrutura checada, sem veredito de juiz herdado, registro refeito do plano | `voznativa/engine.py` | `evals/test_v08_integrity.py::ResumeIsNotAuthority` | 4 testes falham em `2ced479`, 4 controles; 4 mutantes de `engine.py` mortos | CP1 | IMPLEMENTED_AND_TESTED |
| V08-003 | `spans.extract` subquadrático com saída idêntica | `voznativa/spans.py` | a definir | a definir | CP2 | aberto |
