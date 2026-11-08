# Modelo de ameaças (v0.8, CP13)

## Ativos

Texto do usuário (pode ser privado), amostras de voz, documentos de fatos e o repositório usado como fonte; chaves de provider no ambiente; registros de avaliação e evidência; os dados de corpora (com direitos próprios); a autorização do usuário para editar (verso, fatos).

## Fronteiras de confiança

| Fronteira | Do lado de fora (não confiável) | Controle principal |
|---|---|---|
| texto → prompt | texto do usuário, documentos, corpora | cerca com hash do corpo; texto é dado, nunca instrução |
| prompt → provider | o provider e a resposta do modelo | gates sobre a candidata; tokens de protocolo reprovam; provider num diretório temporário |
| dados serializados → engine | planos, registros de `resume`, registros de avaliação, fichas YAML | revalidação a partir do texto e da autorização do chamador |
| repositório → leitores | documentação publicada | validador de segredos e caminhos pessoais |
| máquina → rede | qualquer serviço externo | nenhum comando offline abre conexão |

## Ameaças, controles e prova

| Ameaça | Controle | Prova | Risco residual |
|---|---|---|---|
| texto com instruções ("ignore as regras", `</final>`, tag de fechamento forjada) | `text.fence` fecha o bloco com hash do próprio corpo; `PROTOCOL_TOKENS` na candidata reprovam | `test_v08_security.PromptFence`; `test_document_rewrite` (provider malicioso) | o modelo ainda pode obedecer a instruções dentro do bloco; os gates pegam efeitos em valores, negação e estrutura, não todos os efeitos |
| plano ou registro serializado concedendo permissão (verso, desfecho aceito) | autorização vem do chamador; `resume` só reaproveita texto e revalida | `test_v08_integrity` (CP1) | — |
| registro de avaliação editado | `--verify` (coerência) e `--replay` (reexecução na revisão) | `test_v08_eval_integrity` | resumo não é assinatura; autoria não é provada |
| independência alegada sem prova | `independence_evidence` com commit de congelamento conferido | `IndependenceNeedsEvidence` | pessoas e custódia ficam `DECLARED` |
| caminho fora do repositório (link, junção, `..`) | caminho resolvido precisa ficar na raiz | `PathsStayInside` | — |
| YAML hostil (`!!python/object`) ou malformado em fichas | `yaml.safe_load` em todo o pacote; recusa clara | `HostileYaml` | — |
| XML hostil (XXE, bomba) em corpora TEI | parser sem entidades externas, limites | `test_corpus_tei` | — |
| caracteres invisíveis, bidi, homóglifos | `voznativa integrity` | `test_integrity` | não detecta marca d'água estatística |
| entrada enorme (CPU) | plano de documento até 200 mil palavras; `compare` da CLI recusa acima disso; validação global respeita `timeout_s` | `InputSize`; `test_v08_compare_perf` | `compare` via API Python não tem limite próprio |
| segredo em log, relatório ou documentação | `doctor` mostra só nomes de variáveis; relatórios guardam hashes; validador recusa tokens com cara de segredo nos documentos; registros de assurance sanitizados | `Doctor.test_never_prints_a_secret`; `test_v08_doc_validator`; `test_privacy` | — |
| segredo no ambiente vazando para o provider | `--provider-env minimal` passa só o necessário | `test_providers_hardening` | **o padrão é `inherit`** (o provider herda o ambiente); a documentação recomenda `minimal` |
| envio de texto a terceiros sem pedido | nenhum comando offline usa rede; provider só com `--cmd` explícito | `NothingLeavesWithoutAProvider`; `Doctor.test_ok_here_and_never_touches_the_network` | o comando passado em `--cmd` faz o que quiser com o texto |
| texto de corpus com direitos restritos | política por operação; recusa com exit 77; corpora fora do repositório | `test_corpus_policy`, `test_corpus_cli` (exit 77), smoke do wheel | — |
| autoavaliação do agente como juízo independente | `generator_relation: same_agent` não aprova | `test_v08_judge_relation` | um agente pode mentir sobre a relação; o engine marca sozinho quando gera e julga com o mesmo provider |
| norma de outra edição aplicada; critério sem fonte | resolver por data; critério só com verificação | `test_v08_standards`, `test_v08_rubric` | ficha `SOURCE_CITED` sem hash do arquivo |
| integridade acadêmica (referência, dado ou nota inventados) | `ground` exige fonte para valores; rubrica nunca dá nota; nada é gerado no modo de normas | `test_engine` (ground), `test_v08_rubric` | afirmação sem valor protegido só é pega pelo juiz ou por pessoa |
| `--replay` executando código | só código de uma revisão do próprio repositório, num subprocesso, num diretório temporário | `ReplayIsNotTheDigest` | um registro pode apontar qualquer commit do repositório local |

## Dependências

Única dependência obrigatória: PyYAML (`safe_load` em todo uso). Nenhum script externo é executado pelo pacote. Ferramentas de desenvolvimento (Cosmic Ray, Assertiva, Derivanta Engine) rodam em ambientes separados, nunca dentro do pacote.
