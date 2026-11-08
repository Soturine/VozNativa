# Benchmark externo de detectores de IA (v0.7.0, CP11)

> **Estado: histórico (execução da v0.7).** Registro daquela rodada, não reescrito; a rodada atual está em [v08/EXECUTION_STATE.md](v08/EXECUTION_STATE.md).

**Objetivo:** medir como serviços externos classificam textos de origem conhecida antes e depois de uma revisão do VozNativa. **Não** é objetivo reduzir scores, calibrar o engine contra detectores nem afirmar autoria humana. O engine nunca recebe um score de detector; nenhuma iteração é feita contra um classificador.

Distinções mantidas em todo o código e nos relatórios:

- score de detector = classificação falível de um fornecedor, não prova de autoria;
- um score baixo depois da revisão não é evidência de autoria humana;
- marca d'água estatística, caracteres invisíveis e credenciais de proveniência são coisas diferentes (CP12).

## Infraestrutura (`evals/external_detection/`, `scripts/detector_bench.py`)

Ferramenta opt-in, fora do pacote `voznativa` e fora do fluxo `rewrite`.

| Adapter | Contrato (lido em 2026-11-06) | Estado |
|---|---|---|
| Copyleaks writer-detector | **verificado**: `POST https://api.copyleaks.com/v2/writer-detector/{scanId}/check`, `Authorization: Bearer`, `text` 255–100.000 caracteres, `sandbox`, `language`, `sensitivity`; resposta `summary{human,ai}`, `results[].classification/probability`, `modelVersion`; português listado (`pt`). A documentação **não diz** se `summary` é probabilidade ou contagem → nenhum rótulo é derivado | implementado; live NOT_RUN (sem token) |
| GPTZero | **parcial**: `POST /v2/predict/text`, `modelVersion` (lista em `GET /v2/model-versions/ai-scan`), probabilidades por documento/parágrafo/frase; cabeçalho de autenticação e nomes de campos não estavam na página lida | implementado com resposta guardada crua e `INCONCLUSIVE`; live NOT_RUN |
| Originality.ai | **não verificado**: a página lida não trouxe endpoint nem campos | `UNSUPPORTED` |
| Mock / Replay | rotulados `kind=mock` / `kind=replay`; nunca somados a live | para testes de contrato |

Cada medição é tipada (`Measurement`): `call_status` (PASS/FAIL só da chamada técnica) separado de `evidence_status` (MEASURED, NOT_RUN, BLOCKED, UNSUPPORTED, INCONCLUSIVE); `score_semantics` documenta o que o número significa; `kind` diz a proveniência.

## Protocolo H0/H1/A0/A1 (`protocol.py`)

H0 humano original (autoria verificável ou consentida) · H1 o mesmo revisado pelo VozNativa · A0 gerado por modelo com versão e parâmetros conhecidos · A1 o mesmo revisado. Métricas separadas por detector e por proveniência: falso positivo em H0 e H1, sensibilidade em A0 e A1, trocas de rótulo pareadas, estados não medidos. Grupo vazio = `NOT_RUN`, nunca zero.

Envio externo exige **as duas** autorizações: `--allow-upload` na execução e `upload_permission: true` no item. Texto de corpus é recusado sem checagem de política por operação (`SEND_TO_EXTERNAL_MODEL`; para as fontes com `text_rights: unclear` a resposta é UNKNOWN).

## Estado

| Item | Estado |
|---|---|
| Infraestrutura e testes de contrato (9) | PASS (mocks e replays rotulados) |
| Execução live | **LIVE_NOT_RUN** (`evals/external_detection/runs/baseline_vs_after-2026-11-06.json`): sem chaves, sem autorização de upload, manifesto vazio |
| H0 | NOT_RUN: o repositório não tem texto humano com autoria verificável e permissão de envio |
| A0 | NOT_RUN: nenhum texto com modelo, versão e parâmetros registrados |
| Custo | US$ 0 (nenhuma chamada paga) |

## Para executar de verdade (decisão humana)

1. Reunir H0 com consentimento e direito de envio a terceiros; registrar `authorship_evidence`.
2. Gerar A0 com modelo, versão e parâmetros registrados.
3. Produzir H1/A1 com `voznativa rewrite`, guardando os hashes.
4. Exportar `COPYLEAKS_TOKEN`/`GPTZERO_API_KEY`, revisar a política de retenção do fornecedor e rodar `python scripts/detector_bench.py --allow-upload`.
5. Relatórios guardam estados e scores, nunca o texto nem o payload sensível em artefatos públicos.
