# Integridade de texto, proveniência e automação de navegador (v0.7.0, CP12)

## Quatro coisas diferentes

| Conceito | O que é | O que o VozNativa faz |
|---|---|---|
| Score de detector de IA | classificação falível de um fornecedor | mede em benchmark opt-in (`docs/V07_EXTERNAL_BENCHMARK.md`); nunca otimiza contra ele |
| Marca d'água estatística | padrão probabilístico na escolha de palavras, embutido na geração; verificável só com o método e a chave de quem embutiu | **nada**: não detecta, não remove, não certifica ausência; nenhuma saída diz `watermark_free` |
| Caracteres invisíveis e de formatação | propriedades Unicode do texto | audita e, sob política explícita, remove (`voznativa integrity`) |
| Credenciais/metadados de proveniência | registro verificável de origem e edição | registra o que tocou o texto, sem guardar o texto (`provenance` no resultado do `rewrite`) |

## Auditoria de integridade (`voznativa/integrity.py`, `voznativa integrity`)

Classes: caracteres de tag Unicode (canal conhecido para texto e instruções ocultas), controles bidi (em texto sem escrita da direita para a esquerda podem reordenar o que o leitor vê), largura zero, controles, espaços incomuns, hífen suave, seletores de variação, palavras com mistura de alfabeto latino com cirílico/grego (homóglifos). Cada achado diz se é provavelmente legítimo (espaço inseparável em "R$ 10", junção de emoji, BOM no início, marcas em texto árabe/hebraico) ou suspeito. Saída 2 quando há algo suspeito.

`--clean` remove só as classes nomeadas por `--policy`; espaço inseparável, juntores de emoji, seletores de variação e marcas de texto RTL ficam. A limpeza é de integridade, não de proveniência.

## Proveniência (`provenance_record`)

Todo `voznativa rewrite` devolve um bloco `provenance`: hashes de entrada e saída, se mudou, ferramenta e versão, operação e desfecho, provedor (quando um modelo foi chamado), `ai_assisted`, origem declarada, revisão humana (`not_recorded` por padrão) e, quando um modelo alterou o texto, uma nota de divulgação. O texto não é retido.

Referência regulatória (consulta 2026-11-06, AI Act Service Desk, texto consolidado em 27/07/2026, https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50): o Art. 50 §2 pede que provedores de sistemas que geram texto sintético marquem as saídas de forma legível por máquina e detectável, com exceção para função assistiva de edição padrão ou que não altere substancialmente a entrada; o §4 pede que quem publica texto gerado ou manipulado por IA para informar o público sobre questões de interesse público divulgue isso, salvo revisão humana ou controle editorial com responsabilidade editorial. A data de aplicação não constava na página lida (Art. 113 não incluído). Isto é contexto, não aconselhamento jurídico; o VozNativa não decide se um uso está isento.

## Automação de navegador

Ordem de preferência: API oficial > Playwright determinístico > Playwright MCP (exploração) > Stagehand/Browser Use (fallback autorizado).

| Opção | Decisão | Motivo |
|---|---|---|
| API oficial | adotada onde existe (Copyleaks; GPTZero parcial) | contrato documentado, sem raspar interface |
| Playwright | **não implementado** | nenhum serviço-alvo sem API com termos que autorizem automação foi identificado nesta rodada; criar um adapter de navegador sem alvo autorizado seria código morto |
| Playwright MCP, Stagehand, Browser Use | não adotados | agentes de navegador acrescentam risco (executar instruções vindas de páginas) sem caso de uso autorizado |
| Lightpanda | não avaliado | sem necessidade de compatibilidade |

Estado: **UNSUPPORTED** (não BLOCKED): nada foi tentado contra um site. Se um alvo for autorizado, o requisito é perfil descartável, allowlist de domínio, limites de tempo e passos, snapshots sanitizados, sem contornar CAPTCHA, login, paywall ou limites, e replay por fixtures nos testes.
