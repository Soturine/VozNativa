# Avaliação do VozNativa

O que foi medido, por qual tipo de evidência, e o que **não** foi provado. Atualize sempre que um número mudar.

## Tipos de evidência

| Tipo | O que é | Pode aprovar sozinho? |
|---|---|---|
| Determinística | `compare`, `ground`, `benchmark`: spans, marcadores, relações, estrutura | Só identidade (`identical`) |
| Teste simulado | testes unitários com providers estáticos ou subprocessos que fazem papel de modelo | Não é evidência de integração |
| Execução real de modelo | `scripts/llm_integration.py`: modelo externo de verdade, relatório gravado em `evals/integration/` | Não é revisão humana |
| Juiz LLM | `judge-prompt` + `--judgment`, `kind: llm`, vinculado aos hashes dos textos | Só resultados determinísticos limpos |
| Revisão humana | `voznativa review` (terminal interativo; assinatura HMAC com chave local ou SSH do revisor) | Sim, exceto sobre `fail`; o relatório diz o que a assinatura **não** mostra (identidade, independência) |
| Leitura do agente | eu (o agente que escreveu o código) lendo resultados | **Nunca**: não é revisão humana nem independente |
| Detector de IA | — | Não é usado |

Um JSON com `"kind": "human"` sem assinatura válida vira `human_review_claimed`. `review.assess` separa quatro propriedades: integridade (os bytes foram assinados por aquela chave), posse da chave (a chave HMAC é um segredo da máquina: o desenvolvedor ou um agente com o mesmo usuário também assina; uma chave SSH fica com o revisor), identidade declarada (nunca comprovada) e independência (no máximo declarada em `evals/reviewers/`; revisão HMAC nunca é independente).

## Suítes determinísticas (0.3.0.dev0, 2026-10-20, commit `86830c4`)

Proveniência completa em `evals/semantic/MANIFEST.json`. **Nenhuma suíte é validação independente**: todas foram escritas pelo mesmo agente que escreveu o motor.

| Suíte | Papel | Primeira execução (cega) | Hoje |
|---|---|---|---|
| `cases.jsonl` | dev | — | 59/59 |
| `relations.jsonl` | dev (escrita antes dos detectores de relação) | 14/25 (baseline vermelha) | 32/32 |
| `holdout.jsonl` (`ae479a2c`) | holdout do desenvolvedor | **19/24** | 23/24 estrito, 24/24 por status, contaminado. A falha é `ho-007`: detectado (`review_required` com `possible_addition`), mas o caso congelado pede `span_added`; é divergência de classificação, não detecção perdida, e o caso não foi editado |
| `holdout2.jsonl` (`3981a4ef`) | holdout do desenvolvedor | **16/16** | 16/16, contaminado |
| `holdout-relations.jsonl` (`ba591007`) | holdout do desenvolvedor | **11/12** | 12/12, contaminado |
| `holdout-v030.jsonl` (`09c1b3dd`) | holdout do desenvolvedor, congelado antes das correções da v0.3.0 | **15/24** | 24/24, contaminado |
| `evals/patterns/cases.jsonl` | dev do detector de padrões | — | 20/20 (no teste unitário) |
| `evals/router/cases.jsonl` | dev | — | 15/16 (o erro cai em `unknown`, nunca num gênero errado) |

Testes unitários: 199, todos passando.

Só a primeira execução de um holdout é cega; números posteriores vêm depois de correções motivadas por ele. Desde a v0.4.0 o relatório de cada suíte separa `passed` (status e códigos, a conta oficial) de `status_passed` (só o status) e classifica cada falha (`false_green`, `false_red`, `severity_divergence`, `classification_divergence`). O protocolo para um holdout independente está em `evals/semantic/INDEPENDENT_HOLDOUT.md`.

## Comportamento por categoria

| Categoria | Detecta | Não detecta |
|---|---|---|
| Valores | perda, troca, adição; formatos equivalentes (R$ 1.500,00 = R$1.500,00; 18/10/2026 = 18 de outubro de 2026; 18h30 = 18:30; vinte e três = 23; mil e quinhentos reais = R$ 1.500; meia hora = 30 minutos) | "um/uma" como número (ambíguo com o artigo) |
| Negação | remoção/adição localizada, inclusive em frases curtas; concordância negativa; im+possível; fórmulas (não hesite) não contam | negação morfológica fora da lista |
| Modalidade | pode → causa, sugere → comprova, deve ↔ pode, hedge adicionado | "deve" epistêmico conta sempre como necessidade |
| Causalidade | causa removida; associação → causa; direção invertida dentro da frase e entre frases vizinhas ("X. Por isso, Y.") | relações entre frases distantes |
| Agentes e relações | troca mútua de papéis; agente/paciente trocados entre entidades nomeadas, inclusive ativa ↔ passiva ("a Acme comprou a Beta" → "a Acme foi comprada pela Beta") | pronomes e substantivos comuns ("a proposta do fornecedor" → "do cliente"; o spaCy pegaria este caso, ver abaixo) |
| Atribuição | fonte removida; fontes que trocam de afirmação; "sugere" → "comprova" | fonte em minúscula ("o ministro"); "conforme" + particípio é idioma |
| Antônimos | 13 pares do léxico de polaridade (aumentar/diminuir, aprovar/recusar, habilitar/desabilitar, abrir/fechar…) | antônimos fora do léxico (avançou/travou) |
| Adições | número, data, entidade nova; oração inventada dentro de uma frase (ho-007) | adição sem palavra de conteúdo nova |
| Termos do usuário | `--protect`: termo ausente é `span_missing` | — |
| Estrutura | itens de lista, títulos e blocos de código perdidos (revisão) | — |

Todas as lacunas acima resultam em `no_deterministic_issues` ou `review_required`, nunca em aceitação automática.

## Execuções reais de modelo (2026-10-19)

Modelo `claude-sonnet-5-5` via Claude Code CLI 2.1.301 (`--tools ""`, `--strict-mcp-config`, diretório de trabalho vazio), escritor e juiz em chamadas separadas. Relatórios com as respostas brutas em `evals/integration/`.

| Execução | Código | Resultado |
|---|---|---|
| `…060846Z…ptbr-v1-prefix` | antes da correção do parser do juiz | 7 no_change; o e-mail ficou `needs_judgment` porque o juiz respondeu JSON com vírgula sobrando dentro de ```` ```json ```` |
| `…061506Z…ptbr-ai-drafts-v1` (6 rascunhos com padrões de IA) | `1df5f5e`, limpo | 3 `accepted_by_llm`, 2 `needs_review`, 1 `returned_original` |
| `…061635Z…ptbr-v1` (8 textos já naturais) | `e6a4702`, limpo | 1 `accepted_by_llm`, 1 `needs_review`, 6 `no_change` |

**Leitura do agente** (não é revisão humana) das 9 candidatas não idênticas:

- **Falso verde: nenhum observado.** As 4 candidatas aceitas pelo juiz LLM preservam fatos, prazos, modalidade e condições.
- **Falsos vermelhos encontrados e corrigidos** (`evals/test_integration_findings.py`): "só" lido como o marcador regional "sô"; "não hesite em" lido como negação; "conforme alinhado" lido como atribuição; juiz rejeitando o corte de "E isso muda tudo.".
- Re-pontuando offline as mesmas candidatas com o código corrigido: 2 das 10 decisões mudaram (uma de `fail` para `review_required`, uma de `review_required` para `no_deterministic_issues`).
- **Ruído conservador restante:** 3 das 9 candidatas fiéis ainda caem em `review_required` (paráfrase de uma frase de cortesia, "pode fazer com que não" → "sem ela… pode não", cortesia final removida). É o custo atual da política conservadora, não acerto.
- O modelo devolveu NO_CHANGE para 6 dos 8 textos já naturais do `ptbr-v1`, o comportamento esperado. Por isso foram criados os rascunhos com padrões de IA.
- Resultados não são determinísticos: `ai-tech-001` foi aceito numa execução cujo relatório se perdeu (bug do script, corrigido) e foi para revisão na execução gravada.

Amostra pequena (14 textos, um modelo): isto demonstra que a integração funciona e mostra tipos de erro; não estima taxas.

## Execuções reais da v0.3.0 (2026-10-20)

Mesmo modelo e isolamento das execuções anteriores. Exemplos legíveis em `examples/README.md`.

**Engine guiado por padrões** (`…060212Z…ptbr-ai-drafts-v1` e `…060331Z…ptbr-v1`, commit `264e232`, limpo):

- Rascunhos com padrões de IA: 2 `accepted`, 3 `needs_review`, 1 `returned_original`; nenhum `fail` entregue.
- Textos já naturais: 7 de 8 devolvidos sem chamar o modelo (`no_change`; o engine anterior gastava 7 chamadas para chegar ao mesmo NO_CHANGE); o 8º (`bm-email-001`) é o natural que o detector sinaliza, e foi reescrito e aceito.
- Achados editoriais somados nos 14 textos: 29 antes → 6 depois (o engine anterior chegava a 7). Uma reescrita introduziu um verbo-suporte fraco.

**Benchmark skill-only `ptbr-bench-v1`** (12 casos congelados em `264e232` antes da execução; mesmo LLM em todos os braços; custo total US$ 3,55; `benchmarks/runs/ptbr-bench-v1-20261020T060615Z.json`):

| Braço | Invariantes ok | Gate (fail / revisão / limpo / idêntico) | Juiz: não equivalente | Achados restantes | Naturais alterados |
|---|---|---|---|---|---|
| B0 original | 12/12 | 0 / 0 / 0 / 12 | 0 | 24 | 0/3 |
| B1 prompt de uma linha | 4/12 | 1 / 8 / 3 / 0 | 2 | 4 | 3/3 |
| B2 blader/humanizer | 5/12 | 3 / 6 / 3 / 0 | 8 | 0 | 3/3 |
| B3 work-humanizer | 3/12 | 3 / 9 / 0 / 0 | 4 | 0 | 3/3 |
| B5a VozNativa (só prompt) | 11/12 | 0 / 2 / 8 / 2 | 1 | 0 | 2/3 |
| B5b VozNativa (engine) | 10/12 | 0 / 3 / 2 / 7 | 2 | 5 | 0/3 |

Leitura e ressalvas:

- Os instrumentos (invariantes, gate, detector de padrões) são do próprio VozNativa e favorecem edição conservadora; o juiz LLM é o mesmo modelo que escreveu. Isto não mede naturalidade nem preferência de leitores.
- Os outros sistemas apagam mais achados, mas mudam mais o sentido segundo o juiz (blader: 8 de 12 julgados não equivalentes).
- B4 (Emulate) não rodou: falta chave de API.
- Depois dessa execução, o engine passou a exigir 2 votos concordantes do juiz e a refazer a reescrita com o motivo da recusa. A reexecução do braço B5b (`…061509Z`, **post hoc**, mesmos casos) deu 0 não equivalentes, 2 achados restantes e nenhuma desistência, por US$ 2,14. Por ser posterior, não é comparação justa com os outros braços.

## Experimentos (não adotados)

| Experimento | Resultado | Decisão |
|---|---|---|
| spaCy `pt_core_news_sm` 3.8.0 para papéis sintáticos (`evals/experiments/syntax_roles.json`) | 167 casos; 1 detecção nova (h3-lim-003), 0 falso vermelho | não adotado: ganho de 1 caso não paga dependência de ~15 MB com licença CC BY-SA |
| NLI ASSIN2 (`ruanchaves/bert-base-portuguese-cased-assin2-entailment`, `evals/experiments/nli_probe.json`) | 26/97 violações sinalizadas, nenhuma que o gate não pegasse; 9/56 falsos vermelhos em reescritas válidas e 2/9 em reescritas reais | rejeitado |
| Voice match com autor sintético (`evals/experiments/voice_match_synthetic_a.json`) | distância mediana: original 0,797, sem perfil 0,516, com perfil 0,457; com perfil mais perto em 2 de 4 | inconclusivo: 4 pares, autor escrito pelo desenvolvedor |

## Corpus Carolina (piloto só de metadados)

`evals/corpus/carolina-pilot.json`: cabeçalhos TEI de um recorte da versão 2.0.1 (Bea), sem guardar texto. Licenças por documento no recorte: 4.824 CC BY, 10 CC BY-SA, 2 CC BY-NC-SA, 1 GFDL. A tipologia `social_media` é ficção do Wattpad; não há metadado de região. Isso desfaz a hipótese de usar o Carolina para regionalidade.

## Compatibilidade e empacotamento (verificado em 2026-10-20, commit `e679038`)

Registro: `evals/compat/v0.3.0-dev-e679038.json`.

| Ambiente | Testes | Wheel isolado (`scripts/smoke_installed.py`) |
|---|---|---|
| Linux, Python 3.11.17 / 3.12.15 / 3.13.16 (contêineres oficiais) | 197 OK | 8/8 em cada versão |
| Windows, Python 3.12.6 (instalado) | 197 OK | 8/8 |
| Windows, Python 3.11.9 / 3.13.16 (embeddable) | 197 OK | não executado (sem venv/pip) |

- A rodada achou e corrigiu dois defeitos: os runners quebravam sem `git` instalado, e o smoke do wheel não limpava o diretório temporário no Windows.
- `voznativa review` foi exercitado num pseudo-terminal real no Linux (`scripts/pty_review_check.py`). O script digita as respostas, então isso prova o mecanismo, não uma pessoa.
- **CI não rodou:** o GitHub Actions recusa os jobs por cobrança da conta. A matriz local não substitui o CI.

## O que ainda não foi medido

- Holdout escrito por outra pessoa (protocolo pronto).
- Naturalidade e voz com leitores: o instrumento cego existe (`blind-*`), nenhuma resposta humana foi registrada.
- Emulate (system-level).
- Voice match com amostras reais e consentidas.
- Taxas de falso vermelho e falso verde com amostra estatisticamente útil; calibração de limiares.
- Outros modelos além de `claude-sonnet-5-5`.
