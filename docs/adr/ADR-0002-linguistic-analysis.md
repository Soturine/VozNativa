# ADR-0002 — Camada de análise linguística (v0.7.0, CP9L)

Status: aceito (2026-11-06). Contexto: adendo "Linguistic Intelligence & Morphosyntactic Assurance".

## Decisão

1. **Nenhum contrato paralelo ao Semantic Ledger.** A análise linguística entra como módulo de sinais (`voznativa/morph.py`) consumido pelo `compare` (`tense_changed`) e disponível para o Planner e o long-form. O Ledger continua independente de biblioteca de NLP.
2. **Analisador por regras, stdlib, sem dados de terceiros embutidos.** Terminações regulares das três conjugações e uma tabela de irregulares frequentes (ser, estar, ter, haver, ir, fazer, poder, dizer), escritas a partir da gramática. Saída por token: forma, offsets, lema provável, todas as análises que a terminação permite com traços UD (`VerbForm`, `Mood`, `Tense`, `Person`, `Number`), `analyzer@version`, estado `unique`/`ambiguous`. Perífrases (progressiva, futuro perifrástico, perfeito composto, passiva) com aspecto e tempo do auxiliar.
3. **Abstenção é saída válida.** Formas ambíguas ("falamos", "terminara", "terminar" após "quando") não recebem rótulo forçado; o sinal semântico só usa análises únicas dos dois lados.
4. **Tempo morfológico ≠ tempo do evento.** O módulo descreve a forma e a perífrase; não infere quando o evento ocorre no discurso.
5. **Voz ≠ tempo.** Passiva é comparada pelo tempo do auxiliar ("foi aprovado" ≈ "aprovou").
6. **Sinal, não prova.** `tense_changed` é `major` (revisão), nunca `critical`; sua ausência não prova equivalência.

## Mapeamento para UD (verificado nos dados, não presumido)

Contagem em Bosque, GSD e PetroGold (tokens VERB/AUX): futuro do pretérito = `Mood=Cnd` **sem** `Tense`; imperfeito do subjuntivo = `Mood=Sub|Tense=Imp`; futuro do subjuntivo = `Mood=Sub|Tense=Fut`; mais-que-perfeito simples = `Tense=Pqp`; perfeito = `Tense=Past`. 34% dos tokens VERB/AUX não têm nenhum traço (sobretudo GSD): a avaliação usa só tokens anotados.

## Alternativas avaliadas

| Opção | Fato verificado | Decisão |
|---|---|---|
| spaCy `pt_core_news_sm` | v3.7.0, **CC BY-SA 4.0**, treinado em UD Bosque v2.8 + WikiNER (huggingface.co/spacy/pt_core_news_sm, lido 2026-11-06) | não adotado como dependência: licença share-alike não pode ser embutida no pacote MIT; o experimento da v0.3 trouxe 1 detecção nova em 167 casos (`evals/experiments/`); possível extra opcional isolado no futuro, com medição contra este baseline |
| Stanza | a página de modelos (stanfordnlp.github.io/stanza/available_models.html, lida 2026-11-06) não declara licença dos modelos nem lista português explicitamente | não verificado; não adotado |
| Lista de lemas derivada dos treebanks | melhoraria a cobertura | recusado: derivado de dados CC BY-SA no repositório MIT é negado pela própria política de dados |

## Medição (`scripts/morph_eval.py`, `evals/linguistics/runs/morph-2026-11-06.json`, splits de teste)

| Treebank | Verbos anotados | Cobertura | Única | Acurácia das únicas | Não-verbos com análise /1000 (única) |
|---|---|---|---|---|---|
| Bosque | 2.346 | 70,3% | 68,6% | 95,6% | 64,9 (31,4) |
| GSD | 340 | 74,1% | 66,7% | 94,6% | 61,1 (30,1) |
| PetroGold | 2.348 | 64,7% | 65,9% | 97,4% | 47,2 (24,3) |
| DANTEStocks | 906 | 67,6% | 63,6% | 93,3% | 46,4 (24,5) |

Limite conhecido: ~2,5–3% dos não-verbos recebem análise verbal única. Para o sinal semântico o risco é menor (exige o mesmo lema em frases alinhadas com rótulos únicos diferentes), mas não foi medido em pares de reescrita humanos (não existem no repositório). As suítes semânticas congeladas (dev e 5 holdouts, modo estrito) não mudaram com o sinal.

## Consequências

- `compare` ganha `tense_changed`; o impacto ponta a ponta na reescrita **não** foi medido com modelo (NOT_RUN); não se alega melhora do Rewrite Engine por causa da anotação.
- Backlog: concordância, regência, colocação pronominal, correferência, papéis além de entidades nomeadas, analisador opcional com fallback (ver `docs/V07_LINGUISTICS.md`).

## Adendo (v0.7.0.dev1, CP3): âncoras de predicado

- **Decisão.** O `compare` ganha `predicate_missing` (`major`) e `predicate_replaced` (`info`) sobre as mesmas análises por regras. Para saber *se* há um verbo, basta que as análises concordem num único radical; o tempo pode ser ambíguo ("cancelaram"). Isso não muda o item 3: o sinal `tense_changed` continua exigindo análise única dos dois lados.
- **Ficam de fora das âncoras:** terminações fracas aceitas só pelo contexto ("durante" → "durantar"), verbos leves e modais, palavras funcionais e radicais com menos de 4 letras.
- **Item 5 estendido.** Futuro perifrástico e sintético da mesma referência ("vai depositar" ≈ "depositará"; "ia depositar" ≈ "depositaria") deixam de ser "mudança de tempo". Forma não finita não é evidência de tempo.
- **Alternativas não adotadas:**
  - parser de dependências: dependência nova, sem benchmark de necessidade;
  - NLI ou juiz LLM: não determinístico, e já existe como `--judge-cmd`;
  - lista de pares de verbos: decoraria exemplos.
- **Medição:** só numa amostra do mesmo autor (`evals/predicates/README.md`). A regra é experimental até haver holdout independente (B-L6).

