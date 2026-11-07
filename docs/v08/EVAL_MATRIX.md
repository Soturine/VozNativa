# Matriz de avaliação (v0.8)

O que cada eixo mede, com que instrumento, sobre que conjunto e com que estado de evidência. Protocolo: [`EVAL_PROTOCOL.md`](EVAL_PROTOCOL.md). Nenhuma linha é validação independente.

| Eixo | Instrumento | Conjunto | Resultado mais recente | Estado |
|---|---|---|---|---|
| Risco semântico (gate) | `voznativa evaluate` → `semantic_risk` | suítes semânticas, relações, predicados (`gate-and-planner-v08`) | desenvolvimento 61/61 e 0/17; regressão 86/89 e 1/33 | DEVELOPMENT_BENCH_PASS |
| Eventos, papéis, destinatário | `evaluate` sobre `events-v08` | `evals/events/` (congelado antes do CP6) | desenvolvimento 14/15 e 2/13; holdout prospectivo 11/12 e 3/12 (uma execução) | DEVELOPMENT_BENCH_PASS |
| Decisão (chamar ou não o modelo) | `evaluate` → `decision` | `evals/decision/` | chamadas devidas 14/14; desnecessárias 1/16; decisão exata 28/30 | DEVELOPMENT_BENCH_PASS |
| Gênero (Router) | `scripts/router_audit.py`, `scripts/experiments/v08_router_curve.py` | 7 corpora, split de avaliação, 7.424 janelas | precisão 93,8% (Wilson 91,8–95,4), cobertura útil 8,8%, erradas 0,58% (reproduzido igual à v0.7) | medido; ver §1 |
| Editorial (fórmulas) | `voznativa/axes.py` → `editorial` | por candidata | proxy | IMPLEMENTED (proxy) |
| Mudança desnecessária | `axes` → `unnecessary_change` (plano e aderência) | por candidata | proxy | IMPLEMENTED (proxy) |
| Gíria e época | `axes` → `slang_and_epoch` (léxico atestado) | por candidata | proxy | IMPLEMENTED (proxy) |
| Regional | `axes` → `regional` (packs de evidência) | por candidata | proxy | IMPLEMENTED (proxy) |
| Deriva de gênero | `axes` → `genre` (Router completo; abstém quando o Router abstém) | por candidata | proxy | IMPLEMENTED (proxy) |
| Voz | `axes` → `voice` (distância ao perfil; sem perfil, `not_applicable`) | por candidata, com perfil autorizado | proxy sem calibração | IMPLEMENTED (proxy) |
| Naturalidade, fluidez, qualidade percebida | revisão humana cega (`blind-*`) ou juiz com identidade | — | — | NOT_RUN (pessoas e autorização) |
| Braços B0–B6 | `voznativa/arms.py` | qualquer conjunto de casos | B0, B2 offline; demais sem provider | B0/B2 executáveis; B1, B3–B6 NOT_RUN |
| Desempenho | `scripts/experiments/v08_spans_perf.py`, `v08_compare_perf.py` | docs do repositório | [`PERFORMANCE.md`](PERFORMANCE.md) | medido, uma máquina |

Os eixos de `axes.py` são **proxies determinísticos** construídos com os detectores do engine: `signal` pede olhar humano ou de juiz; `ok` diz que o proxy não viu nada, não que o texto é bom. Nenhum vira nota.

## 1. Curva cobertura × precisão do Router (V08-GAP-05)

`v08_router_curve.py` reproduz a regra de decisão do Router sobre os mesmos 7.424 trechos (a reprodução nos limiares atuais dá exatamente as 697 decisões emitidas pelo Router) e varre os limiares:

| `min_score` | `min_margin` | Emitidas | Cobertura útil | Precisão | Erradas |
|---:|---:|---:|---:|---:|---:|
| 1,0 | 0,5 | 1.883 | 21,2% | 83,4% | 312 |
| 1,0 | 1,0 | 1.839 | 20,9% | 84,2% | 291 |
| 2,0 | 0,5 | 727 | 9,1% | 93,1% | 50 |
| **2,0** | **1,0** (atual) | **697** | **8,8%** | **93,8%** | **43** |
| 2,0 | 2,0 | 610 | 7,7% | 94,3% | 35 |
| 2,5 | 1,0 | 265 | 3,4% | 96,6% | 9 |
| 4,0 | 1,0 | 83 | 1,1% | 100% | 0 |

Leitura: o ponto atual está no joelho da curva. Dobrar a cobertura (limiar 1,0) custa ~10 pontos de precisão e 7 vezes mais decisões erradas; não é ganho. A cobertura baixa vem das pistas, não dos limiares: em notícia e blog quase nenhuma pista dispara (Bosque e GSD 0,4% de cobertura útil, PUD 0%). **Decisão:** nenhum limiar muda na v0.8. A alavanca é ampliar pistas de gênero jornalístico e acadêmico, medindo no split de calibração e confirmando no de avaliação; fica como backlog com esse protocolo. Abstenção continua não sendo erro: mantém as proteções conservadoras.
