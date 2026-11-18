# Instalar o VozNativa

Requer Python 3.11 ou mais novo. A única dependência obrigatória é PyYAML. O pacote **não está no PyPI**: instale a partir do repositório. Nada abaixo precisa de conta, chave de API ou rede depois do download.

## Windows (PowerShell)

```powershell
git clone https://github.com/Soturine/VozNativa.git
cd VozNativa
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
voznativa doctor
```

Se `py` não existir, use `python -m venv .venv`. Se o PowerShell recusar `Activate.ps1`, rode sem ativar: `.\.venv\Scripts\python.exe -m voznativa doctor`.

## Linux e macOS (bash ou zsh)

```bash
git clone https://github.com/Soturine/VozNativa.git
cd VozNativa
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
voznativa doctor
```

macOS: os comandos são os mesmos; a qualificação desta versão rodou em Windows e Linux, não em macOS.

## Sem clonar: pela tag ou pelo wheel da release

Num venv já ativado (Windows ou Linux):

```bash
python -m pip install "git+https://github.com/Soturine/VozNativa.git@v0.9.0"
```

Ou baixe `voznativa-<versão>-py3-none-any.whl` e `SHA256SUMS.txt` da [página de releases](https://github.com/Soturine/VozNativa/releases), confira o hash e instale o arquivo:

```bash
sha256sum -c SHA256SUMS.txt --ignore-missing      # PowerShell: Get-FileHash .\voznativa-*.whl
python -m pip install voznativa-*.whl
```

O wheel traz `references/` e os dados; os comandos funcionam fora do checkout.

Se a instalação a partir do código (clone ou URL `git+`) falhar com `Cannot import build backend 'setuptools.build_meta'`, o isolamento de build do pip está desligado no seu ambiente: veja [problemas comuns](TROUBLESHOOTING.md). O wheel não passa por build e não tem esse problema.

## Ferramenta isolada (sem ativar venv)

Com [`pipx`](https://pipx.pypa.io/) ou [`uv`](https://docs.astral.sh/uv/guides/tools/) já instalados por você:

```bash
pipx install git+https://github.com/Soturine/VozNativa.git
uv tool install git+https://github.com/Soturine/VozNativa.git
```

Estado: **DOCUMENTED_NOT_VERIFIED** nesta versão (nenhum dos dois estava no ambiente de qualificação). Para fixar uma versão, acrescente `@<commit>` à URL.

## Para desenvolver

```bash
python -m pip install -e . build
python scripts/qualify.py
```

## Conferir a instalação

`voznativa doctor` confere Python, os módulos do pacote, PyYAML, as referências, os dados do pacote, o diretório temporário, o arquivo de configuração e o provider configurado (programa encontrado, ferramentas do agente desligadas, credenciais liberadas presentes), e diz se variáveis de provider conhecidas estão definidas (nunca mostra o valor). Não usa rede nem lê textos. Saída 1 só quando algo não vai funcionar; cada problema vem com uma **categoria** (`python_version`, `package`, `dependency`, `package_data`, `permission`, `config`, `provider_not_found`, `provider_unsafe`, `credential`, `provider_call`, `timeout`) e com o que fazer. `voznativa doctor --probe-provider` faz **uma** chamada real ao provider configurado (pode custar e usar a rede) e classifica a falha.

## Configurar uma vez

`voznativa config` mostra os dois arquivos possíveis e de onde vem cada opção do `rewrite`. Precedência: flag > `.voznativa.toml` do projeto (procurado da pasta atual até a raiz do repositório) > arquivo do usuário (`%APPDATA%\voznativa\config.toml` no Windows, `~/.config/voznativa/config.toml` no Linux e macOS, ou o caminho em `VOZNATIVA_CONFIG`) > padrão. Uma tabela `[rewrite]`; chave desconhecida ou tipo errado é erro. Por segurança, `cmd`, `judge_cmd`, `provider_env` e `provider_env_allow` só valem no arquivo do usuário ou na linha de comando. O VozNativa nunca grava esses arquivos nem lê segredos deles: credenciais ficam no ambiente.

Próximo passo: [`QUICKSTART.md`](QUICKSTART.md).
