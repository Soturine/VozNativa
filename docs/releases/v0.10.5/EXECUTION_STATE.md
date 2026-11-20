# Estado de execução da v0.10.5

## Ponto de partida (CP0, conferido ao vivo)

| Item | Valor |
|---|---|
| VozNativa | `main` = `origin/main` = `e274379`; tag `v0.10.0` anotada (`7c8c141`); release Latest; CI #132 8/8 em `e612a43`; branch `dev/v0.10.5` |
| Derivanta Engine | PR #6 **aberto**; release v0.1.0 Latest |
| Assertiva | PR #11 **aberto**; release v1.0.1 Latest |
| Derivanta Framework | `Soturine/Derivanta`, release v0.1.0 Latest |
| Baseline | `qualify --scope release --offline` na worktree de `v0.10.0`: todos os gates locais PASS (INCOMPLETE só pelos externos) |
| Disco | 98% ocupado (13 GB livres); temporários da rodada v0.10 apagados com autorização do mantenedor |

## Checkpoints

| CP | Estado | Commit | Evidência |
|---|---|---|---|
| CP0 + CP1 | concluído | `69e1313` | plano e R1–R18 congelados; corpus real de 427 itens com direitos por operação; 18 tarefas live congeladas; piloto de host real (Skill ativada sem ser nomeada) |
| CP0 (gate de privacidade) | concluído | `441bf79` | V105-GAP-03/04; anotação de tipo não é credencial |
| CP2 + CP3 | concluído | `167c855`, `3ee45c5`, `1082b07`, `05f4ab7`, `8f5ffc1` | campanha offline; falsos verdes de negação e frase apagada; modo explícito; descoberta da Skill; juiz declarado; dígitos colados; ciclos travados; documento longo segmentado |
| CP4 (braços live) | concluído com retrabalho | — | **18/11 19:14**: a conta atingiu o limite de 5 h no meio da campanha do candidato; 83 execuções (T05–T12) foram gravadas como resultado e a retomada as pulava (V105-HARNESS-02). **19/11**: harness corrigido, campanha arquivada fora do repositório e refeita do zero em `8f5ffc1`: 144/144, nenhuma falha de provider |
| CP12a (Observatory) | concluído com retrabalho | `3bedfe5` | a primeira página tinha seções vazias e o QA a aprovava; refeita e QA reescrito (V105-HARNESS-05). **Push**: o remoto estava em `167c855`, então esse push levou 5 commits; o gate de privacidade foi rodado no intervalo inteiro **depois** do envio: PASS (5 commits, 12.109 linhas) |
| CP5 (documentos) | concluído com retrabalho | — | os fluxos de 18/11 19:15 também bateram na cota; replay de 19/11 falhou por caminho relativo no harness (V105-HARNESS-04); terceiro replay completo, sem falha de provider |
| CP6–CP7 (juiz, holdout, correções) | concluído | (este commit) | juiz cego 36/36 (US$ 1,04); holdout congelado rodado uma vez; V105-GAP-15 (lei) corrigido com replay em 144 reescritas; GAP-16/17/18 abertos |
| CP8–CP10 (dogfood recíproco) | concluído | Assertiva `5f18982` (PR #11), Engine `a9eb371` (PR #6) | ver `ASSURANCE_RECIPROCAL.md` |
| CP11 (antes/depois) | concluído | (este commit) | campanha offline **refeita no código final**: a de 18/11 18:56 era de antes de GAP-13/14/15; desempenho remedido intercalado pelo mesmo motivo |
| CP12b (QA do site) | concluído | `95522c9` | QA no Edge 55/55; capturas reais em `docs/observatory/screenshots/` |
| CP13 (qualificação e entrega) | **BLOCKED** na integração | `95522c9` + este commit | `qualify` local: todos os gates locais PASS; gate de privacidade do intervalo PASS e da árvore revisado; PR #4 aberto. O merge do PR #6 (Engine) foi negado pelo controle de permissões do agente; pela regra da rodada, nenhum merge foi tentado por outro caminho. Sem merge: sem CI final na `main`, sem tag, sem release. Assertiva PR #11 `4325936` com CI verde, aberto |
| CP13 (falha de processo) | corrigido | `993be12` → este commit | o push de `993be12` saiu com o gate de privacidade em `FINDINGS`: o comando encadeava gate e push sem condicionar um ao outro. Os achados eram dois exemplos de nome de variável que o próprio texto do R14 citava (nenhuma credencial, nenhum dado privado). Texto reescrito sem os padrões; a partir daqui o push só roda se o gate devolver 0 |
| Continuação (19/11) | concluída localmente | `69b81d8` + este commit | D-03 (juízo em arquivo não aprova), `SKILL.md` revisada a partir das causas medidas, harness com resultado e negação de ferramenta, holdout prospectivo congelado antes de medir e rodado (180 execuções, juiz 20/20), ablação válida, GAP-21 (Framework), Assertiva com artefato PASS, Engine na mesma pasta, PR Soturine/Derivanta#13. Planalto bloqueou o acesso (nenhuma lei nova; não contornado). Custo da continuação US$ 1,74; rodada US$ 5,01. Integração continua bloqueada: nenhum merge feito pelo agente |
| Fechamento 1 (20/11) | publicado na branch | `201b653` | GAP-22 e atribuição do juiz, controles, indexação do planejador e inventário, remoção de código sem uso. Gate de privacidade antes do push |
| Fechamento 2 (20/11) | publicado na branch | `016637e` | relatório por execução da Skill, CLI, empacotamento, entrada única, termos protegidos no PROOFREAD e orçamento de chamadas. Qualificação local e gate de privacidade antes do push |
| Fechamento 3 (20/11) | auditoria e Observatory | veja histórico da branch | QA no Edge, replay offline e prospectivo, registro das medições e pendências. Integração da `main`, CI final e release seguem pendentes |
