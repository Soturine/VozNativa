# Estado de partida (AS-IS) — `v0.9.0`, `6b487f7`

> Inventário do CP0: o que existe, como se conecta e onde a v0.10 entra. Fonte: o código da tag, não documentos anteriores.

## Pacote e dependências

- `voznativa` (Python ≥ 3.11), 53 módulos + `voznativa/corpus` (11), ~15.900 linhas. Dependência obrigatória: `PyYAML`. Opcional: `pypdf` (extra `pdf`). Camada semântica só com biblioteca padrão.
- CLI `voznativa` com 36 subcomandos (`doctor`, `config`, `demo`, `route`, `plan`, `diagnose`, `compare`, `judge-prompt`, `rewrite-prompt`, `rewrite`, `docx`, `pdf`, `packs`, `standards`, `rubric`, `evaluate`, `corpus`, …).
- Hosts: `SKILL.md` (Agent Skill), `.claude-plugin/plugin.json`.

## Fluxo de reescrita

```
texto ─ router.route ─► contrato de contexto v3 (dimensões com source/confidence/evidence)
      ─ patterns.detect + community ─► achados editoriais
      ─ planner.plan (diagnose._grammar, ledger) ─► operações por frase (keep … paragraph_rewrite)
      ─ references.select (orçamento de palavras) ─► referências no prompt
      ─ provider.generate (comando, Emulate, chat-completions HTTP) ─► candidatas
      ─ compare (ledger, spans, eventos, classes, qualificadores) ─► status: identical / no_deterministic_issues / review_required / fail
      ─ juiz (_judge_votes; relação same_agent/different_model/unknown) ─► accepted_by_llm / needs_judgment / …
      ─ longform (unidades, EditorialMemory, orçamento de chamadas) para documentos
```

## Onde cada exigência da v0.10 encontra código existente

| Exigência | Ponto de entrada existente | Lacuna |
|---|---|---|
| TaskContext aberto | `router.route` (contrato v3, `DIMENSIONS`, `_dim` com proveniência) | dimensões fixas; nada para atributos novos, multigênero, conflitos |
| Conhecimento contextual | `references.py` (manifesto YAML, orçamento), `standards.py`, packs, `data/*.json` | sem registro único com licença/data/confiança; seleção por gênero, não por necessidade |
| Status de diagnóstico | `diagnose.CLASSES` (`formal_error`, `possible_contextual_error`, `literary_license`, …) | sem status de variante legítima nem estado único consumível |
| Relações discursivas | `markers_pt_br.json` (causalidade, condição); `compare._causal_direction_issues` | sem contraste, concessão, consequência, finalidade; sem relação implícita |
| Relação do juiz | `engine._generator_relation`, `compare.apply_judgment` | `unknown` aceita (V010-GAP-01) |
| Watcher | `corpus/connectors.py` (conectores HTTP do Corpus Registry) | sem monitoramento, cache condicional, propostas |
| Avaliação | `evaluation.py`, `scripts/qualify.py`, conjuntos congelados v0.7–v0.9 | conjuntos v0.10 congelados no CP0 (`evals/v010`) |

## Repositórios irmãos (dogfood recíproco)

| Repositório | Local | Remoto | Observação |
|---|---|---|---|
| Assertiva | `main` `2618d95` (v0.10.1), 51 commits atrás | `origin/main` `b615b13`, tag `v1.0.1` | usar clone isolado do remoto; checkout local não é tocado |
| Derivanta-Engine | `feat/ci-workflow-checks` `63fd03d` | `origin/main` `37ba01a` (merge do PR #4), tag `v0.1.0` | idem |
| Derivanta (framework) | `feat/approval-consumption-and-required-artifacts` | — | fora do escopo (não é o motor de inspeção) |

Worktree de outra ferramenta (`kilo/.../deeply-pepper`, `8cf27c8`): não é tocada.

## Ferramentas da máquina

Windows 10, CPython 3.12.6 (e 3.11 via `py -3.11`), `gh`, `claude`, Docker instalado (sem resposta na v0.9). Ausentes: `ollama`, `lms`, `llama-server` no PATH, `codex`, `gemini`.
