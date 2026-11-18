# Reconciliação do ROADMAP (CP0 da v0.10)

> Cada `- [ ]` de `ROADMAP.md` em `v0.9.0`, cruzado com código, testes e registros das releases posteriores. Uma marcação histórica não prova falta atual: o estado abaixo vem do repositório, não da caixa. Linhas citam `ROADMAP.md` em `6b487f7`.

## Já resolvidos depois (a caixa ficou desatualizada)

| Linha | Item | Evidência atual |
|---|---|---|
| 222 | normas, editais e rubricas versionados | `voznativa/standards.py`, `rubric.py`, `data/standards/` (v0.8); `voznativa standards`, `voznativa rubric` |
| 236 | convergência de estilo entre unidades | `voznativa/editorial.py`, sinal `style_convergence` (v0.9 CP3, V09-GAP-09 FIXED) |
| 244 | braços com provider real | v0.9 CP7: `evals/v09/runs/arms-haiku-2026-11-18.json` (12 textos, modelo real) |
| 255, 260 | voice / long-form drift | `drift.py`, `voice_profile.py` existem desde a v0.3; o que falta é **calibração** (abaixo) |
| 262, 265 | protocolo de revisão humana; benchmark system-level | `review.py`, `blind.py`, `benchmark.py`; execução humana segue NOT_RUN |

## Parciais

| Linha | Item | O que existe | O que falta |
|---|---|---|---|
| 237 | leitura nativa de DOCX/PDF | DOCX num subconjunto, PDF só extração (v0.9) | caixas por palavra, renderização conferida no Word |
| 37, 160 | claims estruturados; pronomes e troca entre frases | juiz extrai claims; `compare` vê papéis numa frase | correferência entre frases (V09-GAP-05) — **promovido à v0.10 (CP6)**, escopo de abstenção |
| 122, 200 | calibração de limiares em corpus/reescritas reais | limiares autorais; arms reais da v0.9 | **promovido à v0.10 (CP6/CP12)**: falsos alarmes do CP7 |
| 258 | genre | router com 10+ gêneros | gêneros abertos — **promovido à v0.10 (CP2)** |
| 284 | candidate generation + reranking | `--candidates N` com ranking por status | ablação real — **v0.10 CP10**, só com ganho medido |

## Não resolvidos e bloqueados por pessoas, chaves ou dados

| Linha | Item | Estado |
|---|---|---|
| 48, 83, 144, 198, 251 | holdout escrito por outra pessoa | NOT_RUN (depende de pessoa) |
| 82, 174, 220 | revisão humana / regional / cega | NOT_RUN (protocolo pronto) |
| 75 | voz com amostras consentidas | BLOCKED (amostras) |
| 80 | benchmark com Emulate | BLOCKED (chave) |
| 182, 197 | atestação pós-2018 e Corpus Carolina | BLOCKED por licença por documento; **CP7 revisita a licença** sem ingerir texto |
| 175 | `ptbr-bench-v3` | NOT_RUN (congelado) |

## Não resolvidos, fora do escopo da v0.10 ou reservados

| Linha | Item | Decisão |
|---|---|---|
| 67 | planejamento por documento | só com ganho medido; sem medição prevista → fica |
| 130, 171–173, 193 | packs regionais além do piloto, capital/interior, overfit guard, comunidade × região × canal | exigem dados atestados; sem eles, criar packs seria estereótipo. Fora do escopo |
| 176 | triagem de escopo para textos normativos | parcial via `standards`; fica |
| 221 | automação de navegador | UNSUPPORTED (sem alvo autorizado) |
| 285–289 | adapters pessoais, LoRA/PEFT, modelo especializado | trilha opcional; fora desta rodada (custo × licença) |
| 256, 261 | regional e temporal slang como eixos de avaliação | dependem de dados atestados; fica |
