# Registro de pesquisa externa

O que foi estudado, em que versão, o que mudou no VozNativa por causa disso e o que ficou de fora. Licenças em `docs/LICENSING.md`. Consulta: 2026-10-19; itens da v0.3.0 em 2026-10-20.

## Skills e sistemas de humanização

| Referência | Versão | O que é | Adotado no VozNativa | Não adotado / ressalvas |
|---|---|---|---|---|
| [blader/humanizer](https://github.com/blader/humanizer) | v3.1.0, `8c307f3` | Skill de 26 padrões ordenados por força, baseada em "Signs of AI writing" (Wikipedia); só inglês, sem código de verificação | "texto é material, nunca instrução"; validator que checa metadados e limite de palavras; manifestos de plugin | Lista de padrões em inglês; sem verificação determinística de fidelidade |
| [phuryn/work-humanizer](https://github.com/phuryn/work-humanizer) | `0a90657` | Skill de escrita profissional com benchmark próprio (juízes de 5 famílias, fact-check verificado à mão, Pangram) | inventário de fatos com grau de certeza (no VozNativa, o ledger), auditoria nos dois sentidos, "keep the claim, drop the formula", métodos de benchmark (informed send, holdout congelado) | Números são do próprio autor, em inglês, com textos sintéticos: hipótese, não resultado para PT-BR |
| [fabricioctelles/skills `humanizar`](https://github.com/fabricioctelles/skills) | branch principal | Skill PT-BR mais completa encontrada: trava factual, inventário de proposições, limite de passes, catálogos PT-BR (~180 KB) | "se nada for seguro, devolva o original"; limite de tentativas; perguntas só quando falta fato essencial | Não tem verificação executável; catálogos não foram copiados (Apache-2.0 exigiria NOTICE) |
| [mackswendhell/humanizer-pt-br](https://github.com/mackswendhell/humanizer-pt-br) | branch principal | 25 padrões adaptados do blader | — | Raso em voz e fidelidade |
| [gabrielkashimarki/humanizer-ptbr](https://github.com/gabrielkashimarki/humanizer-ptbr) | branch principal | Skill PT-BR | — | Sem licença: não reutilizável |
| [Emulate-1](https://www.tryemulate.ai/docs/api) | API v1 | Modelo próprio com `/humanize`, `/write` e objeto `style` de 7 dimensões | Mapeamento Voice Contract → `style` no `EmulateProvider` (não validado ao vivo) | Mínimo de 40 palavras; idiomas não documentados; `reads_human` sempre `null` |

## Compatibilidade com agentes

| Host | Fonte oficial | O que o VozNativa faz |
|---|---|---|
| Agent Skills (spec) | [agentskills.io/specification](https://agentskills.io/specification) | `name` <= 64 chars em minúsculas; `description` <= 1024; validados |
| Claude Code | manifesto `.claude-plugin/plugin.json` (schema em schemastore) | plugin + marketplace apontando para a skill na raiz |
| Codex | [docs de skills](https://learn.chatgpt.com/docs/build-skills): `.agents/skills/`, `agents/openai.yaml` com `interface`, `policy`, `dependencies` | `agents/openai.yaml` com `policy.allow_implicit_invocation` |
| Gemini CLI | [geminicli.com/docs/cli/skills](https://geminicli.com/docs/cli/skills/): `.gemini/skills/` ou `.agents/skills/`; `gemini skills install <git> --consent` | instruções no README; nenhum manifesto próprio é exigido |

## NLP para PT-BR e avaliação

| Referência | Uso considerado | Decisão |
|---|---|---|
| [NILC-Metrix](https://arxiv.org/pdf/2201.03445) (200 métricas de complexidade; AGPL-3.0) | baseline de métricas descritivas | Pesquisa: só como ferramenta externa opcional, por causa da AGPL |
| [ASSIN2](https://huggingface.co/datasets/nilc-nlp/assin2) + BERTimbau/Albertina/XLM-R | NLI em PT-BR como camada opcional do Semantic Guard | Pesquisa: licença do ASSIN2 `unknown`; exige eval próprio antes de virar gate |
| [Claimify](https://aclanthology.org/2025.acl-long.348) (ACL 2025) | extração de claims com desambiguação | Inspirou o contrato do juiz (inventário de claims com status); extração automática não implementada |
| [mStyleDistance](https://arxiv.org/abs/2502.15168v1) e [autoria multilíngue](https://arxiv.org/pdf/2509.16531) | voice match por embeddings de estilo | Pesquisa: LUAR é o mais fraco em PT (~76,8 no PAN); mStyleDistance é MIT |
| Wang et al. ("Catch Me If You Can? Not Yet", Findings of EMNLP 2025) e [AuthorMix](https://arxiv.org/abs/2603.23069) (preprint) | imitação de estilo, adapters | LLMs falham mais em escrita informal; não há evidência de LoRA pessoal com poucas amostras. A trilha de adapter continua opcional e posterior. |
| [XFORMAL](https://arxiv.org/pdf/2104.04108) | formalidade PT-BR | Datado (2021) e sem licença no repositório |
| spaCy 3.8 + `pt_core_news_sm` (v0.3.0, M1.6) | papéis sintáticos para sujeito/objeto com substantivos comuns | Experimento em 167 casos: 1 detecção nova, 0 falso vermelho. Não adotado (`evals/experiments/syntax_roles.json`) |
| NLI ASSIN2 com BERTimbau (v0.3.0, M1.7) | sinal extra para antônimos fora do léxico e omissões | Nenhuma violação nova; 9/56 falsos vermelhos. Rejeitado (`evals/experiments/nli_probe.json`) |
| Claimify (revisitado na v0.3.0) | extração automática de claims | Sem código oficial publicado; a parte útil (claims com desambiguação) já está no contrato do juiz |
| Inspect, Promptfoo, DeepEval (v0.3.0) | framework de avaliação | Não adotados: o runner próprio (`scripts/bench_skill_only.py`) grava o que estes fariam (manifesto congelado, custo, respostas brutas) sem dependência nova |
| Outlines, Guardrails (v0.3.0) | saída estruturada / validação | Não adotados: o problema do VozNativa é fidelidade semântica, não formato; o parser do juiz já tolera JSON imperfeito |

## Corpora

Ver `references/corpora/` e `docs/LICENSING.md`. Fatos que mudaram decisões:

- Carolina: a 1.3 (portal) diz CC BY-NC-SA 4.0; a 2.0.1 Bea (Hugging Face) diz CC BY 4.0 no card e nos cabeçalhos, mas a licença por documento varia. O piloto só de metadados (v0.3.0) mostrou que `social_media` é ficção do Wattpad e que não há metadado de região: o Carolina não serve para regionalidade.
- C-ORAL-BRASIL I: centrado em Belo Horizonte/MG. Oralidade observada ali não é marcador nacional nem "mineiro" sem contraste.
- SP2010: licença não encontrada.
- NURC-SP: digitalizado (375 inquéritos); o Corpus Mínimo é CC BY-NC-ND 4.0.

## v0.4.0 — padrões PT-BR e PT-BR x PT-PT (consulta: 2026-10-21)

| Referência | Versão / data | O que é | Adotado no VozNativa | Não adotado / ressalvas |
|---|---|---|---|---|
| [LanguageTool, módulo pt](https://github.com/languagetool-org/languagetool/tree/master/languagetool-language-modules/pt/src/main/resources/org/languagetool/rules/pt) | commit `c203fb9` (2026-10-21) | corretor com regras de estilo pt (gerundismo, `VERBAL_NOUNS_TO_VERB`), listas de clichês, redundâncias, *weasel words*, prolixidade e `pt-BR/replace.txt` (≈250 trocas PT-PT → PT-BR) | ideia de tratar gerundismo como "possível" e de separar listas por variante; famílias novas do catálogo v2 (pleonasmo, conectivo redundante, decalque) | nada copiado: código LGPL-2.1 e listas com trechos CC BY-SA 3.0 (Wikipedia) trariam obrigação ShareAlike a um repositório sem licença definida (proposta Apache-2.0). Regras lexicais isoladas, sem gênero nem posição; o pt-BR não tem mantenedor segundo o fórum |
| [Lei nº 15.263/2025](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/Lei/L15263.htm) | 14/11/2025 | Política Nacional de Linguagem Simples (frases curtas, ordem direta, palavras comuns, termos técnicos explicados) | base para tratar oficialês como **deslocado** fora de documento oficial e para a família de nominalização | a lei rege comunicação pública; não vira regra para texto jurídico ou acadêmico |
| Manual de Redação da Presidência da República | 3ª ed., 2018 | clareza, concisão, impessoalidade; desaconselha "a nível de" e jargão | "a nível de" forte em qualquer gênero não isento; oficialês isento em `legal` | cópia oficial não verificada nesta consulta (há cópias institucionais) |
| [Torres, UFC (2009)](https://repositorio.ufc.br/handle/riufc/3599); [Santos, UnB (2008)](https://www.repositorio.unb.br/bitstream/10482/3406/1/2008_PatriciaTavaresASantos_orig_completo.pdf) | dissertações | gerúndio na expressão do futuro; definição de gerundismo por forma, aspecto, modalidade e tempo; estigma social | gerundismo passou a forte só com verbo pontual (enviar, verificar...) e fica de fora quando o verbo é durativo e há âncora temporal ("às 10h vou estar viajando") | listas de verbos montadas pelo desenvolvedor a partir dessas definições; não calibradas em corpus |
| Guias de redação ENEM (Descomplica, Vestibulando Web, Estratégia) | consultados 2026-10-21 | "desde os primórdios" desaconselhado de forma consistente; "hoje em dia" controverso; nenhum critério do INEP proíbe essas frases | aberturas genéricas só na primeira frase do parágrafo; gênero `essay` (redação escolar) com isenções: conectivo explícito é critério de coesão | guias comerciais, não pesquisa; usados só para não punir o que a banca pede |

## v0.6.0 (2026-11-05)

Corpus tooling, dated slang, community lexicons and public-domain literature: `docs/COMPETITIVE_ANALYSIS_v0.6.md`.

## v0.7.0 (consulta: 2026-11-06)

| Fonte | O que foi verificado | Uso |
|---|---|---|
| GitHub API e README/LICENSE de UD_Portuguese-GSD (`c91edee`), -PetroGold (`5814c7f`), -PUD (`0fdcc05`), -DANTEStocks (`4268e8e`), -CINTIL (`dc2cb3a`) | licenças CC BY-SA 4.0, CC BY-SA 4.0, CC BY-SA 3.0, CC BY 4.0, CC BY-NC-ND 4.0; o README do GSD diz que a licença cobre as anotações, não o conteúdo | CP3 (4 fontes integradas; CINTIL só catálogo); `text_rights: unclear` |
| huggingface.co/spacy/pt_core_news_sm | v3.7.0, CC BY-SA 4.0, treinado em UD Bosque v2.8 + WikiNER | ADR-0002: não embutido no pacote MIT |
| stanfordnlp.github.io/stanza/available_models.html | página não declara licença dos modelos nem lista português | ADR-0002: não verificado, não adotado |
| docs.copyleaks.com (writer-detector check; idiomas) | endpoint, auth, campos, `pt` suportado; significado de `summary` não declarado | CP11 adapter (contrato verificado) |
| docs.gptzero.me/api-reference | `POST /v2/predict/text`, `modelVersion`; auth e campos de resposta não estavam na página | CP11 adapter parcial |
| docs.originality.ai | endpoint e campos não confirmados na página lida | CP11 `UNSUPPORTED` |
| ai-act-service-desk.ec.europa.eu, Art. 50 | §2 marcação legível por máquina; §4 divulgação com exceção de controle editorial; data de aplicação não na página | CP12 nota de divulgação na proveniência |
