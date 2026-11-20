# Piloto online e portabilidade da Skill (20/11)

Cinco passagens autênticas em PT-BR foram coletadas diretamente das fontes pela internet. O piloto executou geração ao vivo pelo Codex CLI, revalidou cada saída pelas checagens locais e gravou HTML. Também foram abertas sessões reais do Codex para observar o próprio agente usando a Skill. É desenvolvimento pós-Prova de Fogo, com um exemplar por gênero e sem novo juiz independente.

## Fontes selecionadas

| Caso | Gênero e época | Identificação contextual | Fonte e condições |
|---|---|---|---|
| VON01 | Poesia simbolista, 1893 | Autor catarinense | Duas estrofes de [Antífona, de Cruz e Sousa](https://pt.wikisource.org/wiki/Ant%C3%ADfona_(Cruz_e_Sousa)), domínio público |
| VON02 | Comédia de costumes, 1844 | Ambiente teatral no Rio de Janeiro | Abertura da primeira cena de [O Judas em Sábado de Aleluia, de Martins Pena](https://pt.wikisource.org/wiki/O_Judas_em_S%C3%A1bado_de_Aleluia), domínio público |
| VON03 | Decreto federal, 2017 | Serviços públicos no Brasil | Art. 1º, incisos e parágrafo único do [Decreto nº 9.094](https://www2.camara.leg.br/legin/fed/decret/2017/decreto-9094-17-julho-2017-785213-normaatualizada-pe.html), ato oficial |
| VON04 | Resumo acadêmico, 2008 | História do léxico brasileiro | Resumo de [Os nomes da língua, de Olga Ferreira Coelho](https://revistas.usp.br/rieb/pt_BR/article/view/34619), CC BY declarada pelo periódico |
| VON05 | Manual técnico, edição web consultada em 2026 | Tradução brasileira de documentação | Primeiros dois parágrafos de [Usando listas como pilhas](https://docs.python.org/pt-br/3/tutorial/datastructures.html#using-lists-as-stacks), sob os [termos da documentação Python](https://docs.python.org/pt-br/3/license.html) |

Os recortes e suas saídas ficam fora do Git. O [manifesto](../../../evals/v0105/online_pilot.json) registra fonte, autoria, pedido, contagem, SHA-256 do texto extraído e resultados. A época e o lugar descrevem a fonte, a autoria ou a ambientação. Eles não tornam a amostra representativa de um dialeto contemporâneo.

## Geração e calibração

Na primeira rodada, a CLI calculou o plano local. O Codex recebeu o pedido completo, o texto e o plano, decidiu se e como editar e escreveu as justificativas. A CLI comparou e produziu o relatório. Nesse braço as ferramentas foram mediadas pelo harness. A execução da Skill pelo próprio host foi observada separadamente.

| Caso | Primeira execução com modelo | Leitura editorial ou nova tentativa |
|---|---|---|
| VON01 | `identical` | Original mantido com versos e grafia de época |
| VON02 | `no_deterministic_issues` | O agente inseriu o separador entre a rubrica da personagem e a fala, com a oralidade intacta |
| VON03 | `fail` | O original voltou; na segunda tentativa restou `role_or_order_swapped` e a candidata seguiu para revisão |
| VON04 | `no_deterministic_issues` | O agente corrigiu uma quebra interna de palavra na transcrição; o plano local indicava `no_change` |
| VON05 | `fail` | O original voltou. O sinal de negação injustificado foi reproduzido e corrigido. A modalidade e outras diferenças das candidatas exigiram o retorno ao original também nas novas tentativas |

Os cinco relatórios da primeira rodada foram gravados. O GAP-29 surgiu da revisão do caso técnico. Comparações mínimas mostraram que o mesmo complemento privativo, com ou sem determinante enfático, era contado como duas negações. A correção se aplica à frase alinhada quando o restante coincide e conserva o alerta para mudanças independentes na sentença vizinha. Testes sintéticos cobrem um caso com adição, um com remoção e os controles negativos. O replay pós-correção manteve os 1.632 estados da campanha offline nos 427 itens.

## Hosts

- **Codex.** A instalação de projeto fica em `.agents/skills/voznativa`. Uma sessão explícita no checkout leu o `SKILL.md`, rodou `plan` e `compare --html-out` e gravou `final.txt` e o HTML para o poema. O arquivo final foi conferido byte a byte. O Windows recusou a leitura por shell da cópia instalada nessa execução, e o agente executou o mesmo fluxo pelo `SKILL.md` e pela CLI do checkout. A primeira sondagem isolada também ficou sem arquivos. Esses limites importam para instalações em outros repositórios.
- **Claude Code.** A instalação de arquivos e a CLI local funcionaram. A nova sessão com poema ficou `BLOCKED` pela cota semanal (resposta do host indicando 22/11 às 15h, América/São Paulo).
- **Gemini CLI e outros hosts.** Cópia e CLI verificadas no layout Gemini. Ativação e execução de modelo continuam `NOT_RUN`. O instalador aceita outro caminho de Skills, e todos os layouts usam o mesmo contrato e o mesmo motor.

No checkout, **quatro de cinco casos de host** tiveram chamada observada a `compare --html-out`, texto final e relatório nativo. Poesia, decreto e manual nomearam a Skill no pedido. O caso de teatro cumpriu o fluxo sem nomeá-la. No resumo acadêmico o host gravou arquivos, mas confeccionou um HTML próprio e não executou a CLI. O caso fica `INCOMPLETE`. Outra sondagem em diretório temporário foi recusada pelo ambiente e também ficou incompleta. A tabela do Observatory registra esses resultados por caso.

## Repetir com outros textos

Coloque os recortes autorizados no diretório local, como `VON01.txt`, conforme o manifesto. Para ampliar a amostra, use outro manifesto no mesmo formato, com URLs, pedidos, direitos e hashes verificados. O runner rejeita IDs repetidos, conteúdo diferente do hash e fontes sem autorização registrada. A saída deve ficar em um diretório novo fora do repositório.

```bash
python scripts/v0105_online_pilot.py --manifest evals/v0105/online_pilot.json --texts /pasta/recortes --out-dir /pasta/resultados
```

Acrescente `--host-project /pasta/do/projeto` para medir o Codex usando a Skill instalada e acrescente `--explicit-skill` para nomeá-la no pedido. O runner registra separadamente comparação observada, HTML gerado, texto final e eventuais falhas. Sem essas evidências, a execução do host fica incompleta.

## Cobertura e direitos ainda pendentes

- A página do [C-ORAL-BRASIL I](https://c-oral-brasil.org/c-oral-brasil-i.php) respondeu e confirmou CC BY-NC-SA 4.0 para a fala espontânea informal. O acesso à transcrição ficou sem verificação. O registro do corpus recebeu a evidência primária. O piloto não enviou esse material ao modelo.
- O [Essay-BR](https://github.com/rafaelanchieta/essay) tem código sob MIT e textos descritos como extraídos de sites educacionais. A licença do repositório, por si, não esclarece os direitos de cada redação. Não houve coleta dos textos para o modelo. As referências oficiais do [Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem) seguem disponíveis para metodologia.
- O artigo da Agência de Notícias do IBGE retornou HTTP 403 na coleta direta. Notícias, relatórios técnicos, redações, fala contemporânea e gírias regionais precisam de amostras elegíveis adicionais. A expansão pede evidência por fonte, época, região, registro, uso local, envio e redistribuição.
- A calibração deste piloto produziu um controle do gate e um reparo de implementação. Nenhum peso de modelo foi treinado. Um estudo de qualidade exige mais itens por gênero, controle, juiz separado e amostra prospectiva congelada antes dos ajustes.
