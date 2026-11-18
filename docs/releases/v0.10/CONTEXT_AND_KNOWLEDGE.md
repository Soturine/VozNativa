# Contexto aberto e conhecimento linguístico (v0.10, CP2–CP3)

## TaskContext aberto (CP2)

**Problema (V010-GAP-11).** O contrato do router tem dimensões fixas. Um "roteiro de podcast", uma "legenda de vídeo", um tom "cordial", um propósito "convidar" ou um texto que é metade e-mail e metade post não tinham onde morar sem código novo.

**O que existe agora** (`voznativa/task_context.py`, decisão D-01):

- `--attr NOME=VALOR` (repetível, em `route`, `context`, `rewrite-prompt`, `rewrite`) e `--attrs-file` aceitam **qualquer atributo** com nome válido e valor curto (texto, número, booleano ou lista de até 8 itens). Vírgula faz lista: `--attr genre=e-mail,post`.
- Cada atributo carrega **proveniência** (`explicit`, `agent_proposed`, `inferred`, `genre_default`, …) e confiança. As dimensões do router entram como atributos `inferred`.
- **Campos de segurança são recusados** como atributo (`facts`, `protect`, `judge`, `policy`, `cmd`, `api_url`, …): vêm só das próprias opções. Recusa vai para `rejected`, sem exceção.
- **Proposta do agente**: `voznativa context TEXTO --interpret-prompt` gera o pedido para um agente propor atributos com evidência; a resposta entra com `--context-proposal`. Atributo sem evidência cai; proposta nunca vence o pedido do usuário; o conflito fica registrado.
- **Gênero aberto**: o nome livre vai para o escritor; o pipeline determinístico usa um gênero fechado como *prior* de baixa confiança (`alias_prior`), ou o perfil genérico (`not_mapped`), ou nenhum (`mixed`). Uma palavra nunca vira regra que edita texto.
- **Desconhecido, misto, conflito**: relatados em `uncertainty`, com as escolhas conservadoras em `hypotheses` ("registro não declarado: o registro do original é mantido").
- **Rubricas oferecidas, nunca aplicadas**: um atributo que nomeia uma série do Standards Registry (por exemplo `enem`) gera `rubric.candidates`; aplicar exige `--document-profile` com edição e data.
- O contrato sem atributos não muda (compatibilidade); com atributos ganha `task_context`, e o prompt do escritor ganha o bloco `CONTEXTO DA TAREFA`.

**Prova.** `evals/test_v010_task_context.py` (15 testes: atributos novos, recusa de campos reservados, valores inválidos, misto, desconhecido com proteções, rubrica oferecida e não aplicada, proposta com e sem evidência, conflito, prompt de interpretação com o texto cercado como dado, compatibilidade do contrato, CLI). Conjunto congelado `evals/v010/context`: development **6/6** (v0.9.0: não aplicável).

**Limites.** Nenhuma execução com modelo real ainda (CP10). O prior de gênero é uma tabela pequena e declarada; fora dela, o gênero fica sem perfil e o pipeline usa o genérico.

## Registro de conhecimento linguístico e recuperação seletiva (CP3)

**Problema (V010-GAP-12).** O conhecimento estava espalhado (dados do `compare`, `standards`, packs, referências) sem fonte, natureza (prescrição × descrição), licença nem motivo de uso.

**O que existe agora** (`voznativa/knowledge.py`, `voznativa/data/knowledge_pt_br.yml`, decisão D-03):

- Registro versionado (`schema_version: 1`) com **fontes** (título, URL quando há, natureza `prescriptive`/`descriptive`, licença, acesso `open`/`consultation_only`/`citation_only`/`metadata_only`, data de consulta) e **entradas** (fenômenos, área, enunciado curto escrito para o projeto, onde vale, onde é variante, fontes citadas). 15 entradas, 7 fontes. Nenhum texto das obras citadas é copiado; gramáticas entram como referência bibliográfica (`citation_only`), e a verificação página a página fica para uma pessoa (nenhuma entrada é `VERIFIED` pelo agente).
- **Seleção por necessidade**: o que o `diagnose` achou no texto e os conectivos/condições presentes; orçamento de caracteres (padrão 900); cada item diz **por que** entrou. Texto sem necessidade não recebe nada.
- **Variante legítima**: em registro informal ou gênero literário, a entrada vira `variante` ("forma legítima neste registro, não corrija sem pedido"), não regra.
- **Norma institucional só quando aplicada**: a entrada do Enem exige que o perfil do documento tenha tornado a cartilha aplicável; caso contrário fica em `skipped` com o motivo.
- **Fonte não emite comando**: o bloco no prompt diz que é material de referência; entrada com cara de instrução a modelo, fonte não registrada, URL sem https ou id que sombreia uma entrada embutida são **recusados** na carga (também para registros externos em `VOZNATIVA_KNOWLEDGE_DIR`).
- **Proveniência no resultado**: `rewrite` registra `knowledge` (ids, papel, motivo, fontes; sem o texto).
- **Offline**: o arquivo embutido é o snapshot; nada é buscado na rede nesta camada (o Watcher do CP8 propõe mudanças, não as aplica).
- CLI: `voznativa knowledge list`, `voznativa knowledge select TEXTO`.

**Prova.** `evals/test_v010_knowledge.py` (11 testes: registro válido, entrada hostil recusada, fonte não registrada/http/sombreamento recusados, entrada externa válida usada e marcada, seleção com motivo, variante em registro informal, rubrica sem norma aplicada, orçamento, relação discursiva, bloco "não é instrução", proveniência no `rewrite`).

**Limites.** Sem medição de ganho com modelo real ainda (CP10). A seleção é por fenômeno declarado; fenômeno que o `diagnose` não vê não traz conhecimento.
