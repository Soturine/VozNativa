# Retriagem dos 12 mutantes `==`/`!=` → `is`/`is not` de `temporal.py` (v0.7.0.dev1, CP1)

A rodada 2 da v0.7 (`2026-11-06-v07-cp14/MUTATION.md`) classificou estes 12 sobreviventes como "equivalentes no CPython" porque os operandos seriam literais internados. Esse argumento não vale quando o operando vem de YAML, de um grupo de regex ou de um argumento de linha de comando: o valor é igual, mas não é o mesmo objeto. Aqui cada mutante foi reaberto pela origem real do operando e aplicado à mão.

## Método

- **Revisão:** cópia `git archive` de `bc6f4fd`. `voznativa/temporal.py` é o mesmo de `7d2382b` (a rodada 2); `git diff 7d2382b bc6f4fd -- voznativa/temporal.py` vem vazio. As linhas e colunas são as que o Cosmic Ray gravou em `temporal.sqlite`.
- **Execução:** `identity_mutants.py` (neste diretório) aplica um mutante por vez, apaga todo `__pycache__` e roda `python -B -m unittest <suíte>`. Windows 11, CPython 3.12.10.
- **Suítes:** a mesma da rodada 2 (`identity-mutants-run2-suite.json`) e a mesma mais `evals.test_hardening_h07` (`identity-mutants-with-h07.json`).

## Dois achados de método

1. **Bytecode velho.** A 1ª execução deste harness gravava `.pyc`. Os mutantes das linhas 109 e 149 deixam o arquivo do mesmo tamanho e foram escritos no mesmo segundo, então o 149 rodou com o bytecode do 109 e apareceu como "morto" pelos testes do 109. Rodado sozinho, três vezes, ele sobrevive. Desde então o harness roda sem bytecode. O Cosmic Ray grava o módulo mutado em disco do mesmo jeito; a rerodada do CP5 usa `-B` no comando de teste para eliminar o risco (VN07-DISC-046).
2. **`group(0)` de casamento total.** O 1º oráculo da linha 235 usava o texto "blz" sozinho, e o mutante sobreviveu. Quando a regex casa a string inteira, o CPython devolve em `group(0)` o próprio objeto de entrada, e os dois lados da comparação passam a ser o mesmo objeto. O oráculo agora usa o termo dentro de uma frase ("ok, blz."), onde cada grupo é um objeto novo.

## Resultado

Com a suíte da rodada 2, os 12 sobrevivem. Com os oráculos novos, 5 morrem e 7 sobrevivem.

| Linha | Código | Origem do operando | Com os oráculos novos | Classificação |
|---|---|---|---|---|
| 91 | `amb.get("detection") == "context"` | YAML do léxico | **morto** por `test_context_detection_from_yaml_needs_a_detect_pattern` | era lacuna de teste; agora coberta |
| 109 | `deprecation.status != "active"` (validação) | YAML quando a entrada declara `deprecation`; literal de `_merge` quando não declara. O léxico versionado nunca declara, e por isso a rodada 2 não via a diferença. | **morto** por `test_status_active_from_yaml_is_active` | era lacuna de teste; agora coberta |
| 235 | `x != hit.group(0)` | dois grupos de regex | **morto** por `test_an_ambiguous_form_that_is_also_a_chat_cue_does_not_corroborate_itself` | era lacuna de teste; agora coberta |
| 262 | `spec == "current"` | argumento `--epoch` da CLI ou campo de contexto | **morto** por `test_epoch_current_from_outside_the_module` (YAML e `"".join`) | era lacuna de teste; agora coberta |
| 303 | `deprecation.status != "active"` (`entry_status`) | igual à 109 | **morto** por `test_status_active_from_yaml_is_active` | era lacuna de teste; agora coberta |
| 71 | `schema_version != SCHEMA_VERSION` | inteiro do YAML | sobrevive | equivalente para `int` no CPython (cache de inteiros pequenos, −5..256). Um `2.0` no YAML separaria o mutante, porque `2.0 == 2`; o CP2 passa a exigir `int`, e aí o mutante só difere fora do domínio válido. |
| 149 | `k != "entries"` em `_load` | chave do YAML | sobrevive | **equivalente pela linguagem**: a chave `"entries"` mantida pelo mutante é sobrescrita logo depois no mesmo literal de dict. Não depende do CPython. |
| 188 | `plain[end] == "-"` | indexação de string | sobrevive | equivalente no CPython: caracteres latin-1 de um só código vêm de um cache de singletons. Restrição declarada; outra implementação poderia diferir. |
| 226 | `sense == "slang"` | literais atribuídos na própria função | sobrevive | equivalente no CPython: constantes com forma de identificador são internadas na compilação. Nenhum valor externo chega aqui. |
| 229 | `infer_time_of_text(...)["value"] == "pre_reform_orthography"` | literal de `router.py` | sobrevive | idem: literal de outro módulo do pacote, internado na compilação |
| 243 | `f["sense"] != "other_sense"` | literais da própria função | sobrevive | idem |
| 249 | `f["sense"] == "slang"` em `observe_slang` | saída de `observe` (literais) | sobrevive | idem |

O `MUTATION.md` da rodada 2 listava 11 linhas para "12" mutantes; faltava a 188 (VN07-DISC-038).

## O que não se conclui

- Os 6 equivalentes "no CPython" (71, 188, 226, 229, 243 e 249) não são equivalentes pela linguagem. Valem para CPython 3.11–3.13 e para operandos que hoje só vêm de literais do pacote. Se algum desses valores passar a vir de dados, o mutante deixa de ser equivalente; o teste de contraste mostra como checar.
- Nenhum código de produção mudou: `==` já era o certo. Mudaram a triagem e os oráculos.
