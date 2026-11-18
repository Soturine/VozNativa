# Fontes, corpora e textos reais (v0.10, CP7)

## Matriz de elegibilidade por finalidade

Vale o mais restritivo entre a licença da anotação, a do texto e os termos de acesso. `—` = proibido; `?` = incerto (tratado como proibido até haver evidência); `ok` = permitido com atribuição quando a licença pede. Estados do Corpus Registry (`voznativa/data/corpora/`) entre parênteses.

| Fonte | Consulta | Análise local privada | Calibração de regras | Teste público (fixture) | Treino de modelo | Redistribuir | Publicar exemplo | Uso automatizado |
|---|---|---|---|---|---|---|---|---|
| UD Portuguese-GSD (`EVALUATION_INTEGRATED`) — anotação CC BY-SA 4.0; texto web sem licença declarada | ok | ok (métricas agregadas) | ok (padrões, sem cópia) | — (texto) | ? | — (texto) | — | ok (download do commit fixado) |
| UD Portuguese-Bosque — CC BY-SA 4.0; texto CETENFolha/CETEMPúblico | ok | ok | ok | — | ? | — | — | ok |
| UD Portuguese-Porttinari — anotação CC BY 4.0; notícias da Folha via Kaggle | ok | ? (termos do Kaggle não lidos) | ? | — | — | — | — | ? |
| Machado de Assis corpus (`EVALUATION_INTEGRATED`, CC0) | ok | ok | ok | ok | ok | ok | ok | ok |
| Common Voice PT (CC0) | ok | ok | ok | ok | ok | ok | ok | ok |
| B2W-Reviews01 (CC BY-NC-SA 4.0) | ok | ok | ok | — (NC e SA incompatíveis com MIT) | — (comercial) | — | — | ok |
| C-ORAL-BRASIL I (CC BY-NC-SA, relatado) | ok | ? | ? | — | — | — | — | ? |
| Corpus Carolina (licença **por documento**) | ok | só documentos com licença aberta verificada | idem | — | — | — | — | idem |
| ALiB, NURC, SP2010, PHPB, ALIP/Iboruna | ok (catálogo/consulta) | ? (sem licença declarada ou acesso por pedido) | — | — | — | — | — | — |
| Inep, cartilha de redação 2026 | ok | ok (leitura) | — (norma, não dado) | — | — | — | — | — |
| Gramáticas (Bechara, Castilho, Bagno, Koch) | citação | — | — | — | — | — | — | — |

Nenhum texto de corpus entrou no repositório nesta rodada. As fixtures novas são sentenças inventadas que reproduzem a **forma** dos casos achados.

## Corpus efetivamente lido: UD Portuguese-GSD (diagnóstico em texto editado real)

**Por quê.** As regras de diagnóstico tinham sido medidas só em frases escritas pelo próprio agente. Texto jornalístico e de blog publicado é majoritariamente escrita padrão: cada `ERROR_CONFIRMED` ali é um deslize real da fonte ou um falso alarme, o que mede **precisão** em texto que ninguém escreveu para o teste.

**Protocolo.** `scripts/corpus_false_alarms.py` lê o CoNLL-U fora do repositório (commit fixado `c91edee`, hashes iguais aos do registro), roda `diagnose` em cada sentença e grava só contagens e ids. A triagem foi feita pelo agente (`AGENT_OBSERVED`). O split `test` serviu para achar e corrigir (desenvolvimento); o split `dev` foi rodado **uma vez** com as regras corrigidas antes de ser lido (resultado retido), e depois serviu para uma segunda correção.

| Split (sentenças) | `v0.9.0` `ERROR_CONFIRMED` | v0.10 antes da correção | v0.10 final | Triagem final |
|---|---|---|---|---|
| test (1.200) — desenvolvimento | 11 | 11 (1 real, 10 falsos) | **1** | 1 deslize real |
| dev (1.204) — rodada única retida | 16 | **11 (6 reais, 5 falsos)** | 6 (depois de usá-lo para corrigir) | 6 deslizes reais |

**Defeito real achado (V010-GAP-15, P2).** A regra `plural_agreement` da v0.9 disparava quando o "determinante" era pronome sujeito ("Outras estão", "muitos acharam", "Todos conhecem"), clítico ("os ajudam"), antes de advérbio ("dos cerca de", "às quase", "as então") ou em composto com hífen separado. Como o planner transforma `ERROR_CONFIRMED` em edição pontual, cada falso alarme virava um pedido de "correção" ao modelo. Correção em `voznativa/diagnose.py` com controles: erros reais de concordância ("os resultado", "muitos homem", "esses viagem", "pelos bom resultados") continuam sinalizados. Teste: `evals/test_v010_plural_real_text.py` (3 defeitos vermelhos em `v0.9.0`, controle verde nas duas).

**Limites.** Mede precisão, não recall (o treebank não anota erros). Um gênero (notícia/blog). Triagem pelo mesmo agente que escreveu as regras. Registro: [`evals/v010/runs/corpus-gsd-diagnose-2026-11-18.json`](../../../evals/v010/runs/corpus-gsd-diagnose-2026-11-18.json).

## ENEM como perfil, não como padrão

- A cartilha do Enem 2026 já está no Standards Registry (`inep-enem-redacao-cartilha-2026`), com edição e vigência.
- A rubrica só se aplica com `--document-profile` que a torne `APPLICABLE` (série, edição, data). Um atributo `genre=redação do enem` apenas a **oferece** como candidata (`task_context.rubric.candidates`); WhatsApp, poema ou artigo nunca a recebem (testes do CP2).
- A entrada de conhecimento `kn-enem-competencias` exige a rubrica aplicada (teste do CP3).
- Nenhuma nota é produzida, nem "nota 1000" é tratada como gabarito frase a frase. Redações-exemplo da cartilha não foram copiadas para fixture (licença do documento não declarada).

**Não executado.** Campanha com redações reais e comentários oficiais (exige uso permitido das redações-exemplo e revisores); textos autênticos de WhatsApp com consentimento (não há); revisão regional humana.
