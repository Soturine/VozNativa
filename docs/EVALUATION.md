# Avaliação do VozNativa

O que foi medido, por qual tipo de evidência, e o que **não** foi provado. Atualize sempre que um número mudar.

## Tipos de evidência

| Tipo | O que é | Pode aprovar sozinho? |
|---|---|---|
| Determinística | `compare`, `ground`, `benchmark`: spans, marcadores, relações, estrutura | Só identidade (`identical`) |
| Teste simulado | testes unitários com providers estáticos ou subprocessos que fazem papel de modelo | Não é evidência de integração |
| Execução real de modelo | `scripts/llm_integration.py`: modelo externo de verdade, relatório gravado em `evals/integration/` | Não é revisão humana |
| Juiz LLM | `judge-prompt` + `--judgment`, `kind: llm`, vinculado aos hashes dos textos | Só resultados determinísticos limpos |
| Revisão humana | `voznativa review` (terminal interativo, assinatura HMAC com chave local) | Sim, exceto sobre `fail` |
| Leitura do agente | eu (o agente que escreveu o código) lendo resultados | **Nunca**: não é revisão humana nem independente |
| Detector de IA | — | Não é usado |

Um JSON com `"kind": "human"` sem assinatura válida vira `human_review_claimed`. A assinatura prova que o dono da chave, nesta máquina, aprovou aqueles textos exatos; não prova quem é a pessoa, e quem lê o arquivo da chave consegue forjá-la.

## Suítes determinísticas (0.2.0.dev0, 2026-10-19)

Proveniência completa em `evals/semantic/MANIFEST.json`. **Nenhuma suíte é validação independente**: todas foram escritas pelo mesmo agente que escreveu o motor.

| Suíte | Papel | Primeira execução (cega) | Hoje |
|---|---|---|---|
| `cases.jsonl` | dev | — | 50/50 |
| `relations.jsonl` | dev (escrita antes dos detectores de relação) | 14/25 (baseline vermelha) | 25/25 |
| `holdout.jsonl` (`ae479a2c`) | holdout do desenvolvedor | **19/24** | 23/24, contaminado |
| `holdout2.jsonl` (`3981a4ef`) | holdout do desenvolvedor | **16/16** | 16/16, contaminado |
| `holdout-relations.jsonl` (`ba591007`) | holdout do desenvolvedor | **11/12** | 12/12, contaminado |
| `evals/router/cases.jsonl` | dev | — | 15/16 (o erro cai em `unknown`, nunca num gênero errado) |

Só a primeira execução de um holdout é cega; números posteriores vêm depois de correções motivadas por ele. O protocolo para um holdout independente está em `evals/semantic/INDEPENDENT_HOLDOUT.md`.

## Comportamento por categoria

| Categoria | Detecta | Não detecta |
|---|---|---|
| Valores | perda, troca, adição; formatos equivalentes (R$ 1.500,00 = R$1.500,00; 18/10/2026 = 18 de outubro de 2026; 18h30 = 18:30; três = 3) | número por extenso composto; "um/uma" como número |
| Negação | remoção/adição localizada, inclusive em frases curtas; concordância negativa; im+possível; fórmulas (não hesite) não contam | negação morfológica fora da lista |
| Modalidade | pode → causa, sugere → comprova, deve ↔ pode, hedge adicionado | "deve" epistêmico conta sempre como necessidade |
| Causalidade | causa removida; associação → causa; direção invertida dentro da frase (orientação dos conectores, causativas fazer/levar) | causalidade entre frases |
| Agentes e relações | troca mútua de papéis ("a Ana revisa e o Bruno assina" → inverso; "a Acme comprou a Beta" → inverso) | pronomes; inversão ativa/passiva com a mesma ordem de nomes |
| Atribuição | fonte removida; fontes que trocam de afirmação; "sugere" → "comprova" | fonte em minúscula ("o ministro"); "conforme" + particípio é idioma |
| Antônimos | 13 pares do léxico de polaridade (aumentar/diminuir, aprovar/recusar, habilitar/desabilitar, abrir/fechar…) | antônimos fora do léxico (avançou/travou) |
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

## Compatibilidade e empacotamento (verificado em 2026-10-19)

| Ambiente | Validador | Testes | Eval dev |
|---|---|---|---|
| Linux, Python 3.11.17 / 3.12.15 / 3.13.16 (contêineres oficiais) | ok | todos passando | 50/50 |
| Windows, Python 3.12.6 (instalado) | ok | todos passando | 50/50 |
| Windows, Python 3.11.9 / 3.13.16 (pacotes embeddable oficiais) | ok | todos passando | — |

- Wheel construído a partir do sdist, instalado num venv limpo no Linux e executado fora do checkout: 33 arquivos de referência embutidos, 8/8 comandos (`scripts/smoke_installed.py`).
- `voznativa review` exercitado num pseudo-terminal real no Linux (`scripts/pty_review_check.py`): revisão assinada aceita; sem terminal, recusada (exit 64). O script digita as respostas, então isso prova o mecanismo, não uma pessoa.
- O CI repete tudo isso em Linux e Windows com 3.11–3.13. Até o push, o CI desta versão não tinha rodado.

## O que ainda não foi medido

- Holdout escrito por outra pessoa.
- Naturalidade e voz com leitores (pairwise cego) e revisão humana real de qualquer saída.
- Benchmark contra blader, work-humanizer, Emulate e prompt simples (protocolo e runner prontos, execução não feita).
- Taxas de falso vermelho e falso verde com amostra estatisticamente útil; calibração de limiares.
- Outros modelos além de `claude-sonnet-5-5`.
