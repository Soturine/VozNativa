# Packs linguísticos: contrato e extensão

Um pack diz **que formas pertencem a um contexto** (uma comunidade de prática, uma região com evidência citada). Ele nunca acrescenta termo ao texto do autor, nunca muda o que os gates verificam e nunca executa código. Política de contribuição: [`../policy/CONTRIBUTING_LINGUISTIC_DATA.md`](../policy/CONTRIBUTING_LINGUISTIC_DATA.md).

## Tipos

| Tipo (`kind`) | Onde | Validador próprio | Pode vir de fora? |
|---|---|---|---|
| `voznativa.community_pack` | `voznativa/data/community_packs/` | `community.validate_pack` | sim, por `VOZNATIVA_PACKS_DIR` |
| `voznativa.regional_evidence_pack` | `voznativa/data/regional_packs/` | `regional.validate_pack` | não nesta versão (exige revisão de fonte; contribua por PR) |

## Envelope comum (v1)

Todo pack passa pelo envelope (`voznativa/packs.py`) e depois pelo validador do tipo.

| Regra | Por quê |
|---|---|
| `id` com 2–64 letras minúsculas, dígitos ou hífen, igual ao nome do arquivo | um pack não se passa por outro |
| `kind` conhecido, `schema_version` inteiro | nada de tipos inventados |
| arquivo até 512 KiB, YAML lido com `safe_load` (sem tags `!!python`) | dado não vira objeto nem código |
| texto até 2.000 caracteres; expressão regular até 300 e compilável | sem payloads nem expressões quebradas |
| campo de caminho (`*_path`, `*_file`, `*_dir`) sem caminho absoluto nem `..` | nada fora do pack |
| chaves recusadas em qualquer nível: `severity`, `guards`, `gate`, `compare`, `protect`, `unprotect`, `override`, `exec`, `eval`, `code`, `python`, `module`, `import`, `callable`, `script`, `hook`, `command` | **um pack não relaxa o Semantic Ledger, o `compare` nem guard nenhum** |
| `license` (SPDX ou `proprietary-facts-only`; no regional, `license.spdx`) e `provenance` com `authors` e `created` | obrigatórios em pack externo; aviso em pack embutido antigo |

## Usar um pack externo

```bash
voznativa packs validate meu-pack.yml          # exit 1 se inválido, com cada erro
VOZNATIVA_PACKS_DIR=examples/packs voznativa packs list
VOZNATIVA_PACKS_DIR=examples/packs voznativa plan texto.txt --genre academic --community pesquisa-ux
```

Exemplo executável: [`examples/packs/pesquisa-ux.yml`](../../examples/packs/pesquisa-ux.yml). Com ele, "feedback" e "insights" deixam de ser sugeridos para troca num texto acadêmico **quando** a comunidade é pedida (`--community`); sem o pedido, nada muda. A pasta é lida quando um pack de comunidade é usado; um arquivo inválido recusa a pasta inteira (exit 64), nunca é pulado em silêncio. Um pack externo não pode ter o mesmo `id` de um embutido.

## O que um pack de comunidade faz

- `preserve`: o termo do autor fica; o achado de estrangeirismo sobre ele é retirado (`withdrawn_by`).
- `avoid_outside` / `never_add`: o termo não é acrescentado; se a reescrita o acrescentar, a revisão acusa.
- `generation.allowed` só com pack não-rascunho e evidência E2 ou maior; nenhum pack embutido permite geração hoje.
