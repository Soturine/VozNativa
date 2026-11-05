# Protocolo de revisão humana cega — v0.5.0 (estado: NOT_RUN)

Instrumento pronto; nenhuma rodada feita. Nenhum resultado humano pode ser citado até existir uma rodada com respostas assinadas e registradas aqui.

## Perguntas

Para cada par cego (A/B em ordem aleatória, mesmo texto de origem):

1. **Sentido**: o texto B diz o mesmo que A? (sim / mudou algo / não sei) — e o quê, se mudou.
2. **Canal**: qual dos dois soa mais adequado ao canal indicado (WhatsApp, e-mail, LinkedIn, documentação)? (A / B / igual)
3. **Preferência**: qual você mandaria? (A / B / nenhum)
4. **Regional** (só pares marcados como regionais e só para revisores da região): as palavras regionais soam naturais, forçadas ou caricatas? A troca mudou do que se fala (ex.: mandioca de mesa x mandioca brava)?

Os eixos ficam separados no resultado: sentido não é preferência, e preferência não é regionalidade.

## Material

- Pares de uma execução **oficial** do `ptbr-bench-v3` (`voznativa blind-tasks benchmarks/runs/<execução>.json --out tarefas.json`). Sem execução oficial, não há material: a rodada continua NOT_RUN.
- Textos de casos escritos para o benchmark; nenhum texto pessoal ou privado.

## Revisores

- Independentes: não escreveram nem leram o código, as regras ou os casos (declaração no `registry.json`, `relationship: independent`).
- Assinatura com a chave SSH do próprio revisor (`--ssh-key`, `allowed_signers`); revisão com a chave HMAC local nunca conta como independente.
- Itens regionais do Norte: só revisores que declarem viver ou ter vivido na Região Norte; a declaração é registrada como declarada, nunca como comprovada.
- Piso sugerido: 5 revisores gerais e 3 regionais; o mantenedor decide N antes da rodada e registra aqui antes de abrir os pacotes.

## Análise pré-registrada

- Uma resposta válida por tarefa e chave (`voznativa blind-summary`); respostas com hash ou mapeamento adulterado são descartadas e contadas.
- Por braço: proporção de "mudou algo" com intervalo de Wilson 95%; preferência por par com contagem simples. Sem agregar em nota única.
- Itens regionais relatados à parte, com o número de revisores regionais.

## Estado

| Item | Estado |
|---|---|
| Instrumento (`blind-tasks`, `blind-review`, `blind-summary`) | pronto, testado (`evals/test_review_assurance.py`, `evals/test_blind_review.py`) |
| Execução oficial do `ptbr-bench-v3` | NOT_RUN |
| Revisores registrados | nenhum (`registry.json` vazio) |
| Rodada | **NOT_RUN** |
