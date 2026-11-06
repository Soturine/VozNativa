# Dogfood cruzado da v0.7.0 — VozNativa ↔ Assertiva ↔ Derivanta Engine/Framework

Saída de ferramenta é hipótese. Classificação: `CONFIRMED`, `FALSE_POSITIVE`, `INCONCLUSIVE`, `ACCEPTED_RISK`, `DUPLICATE`, `UPSTREAM_GAP`. O mesmo agente construiu, rodou e julgou: autoavaliação com evidência de ferramenta, não qualificação independente. Histórico da v0.5/v0.6: `evals/assurance/DOGFOOD.md`.

## Instrumentos

| Ferramenta | Versão / revisão | Instalação |
|---|---|---|
| Assertiva | 0.10.1, `2618d95` (= `origin/main` em 2026-11-06) | venv próprio, wheel da tag `v0.10.1` |
| Derivanta Engine | 0.1.0, `17fa564` (= `origin/main`) | venv próprio |
| Derivanta Framework | `218761d` (= `origin/main`) | leitura |

## Execuções

| Run | CP | Revisão VozNativa | Comando | Exit | Resultado |
|---|---|---|---|---|---|
| `2026-11-06-v07-cp0` | CP0 | `bf8e1a4` | `derivanta-engine inspect . --maintainability --format json` | 0 | 97 candidatos INFO: 65 `HIGH_COMPLEXITY`, 30 `DUPLICATE_TABLE`, 2 `UNREFERENCED_DEFINITION` (mesmo conjunto do fim da v0.6) |
| `2026-11-06-v07-cp0` | CP0 | `bf8e1a4` | `assertiva audit . --output json` (estático) | 0 | 1 achado `UNCLASSIFIED_VERIFICATION` (info) |

## Achados

| ID | Ferramenta | Achado | Classificação | Correção local | Upstream | Estado |
|---|---|---|---|---|---|---|

## Encaminhamento upstream

| Destino | PR | Estado em 2026-11-06 |
|---|---|---|
| Assertiva | #8 (`docs/voznativa-v05-dogfood-intake-20261105`, `3d55391`) | aberta; nada corrigido |
| Derivanta Engine | #3 (`docs/voznativa-v05-dogfood-intake-20261105`, `d38214d`) | aberta; nada corrigido |
