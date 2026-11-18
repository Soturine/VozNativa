# Registro de gaps da v0.10

> Estados: OPEN, FIXED (com teste vermelho→verde), PARTIAL, ACCEPTED_RISK, BLOCKED, NOT_RUN, OUT_OF_SCOPE. Reprodução medida em `v0.9.0` (`6b487f7`) salvo indicação. IDs herdados mantêm o número de origem.

| ID | Gap | Reprodução / fonte | Sev. | Estado | CP |
|---|---|---|---|---|---|
| V010-GAP-01 | Juiz com relação `unknown` ao escritor aprova (`accepted_by_llm`) | `compare.apply_judgment`: só `same_agent` é tratado como autoavaliação; dois comandos sem modelo declarado dão `unknown` e o voto `equivalent` aceita | P1 | OPEN | CP6 |
| V010-GAP-02 | Taxonomia de relação do juiz não distingue mesmo fornecedor, mesmo modelo, independência verificada | `judge.GENERATOR_RELATIONS = {same_agent, different_model, unknown}`; Opus × Haiku vira `different_model` e aceita como se fosse independente | P2 | OPEN | CP6 |
| V010-GAP-03 | Relação discursiva inventada ou trocada sem sinal próprio: concessão → causa, contraste → consequência, finalidade → causa | `sd-03`, `sd-04`, `sd-08` em `evals/v010/semantic`: só caem por coincidência (tempo verbal); `sd-15` (sinônimo de concessão) dá falso alarme | P1 | OPEN | CP5 |
| V010-GAP-04 | Futuro → passado com perífrase passa verde | `sf-10`: "vai ser no domingo" → "foi no domingo": `no_deterministic_issues` | P1 | OPEN | CP6 |
| V010-GAP-05 | Particípio/verbo coordenado perdido passa verde (resto de V09-GAP-07) | `se-02`, `se-03`, `se-04`: "revisado e enviado" → "revisado", 0 sinais | P1 | OPEN | CP6 |
| V010-GAP-06 | Falsos alarmes do CP7 da v0.9: "será feita" → "será"; "vai ser" → "é" com data; crase de código `data` → `` `data` ``; "a tarde inteira" → "a tarde toda" | arms da v0.9 (`a-01`, `a-07`, `a-09`, `a-11`); reproduzidos no CP0 (`sf-02`..`sf-04`) | P2 | OPEN | CP6 |
| V010-GAP-07 | "inteiro" → "parte" passa verde (o quantificador só vê "toda") | `sf-07` | P2 | OPEN | CP6 |
| V010-GAP-08 | Causal reordenado ("porque" → "Como …,") dá `fail` | `sd-18` | P2 | OPEN | CP5 |
| V010-GAP-09 | Erros de alta confiança fora do diagnóstico: "daqui há", "seje/esteje", "menas" | `dg-01`, `dg-02`, `dg-03`, `dg-16` | P2 | OPEN | CP4 |
| V010-GAP-10 | Diagnóstico sem status contextual (erro confirmado × variante legítima × escolha literária × dependente de contexto) | `diagnose` só tem classes; o consumidor não distingue variante legítima de erro | P2 | OPEN | CP4 |
| V010-GAP-11 | Contexto fechado: gênero/canal/tom fora das listas não têm onde morar; atributos novos exigem código | `router.route(genre=...)` aceita qualquer string mas nada além de `genre/channel/register/audience`; `tone`, `constraint`, `voice`, multigênero não existem | P2 | OPEN | CP2 |
| V010-GAP-12 | Sem registro de conhecimento linguístico com proveniência nem recuperação seletiva | conhecimento espalhado em `data/*.json`, `standards`, packs, referências | P2 | OPEN | CP3 |
| V010-GAP-13 | Sem monitoramento de fontes (normas, cartilhas, corpora, dependências, modelos) | nada no repositório | P2 | OPEN | CP8 |
| V010-GAP-14 | Assertiva local 51 commits atrás do remoto (v1.0.1); a v0.9 auditou com 0.10.1 | `git status` no CP0 | P3 | OPEN (usar clone isolado de `origin/main`) | CP11 |
| V09-GAP-05 / V08-GAP-19 | Correferência, troca de papéis com complemento deslocado e conversos | herdado | P2 | OPEN | CP6 |
| V09-GAP-12 | Router com empate e baixa cobertura | herdado | P2 | OPEN | CP2 |
| V09-GAP-15 | Modelo local real nunca executado | herdado; execução do `llama-server` negada na v0.9 | P2 | BLOCKED (não contornar) | CP13 |
| V09-GAP-16 | Emulate ao vivo | sem chave | P3 | BLOCKED | — |
| V09-GAP-17 | Codex / Gemini CLI | não instalados | P3 | NOT_RUN | — |
| V08-GAP-23 | `--provider-env inherit` como padrão | herdado | P2 | OPEN | CP13 |
| V08-GAP-28 | Ciclos de import | herdado | P3 | OPEN | CP9 |
| V08-GAP-29 | Caminhos locais em registros históricos | herdado | P3 | OPEN | CP9 |
