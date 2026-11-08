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

`voznativa doctor` confere Python, PyYAML, as referências, os dados do pacote e o diretório temporário, e diz se variáveis de provider conhecidas estão definidas (nunca mostra o valor). Não usa rede nem lê textos. Saída 1 só quando algo não vai funcionar; cada problema vem com o que fazer.

Próximo passo: [`QUICKSTART.md`](QUICKSTART.md).
