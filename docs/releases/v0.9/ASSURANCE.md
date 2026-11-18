# Assurance da v0.9 (CP8): Assertiva, Derivanta e segurança

## Derivanta Engine 0.1.0

`derivanta-engine inspect --maintainability --format json` em clones limpos de `17d1f10` (`v0.8.1`) e `3e410b9` (candidata do CP8), depois `compare`. Inspeção estática: nada foi instalado nem executado.

| Resultado | Quantidade |
|---|---|
| comparabilidade | COMPARABLE |
| persistentes | 176 |
| ausentes | 1 (complexidade em `cli.py` que a refatoração do `rewrite` dividiu) |
| novos | 25, todos INFO |

Triagem dos novos (fundamentada; INFO não é ordem de refatoração):

| Regra | Onde | Decisão |
|---|---|---|
| `DUPLICATE_BODY` | `providers.py`: laço de novas tentativas e envio HTTP copiados para o `ChatAPIProvider` no CP2 | **corrigido** em `195137e`: um dono (`_generate_with_retries`, `_send_request`); testes de provider iguais |
| `HIGH_COMPLEXITY` (18) | funções novas de `docx`, `cli`, `diagnose`, `compare._class_issues`, `config`, `packs`, `pdf`, `onboarding`, `providers`, `privacy_gate` | aceito: cada uma é coberta por testes de defeito e controles, e 20/20 mutantes dirigidos morreram ([EVALUATION.md](EVALUATION.md)); dividir sem defeito demonstrado só mexeria em código verificado |
| `DUPLICATE_TABLE` (4) | tabelas de argumentos em testes e no script de braços; a lista de tipos gramaticais repetida no teste | aceito: especificação deliberada no teste, argumentos de linha de comando |
| `UNREFERENCED_DEFINITION` (2) | classes de teste em `test_v09_docx.py` | aceito: o `unittest` as descobre dinamicamente |

## Assertiva 0.10.1

`assertiva audit --execute` em clones limpos (sem mudanças locais), suíte executada numa cópia isolada; relatórios fora do repositório.

| Run | Revisão | Suíte (invocações) | Achados | O que foi feito |
|---|---|---|---|---|
| 1 | `195137e` | FAIL (1.395) | `NATIVE_TESTS_FAILING` (high): `test_corpus_tei.test_connector_reads_gzipped_tei` com `MemoryError`; 1 `info` (checks da CI não classificados, como nas rodadas anteriores) | causa achada: **defeito latente anterior à v0.9**: `read_tei` pedia `read(500_000_001)` e o descompressor alocava 500 MB para qualquer arquivo. Corrigido em `7176d24` (leitura em blocos de 1 MiB, limite igual), com teste que registra a leitura de 500.000.001 bytes no código antigo. A mesma falha tinha aparecido uma vez na suíte local e eu a atribuíra à carga da máquina: a Assertiva mostrou que não era ruído |
| 2 | `7176d24` | FAIL (1.396) | `NATIVE_TESTS_FAILING` (high): `test_v08_evidence_paths` exige `docs/releases/v0.9/RELEASE_QUALIFICATION.md`, que ficou fora daquele commit (passava localmente porque o arquivo existia na árvore de trabalho); `BROAD_ERROR_EXPECTATION_SIGNAL` (medium): o teste novo usava `assertRaises(Exception)` | o registro entrou no commit seguinte; o teste passou a esperar `AccessError` |
| 3 | commit seguinte | ver abaixo | ver abaixo | — |

Em todas as execuções: wheel construído, instalado e importado com fechamento de dependências PASS; testes contra o wheel NOT_RUN **pela ferramenta** (sem adaptador; a suíte contra o wheel roda no gate de pacote do `qualify.py`); 0 candidatos a falso verde.

RESULTADO_ASSERTIVA_3

## Segurança das superfícies novas (CP8.5)

| Superfície | Ameaça | Controle | Prova |
|---|---|---|---|
| configuração do projeto | repositório clonado escolhe o comando, o servidor ou as credenciais do provider | `cmd`, `judge_cmd`, `provider_env*`, `api_*` só no arquivo do usuário ou na linha de comando | `test_v09_cli_config.ProjectFileTrustBoundary` (provider nunca chamado) |
| `doctor` | carregar código de rede sem pedido | só módulos do núcleo; `--probe-provider` explícito | `test_v08_security` (socket proibido) e `DoctorCategories` |
| adapter HTTP | texto enviado a outro host por engano; chave em mensagem | endereço não local recusado sem `--api-allow-remote`; chave só por variável de ambiente, nunca no id nem em erro; resposta limitada em bytes; um redirecionamento 307/308 de POST não é seguido e 301/302/303 viram GET sem corpo (comportamento do `urllib`) | `test_v09_providers.ChatAPIContract` |
| juiz | o próprio modelo aprova a própria reescrita | relação pelo modelo declarado e pelo CLI de agente | `GeneratorRelation`; real antes × depois |
| DOCX | XML com DTD/entidades, bomba de descompressão, original sobrescrito, parágrafo protegido alterado | recusa de DTD/entidades e de `document.xml` acima de 50 MB; saída sempre arquivo novo; `check` parte a parte | `test_v09_docx` (incl. `test_dtd_and_entities_are_refused`) |
| PDF | arquivo malformado ou cifrado | erro claro, sem tentar senha | `test_v09_pdf.test_a_malformed_pdf_is_a_clear_error` |
| packs | dado linguístico vira código ou autoridade sobre os gates; caminho para fora; substituir pack embutido | envelope v1 (chaves proibidas, `safe_load`, limites, caminhos, id) | `test_v09_packs` (8 tipos de recusa; `compare` idêntico com e sem pack) |
| privacidade no push | fragmento de documento privado publicado (incidente da v0.8.1) | `scripts/privacy_gate.py` em cada push, sobre o patch de cada commit | até o CP7: 9 pushes, 12 execuções do gate; bloqueou 3 vezes antes do push (valores plantados no teste, variável com forma de credencial, um nome público que coincidia com um documento privado), sempre corrigido no commit local |

Continua valendo o modelo de ameaças da v0.8 ([`../v0.8/THREAT_MODEL.md`](../v0.8/THREAT_MODEL.md)); o risco aceito V08-GAP-23 (`--provider-env inherit` como padrão) segue até a 1.0.
