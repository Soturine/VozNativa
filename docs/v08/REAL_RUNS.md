# Execuções reais (CP9): cenários, consumo estimado e autorização

Nada aqui foi executado. Estado de todos os cenários: **NOT_RUN, aguardando autorização explícita do mantenedor** (ponto 4 dos adendos). Nenhuma chamada paga sem consentimento para aquela chamada específica.

## Pré-requisitos ausentes nesta máquina (2026-11-07)

- Nenhum CLI de agente no PATH do shell (`claude`, `codex`, `gemini`: não instalados).
- Nenhuma variável de provider definida (`voznativa doctor`).
- Logo, qualquer cenário abaixo precisa de: um CLI de agente instalado e autenticado pelo mantenedor, **ou** uma chave de API fornecida por ele no ambiente da sessão (nunca gravada no repositório).

## O que seria enviado

Somente textos autorais do próprio repositório (`ptbr-bench-v5`, `evals/events/`, `examples/quickstart/`), sem dado pessoal nem texto de corpus de terceiros. Os registros guardam hashes, não os textos (`voznativa/arms.py`, `evaluate`).

## Cenários e estimativa

Tokens estimados a partir dos prompts reais desta revisão (média do prompt da Skill: ~3.040 caracteres ≈ 870 tokens; prompt do juiz ≈ 850 tokens; razão de 3,5 caracteres por token para português, aproximada). Preço não é estimado aqui: depende do provedor e do plano (assinatura de CLI consome a cota do plano; API cobra por token).

| ID | Cenário | Casos | Chamadas | Entrada estimada | Saída estimada |
|---|---|---|---|---|---|
| R1 | Braços B1, B3 e B5 (instrução simples, prompt da Skill sem gates, ablação) | 36 (v5) | 108 | ~66 mil tokens | ~7 mil |
| R2 | Braço B4 (engine completo + juiz com 2 votos) | 36 (v5) | 108 a 180 | ~92 mil (típico) a ~155 mil (pior caso) | ~25 mil |
| R3 | Agent Skill operada por agente real (procedimento do `SKILL.md`, com ferramentas) | 10 (v5, estratificados) | 10 sessões | ~150 a 400 mil (incerto: depende do agente) | ~20 a 50 mil |
| R4 | Documentos longos (`documento-longo.md` e um de ~5 mil palavras) com juiz | 2 | ~20 a 30 | ~30 a 60 mil | ~10 mil |
| R5 | Falhas: provider indisponível, credencial ausente, orçamento esgotado, timeout | — | 0 (simulados localmente) | 0 | 0 |

Total se tudo for autorizado: até ~0,7 milhão de tokens de entrada e ~0,1 milhão de saída, dominado por R3. R5 não precisa de autorização (não chama provedor) e já é coberto por testes com stubs.

## Limites que cada execução respeita

- `--max-calls` / `Limits.max_provider_calls` por cenário igual ao teto da tabela; o engine para e marca `not_run` ao atingir.
- `timeout_s` por documento; `--provider-env minimal` com só a variável autorizada.
- Uma única execução por cenário e configuração; nenhum run escolhido entre vários.
- Juiz do mesmo modelo que gerou é registrado como **autoavaliação dependente** (lacuna V08-GAP-16, a corrigir no CP12 antes de qualquer R2/R3).
- Resultado com provider real é `PROVIDER_EXECUTED` com modelo, versão, host e data; nunca "validação independente".

## Ordem recomendada

1. CP12 corrige V08-GAP-16 (rótulo de autoavaliação), para que R2 e R3 não registrem juízo do próprio agente como juízo independente.
2. R1 (mais barato, compara com e sem os gates).
3. R2 e R4.
4. R3 por último, com 3 casos primeiro para medir o consumo real antes dos outros 7.
