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
