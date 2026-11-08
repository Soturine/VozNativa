# Primeiros passos

Tudo aqui roda localmente, sem modelo e sem chave, a partir da raiz do repositório. O comentário `# exit N` é o código de saída esperado; um teste roda estes comandos e confere.

## 1. Ver funcionando

```bash
voznativa doctor   # exit 0
voznativa demo     # exit 0
```

`demo` mostra o gate reprovando uma negação removida, pedindo revisão quando uma ação some e deixando passar (sem provar equivalência) uma reescrita boa.

## 2. Conferir uma reescrita

```bash
voznativa compare examples/quickstart/original.txt examples/quickstart/candidata-boa.txt         # exit 3
voznativa compare examples/quickstart/original.txt examples/quickstart/candidata-ruim.txt        # exit 1
voznativa compare examples/quickstart/original.txt examples/quickstart/candidata-perde-acao.txt  # exit 2
```

| Saída | Status | O que significa |
|---|---|---|
| 0 | `identical`, `accepted_*` | igual, ou aceito por um juiz independente ou revisão humana assinada |
| 1 | `fail` | algo protegido mudou (valor, negação, modalidade...): não entregar |
| 2 | `review_required` | sinal de risco: uma pessoa revisa |
| 3 | `no_deterministic_issues` | os gates não acharam nada; **isso não prova** que o sentido foi mantido |

## 3. Decidir se precisa mudar e diagnosticar o original

```bash
voznativa plan examples/quickstart/original.txt   # exit 0
voznativa plan examples/quickstart/email.txt      # exit 0
voznativa diagnose examples/quickstart/erros.txt  # exit 0
voznativa rewrite examples/quickstart/erros.txt --mode PROOFREAD --text-only  # exit 3
```

`plan` diz `edit` para o rascunho com fórmulas e `no_change` para o e-mail. `diagnose` acha "o o" repetido e terça-feira que não bate com 13/11/2026; `PROOFREAD` corrige só o erro formal e deixa a data para o autor.

## 4. Desfechos do `rewrite`

| Desfecho | Quando |
|---|---|
| `no_change` | nada a mudar (sem chamar o modelo) ou o modelo respondeu NO_CHANGE |
| `needs_judgment` | a candidata passou nos gates; falta um juiz ou uma pessoa |
| `needs_review` | passou com sinais de risco; uma pessoa revisa |
| `accepted` | gates e juiz independente concordam |
| `returned_original` | nenhuma candidata segura: o original volta |
| `provider_error` | o provider falhou; o original volta |

## 5. Com um provider

O `rewrite` chama um comando que lê o prompt no stdin e escreve a resposta. O repositório traz um stub determinístico (não é modelo). No Bash:

```bash
voznativa rewrite examples/quickstart/original.txt --cmd "python $PWD/examples/quickstart/stub_provider.py"  # exit 3
```

No PowerShell, troque `/` por `\` no caminho. Com um modelo de verdade (consome a sua conta e envia o texto ao provedor), veja [`AGENT_SKILL.md`](AGENT_SKILL.md) e o README.

## 6. Documento longo, normas e avaliação

```bash
voznativa rewrite examples/quickstart/documento-longo.md --long-form on --segment-words 80 --cmd "python $PWD/examples/quickstart/stub_provider.py"  # exit 3
voznativa standards list   # exit 0
voznativa evaluate evals/v08/datasets/events.json   # exit 0
```

Mais: [referência da CLI](CLI.md), [problemas comuns](TROUBLESHOOTING.md).
