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
