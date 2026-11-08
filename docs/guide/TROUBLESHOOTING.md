# Problemas comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| `voznativa: arquivo não encontrado: ...` (exit 64) | caminho errado ou relativo a outra pasta | a mensagem mostra o diretório atual; caminhos com espaço vão entre aspas |
| `o arquivo não está em UTF-8` (exit 64) | arquivo salvo em ANSI/Latin-1 | salve como UTF-8 e rode de novo |
| `... é uma pasta` (exit 64) | passou uma pasta | passe o arquivo de texto |
| acentos viram `?` | pipe do PowerShell 5.1 troca acentos antes de o texto chegar | passe o arquivo como argumento, sem pipe |
| `--cmd, --emulate or --candidate is required` | `rewrite` precisa de um provider | sem modelo: `voznativa demo`, `plan`, `diagnose`, `compare`; com stub: [QUICKSTART](QUICKSTART.md#5-com-um-provider) |
| `provider_error` com "No such file" | o provider roda num diretório temporário vazio | use caminho absoluto no `--cmd` (ou a forma JSON para caminhos com espaço) |
| o `rewrite` devolveu o texto igual | `no_change` (nada a mudar) ou `returned_original` (nenhuma candidata segura) | leia `reason`; `--force` chama o modelo mesmo sem achados |
| `needs_judgment` em vez de `accepted` | gates não provam equivalência | juiz independente (`--judge-cmd` com outro modelo) ou revisão humana assinada; o juízo do próprio agente não aprova |
| `evaluate` dá `INVALID` | especificação errada, arquivo congelado alterado, independência sem evidência, caminho fora do repositório | leia `problems` no JSON |
| `--replay` dá `NOT_REPLAYABLE` | o run foi gravado com a árvore suja ou sem a especificação | grave runs com a árvore limpa |
| `standards resolve` dá `UNKNOWN` | nenhuma edição registrada valia naquela data, ou a fonte só está catalogada | registre a edição certa com a fonte oficial; a mais recente nunca é presumida |
| `voznativa doctor` com FAIL | dependência ou dados ausentes | siga a dica de cada linha; em geral `python -m pip install .` de novo |
