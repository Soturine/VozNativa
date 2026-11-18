# Problemas comuns

| Sintoma | Causa | O que fazer |
|---|---|---|
| `pip install` falha com `Cannot import build backend 'setuptools.build_meta'` | o ambiente desliga o isolamento do build: `PIP_NO_BUILD_ISOLATION=0` (o pip lê esse `0` ao contrário: isolamento **desligado**), `pip config` com `no-build-isolation`, ou `--no-build-isolation`; num venv novo não há setuptools para o build | rode sem a variável (`Remove-Item Env:PIP_NO_BUILD_ISOLATION` no PowerShell, `unset PIP_NO_BUILD_ISOLATION` no bash), ou instale o build antes (`python -m pip install "setuptools>=77"`), ou instale o wheel da release, que não precisa de build |
| `voznativa: arquivo não encontrado: ...` (exit 64) | caminho errado ou relativo a outra pasta | a mensagem mostra o diretório atual; caminhos com espaço vão entre aspas |
| `o arquivo não está em UTF-8` (exit 64) | arquivo salvo em ANSI/Latin-1 | salve como UTF-8 e rode de novo |
| `... é uma pasta` (exit 64) | passou uma pasta | passe o arquivo de texto |
| acentos viram `?` | pipe do PowerShell 5.1 troca acentos antes de o texto chegar | passe o arquivo como argumento, sem pipe |
| `--cmd, --api-url/--api-model, --emulate or --candidate is required` | `rewrite` precisa de um provider | sem modelo: `voznativa demo`, `plan`, `diagnose`, `compare`; com stub: [QUICKSTART](QUICKSTART.md#5-com-um-provider) |
| `provider_error` com "No such file" | o provider roda num diretório temporário vazio | use caminho absoluto no `--cmd` (ou a forma JSON para caminhos com espaço) |
| o `rewrite` devolveu o texto igual | `no_change` (nada a mudar) ou `returned_original` (nenhuma candidata segura) | leia `reason`; `--force` chama o modelo mesmo sem achados |
| `needs_judgment` em vez de `accepted` | gates não provam equivalência | juiz independente (`--judge-cmd` com outro modelo) ou revisão humana assinada; o juízo do próprio agente não aprova |
| `evaluate` dá `INVALID` | especificação errada, arquivo congelado alterado, independência sem evidência, caminho fora do repositório | leia `problems` no JSON |
| `--replay` dá `NOT_REPLAYABLE` | o run foi gravado com a árvore suja ou sem a especificação | grave runs com a árvore limpa |
| `standards resolve` dá `UNKNOWN` | nenhuma edição registrada valia naquela data, ou a fonte só está catalogada | registre a edição certa com a fonte oficial; a mais recente nunca é presumida |
| `voznativa doctor` com FAIL | a categoria na linha diz o tipo: `package`/`package_data`/`dependency` (instalação), `config`, `provider_not_found`, `permission` | siga a dica de cada linha; para instalação, `python -m pip install .` de novo num venv limpo |
| `'cmd' is refused in a project file` (exit 64) | um `.voznativa.toml` do projeto tentou escolher o comando do provider | é proteção: um repositório não decide o que roda na sua máquina. Ponha `cmd` no arquivo do usuário (`voznativa config` mostra o caminho) ou passe `--cmd` |
| `unknown key` / `wrong type` / `invalid TOML` (exit 64) | erro no arquivo de configuração | corrija a chave indicada; `voznativa config` lista as chaves válidas |
| não sei quantas chamadas um `rewrite` vai fazer | — | `voznativa rewrite texto.txt --dry-run` mostra plano, unidades e o teto de chamadas sem iniciar o provider |
