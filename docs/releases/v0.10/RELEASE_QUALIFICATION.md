# Qualificação da v0.10.0

> Critérios R1–R15 congelados no CP0 ([`PLAN.md`](PLAN.md)), antes de qualquer mudança de comportamento. Preenchido com o que de fato rodou; o que não rodou fica NOT_RUN. Três coisas nunca somadas: implementação, qualificação local e qualificação externa.

Revisão qualificada localmente: **`132f3a5`** (`dev/v0.10.0`, árvore limpa). A CI final e a revisão da tag estão em [`EXECUTION_STATE.md`](EXECUTION_STATE.md).

## Resultados

| # | Critério | Resultado |
|---|---|---|
| R1 | baseline v0.9.0 reproduzida | **PASS** (CP0): `qualify.py --scope release --offline` numa worktree da tag, todos os gates locais PASS; conjuntos congelados das v0.7–v0.9 sem mudança |
| R2 | sem regressão P0/P1 | **PASS**: testes de privacidade e segurança PASS; holdout v0.9 18/18; regressão congelada 88/89; os falsos verdes novos achados na rodada (V010-GAP-01, -03, -04, -05, -16) foram corrigidos com teste |
| R3 | testes locais e pacote | **PASS** em `132f3a5`, Windows 10, CPython 3.12.6: validador, unittest (**1.116**: 1.114 PASS, 2 skips com motivo), semântica dev, holdouts safety e strict, decisão, roteador, códigos de saída, gatilhos da CI, pacote (sdist → wheel → venv limpo → smoke → suíte contra o wheel). Veredito INCOMPLETE só pelos externos (`review:pty` só POSIX, CI offline, holdout independente, revisão humana) |
| R4 | benches, predicados, regressões ≥ v0.9 | **PASS** (CP12): v4 22/22, v5 36/36, predicados 19/20 e 1/18, regressão 88/89 e 1/33, eventos e conjuntos da v0.9 iguais |
| R5 | capacidades contextuais operacionais com modelo real | **PASS (operação)**: contexto development 6/6, holdout 4/4; braços com modelo real em 10 textos de gêneros não mapeados (inclui misto e desconhecido), saídas registradas. **Ganho não demonstrado**: B4 × B5 sem diferença mensurável (n = 1); a release não alega melhora de qualidade pelo contexto aberto |
| R6 | semântica, diagnóstico, edição desnecessária | **PASS**: semântica dev 21/21 e 0/13 (piso 20/21 e ≤ 2/13), holdout 12/12 e 0/10 (base 10/12, 5/10); diagnóstico dev 7/7 e 0/9 (piso 6/7 e 0/9), holdout 5/5 e 0/5 (base 1/5, 0/5); engine 0/4 edições desnecessárias com modelo real (v0.9 0/4) |
| R7 | Watcher seguro em report/propose | **PASS**: 19 testes (rede negada, 403, 429, 5xx, endereço privado, resposta grande, licença alterada, fonte removida, arquivo de fontes inválido, sem modo apply); 6 fontes reais consultadas, 304 na segunda verificação |
| R8 | fontes e dados | **PASS**: matriz de elegibilidade ([`SOURCES_AND_CORPORA.md`](SOURCES_AND_CORPORA.md)); nenhum texto de corpus no Git (só contagens e ids); fixtures inventadas |
| R9 | dogfood recíproco real | **PASS**: Assertiva `audit --execute` em `v0.9.0` (1.402 invocações) e no candidato (1.495); Derivanta antes × depois `COMPARABLE`; VozNativa nos READMEs reais de Assertiva e Derivanta; defeitos confirmados corrigidos no dono com teste vermelho→verde e suíte do dono: VozNativa (inglês lido como português), Derivanta PR #6 (2), Assertiva PR #11 (1 + doc). Integração dos PRs nos outros repositórios: pendente do mantenedor (merge do Derivanta negado pelo controle de permissões da sessão) |
| R10 | mutação | **PASS**: 24/25 mortos (96%), o sobrevivente é mutante equivalente documentado; defeito do harness (bytecode velho) achado e corrigido; v0.9 reconferida 20/20 |
| R11 | desempenho ≤ 1,15 × v0.9.0 | **PASS** pelo método intercalado na mesma sessão: 6,34 s × 6,25 s (≈ 1,015). Desvio registrado: a primeira medição isolada do candidato deu 1,30 contra a baseline do CP0, porque a própria v0.9.0 passou de 5,52 s para 6,25 s entre as sessões; o perfil não mostra ponto quente novo; limite não alterado. Razão 800/100 blocos 14,8× (teste de tempo com limite 19× inalterado) |
| R12 | integrações honestas | **PASS**: [`RELEASE_NOTES.md`](RELEASE_NOTES.md#integrations) separa REAL_EXECUTED, TESTED_WITH_STUB, BLOCKED e NOT_RUN |
| R13 | privacidade | gate antes de cada push (bloqueou 1 vez: coincidência numérica de um quantificador de regex com um documento privado; código alterado, sem exceção); intervalo inteiro e `--tree` no fechamento: ver [`EXECUTION_STATE.md`](EXECUTION_STATE.md) |
| R14 | plataformas | Windows CPython 3.12.6 (R3) e **3.11.18**: gates locais PASS em `132f3a5` (1.116 testes; venv só com PyYAML e pypdf). Linux: pela CI final. macOS: NOT_RUN |
| R15 | coerência de release | versão `0.10.0` no pacote, `SKILL.md`, manifest do plugin e README (`test_readme`); tag, artefatos e checksums: ver [`EXECUTION_STATE.md`](EXECUTION_STATE.md) |

## Externos (não obrigatórios)

| Item | Estado |
|---|---|
| holdout independente | NOT_RUN: ninguém além do agente escreveu conjuntos |
| revisão humana cega | NOT_RUN: sem revisores |
| juiz de outro fornecedor | NOT_RUN: um fornecedor disponível |
| Codex, Gemini CLI | NOT_RUN: não instalados |
| modelo local real | BLOCKED/NOT_RUN: execução do servidor negada na v0.9 e não tentada de novo; Ollama e LM Studio não instalados |
| Emulate | BLOCKED: sem chave |
| macOS, Linux local | NOT_RUN (Linux coberto pela CI) |
| renderização DOCX no Word | NOT_RUN |
| Watcher agendado | SCHEDULER_READY: comando e instruções prontos, nada agendado |

## O que os testes não dizem

Nenhum resultado acima comprova equivalência semântica de reescritas nem melhora percebida por leitores. Os conjuntos, as regras, as triagens de texto real e os braços foram escritos ou lidos pelo mesmo agente; o modelo dos braços é de um único fornecedor.
