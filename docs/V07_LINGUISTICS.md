# Inteligência linguística e compreensão de documento — AS-IS e backlog (v0.7.0)

Responde aos adendos "Linguistic Intelligence & Morphosyntactic Assurance" (CP9L) e "Document Understanding, Contextual Reasoning & Editorial Intelligence" (CP9D). Estados: IMPLEMENTED, PARTIAL, UNCALIBRATED, NOT_IMPLEMENTED, BLOCKED. A evidência é código + teste; documentação sozinha não conta.

## Inventário de capacidades linguísticas

| Capacidade | Estado | Onde | Evidência / limite |
|---|---|---|---|
| Classes gramaticais e lematização | PARTIAL | `morph.py` (só verbos), `text.stem` (radical) | sem POS geral; lema de verbo provável por terminação |
| Conjugação: tempo, modo, pessoa, número | IMPLEMENTED (regras) | `morph.py` | acurácia 93–97% das análises únicas em 4 treebanks; ~35% abstém (ADR-0002) |
| Infinitivo, gerúndio, particípio; formas compostas e perífrases | IMPLEMENTED (regras) | `morph.constructions` | progressiva, futuro perifrástico, perfeito composto, passiva |
| Tempo morfológico × tempo do evento | IMPLEMENTED como separação; inferência do tempo do evento NOT_IMPLEMENTED | `morph.py` | o módulo não infere o tempo do evento (decisão) |
| Negação, modalidade, condição, causalidade, temporalidade | IMPLEMENTED | `signals.py`, `ledger.py`, `compare.py` | v0.2–v0.4; v0.7 adiciona `*_moved` entre frases |
| Sujeito/agente/paciente; voz ativa e passiva | PARTIAL | `compare._role_issues`, `_crossing_issues` | entidades nomeadas e substantivos comuns; sem sujeito implícito nem pronomes |
| Concordância, regência, crase, colocação | NOT_IMPLEMENTED | — | backlog B-L3 |
| Pronomes, correferência, elipse | NOT_IMPLEMENTED (só retomada de abertura) | `longform._BACK_OPENINGS`, `compare._order_issues` | sem resolvedor; ambiguidade → revisão |
| Coesão entre orações e parágrafos | PARTIAL | `longform.dependency_map`, `compare._order_issues` | conectores e aberturas; não semântica profunda |
| Advérbios, locuções, conectores | PARTIAL | `signals`, padrões | temporais e causais; não classe geral |
| Variação regional, histórica, de registro | PARTIAL | `regional.py`, `temporal.py`, `router.infer_time_of_text`, `ptbr.py` | grafia pré-reforma datada (v0.7); regional piloto E0 |

## Inventário de compreensão de documento

| Capacidade | Estado | Onde |
|---|---|---|
| Semantic Ledger / Fact Guard | IMPLEMENTED | `ledger.py`, `compare.py`, `spans.py` |
| Context Router / Voice Contract | IMPLEMENTED (contrato v3) | `router.py`, `contract.py` |
| Planner e Rewrite Engine (incl. documento longo) | IMPLEMENTED | `planner.py`, `engine.py`, `document.py` |
| Estrutura de documento (blocos, verso, diálogo, lista, código, tabela, citação) | IMPLEMENTED | `longform.py`, `document.py` |
| Dependências entre parágrafos e carry de nomes/siglas | IMPLEMENTED (superfície) | `longform.py`, `document.py` |
| Consistência de entidades e terminologia | PARTIAL | `compare` (valores, entidades); carry no long-form |
| Validação contra fontes autorizadas | IMPLEMENTED (create) | `project.ground`, juiz de fundamentação |
| Contradição interna do documento | PARTIAL | `planner` (dia da semana × data); CP9D |
| Narrador, ponto de vista, personagens | NOT_IMPLEMENTED | backlog B-D2 |
| Erros do original classificados por tipo | IMPLEMENTED (base) | `diagnose.py`, `voznativa diagnose`, `rewrite --mode` |

## Backlog com critério de aceite

| ID | Item | Critério de aceite | Dependência |
|---|---|---|---|
| B-L1 | analisador opcional (spaCy/Stanza) como extra isolado | instalação opcional, fallback para regras, comparação contra `morph-2026-11-06.json` nos mesmos splits, licença do modelo fora do pacote MIT | decisão de licença do mantenedor |
| B-L2 | sujeito implícito e pessoa morfológica × agente | casos "Terminei", "A gente terminou", "Venderam" com abstenção para indeterminado; nunca inventar agente | B-L1 ou regras de concordância |
| B-L3 | concordância e regência como diagnóstico (nunca correção automática fora de PROOFREAD autorizado) | precisão medida em texto humano dos 7 corpora; variação legítima não marcada | CP9D modos |
| B-L4 | correferência pronominal limitada | só quando há um único antecedente compatível; senão revisão | B-L1 |
| B-L5 | pares de reescrita humanos para medir o sinal `tense_changed` | ≥ 100 pares rotulados por pessoa independente | pessoas |
| B-D2 | modelo de narrativa (narrador, pessoa narrativa, personagens) | personagens consistentes entre segmentos do long-form | B-L4 |

## CP9D — consciência de erro e modos editoriais

`voznativa/diagnose.py` (`voznativa diagnose`, `voznativa rewrite --mode`): 8 classes tipadas (as 7 do adendo + `no_evidence`), cada diagnóstico com tipo, severidade, confiança, impacto, offsets e ação (`auto_fix` só para erro formal de alta confiança; `suggest`; `preserve`). Modos: PRESERVE/REVIEW nunca alteram e não chamam modelo; PROOFREAD aplica só correções formais e passa pelo `compare`; POLISH/ADAPT seguem o Rewrite Engine; CREATE = tarefa `create`. Fatos, enredo, causalidade, intenção e compromissos nunca são automáticos.

Detectores implementados: palavra repetida (com reduplicações legítimas, nomes, símbolos, ênfase informal e licença literária separados), dia da semana × data, sigla redefinida, frase repetida, grafia pré-reforma (escolha legítima), troca pretérito → presente na narração (ambiguidade, nunca erro), valores contra fontes autorizadas (divergência × ausência de evidência; ficção não é checada).

Falsos positivos em texto humano publicado (`scripts/diagnose_eval.py`, `evals/linguistics/runs/diagnose-2026-11-06.json`, split de avaliação, até 600 janelas por fonte): `formal_error` 0,01–0,23 por mil palavras depois de corrigir três classes de falso positivo vistas nos próprios dados (nomes reduplicados, "se se"/"-nos nos", título seguido de parágrafo com a mesma palavra) e mais duas (interjeições, símbolos de fórmulas). Os erros restantes lidos são erros reais ("para para", "entre entre", "com com"). Os números finais não são independentes: as regras foram ajustadas lendo essas unidades. `tense_switch` (ambiguidade, informação) aparece 0,3–1,9 por mil; é deliberadamente baixa confiança.

Não implementado (backlog): narrador e personagens (B-D2), contradição numérica entre seções, citações e referências inexistentes, políticas por gênero além da literária/verso.
