# Inventário AS-IS no início da v0.6.0 (2026-11-05, `106fd50`)

Estados: IMPLEMENTED (código + testes executados), PARTIAL (código com lacuna documentada), BROKEN, UNCALIBRATED (funciona, mas limiares/listas sem dados reais), NOT_RUN, EXTERNAL_BLOCKED, NOT_APPLICABLE. A classificação vem do código, dos testes e das execuções registradas, não dos nomes dos arquivos.

## Baseline executada

- Windows 11, CPython 3.12.10, `scripts/qualify.py --scope release` em `3c5d284`: 348 testes PASS; validador, suítes dev/holdouts, decisão, router, exit codes e pacote PASS; `review:pty` NOT_RUN (POSIX); externos NOT_RUN.
- Conjuntos congelados: 9, todos com sha256 igual ao registrado (`evals/assurance/runs/2026-11-05-v06-cp0/frozen-sets.json`).
- Ferramentas: Derivanta Engine `17fa564` (66 candidatos INFO); Assertiva 0.10.1 (1 candidato contextual); Framework `218761d`. Assertiva PR #8 e Engine PR #3 abertos, nada corrigido lá.
- CI: verde em `40e19e4` (run #123, 8/8); #122 falhou na mesma revisão por teste instável (classe de defeito corrigida em `daca4bc`); bloqueio real por cobrança só em #100–#106. Desde `3c5d284`, só disparo manual.

## Componentes

| Componente | Estado | Base |
|---|---|---|
| Semantic Ledger + `compare` | IMPLEMENTED; PARTIAL em pronomes, trocas entre frases e inflexões | `evals/test_semantic_layer.py`, `evals/test_metamorphic.py`, H4 |
| Juiz LLM/humano, revisão assinada | IMPLEMENTED; revisão humana real NOT_RUN | `evals/test_review_assurance.py` |
| Pattern Library v2 (27 padrões) | IMPLEMENTED, **UNCALIBRATED** (listas e limiares do desenvolvedor; `dc-029`) | `evals/test_patterns.py` |
| Camada PT-BR (PT-PT, estrangeirismos, tratamento) | IMPLEMENTED, **UNCALIBRATED** | `evals/test_ptbr_layer.py` |
| Planejador | IMPLEMENTED; decisão 28/30 conhecida | `evals/decision/` |
| Router, Reference Selector | IMPLEMENTED | `evals/test_context_layer.py` |
| Voice Profile v2 + Voice Contract | IMPLEMENTED, UNCALIBRATED (drift) | `evals/test_voice_layer.py` |
| Rewrite Engine + providers | IMPLEMENTED; árvore de processos no Windows corrigida no CP0 | `evals/test_engine.py`, `evals/test_providers_hardening.py` |
| Regional Evidence Packs (`regional.py`) | IMPLEMENTED (piloto, um referente); avaliação humana NOT_RUN | `evals/test_regional.py` |
| Guard de exagero regional E0 (`region.py`) | IMPLEMENTED (heurística E0 de densidade; usada por `audit`, engine e bench v3) | testes foundation |
| Gírias temporais | **NOT_RUN / vazio**: `references/slang/schema.yml` (v2) é só um molde sem entradas; nenhum código lê o schema; `evals/slang/` só tem README | — |
| Community packs | **PARTIAL**: `references/communities/*.yml` com listas `preserve_if_natural` (draft, sem evidência) lidas pelo Voice Contract e pelo Voice Profile; sem ativação, guard ou proveniência | `contract.py`, `profile.py` |
| Corpus | **PARTIAL**: registro em prosa (`references/corpora/*.md`) + molde `source.schema.yml` não validado; piloto de metadados do Carolina (`scripts/carolina_metadata.py`, `evals/corpus/carolina-pilot.json`), sem código de registro, política, conectores nem processamento | — |
| Benchmark e eixos | IMPLEMENTED; `ptbr-bench-v3` congelado, NOT_RUN | `evals/test_benchmark_axes.py` |
| Textos longos / literatura | **PARTIAL**: drift por janelas e `long_text_drift` no engine; sem mapa de dependências globais, sem segmentação, sem política para poesia | `drift.py`, `engine.py` |
| Qualificação local | IMPLEMENTED | `scripts/qualify.py` |
| Licença do repositório | **NÃO DEFINIDA** até esta rodada (decisão do mantenedor: MIT) | — |
| Holdout independente, revisão humana cega | NOT_RUN (dependem de pessoas) | `evals/qualification/external.json` |

## Sobreposição `region.py` × `regional.py` × componentes planejados

- `region.py`: densidade e repetição de uma lista E0 de marcadores ("uai uai uai"); não sabe de evidência nem de pack.
- `regional.py`: contrato de pack de evidência, ativação, guards de referente e de forma não licenciada.
- Planejado: guard de inserção de gíria/termo de comunidade. A lógica de densidade é a mesma do `region.py`; consolidar a densidade num único detector, reutilizado pela região, pela época e pela comunidade, é ganho real (uma implementação em vez de três). `regional.py` continua dono da evidência regional; o novo módulo temporal/comunitário reutiliza o mesmo padrão de contrato, sem copiá-lo.

## Lacunas que a v0.6.0 enfrenta

1. Não existe registro de corpora executável nem política de dados por operação.
2. Nenhum corpus foi processado de ponta a ponta; padrões e camada PT-BR sem dados reais.
3. O schema de gíria não tem consumidor; packs de comunidade não têm evidência nem guard.
4. Textos longos e literatura sem tratamento próprio.
5. Licença ausente.
