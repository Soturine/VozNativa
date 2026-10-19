# Avaliação do VozNativa

Resultados das evals próprias, com o que eles provam e o que **não** provam. Atualize este arquivo sempre que um número mudar.

## Camadas

| Camada | O que mede | Onde | Pode aprovar sozinha? |
|---|---|---|---|
| Determinística | spans protegidos, marcadores de sentido, invariantes, grounding | `voznativa compare`, `ground`, `benchmark` | Só identidade (`identical`) |
| Juiz LLM | preservação claim a claim, adições | `judge-prompt` + `--judgment` | Só resultados determinísticos limpos |
| Revisão humana | o mesmo, com autoridade final | `--judgment` com `kind: human` | Sim, exceto sobre `fail` |
| Detector de IA | — | não usado | Nunca |

## Suítes determinísticas (2026-10-19, 0.2.0.dev0)

sha256 calculado sobre o arquivo com quebras de linha LF.

| Suíte | sha256 (prefixo) | Resultado | Observação |
|---|---|---|---|
| `evals/semantic/cases.jsonl` (dev) | `f3520f40` | 50/50 | Escrita junto com o motor; o motor foi ajustado até passar. Não é evidência independente. |
| `evals/semantic/holdout.jsonl` | `ae479a2c` | **19/24 na primeira execução**; 23/24 depois de correções gerais | Congelado antes de rodar. Depois das correções passou a ser conjunto de desenvolvimento. Falha restante (ho-007): a expectativa de código estava errada (pedia `span_added` sem span protegido); o status `review_required` está certo. |
| `evals/semantic/holdout2.jsonl` | `3981a4ef` | **16/16 na única execução cega** | Depois, três casos motivaram correções de léxico (subjuntivo, antes/depois, concordância negativa); o resultado cego vale para a versão anterior. |
| `evals/router/cases.jsonl` | — | 15/16 | O caso que falha devolve `unknown` (fallback seguro), não um gênero errado. |

Gates no CI: o dev precisa passar 100%; nos holdouts, nenhum caso que espera violação pode sair como `no_deterministic_issues` ou `identical` (falso verde), e nada além da identidade é aceito sem julgamento.

**Limitação principal:** todos os casos foram escritos pelo mesmo autor do motor. O próximo passo de evidência é um holdout escrito por outra pessoa, congelado antes de ver o código.

## Comportamento por categoria

| Categoria | Detecta | Não detecta (limitação conhecida) |
|---|---|---|
| Valores | perda, troca, adição; formatos equivalentes (R$ 1.500,00 = R$1.500,00; 18/10/2026 = 18 de outubro de 2026; 18h30 = 18:30; três = 3; 3 mil reais = R$ 3.000) | número por extenso composto ("vinte e três"); "um/uma" como número |
| Negação | remoção/adição localizada; concordância negativa ("não ... nenhum" conta uma vez); compostos im+possível | negação morfológica fora da lista (desabilitar, inválido, ilegal) |
| Modalidade | pode → causa, sugere → comprova, deve ↔ pode, hedge adicionado | "deve" epistêmico é sempre contado como necessidade |
| Causalidade | causa removida; associação → causa; conector causal adicionado (revisão) | direção causal invertida com as mesmas palavras |
| Quantificadores/condições | apenas, até N, todos → alguns, cerca de, se/caso, antes/depois | escopo de quantificador em frases longas |
| Agentes | presença de nomes | troca de agentes ("Ana revisa, Bruno assina" → inverso) |
| Antônimos | — | aumentou ↔ diminuiu, aprovado ↔ reprovado |

Todas as limitações acima resultam em `no_deterministic_issues` ou `review_required`, nunca em aceitação automática: o juiz e o humano existem para elas.

## Teste de integração no modo skill (2026-10-19)

Um e-mail corporativo de 54 palavras (`bm-email-001`) foi reescrito pelo agente seguindo `rewrite-prompt`, sem ajustes para passar no gate:

- resultado determinístico `review_required`: um falso alarme real ("é só me chamar" contado como restritivo) foi corrigido de forma geral (categoria `idiom`); restou um `possible_omission` por paráfrase de "fico à disposição", que é ruído conservador;
- o julgamento LLM ficou registrado sem resolver a revisão; só um julgamento humano levou a `accepted_by_human`.

Nenhum modelo externo foi chamado: `claude`, `codex`, `gemini` e `ollama` não estavam instalados no ambiente. O `CommandProvider` foi testado com um subprocesso real que faz o papel do modelo.

## O que ainda não foi medido

- Naturalidade e voz com leitores (pairwise cego).
- Desempenho contra blader, work-humanizer, Emulate e prompt simples (protocolo pronto, execução não feita).
- Calibração dos limiares (`ALIGN_MIN_SIMILARITY`, cobertura, novidade, drift) contra dados reais.
- Taxa de falso vermelho em reescritas reais: um teste não é estatística.
