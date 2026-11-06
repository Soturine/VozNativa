# Amostra de predicados (v0.7.0.dev1)

`cases-h07.jsonl` reúne 20 pares em que a candidata perde ou troca a ação, o compromisso, o destinatário, a condição, o quantificador ou a atribuição (`risk`), e 18 paráfrases legítimas (`clean`): sinônimo de verbo, passiva com agente, nominalização, perífrase de futuro, elipse e inversão literária. O sha256 foi congelado em `MANIFEST.json` antes de existir qualquer código da regra, e `scripts/predicate_eval.py` recusa rodar se o arquivo mudar.

**Não é holdout independente.** Quem escreveu a amostra escreveu a regra, e os números abaixo medem regressão nesta amostra. Não estimam desempenho em reescritas reais.

| Medição | Revisão | Riscos sinalizados | Falsos alarmes | Arquivo |
|---|---|---|---|---|
| antes da regra | `e7506f5` (código) | 7/20 | 4/18 | `runs/predicates-2026-11-06-before.json` |
| 1ª versão da regra (âncora exige tempo único) | árvore de trabalho do CP3 | 14/20 | 1/18 | registrada só aqui |
| regra do CP3 (âncora exige radical único e terminação forte) | commit do CP3 | 16/20 | 1/18 | `runs/predicates-2026-11-06-after.json` |

Da 1ª versão para a do CP3, os dois ajustes foram feitos olhando esta amostra, e os 2 casos ganhos (`pr-06`, `pr-15`) já não são prospectivos.

- **Tempo verbal ambíguo:** "cancelaram" pode ser perfeito ou mais-que-perfeito. Essa ambiguidade não diz nada sobre ser verbo, então deixou de impedir a âncora.
- **Terminação fraca aceita pelo contexto:** fazia "durante" virar "durantar". Deixou de valer como âncora, e com isso a regra produz menos alarmes.

O que continua sem sinal:

- `pr-09` ("assinou" → "recebeu") e `pr-10` ("aprovou" → "avaliou"): outro verbo pleno vira `predicate_replaced` (info). Distinguir sinônimo de evento diferente exige recurso lexical (backlog v0.8).
- `pr-13` ("pagará" → "é em março"): o radical `pag` tem menos de 4 letras e a regra se abstém.
- `pr-17` (destinatário omitido): fora do escopo da regra.

O falso alarme que resta (`pc-09`, "durante" → "no") vem de `condition.temporal`, não da regra nova, e é risco aceito (VN07-DISC-042).

Os dois falsos alarmes de futuro da linha de base (`pc-03`, `pc-08`, `pc-11` com `tense_changed`) motivaram a equivalência entre futuro perifrástico e sintético. Por isso esses 3 controles também deixaram de ser prospectivos.

Suítes congeladas depois da regra, ainda na árvore de trabalho: semântica dev e holdouts PASS, regressões de decisão e roteador PASS, `ptbr-bench-v4` 22/22, `ptbr-bench-v5` 36/36. Os registros por revisão saem no CP6.
