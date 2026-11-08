# Independência e vazamento entre conjuntos (v0.8, CP5)

Responde a V08-GAP-08 e aos pontos de auditoria 1 e 2 do mantenedor (2026-11-07). Ferramentas: `voznativa evaluate` (`--verify`, `--replay`) e `scripts/experiments/v08_leakage_audit.py`.

## 1. O que um registro de avaliação prova

| Verificação | Prova | Não prova |
|---|---|---|
| `--verify` | o registro é coerente por dentro: `results_sha256` bate com os resultados e as métricas decorrem deles | autenticidade. O resumo não é assinatura: quem edita os resultados recalcula o resumo e as métricas, e `--verify` passa. O teste `test_a_forger_passes_verify_but_not_replay` mostra exatamente isso |
| `--replay` | os resultados registrados saem do código e das entradas da revisão gravada: `git archive` da revisão, entradas conferidas pelo sha256, nova execução num subprocesso, mesmo resumo | quem executou o original, em que máquina, ou que o conjunto é independente; reprodução vale para esta máquina e versão de Python |
| `independence_evidence` | o commit que congelou o arquivo existe e contém o arquivo com o sha256 do MANIFEST; o arquivo de atestado existe dentro do repositório; o autor declarado não é o desenvolvedor | quem são as pessoas, a custódia real, o consentimento. Essas partes ficam `DECLARED` no registro |

Registro sem árvore limpa ou sem a especificação embutida é `NOT_REPLAYABLE`, nunca reproduzido. O primeiro run da v0.8 (`evals/v08/runs/gate-and-planner-047276d.json`) é anterior a esta mudança e não traz a especificação: é `NOT_REPLAYABLE`, e fica assim.

## 2. Independência exige evidência

Antes, `independent: true` no MANIFEST bastava para um split independente. Agora o run é `INVALID` sem um bloco `independence_evidence` com `prepared_by`, `custodian`, `frozen_commit` e `attestation`, e o que dá para checar é checado (seção 1). Isso impede que uma bandeira solta vire alegação; não transforma um conjunto em independente. Nenhum conjunto do repositório tem esse bloco hoje: **não existe holdout independente** na v0.8 até haver pessoas reais.

Caminhos: além de recusar `..` e caminho absoluto, o caminho resolvido (link simbólico ou junção) precisa ficar dentro da raiz. Testado com junção no Windows (`mklink /J`, sem privilégio); o teste com link simbólico pula neste Windows por falta de privilégio e roda no Linux.

## 3. Vazamento encontrado nos conjuntos do repositório

Auditoria em 471 textos de 27 arquivos (suítes semânticas, de relações, predicados, decisão, roteador, gíria, todos os benchmarks e o quickstart). Igualdade depois de dobrar caixa, acentos, pontuação e espaços; quase-duplicata por trigramas de palavras com Jaccard ≥ 0,8 (textos de 6+ palavras).

| Ligação | Tipo | Consequência |
|---|---|---|
| `relations:rel-agent-001` = `holdout:ho-022` | **mesmo caso** (original e candidata iguais) | o holdout de desenvolvedor `holdout.jsonl` tem um caso que já estava no conjunto de desenvolvimento usado para construir os detectores de papéis. O resultado desse caso nunca mediu generalização |
| `relations:rel-agent-003` ~ `holdout:ho-022` | mesmo original, candidata diferente (passiva legítima) | variação do mesmo texto; menos grave |
| `slang/cases-v07:sl7-16` = `ptbr-bench-v5:bv5-sl-4` | mesmo texto | o `ptbr-bench-v5` foi congelado como **fora de distribuição** em `36dd20c`, mas este texto entrou antes (`2e88a46`) num conjunto de desenvolvimento da correção de gíria. 1 dos 36 casos do v5 não é fora de distribuição |
| `ptbr-bench-v5:bv5-nc-email` = `quickstart:email` | mesmo texto | o exemplo do README (`7d2382b`) foi tirado do benchmark; não muda número de benchmark, mas o quickstart não é caso novo |
| `cases` × `relations` (8 ligações, 3 casos idênticos) | dentro de `development` | duplicação sem efeito em alegação |

Os arquivos congelados ficam como estão (são registros). As alegações mudam: o README passa a dizer que 1 caso do v5 vem de um conjunto de desenvolvimento, e o `ho-022` fica anotado aqui. Os cinco benchmarks congelados (v1–v5) continuam byte-idênticos aos seus manifestos.

## 4. Como um conjunto novo deve entrar

1. Escrever e congelar (sha256 no MANIFEST, commit próprio) **antes** de qualquer código que ele vá medir.
2. Rodar `v08_leakage_audit.py`: nenhuma ligação com conjuntos já usados para ajuste.
3. Para alegar independência: `independence_evidence` com autor e custódia reais e atestado versionado.
4. Primeiro run registrado com árvore limpa; `--replay` desse registro antes de citá-lo.
