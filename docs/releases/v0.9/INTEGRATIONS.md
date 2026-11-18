# Integrações e providers da v0.9 (CP2)

Registro do que foi executado de verdade, com estado por integração. Todos os textos usados são **sintéticos**; transcrições, prompts e respostas ficam fora do repositório. Ambiente: Windows 10, CPython 3.12.6, Claude Code 2.1.317, 2026-11-18.

## Estado por integração

| Integração | Estado | Evidência |
|---|---|---|
| `CommandProvider` + `claude -p` (modo assistido por modelo) | **REAL_PROVIDER_VERIFIED** | `rewrite` de um e-mail sintético com escritor `claude-haiku-5-5` e juiz `claude-sonnet-5-5`, sem ferramentas, `--provider-env minimal`: 3 chamadas (1 escrita, 2 votos), US$ 0,049, desfecho `accepted` com `generator_relation: different_model`. **Não é julgamento independente**: mesmo fornecedor, e um juiz LLM continua falível |
| Relação gerador × juiz pelo modelo declarado | **REAL_PROVIDER_VERIFIED** (antes × depois) | mesmo modelo nos dois papéis, linhas de comando diferentes num argumento: `v0.8.1` = `unknown` → `accepted_by_llm`; v0.9 = `same_agent` → `needs_judgment` (3 chamadas reais em cada, US$ 0,006 cada) |
| Claude Code como host agent-led (Skill no projeto) | **REAL_HOST_VERIFIED** (AGENT_OBSERVED) | sessão headless com a Skill copiada para `.claude/skills/voznativa`, ferramentas restritas a `python`, leitura e escrita, teto de US$ 1,50: Skill descoberta e invocada; 11 comandos da CLI real; um texto reescrito (exit 3, autoavaliação `same_agent`, nada aprovado), outro NO_CHANGE; US$ 0,21, 23 turnos |
| `ChatAPIProvider` (formato chat-completions: Ollama, llama.cpp, LM Studio, vLLM) | **TESTED_WITH_STUB** | servidor HTTP real em `127.0.0.1` com respostas fixas: sucesso e tokens relatados, 404/400 de modelo, 401, 429 com nova tentativa, 503, JSON inválido, resposta vazia, timeout, URL remota recusada sem permissão, chave lida só do ambiente; pelo engine, candidata sem a negação nunca volta e candidata limpa ainda pede julgamento. Conexão recusada **real** (nenhum servidor na porta): `provider_error`, sem novas tentativas |
| Modelo local real (llama.cpp `llama-server` + Qwen2.5-0.5B-Instruct Q4_K_M, 491 MB, sha256 `74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db`) | **NOT_RUN** | binário e modelo baixados para fora do repositório; a execução do servidor foi **negada pelo controle de permissões da sessão**. Para rodar: iniciar `llama-server -m <modelo> --port 8089` e `voznativa rewrite texto.txt --api-url http://127.0.0.1:8089/v1 --api-model <alias>` |
| Plugin do Claude Code pela marketplace | DOCUMENTED_NOT_VERIFIED | instalar alteraria a configuração global do Claude Code do mantenedor |
| Codex | NOT_RUN | não instalado; caminhos (`.agents/skills/`, `~/.agents/skills/`) conferidos na [documentação oficial](https://developers.openai.com/codex/skills) |
| Gemini CLI | NOT_RUN | não instalado; `gemini skills install`, escopos e `/skills list` conferidos na [documentação oficial](https://geminicli.com/docs/cli/skills/) |
| Emulate | BLOCKED | sem `EMULATE_API_KEY`; adapter só com transporte simulado (`test_providers_hardening`). Erros agora tipados pelo mesmo mapeamento HTTP do `ChatAPIProvider` |

## Contrato de provider

O contrato continua mínimo: `id` e `generate(prompt, n) -> list[str]`. O engine — nunca o provider — aplica Ledger, `compare`, guards, orçamento (geração e juiz, DF-01) e proveniência, então nenhum adapter os contorna. Acrescentado na v0.9:

- `ProviderError.kind`: `not_found`, `connection_refused`, `timeout`, `auth`, `rate_limit`, `model_not_found`, `server_error`, `bad_request`, `invalid_response`, `empty_answer`, `too_large`, `exit_status`, `unsupported`; `transient` continua decidindo nova tentativa (conexão recusada e formato inválido não são repetidos).
- `identity(provider)`: programa e modelo **como configurados** (`--model`/`-m` na linha de comando, inclusive atrás de um wrapper; o modelo do adapter HTTP). Nada é adivinhado.
- `usage` (adapter HTTP): tokens somados só quando o servidor os informa. O relatório do `rewrite` traz `provider_identity` por papel.

### Relação gerador × juiz

| Situação | Relação | Efeito |
|---|---|---|
| mesmo objeto ou mesma linha de comando | `same_agent` | autoavaliação, não aprova (V08-GAP-16) |
| os dois declaram o mesmo modelo | `same_agent` | idem (novo) |
| mesmo CLI de agente ou mesmo adapter HTTP, sem prova de modelo diferente | `same_agent` | idem (novo, conservador) |
| os dois declaram modelos diferentes | `different_model` | o juízo conta; continua falível e não é independente se o fornecedor for o mesmo |
| demais | `unknown` | o juízo conta, como antes |

## Custos observados

| Execução | Chamadas | US$ |
|---|---|---|
| assistido por modelo, juiz de outro modelo | 3 | 0,049 |
| mesmo modelo como juiz, `v0.8.1` | 3 | 0,006 |
| mesmo modelo como juiz, v0.9 | 3 | 0,006 |
| agent-led (Claude Code) | 23 turnos | 0,212 |
| **total do CP2** | | **0,273** |
