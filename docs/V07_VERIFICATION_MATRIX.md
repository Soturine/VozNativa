# Matriz de verificação da v0.7.0

Requisito → teste → resultado → evidência. Status: PASS só quando o teste rodou e passou na revisão indicada. Revisão humana e ferramentas externas sempre em colunas próprias.

| Req. | Unitário / negativo | Contrato / integração / E2E | Metamórfico / mutação | Benchmark | Humano / externo | Estado |
|---|---|---|---|---|---|---|
| RF-01 harness | | | | | | pendente |
| RF-02 CI | | | | | CI live: NOT_RUN | pendente |
| RF-03 TEI | | | | | | pendente |
| RF-04 corpora | | | | | | pendente |
| RF-05 G2 | `test_known_gaps_v06` G2 (xfail) | | | | | aberto |
| RF-06 G1 | `test_known_gaps_v06` G1 (xfail) | | | | | aberto |
| RF-07 G3 | `test_known_gaps_v06` G3 (xfail) | | | | | aberto |
| RF-08 contrato long-form | | | | | | pendente |
| RF-09 G4 | | | | | | aberto |
| RF-10 guards | | | | | | pendente |
| RF-11 bench v5 | | | | | | pendente |
| RF-12 detectores | | | | | live: LIVE_NOT_RUN | pendente |
| RF-13 Unicode/proveniência | | | | | | pendente |
| RF-14 humano | | | | | NOT_RUN | — |
