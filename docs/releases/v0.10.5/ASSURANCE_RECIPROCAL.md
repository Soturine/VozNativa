# Dogfood recíproco da v0.10.5 (R10, R11)

Quatro trilhas, cada uma com o instrumento certo e o seu estado. Nenhuma conclusão de uma ferramenta é atribuída a outra.

| Trilha | Natureza | O que rodou | Estado |
|---|---|---|---|
| **VozNativa** | Skill + CLI (produto sob prova) | campanha offline (427 textos), braços live com sessões reais da Skill, 3 documentos inteiros | `REAL_HOST_EXECUTED` — resultados em [`FIRE_TRIAL_RESULTS.md`](FIRE_TRIAL_RESULTS.md) e [`SKILL_LIVE_DOGFOOD.md`](SKILL_LIVE_DOGFOOD.md) |
| **Derivanta Framework** (`Soturine/Derivanta`, `12f1dc3`, v0.1.0) | orientação de agente host | 2 sessões reais do Claude Code (Sonnet) com a Skill do Framework instalada no projeto, sobre cópia só-leitura do VozNativa | `REAL_HOST_EXECUTED` |
| **Derivanta Engine** (`Soturine/Derivanta-Engine`, branch do PR #6, `a9eb371`) | inspeção estática; não executa testes | `inspect --maintainability --format json` em v0.10.0 e v0.10.5 na mesma pasta; `compare` | `CLI_EXECUTED_STATIC` |
| **Assertiva** (`Soturine/Assertiva` 1.0.1 + branch do PR #11) | auditoria executável de testes | `audit --execute` no VozNativa v0.10.0 e no candidato | `AUDIT_EXECUTED` |

## Derivanta Framework → VozNativa

| Sessão | Pedido | Skill ativada? | Arquivos do Framework lidos | Conta como achado do Framework? |
|---|---|---|---|---|
| implícita | "audite este projeto de IA" sem nomear o Framework | **não** | nenhum | **não**: opinião espontânea do modelo |
| explícita | auditoria pedida com o Framework | sim | `workflows/AUDIT.md` | sim |

Achados da sessão explícita (feita só por leitura; o próprio agente declarou que não rodou testes nem CLI):

1. **Independência do juiz declarada parecia observada.** Um juízo lido de arquivo com `generator_relation: different_model` aprova, e o relatório não dizia que a relação era só declarada por quem julgou (no fluxo da Skill, o próprio agente). Confirmado por leitura de `compare.apply_judgment` e por teste → **V105-GAP-11**, corrigido em parte (`relation_evidence: DECLARED | ENGINE_OBSERVED`). Limite que permanece: um agente desonesto ainda pode declarar uma relação falsa; mudar a aceitação mudaria o contrato da v0.10.
2. **Registro citava documento inexistente** (`SKILL_LIVE_DOGFOOD.md`) → **V105-GAP-12**. Observação desta retomada: o registro chegou a marcar o gap como FIXED sem que o arquivo existisse na árvore; o documento foi escrito agora, com os números finais.
3. Qualificação da v0.10.5 sem resultados além do R1 e versão ainda 0.10.0 no momento da auditoria: correto naquele ponto; endereçado no fechamento.
4. Nenhum holdout independente: correto; segue `NOT_RUN` (depende de terceiros).

**Retorno ao Framework** (falha real de uso, não opinião): o README não diz como instalar o Framework como Skill de projeto, e os links `../` da Skill exigem as pastas irmãs ao lado dela. Registrado aqui; nenhuma mudança foi feita no repositório do Framework nesta rodada.

## Derivanta Engine → VozNativa

Detalhes e triagem em [`MAINTAINABILITY.md`](MAINTAINABILITY.md). Resumo: a primeira comparação (duas pastas com nomes diferentes) saiu `DIFFERENT_TARGET` com zero achados em tudo, o que poderia ser lido como "nada mudou". Na mesma pasta: `COMPARABLE`, 212 persistentes, 15 novos (14 no harness da rodada, 1 de complexidade em `compare.py`), 1 ausente. Nenhum candidato de código não referenciado.

**PR #6** (classes de teste herdadas e `SyntaxWarning` vazando do código inspecionado): o segundo commit (`a9eb371`) decide classe de teste pela ancestralidade, não pelo nome, e resolve aliases importados de `TestCase`; controle: classe local cujo nome termina em `TestCase` e que não herda de `TestCase` **não** é teste. `tools/verify.py`: `GATE PASSED` (format, types, tests, conformance).

## Assertiva → VozNativa

`audit --execute` no VozNativa `v0.10.0` (`e274379`) e no candidato (`3ee45c5`), mesmo interpretador:

| | v0.10.0 | candidato |
|---|---|---|
| Suíte do projeto executada | `PASS` (exit 0) | `PASS` (exit 0) |
| Artefato (wheel) | `FAIL` | `FAIL` |
| Causa atribuída | `ENVIRONMENT`: `setuptools` ausente no interpretador que construiu | idem |

A atribuição está certa e foi conferida: o venv usado não tem `setuptools`, e o ambiente do usuário define `PIP_NO_BUILD_ISOLATION=0`, que o pip lê como **desligar** o isolamento; o `qualify` do próprio VozNativa constrói o mesmo wheel. O status do projeto (suíte PASS) ficou separado do status do ambiente.

**PR #11** refinado (`5f18982`): `ModuleNotFoundError` sozinho não prova que a culpa é do ambiente.
- Backend que o build importa mas que `build-system.requires` **não declara** → `PROJECT_CONFIGURATION`, com recomendação de declarar (com isolamento, o build falharia igual); projeto sem tabela `build-system` mantém o padrão setuptools.
- `PIP_NO_BUILD_ISOLATION` no ambiente fica registrado na evidência, e a linhagem diz "isolamento sobrescrito pelo ambiente" em vez de "build isolado".
- 2 testes novos vermelhos sem a mudança; os 10 testes do arquivo passam.

**As falhas herdadas da suíte da Assertiva nesta máquina.** Na v0.10 eram 5, todas ambientais (passam num venv limpo com as dependências da CI). Nesta rodada sobrou 1 na suíte completa (1362 passaram): `test_installed_artifact_context::test_self_tests_that_read_the_repository_hold_without_git_source_or_editable_install`. Ela **também falha no `main` limpo**, então não vem do PR. Causa provada, não presumida: a suíte interna roda num subprocesso que usa a pasta temporária compartilhada do pytest (`%TEMP%\pytest-of-<usuário>`), e essa pasta dá `PermissionError: Acesso negado` nesta máquina; com uma pasta temporária própria (`PYTEST_ADDOPTS=--basetemp=…`) o mesmo teste **passa no `main`**. Tirar `PIP_NO_BUILD_ISOLATION` não mudava nada, então essa hipótese foi descartada.

## VozNativa → as três ferramentas

Os READMEs da Assertiva, do Engine e do Framework estão em inglês. A guarda de idioma do VozNativa classifica esses textos como não-português (V010-GAP-16, mantido) e não os revisa. Nenhuma documentação em PT-BR dessas ferramentas existia para revisar, e nenhuma tradução foi feita para preencher o lugar. Estado: `NOT_RUN` para revisão de conteúdo PT-BR; controle negativo de idioma `PASS`, executado: `voznativa plan` nos primeiros 3 mil caracteres de cada README devolveu `language: en` (90, 106 e 92 palavras funcionais inglesas contra 1 portuguesa) e `decision: no_change` nos três.
