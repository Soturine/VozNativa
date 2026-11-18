# Plano da v0.9.0: Packaging, Integrations, Editorial Intelligence & Real-World Quality

Plano da rodada v0.9, escrito no CP0 **antes** de qualquer mudança de comportamento. Estado e retomada: [`EXECUTION_STATE.md`](EXECUTION_STATE.md) (o Git vence os dois). Lacunas: [`GAP_REGISTER.md`](GAP_REGISTER.md). Requisitos, testes e evidência: [`TRACEABILITY.md`](TRACEABILITY.md).

- **Partida:** `main` = `origin/main` = `17d1f10` (tag anotada `v0.8.1`, objeto `f10de1e`; release estável Latest com wheel, sdist e `SHA256SUMS.txt`), conferido com `git fetch --tags` em 2026-11-18. Árvore limpa.
- **Branch:** `dev/v0.9.0`, criada de `17d1f10`.
- **Commits:** por CP (um ou mais atômicos), identidade local do repositório (Rafael Souza, noreply Soturine), **sem trailers de coautoria de IA**. Sem force push, sem `reset --hard`, sem reescrita de histórico público.
- **Push:** só depois do gate de privacidade (abaixo), executado e lido **como comando separado**. Depois do push, SHA remoto conferido.
- **CI:** o workflow continua só `workflow_dispatch`. Nenhum dispatch durante os CPs; um dispatch na `main` integrada no CP9 (repetido só se uma falha for corrigida).
- **Release:** tag anotada `v0.9.0` e GitHub Release estável só no CP9, se os critérios abaixo passarem. Sem PyPI.

## Marcos e prioridade

O tema do roadmap é *Packaging & Integrations*, mas a meta da rodada é **melhorar a escrita de verdade**, não só somar integrações ou baixar contagens de heurísticas. Os dogfoods da v0.8.1 mostraram que um gate limpo ou menos achados de padrão não garantem nem equivalência semântica nem boa redação.

| Marco | CPs | Resultado esperado |
|---|---|---|
| M1 — Integrações e providers | CP1, CP2, parte do CP6 | Skill usável em hosts reais; provider local/custom; mesmo engine e mesmos gates em todos os hosts |
| **M2 — Qualidade de documentos longos** | **CP3**, CP7 | voz e terminologia consistentes entre capítulos; repetição introduzida pela reescrita detectada; antes × depois medido |
| **M3 — Preservação semântica robusta** | **CP4**, CP7 | ações, papéis, qualificadores, condições, modalidade e tempo cobertos; menos falsos verdes sem excesso de falsos vermelhos |
| M4 — Documentos e normas | CP5 | DOCX seguro num subconjunto declarado; PDF com extração e anotação; normas com fonte e vigência |
| M5 — Dogfood, benchmarks e release | CP7, CP8, CP9 | gêneros variados; Assertiva e Derivanta reais; qualificação multiplataforma; release |

**M2 e M3 são prioridade de resultado.** Se o tempo apertar, encolhem primeiro as integrações secundárias (hosts não instalados, Emulate sem chave, modelos locais além de um adapter executável) e os formatos (PDF além de extração e anotação), sempre com estado `PARTIAL`/`NOT_RUN` declarado. A v1.0 fica reservada a contratos estáveis; nada desta rodada a antecipa.

## Gate de privacidade antes de cada push

`scripts/privacy_gate.py` (CP0) compara o diff e as mensagens de **todos os commits ainda não publicados** (`origin/<branch>..HEAD`, ou `origin/main..HEAD` no primeiro push) com:

1. os documentos privados usados nos dogfoods (lidos fora do repositório, nunca copiados): sequências de cinco palavras e tokens característicos ausentes do repositório na base;
2. uma lista de termos sensíveis guardada fora do repositório (nomes, instituição, nomes de arquivo);
3. credenciais (padrões de `voznativa.redact`), caminhos pessoais (`C:\Users\<nome>`, `/home/<nome>`) e e-mails que não sejam noreply.

Exit 0 = PASS; qualquer achado bloqueia o push até ser removido do commit local (os commits ainda não publicados podem ser refeitos; os publicados, não). No CP9, o gate roda também com `--tree` sobre o intervalo inteiro `17d1f10..final`.

## Escopo por CP

| CP | Conteúdo | Aceite |
|---|---|---|
| CP0 | estado real, leitura, baseline limpa em `17d1f10`, gate de privacidade, plano, gaps, rastreabilidade, critérios de release congelados | baseline registrada; critérios abaixo escritos antes de qualquer correção |
| CP1 | instalação (Windows 3.11/3.12, Linux em contêiner, wheel fora do checkout), `doctor` com causas separadas e ação por causa, configuração por usuário e por projeto com precedência documentada, `rewrite --dry-run`, correções documentais já conhecidas | instalação limpa, `doctor`, `demo`, configuração, execução e leitura do resultado testados |
| CP2 | contrato de provider mínimo (capacidades, custo, chamadas, erros tipados), adapter HTTP compatível com a API de chat da OpenAI para modelos locais (Ollama, llama.cpp, LM Studio), Emulate, juiz × gerador, hosts (Claude Code, Codex, Gemini CLI) | contrato testado; um fluxo agent-led real e um provider real ponta a ponta; demais com estado verificável |
| CP3 | memória editorial entre unidades (termos, grafias, aberturas recorrentes), guard global de convergência de estilo, desempenho e teste de tempo estável | replay real antes × depois; falsos alarmes medidos; sem regressão crítica |
| CP4 | qualificador apagado, troca de evento/estado (executado × planejado × testado × hipotético), gaps morfológicos GAP-04/18/19/20/27, diagnóstico gramatical de alta confiança, siglas, Router | conjunto prospectivo congelado antes da regra; caso falha antes e passa depois; controles |
| CP5 | representação intermediária reversível, DOCX seguro (extração, reinjeção em cópia, ida e volta), PDF com escopo honesto (extração rastreável, anotação), normas | um fluxo documental real com ida e volta testada; sem edição do original |
| CP6 | contrato e validador de packs, política de contribuição, Corpus Registry reavaliado, pack exercitado no fluxo real | especificação, validação, política e exemplo executável |
| CP7 | eixos separados, conjuntos novos com manifesto e auditoria de vazamento, braços comparáveis, mutação dirigida | relatório antes × depois com método, incerteza e estados por braço |
| CP8 | dogfood real, segurança, Assertiva, Derivanta, documentação final | registros de dogfood, auditorias, docs consistentes |
| CP9 | versão `0.9.0`, qualificação final, PR com merge commit, CI final, tag anotada, release | ver critérios |

**Fora de escopo** (escopo negativo do mantenedor): modelo PT-BR treinado, LoRA, interface web, editor universal de PDF, CLI estável antes da 1.0, equivalência semântica universal, nota de "humanização", evasão de detectores, provider declarado sem execução real, corpus de licença incerta no repositório, refatorar todos os INFO do Derivanta.

## Critérios de release (congelados no CP0, antes do desenvolvimento)

### Obrigatórios para release estável `v0.9.0`

Qualquer FAIL bloqueia a release estável.

| # | Critério |
|---|---|
| R1 | `qualify.py --scope release` em árvore limpa, Windows 10, CPython 3.12: unittest, validador, semânticas dev e holdouts (safety e strict), regressões de decisão e roteador, códigos de saída, gatilhos da CI, pacote (sdist → wheel → venv limpo → smoke → suíte contra o wheel), todos PASS |
| R2 | unittest e gate de pacote também em CPython 3.11 no Windows, e a qualificação em Linux (contêineres 3.11, 3.12, 3.13). Se o Docker não responder, Linux é substituído pela CI de R6 (mesma política da v0.8.1), com o desvio registrado |
| R3 | `ptbr-bench-v4` 22/22, `ptbr-bench-v5` 36/36 e amostra de predicados sem piora (≥ 17/20 riscos, ≤ 1/18 falsos alarmes); holdouts e congelados byte-idênticos a `17d1f10` |
| R4 | cada correção de comportamento da v0.9 tem teste que falha em `17d1f10` e passa no final; controles passam nas duas |
| R5 | gate de privacidade PASS em cada push e no intervalo inteiro `17d1f10..final` com `--tree` |
| R6 | CI do GitHub no commit final da `main`, conferida ao vivo por `scripts/ci_evidence.py`, 8/8 jobs. Se a CI não puder rodar por limite externo (billing, cota), R6 fica NOT_RUN e a release estável depende de R1 e R2 completos com Linux em contêiner; motivo registrado na qualificação e nas notas |
| R7 | toda funcionalidade declarada nas notas tem teste executado; integração declarada como verificada tem execução real registrada (stub nunca vale como `REAL_PROVIDER_VERIFIED`) |
| R8 | nenhum falso verde semântico P1 conhecido sem correção ou `ACCEPTED_RISK` explícito no registro de gaps e nas notas |
| R9 | desempenho: o teste de tempo do `compare` com método definido no CP3 passa; tempo do `compare` no documento de referência sem piora acima de 20% em relação a `17d1f10`, medido na mesma máquina e com o mesmo método |
| R10 | versão `0.9.0` igual em `voznativa/__init__.py`, `SKILL.md`, `.claude-plugin/plugin.json`, README e metadados; wheel e sdist construídos da revisão exata da tag, `SHA256SUMS.txt` conferido depois do download |

### Externos, não obrigatórios

Registrados como `NOT_RUN` quando não houver pessoas, acesso ou autorização: holdout independente, revisão humana cega, juiz de outro fornecedor, hosts não instalados nesta máquina (Codex, Gemini CLI), Emulate ao vivo (sem chave), macOS.

### Complementares

Assertiva `audit --execute` e Derivanta Engine `inspect --maintainability` + `compare` com a v0.8.1, na revisão candidata.

### Pre-release

Se R1, R3, R4, R5 e R10 passarem mas algum outro obrigatório falhar por motivo não corrigível na rodada, a publicação possível é a pre-release `v0.9.0.dev0`, com versão do pacote, manifests e tag coerentes. Se R1, R3, R4, R5 ou R10 falharem, nada é publicado e o bloqueio fica registrado.

## Custos

Execuções com provider real usam `claude -p` sem ferramentas, `--provider-env minimal`, teto por chamada (`--max-budget-usd`) e teto de chamadas por execução. Custo observado é registrado por execução. Escritor e juiz do mesmo modelo nunca contam como julgamento independente.
