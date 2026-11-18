# Knowledge Watcher (v0.10, CP8)

**O que é.** Um verificador de mudanças nas fontes de que o projeto depende (dependências, treebanks, artigos, documentos do Inep), que **propõe** e nunca aplica (decisão D-04). Módulo `voznativa/watcher.py`; fontes em `voznativa/data/watch_sources.yml`; HTTP pelo mesmo `fetch` do Corpus Registry (`voznativa/corpus/connectors.py`), agora com GET condicional e bloqueio de endereços privados.

## Uso

```bash
voznativa knowledge sources                    # fontes, host oficial, acesso, custo, o que uma mudança afetaria
voznativa knowledge check                      # report: consulta as fontes vencidas, não grava nada
voznativa knowledge check --mode propose       # grava snapshots e Change Proposals em VOZNATIVA_WATCH_DIR
voznativa knowledge check --only pypi-pypdf --force
voznativa knowledge status                     # offline: última verificação e idade de cada fonte
voznativa knowledge proposals                  # propostas guardadas (estado, diferença, o que afetam)
```

Diretório de estado: `VOZNATIVA_WATCH_DIR` (padrão `~/.voznativa/watch`), fora do repositório.

## Fontes da v0.10

| Fonte | Tipo | Acesso e custo | Afeta |
|---|---|---|---|
| `pypi-pyyaml`, `pypi-pypdf` | PyPI JSON | público, sem chave, 1 requisição | dependências |
| `ud-portuguese-gsd`, `ud-portuguese-bosque` | GitHub commits | API sem token (60/h por endereço) | Corpus Registry (commit fixado e hashes) |
| `crossref-ptbr-variation` | Crossref works | público, sem chave; `from-index-date`/`until-index-date` (orientação da Crossref) | lista de leitura do Research Register; nunca regra |
| `inep-enem-documents` | página | pública; sem licença de reuso declarada | Standards Registry (edição nova, errata) |
| `openalex-ptbr` | — | **desligada**: chave obrigatória e cobrança por uso desde 2026 | — |

## Ciclo de uma mudança

`DISCOVERED → SOURCE_VERIFIED → LICENSE_CHECKED → DIFFERENCE_ANALYZED → RELEVANCE_TRIAGED → CANDIDATE | NEEDS_HUMAN`. Os estados seguintes (`ISOLATED_EVAL`, `APPROVED`/`REJECTED`, `VERSIONED_ACTIVATION`) são de uma pessoa, num commit revisado e com os gates da release. Licença alterada e mudança de página institucional vão direto para `NEEDS_HUMAN`. Fonte que some (404/410) vira proposta `source_removed`. Novos trabalhos da Crossref viram **uma** proposta por verificação (lista de leitura), não uma por artigo.

Cada proposta registra: fonte, diferença, hash do resumo, verificação de licença, o que afeta, testes que provariam a mudança, "apply: never automatic" e rollback ("nada foi alterado pelo watcher").

## Segurança

- Só hosts declarados na fonte; cada redirecionamento é conferido; host que resolve para endereço privado, loopback, link-local ou não resolve é recusado **antes** da requisição (`private_address`).
- Resposta limitada a 2 MB e 20 s; resumo limitado a 4.000 caracteres; títulos sem caracteres de controle e truncados; todo conteúdo é marcado `untrusted_content` e nunca interpretado.
- 429: espera o `Retry-After` uma vez (no máximo 30 s); 5xx: uma nova tentativa; 403 e demais: erro registrado, sem insistência.
- `User-Agent` genérico do projeto; nenhum dado do mantenedor nas consultas (a Crossref sugere e-mail para o "polite pool": não enviado).
- Sem modo `apply`: o código recusa qualquer modo além de `report` e `propose`.

## Agendamento: `SCHEDULER_READY`, não "monitoramento ativo"

Nada foi agendado nesta máquina nem no GitHub (um workflow hospedado precisaria de consentimento de custo e não deve misturar-se à CI manual). Para ativar localmente:

```powershell
# Windows (Agendador de Tarefas), semanal
schtasks /Create /TN "VozNativa Knowledge Watcher" /SC WEEKLY /D MON /ST 09:00 /TR "cmd /c set VOZNATIVA_WATCH_DIR=%USERPROFILE%\.voznativa\watch && voznativa knowledge check --mode propose >> %USERPROFILE%\.voznativa\watch\log.jsonl"
```

```bash
# Linux/macOS (cron), segunda às 9h
0 9 * * 1 VOZNATIVA_WATCH_DIR=$HOME/.voznativa/watch voznativa knowledge check --mode propose >> $HOME/.voznativa/watch/log.jsonl
```

## Execução real (18/11/2026)

Registro: [`evals/v010/runs/watch-live-2026-11-18.json`](../../../evals/v010/runs/watch-live-2026-11-18.json). Primeira verificação: seis fontes ativas lidas (`first_snapshot`), OpenAlex `disabled`. Segunda, forçada: PyPI (2) e GitHub (2) responderam **304** ao GET condicional; a página do Inep ficou igual pelo hash; a Crossref trouxe trabalhos recém-indexados (o que motivou agregar a proposta). Achado útil já na primeira leitura: o `UD_Portuguese-GSD` tem commit novo (`58dccb5`, 10/11/2026) depois do commit fixado no registro (`c91edee`); os arquivos lidos no CP7 têm os mesmos hashes do registro, então o pin não mudou nada nesta rodada — uma pessoa decide se atualiza.

**Prova.** `evals/test_v010_watcher.py`: 19 testes (ciclo de snapshot e proposta, 304 com `If-None-Match`, licença alterada → `NEEDS_HUMAN`, modo report não grava, sem modo apply, vencimento e `--force`, 403 sem nova tentativa, 429 com espera limitada, 5xx duas vezes, fonte removida, resposta grande demais, endereço privado, JSON inválido, offline com envelhecimento, guarda de endereço privado antes da requisição, host fora da fonte, conteúdo hostil truncado e limpo, arquivo de fontes inválido, Crossref agregada, repositório intocado).

**Limites.** Detecta mudança; não avalia se a mudança é boa. Páginas institucionais por hash do texto visível podem gerar ruído. A busca da Crossref é por relevância, não exaustiva.
