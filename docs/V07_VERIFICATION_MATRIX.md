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
| RF-08 contrato long-form | `Contract` (sem perda, JSON ida e volta, adulteração, protegido não substituível, verso, dependências/carry) | — | CRLF ida e volta | — | — | PASS |
| RF-09 G4 | `SegmentedRewrite` (12 cenários), `CommandSplitting` | `CommandLine`: `python -m voznativa rewrite --long-form on` com provedor de comando | — | — | modelo externo: NOT_RUN | PASS (stubs); live NOT_RUN |
| RF-10 guards | `CrossParagraph` (3 falsos verdes + detecções antigas + 3 controles) | `DocumentGuards` (gíria introduzida em unidade → revisão) | `Metamorphic` (CRLF, NFD, NBSP, quebra, tab, espaço duplo) + controle negativo | `ptbr-bench-v4` 22/22 | — | PASS |
| RF-11 bench v5 | — | runner recusa hash divergente | invariâncias via suítes CP5/CP9 | `ptbr-bench-v5` 1ª: 34/36 (`e634a3b`); pós-correção 36/36 | modelo/humano: NOT_RUN | PASS (determinístico); braços NOT_RUN |
| RF-12 detectores | `Contracts` (manifesto, autorização dupla, curto, HTTP, sandbox, parser sem rótulo inventado, contratos não verificados) | `ProtocolMetrics` (métricas separadas, grupo vazio NOT_RUN, replay ≠ live) | — | — | live: LIVE_NOT_RUN | PASS (contrato); live NOT_RUN |
| RF-13 Unicode/proveniência | | | | | | pendente |
| RF-18 linguística | `AddendumExamples`, `UDMapping`, `NotEverythingIsAVerb`, `NoInventedAgent` | `TenseAsASemanticSignal` (3 sinais + 4 controles) | suítes semânticas congeladas inalteradas | `morph-2026-11-06.json` (ouro UD, 4 treebanks) | pares humanos: NOT_RUN | PASS (regras); impacto E2E com modelo NOT_RUN |
| RF-19 documento/erros | `ErrorClasses`, `Grounding`, `Modes` | CLI `diagnose` e `rewrite --mode` | — | `diagnose-2026-11-06.json` (FP em texto humano) | — | PASS (base); narrador/personagens NOT_IMPLEMENTED |
| RF-14 humano | | | | | NOT_RUN | — |
