# Roadmap

Legenda: `[x]` implementado e testado · `[~]` parcial · `[ ]` não implementado.

## v0.1 — Foundation
- [x] visão e arquitetura
- [x] SKILL.md roteador
- [x] pesquisa comparativa
- [x] design spec completo
- [x] matriz de rastreabilidade
- [x] agent metadata inicial
- [x] assets/templates iniciais
- [x] regras de regionalidade, gírias e idioleto
- [x] biblioteca inicial de padrões PT-BR
- [x] referências por gênero e registro
- [x] community-pack scaffolds
- [x] analisador determinístico
- [x] Semantic Guard lexical inicial
- [x] wrappers protect_spans/fact_guard
- [x] controle de spans sobrepostos e multiplicidade
- [x] Voice Profile estatístico inicial
- [x] Regional Overfit/Dialect Mixing baseline guard
- [x] Voice Drift baseline
- [x] Audit baseline
- [x] schemas versionados iniciais
- [x] suíte de regressão foundation
- [x] scaffolds de eval por domínio
- [x] corpus/evidence strategy
- [x] competitive benchmark protocol
- [x] benchmark runner determinístico inicial
- [x] model/adapter research track
- [x] validador de pacote
- [x] CI

## v0.2 — Semantic Ledger
- [x] ledger determinístico por sentença (spans + marcadores)
- [ ] ledger estruturado de claims (extração automática; hoje só via juiz) → pesquisa em v0.3.0 M1
- [~] entidades/relações: presença; troca de valores, de agentes e de atribuições (troca mútua); NÃO detecta pronomes, inversão ativa/passiva com a mesma ordem, fontes em minúscula
- [x] modalidade e negação (léxico E1, concordância negativa, compostos im+possível)
- [x] temporalidade: datas, horas, dias, relativos; antes/depois
- [x] causalidade: causal x correlacional; direção invertida dentro da frase e entre frases adjacentes (v0.3.0)
- [~] antônimos: 13 pares do léxico de polaridade; antônimos fora do léxico NÃO detectados
- [x] julgamentos vinculados ao sha256 dos textos; revisão humana assinada (`voznativa review`)
- [x] spans protegidos configuráveis pelo usuário (v0.3.0 M1)
- [x] semantic-loss report (`voznativa compare`) com política conservadora
- [x] contrato de juiz LLM/humano
- [x] modelo NLI PT-BR opcional: pesquisado e rejeitado na v0.3.0 M1 (`evals/experiments/nli_probe.json`)
- [ ] holdout escrito por terceiros (os atuais foram escritos pelo mesmo autor do motor) → v0.3.0 M4

## v0.3.0 — Semantic Intelligence & Author Voice (em andamento)

Plano, work packages e critérios obrigatórios: `docs/PLAN_v0.3.0.md`. Não será marcada como concluída enquanto houver critério obrigatório pendente (holdout independente, revisão humana cega e CI dependem de terceiros).

### M1 — Semantic Intelligence
- [x] holdout prospectivo v0.3 congelado antes das correções (1ª execução 15/24; após M1 24/24, não cego)
- [x] adições dentro da frase (novidade por oração; regressão ho-007)
- [x] números por extenso compostos e equivalências ("um/uma" segue ambíguo)
- [x] causalidade entre frases adjacentes
- [x] papéis agente/paciente em voz ativa/passiva (só entidades nomeadas)
- [x] spans protegidos configuráveis pelo usuário (de v0.2)
- [x] experimento de sintaxe opcional (spaCy): 1 detecção nova em 167 casos; não adotado
- [x] experimento de NLI PT-BR opcional (de v0.2): rejeitado (nada novo, 9/56 falsos vermelhos)

### M2 — PT-BR Writing Quality
- [x] detector de padrões operacional com isenções por gênero (absorve v0.4)
- [x] decisão de NO_CHANGE e reescrita dirigida aos achados, validada em execução real (achados 29 → 6)
- [ ] planejamento por documento — só com ganho medido

### M3 — Author Voice
- [x] perfil por canal (`channels` no Voice Profile v2)
- [x] comparação de voice vectors normalizados (`voznativa drift --profile`)
- [~] Voice Drift por janelas (normalizado; limiar NÃO calibrado)
- [~] voice match mensurável no relatório do engine (implementado; experimento com autor sintético inconclusivo)
- [~] estabilidade em textos longos (drift reportado; limiar sem calibração)
- [ ] calibração com amostras consentidas (bloqueado: depende de amostras reais)

### M4 — Evidence & Benchmarks
- [x] dataset de benchmark congelado antes da execução
- [x] benchmark skill-only com o mesmo LLM (raw, prompt simples, blader, work-humanizer, VozNativa) (de v0.8); instrumentos são do próprio VozNativa
- [ ] benchmark system-level com Emulate (bloqueado: chave de API) (de v0.8)
- [x] instrumento de revisão humana cega (de v0.8)
- [ ] rodada de revisão humana registrada (depende de pessoas)
- [ ] holdout independente executado (depende de outra pessoa)

### M5 — Corpus Pilot
- [x] ingestão metadata-only de um recorte do Corpus Carolina

### M6 — Release Qualification
- [x] retries e erros de provider sem derrubar o engine
- [x] privacidade em relatórios de integração (`--redact`)
- [x] exemplos reais antes/depois (`examples/`)
- [x] matriz de compatibilidade final (local; `evals/compat/`)
- [x] CI verde: run #123 em `40e19e4` (8/8 jobs, Linux e Windows, 3.11–3.13); bloqueado por cobrança só em 20–21/10

## v0.4.0 — PT-BR Writing Intelligence & Hardening (em desenvolvimento, `0.4.0.dev0`)

Plano e status: `docs/PLAN_v0.4.0.md`. Não qualificada: herda os critérios externos abertos da v0.3.0 (holdout independente, revisão humana cega, CI).

### M0 — Hardening da v0.3
- [x] `ho-007`: divergência de classificação separada de detecção perdida (caso congelado intacto)
- [x] create mode: juiz de fundamentação contra as fontes autorizadas, com evidência literal
- [x] NO_CHANGE: destino pedido (canal, gênero, registro, público, voz) separado de "sem problema editorial"
- [x] `blind-summary`: todos os hashes, uma resposta por tarefa e chave, mapeamento de braços assinado
- [x] assinatura: integridade, posse da chave, identidade declarada e independência separadas; chave SSH do revisor
- [x] `--redact`: credenciais, erros, caminhos e hashes adivinháveis
- [x] providers: árvore de processos, limite de saída, erros do Emulate, avisos de sandbox, ambiente mínimo; cercas no prompt
- [x] documentação corrigida (`claim_added`, `--cmd "claude -p"`, CI)
- [x] achados na fase: `voznativa rewrite` quebrado desde a v0.3.0; saída cp1252 de providers no Windows; juiz fora do ar descartava candidata; dia da semana sem preposição

### M1 — PT-BR Pattern Library v2
- [x] oficialês deslocado (`officialese`; `a nível de` forte)
- [x] ENEM-ismo fora da redação escolar (`enem_formula`); aberturas só quando abrem o parágrafo
- [x] gerundismo com verbo pontual x durativo ancorado; gerúndio de consequência (`gerund_tail`)
- [x] conectivos empilhados e redundantes (`connector_pleonasm`); isenção em redação escolar
- [x] trios e paralelismos formulaicos (`formulaic_triad`, `anaphora_run`)
- [x] nominalização e verbos-suporte (colocações fixas preservadas)
- [x] linguagem corporativa vaga e promocional (claim atribuído preservado)
- [x] fechamentos genéricos por posição (`closing_formula`, `generic_closing` só no fim de texto curto)
- [x] redundância e repetição (`pleonasm`, `repeated_evaluation`)
- [x] traduções literais (`calque_construction`, `calque_collocation`)
- [x] cada padrão com casos positivos, falsos positivos, justificativa e fontes (teste obrigatório)
- [ ] calibração em corpus (limiares e listas montados pelo desenvolvedor)

### M2 — Brazilian Portuguese Contextual Intelligence
- [x] PT-BR x PT-PT: léxico, `estar a + infinitivo`, grafia; falsos amigos marcados, não trocados
- [x] estrangeirismos por domínio (técnico, negócios, marketing); termos do domínio preservados na reescrita
- [x] tratamento formal/informal (mistura e troca sem pedido)
- [x] oralidade escrita x registro alvo (chat x fala)
- [x] LanguageTool 6.6 avaliado e não adotado (`evals/experiments/languagetool_probe.json`)
- [ ] packs regionais e gírias (fora do escopo sem evidência)

### M3 — Contextual Rewrite Planner
- [x] `voznativa plan`: trechos, motivo, prioridade, operação (manter, troca pontual, corte, frase, parágrafo, documento)
- [x] preservação por frase (valores, negação, modalidade, compromissos, condições, causalidade), dependência entre frases, consistência
- [x] aderência ao plano (edições fora do plano, padrões introduzidos) no ranking e no relatório
- [x] inconsistência da fonte reportada (dia da semana x data)
- [~] múltiplas candidatas + reranking: só desempate determinístico por aderência; benefício de N>1 não medido com modelo real

### M4 — Evals e benchmarks
- [x] `holdout-v040` congelado (32 casos por canal e risco): 32/32, não discrimina v0.3 x v0.4
- [x] suíte de decisão congelada (30 casos): v0.4 27/30 na primeira execução; v0.3 22/30 na decisão de chamar o modelo
- [x] `ptbr-bench-v2` congelado antes da execução; resultados em `docs/EVALUATION.md`
- [x] latência do pipeline determinístico (`scripts/perf_probe.py`)
- [ ] revisão humana e holdout independente (dependem de pessoas)

### M5 — Qualificação
- [x] matriz local Linux/Windows 3.11–3.13, wheel e instalação isolada (`evals/compat/v0.4.0-dev-4bd8fb1.json`)
- [x] demonstração antes/depois reproduzível (`examples/v0.4.0-demo.md`, `scripts/demo.py`)
- [x] CI verde: run #123 em `40e19e4` (8/8 jobs, Linux e Windows, 3.11–3.13); bloqueado por cobrança só em 20–21/10

### Hardening da v0.4.0 (CP4, 2026-11-05)
- [x] runner único de qualificação local (`scripts/qualify.py`) com exit codes preservados
- [x] erro de uso sai 64 em todo comando (antes 2 = `review_required`)
- [x] falso verde de suíte congelada corrigido (conjunto fixo; decisão e benchmark com hash)
- [x] benchmark em eixos separados; `provider_error` nunca conta como sucesso; v2 reanalisado sem alterar o oficial
- [x] `dc-021`/`dc-029` determinados sem ajuste de limiar (`dc-029` INCONCLUSIVE até haver dados)
- [x] ledger: dia da semana sem preposição, "2 da tarde", verbos multiplicadores (`ho-007` 24/24), troca de papéis/ordem com substantivos comuns
- [x] desempenho: `compare` 10× mais rápido; loop sem modelo 48,6 s → 1,1 s
- [x] chave de revisão criada privada; sanitizador de relatórios testado
- [ ] pronomes, troca entre frases, inflexões diferentes (limitações registradas; extração de claims como experimento)

## v0.5 — Regional Layer (em desenvolvimento, `0.5.0.dev0`)

Plano e status: `docs/PLAN_v0.5.0.md`.

- [x] registro de fontes (ALiB, SP2010, C-ORAL-BRASIL, ALIP, PHPB, Carolina, NURC) com licença, amostragem e decisão
- [x] contrato versionado de Regional Evidence Pack (escopo, época, gênero/canal, formas, contextos, confusões, confiança, ativação, proveniência, licença) e ADR-0001
- [~] packs com fonte, período e confiança: **um** piloto (Norte, um referente), confiança baixa
- [x] abstenção por padrão; região nunca inferida; voz do autor vence; troca que muda o referente pede revisão
- [x] Regional Overfit / Dialect Mixing por evidência (`regional_form_introduced`)
- [ ] taxonomia região/estado/localidade além do piloto
- [ ] distinções capital/interior sustentadas por dados
- [ ] calibração do Regional Overfit Guard
- [ ] avaliação humana regional (protocolo pronto; NOT_RUN)
- [ ] `ptbr-bench-v3` executado (congelado; NOT_RUN)
- [ ] triagem de escopo para textos normativos ou de segurança crítica (ADAPT do `humanizar`)

## v0.6 — Universal Corpus, Temporal Language & Community Intelligence (em desenvolvimento, `0.6.0.dev0`)
- [x] Corpus Registry, política de dados, conectores limitados, proveniência e divisões sem vazamento; CLI `voznativa corpus`
- [x] calibração em texto humano (Bosque, B2W); `dc-029` continua INCONCLUSIVE
- [x] léxico temporal v2 com atestação datada (E2 só para 4 formas, até 2018); aging/deprecation no contrato
- [ ] atestação posterior a 2018 (Carolina com licença por documento) — sem ela, nenhuma gíria pode ser gerada
- [x] community packs v2 com taxonomia (4 `draft`, E0); [ ] packs validados com fonte (E2+)
- [x] slang stuffing guard (compartilhado com o regional)
- [x] integração no Router, Contract, Planner, Engine (revisão), Profile e CLI, com precedência explícita
- [x] textos longos: mapa de dependências, segmentação, política literária e de verso; [x] reescrita ponta a ponta por segmentos (v0.7.0, G4)
- [x] `ptbr-bench-v4` congelado e com braço determinístico; [ ] braços com modelo e revisão humana (NOT_RUN)
- Backlog com teste reproduzível (`evals/test_known_gaps_v06.py`); os quatro foram fechados na v0.7.0:
  - **P1 G1:** o roteador lê como `whatsapp` a literatura com quebra de linha fixa e diálogo com "--" (259 de 804 segmentos). Corrigir pede desfazer as quebras antes da inferência e reavaliar a suíte congelada do roteador.
  - **P2 G2:** um capítulo contido no romance inteiro não forma cluster com ele. É preciso uma medida de contenção antes de chamar de independentes as divisões que misturam edições.
  - **P3 G3:** a forma "de boa" seguida de palavra não é detectada. Uma correção pede amostra separada nova.
  - **P2 G4:** o engine não reescreve documento longo por segmentos.
- [ ] interação comunidade x região x canal medida com dados

## Pesquisa/decisões pendentes
- [x] licença do repositório: MIT para o material original (v0.6.0; `LICENSE`, `docs/LICENSING.md`)
- [ ] resolver o conflito de licença do Corpus Carolina antes de qualquer ingestão (o piloto metadata-only da v0.3.0 M5 não ingere texto)
- [ ] holdout semântico escrito por outra pessoa
- [x] execução real do benchmark skill-only (B0–B3, B5) com manifesto e juízes; B4 (Emulate) bloqueado
- [ ] calibração dos limiares do `compare` e do drift com reescritas reais

## v0.7.0 — Generalização, documento inteiro e evidência (em desenvolvimento, `0.7.0.dev1`; estabilização em `docs/PLAN_v0.7.0.dev1.md`)

Plano: `docs/PLAN_v0.7.0.md`. Estado por checkpoint: `docs/V07_EXECUTION_STATE.md`. Matriz requisito -> teste: `docs/V07_VERIFICATION_MATRIX.md`.

- [x] G1: roteador estrutural, contrato v3 e proteções na abstenção (`router.py`; `evals/test_router_v3.py`)
- [x] G2: contenção direcional em dedup e splits por várias chaves (`corpus/processing.py`; `evals/test_containment.py`)
- [x] G3: gíria por sentido de ocorrência (`temporal.py`; `evals/test_slang_v07.py`)
- [x] G4: reescrita por unidades com validação global (`document.py`, `engine.rewrite_document`; `evals/test_document_rewrite.py`)
- [x] guards entre frases e parágrafos; estabilidade metamórfica (`compare.py`; `evals/test_global_guards.py`)
- [x] TEI seguro, licença por documento, direitos do texto separados da licença de anotação (`corpus/tei.py`, `policy.py`; `evals/test_corpus_tei.py`, `evals/test_corpus_v07.py`)
- [x] 7 corpora integrados à avaliação (eram 3) e avaliação cruzada (`scripts/corpus_crossgenre.py`)
- [~] análise linguística: verbos com abstenção (`morph.py`; `evals/test_morph.py`); concordância, regência, correferência: não
- [~] diagnóstico do original e modos editoriais (`diagnose.py`; `evals/test_diagnose.py`); narrador e personagens: não
- [x] integridade de caracteres e proveniência (`integrity.py`; `evals/test_integrity.py`)
- [x] `ptbr-bench-v5` congelado antes de rodar, braço determinístico (`scripts/bench_v5.py`)
- [~] benchmark de detectores: infraestrutura e protocolo (`evals/test_external_detection.py`); execução real NOT_RUN
- [x] harness de checkpoint e evidência de CI ao vivo (`scripts/checkpoint.py`, `scripts/ci_evidence.py`; `evals/test_ci_evidence.py`)
- [x] README verificado por teste (`evals/test_readme.py`)
- [ ] braços com modelo, revisão humana cega, holdout independente (dependem de orçamento e de pessoas)
- [ ] automação de navegador (sem alvo autorizado: UNSUPPORTED)
- [ ] normas, editais e rubricas versionados (visão: `docs/V08_STANDARDS_VISION.md`)

## v0.7 — Rewrite Engine Contract (contrato original, entregue nas v0.3–v0.6)
- [x] contrato agnóstico de modelo
- [x] provider adapter interface (command, static, emulate)
- [x] Context Router executável
- [x] montagem dinâmica de referências (orçamento de palavras)
- [x] retries por falha dominante
- [x] compare original/candidate
- [x] saída JSON estável (`kind` + `schema_version` em cada relatório)

## v0.8 — Evaluation System
- [x] factual/semantic (dev + 2 holdouts)
- [ ] voice → v0.3.0 M3
- [ ] regional
- [~] false-positive (casos `false_red` e NO_CHANGE; sem detector de edição desnecessária)
- [ ] genre
- [~] adversarial (limitações conhecidas viram casos `known_limitation`)
- [ ] long-form drift → v0.3.0 M3
- [ ] temporal slang
- [ ] human review protocol → v0.3.0 M4
- [~] eval provenance (hashes congelados; corpus não ingerido)
- [x] benchmark skill-only: execução oficial registrada (v0.3.0 M4)
- [ ] benchmark system-level reproduzível → v0.3.0 M4
- [~] blind pairwise harness: instrumento pronto, sem rodada humana (v0.3.0 M4)
- [x] frozen benchmark manifests (`cases_sha256`, `manifest.example.json`)

## v0.9 — Packaging & Integrations
- [x] manifests para hosts suportados (Claude Code plugin, Codex `openai.yaml`; Gemini via SKILL.md)
- [~] CLI (`voznativa`); estável só a partir da 1.0
- [x] exemplos antes/depois de execuções reais (v0.3.0 M6)
- [ ] documentação de extensão de packs
- [ ] política de contribuição de dados linguísticos
- [~] provider adapter para Emulate (não validado ao vivo)
- [ ] adapters para modelos locais/custom

## Research track — Optional Model / Adapter
- [x] arquitetura e gates documentados
- [ ] candidate generation + reranking
- [ ] dataset contract para adapters pessoais
- [ ] LoRA/PEFT experiment
- [ ] channel holdout
- [ ] domain adapter experiment
- [ ] specialized PT-BR model feasibility study

Essa trilha é opcional e nunca substitui Semantic Ledger, Fact Guard ou evals.

## v1.0 gate

1. Preservação semântica avaliada separadamente da naturalidade.
2. Voice consistency validada em múltiplos gêneros/canais.
3. Regionalidade calibrada com evidência e revisão humana.
4. Falsos positivos medidos.
5. Packs têm proveniência/licença.
6. Regressões bloqueiam release.
7. Nenhuma dependência de "AI detector score".
8. Benchmark competitivo diferencia skill-only de system-level.
9. Qualquer adapter/modelo especializado precisa passar pelos mesmos semantic gates.
