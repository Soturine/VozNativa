# Segundo dogfood agent-led: relatório acadêmico longo disponível só em PDF (v0.8.1)

Estado: **concluído na branch** `dev/v0.8.1-dogfood-tcc2`, criada de `b52af15` (topo de `dev/v0.8.1-dogfood-tg1`). Sem tag, release ou CI.

> **Integração posterior:** estas correções entraram na `main` pelo histórico limpo (merge `159eda5`) e foram publicadas na release estável [`v0.8.1`](../v0.8.1/RELEASE_NOTES.md) (tag em `17d1f10`). Os SHAs citados abaixo são da branch da época. O texto abaixo é o registro da época e não foi reescrito.

## Escopo e privacidade

- Documento: relatório parcial de Trabalho de Graduação de engenharia (PT-BR acadêmico), 58 páginas geradas por pdfTeX, sem DOCX nem fonte. 148 parágrafos editáveis, cerca de 8.300 palavras, com equações exibidas e inline, listagens de código, 19 figuras, 4 tabelas e 37 referências.
- O documento é de outra pessoa e não entra no repositório. As fixtures dos testes são **sintéticas e de outro domínio** (logística). Este registro traz só contagens, códigos e exemplos sintéticos.
- **PDF → texto foi feito fora do produto.** Linhas por linha de base, com papel atribuído por fonte, tamanho e posição; 169 hifenizações de fim de linha decididas com base no próprio vocabulário do texto (0 ambíguas); uma ligadura "ff" partida reunida; equações, código, legendas, referências e apêndices protegidos; notação matemática inline e identificadores passados com `--protect-file`. Cada palavra guarda a sua caixa no PDF, de modo que as sugestões viram anotações sobre as palavras originais.

## Ambiente

Windows 10, CPython 3.12.6. Provider real `claude -p` (`claude-sonnet-5-5`, sem ferramentas, `--provider-env minimal`). Escritor e juiz são o mesmo modelo, então nenhum julgamento é independente.

## Defeitos encontrados e corrigidos

| Id | Defeito | Prova em `b52af15` | Correção |
|---|---|---|---|
| DF-06 | `--mode PROOFREAD` apagava a conjunção depois de um rótulo de uma letra | CLI, frases sintéticas: "lotes C, E e G" → "C, E G" | par de uma letra com caixa diferente não é repetição |
| DF-07 | `acronym_redefined` (major) falso | 4 no documento, todos de títulos | expansão = menor sufixo cujas iniciais cobrem a sigla; sem isso, não há definição |
| DF-08 | entidade extraída dentro de um token ("×n" em "Rm×n") nunca era "encontrada": qualquer edição dava `span_missing` crítico | execução real: 13 de 13 unidades revertidas, documento devolvido intacto | presença também pela mesma extração no outro texto |
| DF-09 | divisão de frase e citação após o ponto, distantes, viravam `causality_moved` crítico | replay após DF-08: 6 unidades revertidas, 5 delas inocentes | frase sem palavra de conteúdo fora da contagem; frase nova não alinhada conta com o par vizinho |

Testes: `evals/test_v081_diagnose_labels.py`, `evals/test_v081_entity_in_token.py`, `evals/test_v081_moved_groups.py`. Em `b52af15`, os testes de defeito falham e os controles passam. Movimentos reais de negação, distantes ou vizinhos, continuam críticos.

Uma primeira versão do DF-09 (somar grupos de alinhamento) foi descartada: com frases quase idênticas, o alinhamento por empate gerava novos falsos "movidos".

## Antes × depois

Replay com as mesmas respostas gravadas do modelo:

| Motor | Desfecho | Unidades revertidas |
|---|---|---|
| `b52af15` | `returned_original` | 13/13 |
| + DF-08 | `needs_review` | 6 |
| + DF-09 | `needs_review` | 0 |

Execuções reais: em `b52af15`, 24 chamadas e nenhuma edição aproveitada; no motor corrigido, 25 chamadas e 39 parágrafos editados, com 0 revertidos. Chamadas contadas = chamadas reais nas duas (DF-01). Custo observado nas três execuções: US$ 4,25.

## Qualificação

Gate local PASS na árvore de cada commit (926, 929 e 933 testes). Benches `ptbr-bench-v4` 22/22 e `v5` 36/36 e amostra de predicados 17/20 e 1/18, inalterados. O teste de tempo `test_v08_compare_perf` falhou uma vez (razão 21,2 > 19) e também falha em 1 de 3 rodadas isoladas sem mudança no `compare`: é instável na máquina de desenvolvimento.

## Achados sem correção (limitações)

- **Convergência de estilo entre unidades.** Os achados de `patterns` caíram de 37 para 8, mas a construção "Essa X permite/promove/contribui" subiu de 3 para 11. As unidades são reescritas em separado e convergem para a forma que o achado `gerund_tail` sugere. Nenhum detector vê a nova repetição. Um critério por primeira palavra não separa o caso, e calibrar com um único documento seria ajuste artificial. Recomendação: registro de estilo entre unidades.
- **Qualificador de conteúdo removido** (exemplo sintético: "envio automático do lote" → "envio do lote") dá `no_deterministic_issues`. Fica abaixo dos limiares por oração, e detectar toda remoção de adjetivo geraria alarme em reescritas legítimas.
- **`accepted` não independente:** uma unidade aceita pelo juiz (o mesmo modelo) continha "também permitiu" → "passou a permitir". A revisão humana rejeitou.
- **Erros gramaticais** (regência, concordância, "-se" faltando) não viram achado. Uma unidade sem achados fica `no_change` sem chegar ao modelo. Nomes próprios são protegidos, então um erro de digitação dentro de um nome nunca é corrigido (correto, mas precisa ser dito).
- **Roteador:** com títulos em `## `, um texto acadêmico vira `documentation`.
- **DF-07 se abstém** em siglas formadas por letras internas (por exemplo, RADAR, de "Radio Detection And Ranging").
- **Suporte a PDF no produto:** não implementado. Equações exibidas no meio de uma frase saem da representação sem marcador; um conversor geral precisaria de placeholders protegidos.
