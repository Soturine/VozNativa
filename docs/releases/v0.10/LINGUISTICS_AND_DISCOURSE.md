# Gramática, variação e discurso (v0.10, CP4–CP6)

## Mapa de cobertura (a partir das áreas de Letras, sem copiar ementas)

| Área (ementas UEL/UEM/UFMG, [`RESEARCH_REGISTER.md`](RESEARCH_REGISTER.md)) | Onde no VozNativa | Estado na v0.10 |
|---|---|---|
| ortografia, acentuação, crase | `diagnose` (`crase`, `daqui_ha`), `ptbr` | regras de alta confiança com controles |
| morfologia (flexão, formas verbais) | `morph`, `diagnose` (`nonstandard_subjunctive`, `menas`) | idem |
| morfossintaxe (concordância, regência) | `diagnose` (`plural_agreement`, `existential_haver`, `impersonal_fazer`, `a_gente_plural`, `para_mim_infinitive`) | com status contextual |
| sociolinguística, variação, registro | `diagnose` (status `ACCEPTABLE_VARIANT`), `knowledge` (`variant_in`), `regional`, `temporal` | variante legítima separada de erro |
| semântica (modalidade, negação, quantificação, tempo, aspecto, eventos) | `compare`, `ledger`, `semantic_classes.json` | herdado; CP6 amplia |
| linguística textual (coesão, conectivos, referenciação) | `compare` (relações discursivas, CP5), `editorial` | CP5 |
| pragmática, gêneros, estilística | `task_context`, `router`, `patterns`, `drift` | contexto aberto (CP2); voz sem calibração nova |
| fonética/fonologia | — | fora do escopo (texto escrito); sem regra |

## Status de diagnóstico (CP4, V010-GAP-10)

Cada diagnóstico ganhou `status` e `recommend_edit` (schema 2 do `diagnose`; os campos antigos ficam):

| Status | Quando | Recomenda editar |
|---|---|---|
| `ERROR_CONFIRMED` | erro de forma de alta confiança no contexto (classe `formal_error`) | sim |
| `ACCEPTABLE_VARIANT` | forma legítima neste registro (informal: plural só no determinante, "haver" no plural, "ter" existencial, "pra mim + infinitivo"; grafia pré-reforma) | não |
| `STYLE_PREFERENCE` | preferência editorial, não erro ("ter" existencial em texto formal) | não |
| `CONTEXT_DEPENDENT` | pode ser desvio; depende de quem escreve e para quem ("a gente vamos" em mensagem; "para mim aceitar" em texto formal, que é gramatical em "difícil para mim aceitar") | não |
| `LITERARY_CHOICE` | texto literário ou verso | não |
| `UNCERTAIN` | ambiguidade, contradição interna ou valor sem fonte: uma pessoa decide | não |

Detectar o fenômeno não é recomendar a edição. O planner só planeja edição para `ERROR_CONFIRMED`.

## Regras novas (CP4, V010-GAP-09)

| Tipo | Exemplo | Status por contexto | Correção automática |
|---|---|---|---|
| `daqui_ha` | "daqui há duas semanas" | erro em qualquer registro escrito; escolha literária em ficção | sim (`daqui a`) |
| `nonstandard_subjunctive` | "seje", "esteje" | erro em texto formal; dependente de contexto em mensagem; escolha literária | sim, só em modo PROOFREAD |
| `menas` | "menas pessoas" | idem | sim, idem |
| `a_gente_plural` | "a gente vamos" | erro em texto formal; dependente de contexto em mensagem | não (a troca por "nós" muda a voz) |
| `para_mim_infinitive` | "pra mim passar" | variante em mensagem; dependente de contexto em texto formal | não |
| `ter_existential` | "Tem muita gente na fila" | variante em mensagem; preferência editorial em texto formal | não |

**Prova.** `evals/test_v010_diagnose_status.py`: 11 testes; em `v0.9.0` 8 falham (3 falhas, 5 erros) e os 3 controles passam. Conjunto congelado `evals/v010/diagnose`, development: erros **3/7 → 7/7**, falsos alarmes **0/9 → 0/9**. Conjuntos da v0.9 sem mudança (development 11/11 e 0/11; holdout 6/6 e 0/6).

**Limites.** Regras por padrão de superfície; "Tem dois filhos" com sujeito oculto vira `STYLE_PREFERENCE` (informação, sem edição). Sem revisão de especialista em sociolinguística.

## Relações discursivas (CP5, V010-GAP-03/08)

`voznativa/discourse.py` conta relações explícitas por **família**: `counter` (contraste e concessão: o segundo fato vale *apesar* do primeiro), `causal` (causa e consequência) e `purpose` (finalidade). No `compare`:

| Código | Severidade | Quando |
|---|---|---|
| `relation_changed` | major | uma família some de um lado e uma família oposta aparece do outro ("embora" → "como", "contudo" → "assim", "para que" → "porque") |
| `relation_invented` | major | aparece uma relação causal sem que nenhuma tenha saído (fatos justapostos unidos por "assim", "porque"); não duplica o `causality_changed` já localizado |
| `relation_dropped` | info | contraste/concessão deixa de ser marcado sem nada no lugar (pode ter ficado implícito: uma pessoa decide) |

Troca dentro da mesma família preserva a relação: "porém" → "mas", "Entretanto" → "No entanto", "para que" → "a fim de que", "porque" → "Como …, ". Neste último caso o `causality_changed` gerado pela troca de marcador vira `info` (a causa continua afirmada); a **direção** da causa continua com a checagem própria (`causal_direction_reversed`, controle no teste).

Conectivos com várias leituras só contam na leitura que o padrão fixa: "Como" abrindo oração fechada por vírgula (não "Como sempre,", "Como previsto,"); "assim" fora de "assim como"; "logo" fora de "logo depois/após". O resto fica de fora: a checagem se abstém em vez de adivinhar. Relação implícita nunca é lida como causa.

Exemplos obrigatórios do prompt mestre: "O servidor apresentou instabilidade. Entretanto, o serviço ficou indisponível." → "Por isso, …" é `relation_changed` (contraste → consequência), sem inventar qual era a relação "certa"; "Cê consegue me mandar até sexta? Se não der, avisa" → sem a condição é sinalizado, com informalidade mantida não é; "testado" ≠ "aprovado" (`event_changed`, herdado); "desde que", "salvo", "exceto", "somente se" protegidos (`condition_changed`, herdado).

## Calibração de falsos alarmes e lacunas antigas (CP6, V010-GAP-04..07)

| Gap | Antes (`v0.9.0`) | Agora | Por quê |
|---|---|---|---|
| "será feita" → "será" (a-01) | `tense_changed` em uma das formas | sem sinal no par congelado `sf-01` | já passava no par isolado; o caso do arms dependia de outro trecho |
| "vai ser no sábado" → "é no sábado" (a-07) | `tense_changed` major | sem sinal | presente com âncora de futuro (dia, data, "amanhã", "próximo"…) é o mesmo tempo; **sem âncora continua sinalizado** (controle) |
| "pasta data" → "pasta `data`" (a-09) | `span_added` crítico | `code_marking_added` info | só marca como código uma palavra que o original já tem; conteúdo de código trocado continua `fail` (controle) |
| "a tarde inteira" → "a tarde toda" (a-11) | `quantifier_changed` major | sem sinal | "inteiro/inteira" entram como quantificador universal; e assim "a tarde inteira" → "parte da tarde" passa a ser sinalizado (V010-GAP-07, antes verde) |
| "vai ser no domingo" → "foi no domingo" | **verde** | `tense_changed` major | "foi/foram" são pretérito de ser e de ir: passado nas duas leituras, então a abstenção da morfologia não esconde futuro → passado |
| "tenha começado" → "ter começado" | `tense_changed` major | sem sinal | auxiliar no infinitivo não tem tempo próprio |
| "revisado e enviado" → "revisado" (V09-GAP-07) | **verde** | `coordinated_action_dropped` major | ação coordenada (particípio ou pretérito) cujo radical some do texto inteiro; "revisado e, em seguida, enviado" não dispara |

Nenhuma checagem foi desligada: cada correção de falso alarme tem controle que continua sinalizado.

**Prova.** `evals/test_v010_discourse.py`: 18 testes; em `v0.9.0`, 12 falham (11 defeitos + perfil do módulo novo) e os 6 controles passam. Conjunto congelado `evals/v010/semantic`, development: riscos **16/21 → 21/21**, falsos alarmes **5/13 → 0/13**. Instrumentos anteriores na mesma execução (`v09_before_after.py`): regressão congelada 88/89 e 1/33, eventos 15/15 e 2/13 (holdout 11/12 e 2/12), gate-and-planner 61/61 e 0/17, conjuntos da v0.9 31/31 e 4/20 (holdout 18/18 e 1/10): **idênticos** antes e depois.

**Limites.** Família por conectivo explícito; relações sem conectivo nos dois lados não são comparadas. "Como" causal depende da vírgula. Coordenação só entre duas formas do mesmo tipo (particípio + particípio, pretérito + pretérito).
