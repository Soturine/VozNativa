# Matriz de verificação da v0.7.0

Requisito → teste → resultado → evidência. Status: PASS só quando o teste rodou e passou na revisão indicada. Revisão humana e ferramentas externas sempre em colunas próprias.

| Req. | Unitário / negativo | Contrato / integração / E2E | Metamórfico / mutação | Benchmark | Humano / externo | Estado |
|---|---|---|---|---|---|---|
| RF-01 harness | `CheckpointHarness` (1º estágio falho derruba; timeout; programa ausente; push rejeitado) | push verificado contra bare repo real | — | — | — | PASS (Windows 3.12) |
| RF-02 CI | `LiveCiEvidence` (adulteração, SHA errado, matriz incompleta, cancelled/neutral, query fora, branch divergente, commit só de evidência) | `WorkflowTriggerAudit`; consulta live real | — | — | CI live do HEAD: NOT_RUN | PASS (contrato); CI: NOT_RUN |
| RF-03 TEI | `TeiReader` (DOCTYPE/ENTITY, malformado, raiz errada, tamanho, sem texto) | conector com `.xml.gz`; `PerDocumentLicences`; `ManifestAndCache` | negativo: sem a recusa prévia o XXE vira `malformed` (o teste exige `unsafe_xml`) | — | — | PASS (Windows 3.12) |
| RF-04 corpora | `TextRights` (inclui precedência DENIED), `CrossGenreEvaluators` | prepare + integrity + crossgenre reais em 7 fontes | — | `evals/corpus/runs/crossgenre-2026-11-06.json` | — | PASS (3 → 7 integradas) |
| RF-05 G2 | `Containment` (direcional; capítulo; trecho entre fontes; edição modernizada; mesmo tema ≠ duplicata; citação comum; frase curta), `MultiKeySplits` | integridade real em 7 fontes | controle negativo: `with_containment=False` reproduz o gap | `integrity-2026-11-06-cp4.json` | — | PASS |
| RF-06 G1 | `G1EndToEnd` (gênero + proteções + planner local), `AbstentionKeepsProtections` (com controle), `ChatNeedsCorroboration`, `HistoricSpellingIsNotPtPt` | 14 oráculos congelados `cases-v07` (literatura, poesia, 3 chats, oral, manual, relatório, e-mail, fórum, Markdown, flags de CLI) | CRLF, NBSP, nomes de fonte trocados | `crossgenre-2026-11-06-cp5b.json` | — | PASS |
| RF-07 G3 | `HeldOutSample` (2 amostras congeladas), controle negativo do padrão v0.6, `FalseFriendNeedsCorroboration` | `ConsumersCountTheSlangSenseOnly` (engine, perfil, guard de introdução) | mutação: CP14 | `crossgenre-2026-11-06-cp6b.json` | — | PASS |
| RF-08 contrato long-form | | | | | | pendente |
| RF-09 G4 | | | | | | aberto |
| RF-10 guards | | | | | | pendente |
| RF-11 bench v5 | | | | | | pendente |
| RF-12 detectores | | | | | live: LIVE_NOT_RUN | pendente |
| RF-13 Unicode/proveniência | | | | | | pendente |
| RF-14 humano | | | | | NOT_RUN | — |
