# CP7 — atestação temporal do léxico de gírias (2026-11-05)

Execução: `scripts/slang_attest.py`. Ela gera `evals/corpus/runs/slang-attestation-2026-11-05.json` (só contagens) e `voznativa/data/slang/attestations.yml`.

Corpora usados, divisão `calibration`:
- Bosque CF: jornalismo da Folha, 1994–95, 33.792 palavras;
- B2W-Reviews01: prefixo de 8 MB com avaliações de produtos de 2018, 233.803 palavras.

Os períodos vêm do Corpus Registry.

## Resultado

O léxico tem 30 entradas, todas hipóteses do desenvolvedor (E0). A regra para subir a E2 exige duas condições: pelo menos 3 ocorrências numa fonte com proveniência, e uma forma sem ambiguidade ou detectada por contexto.

| entrada | Bosque 1994–95 | B2W 2018 | nível |
|---|---|---|---|
| `show de bola` | 0 | 18 | E2 |
| `top` (contexto) | 0 | 19 | E2 |
| `kkk` | 0 | 21 | E2 |
| `de boa` (contexto) | 0 | 3 | E2 |
| 26 outras | 0–1 | 0–1 | E0 |

- Nenhuma entrada aparece no jornalismo de 1994–95. A diferença é de **gênero e época ao mesmo tempo** (jornal x avaliação de usuário), e os dados não separam as duas causas.
- **Nenhuma entrada tem atestação posterior a 2018.** Para a época `current` (2024–2026), a atestação não existe, e a geração de gírias continua desligada em todas as entradas (`generation.allowed: false`). A força efetiva de gíria continua 0, agora com razões por entrada.

## Conferência de sentido (agente, não humana)

Detalhe em `evals/corpus/runs/slang-sensecheck-2026-11-05.json`. Quem leu as ocorrências localmente fui eu, o agente; nenhum texto foi exportado. **Isto não é avaliação humana.**

| entrada / padrão | divisão | ocorrências | sentido gíria | separada? |
|---|---|---|---|---|
| `show de bola` | calibration / evaluation | 18 / 5 | 18 / 5 | sim |
| `top` (inicial) | calibration / evaluation | 19 / 18 | 19 / 17 ("top de linha") | sim |
| `kkk` | evaluation | 26 | 26 | sim |
| `de boa` (inicial) | calibration / evaluation | 14 / 16 | 4 / 9 | sim |
| `de boa` (revisão 1, cópula) | evaluation | 26 | 8 ("é de boa qualidade") | sim |
| `de boa` (final) | calibration / evaluation | 3 / 9 | 3 / 9 | **não**: escrito depois de ler a avaliação |
| `mano` | calibration | 4 | 1 ("mano-a-mano", nome próprio) | — |

Padrões com precisão separada, medida antes de qualquer ajuste:
- `show de bola`: 5/5;
- `kkk`: 26/26;
- `top`: 17/18.

A exclusão de "top de linha" e o padrão final de `de boa` foram escritos depois de ler a divisão de avaliação. Por isso a precisão desses dois padrões **não tem medida separada**. Uma nova medição separada precisa de outra amostra.

## O que isto prova e o que não prova

- **Prova (E2, ferramenta):** as quatro formas aparecem em avaliações de produtos de 2018 e não aparecem no jornalismo de 1994–95, considerando estes recortes.
- **Não prova:**
  - uso atual;
  - região;
  - comunidade;
  - adequação a outro gênero;
  - que as outras 26 formas não existam. Ausência em dois corpora não é ausência na língua.
- **Comportamento seguro decorrente:**
  - o VozNativa preserva as formas que o autor usou;
  - aponta quando uma forma não tem atestação na época pedida, como nota e não como correção;
  - acusa gíria introduzida pelo modelo sem licença (guarda de stuffing);
  - nunca acrescenta gíria nesta versão.
