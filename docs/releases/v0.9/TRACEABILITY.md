# Rastreabilidade da v0.9

Requisito → código → teste → evidência. Os requisitos foram escritos no CP0, antes da implementação; as colunas de código, teste e prova são preenchidas por CP. Estados: `PLANNED`, `IMPLEMENTED`, `TESTED_WITH_STUB`, `REAL_PROVIDER_VERIFIED`, `INDEPENDENTLY_VERIFIED`, `PARTIAL`, `NOT_RUN`, `BLOCKED`, `ACCEPTED_RISK`. "Teste definido" não é "teste executado", e executado não é "mata o defeito": a coluna Prova diz o que foi demonstrado.

| ID | Requisito | Aceite | Gap | Sev. | CP | Código | Teste | Prova | Estado |
|---|---|---|---|---|---|---|---|---|---|
| V09-001 | Gate de privacidade antes de cada push | vazamento plantado é pego; faixa limpa passa; entrada privada dentro do repositório é recusada | GAP-22 | P1 | CP0 | `scripts/privacy_gate.py` | `evals/test_v09_privacy_gate.py` | 7 testes; reproduz o veredito limpo do intervalo da v0.8.1 contra os dois documentos privados | IMPLEMENTED |
| V09-002 | Medição de tempo do `compare` com método fixo | mesmo script mede baseline e candidata; CPU e parede; amostras guardadas | GAP-14 | P2 | CP0 | `scripts/perf_compare.py` | — | baseline `17d1f10` registrada no CP0 | IMPLEMENTED |
| V09-010 | `doctor` separa causas e diz a ação de cada uma; checa o provider configurado sem gastar | cada causa tem teste com o código e a ação | GAP-18 | P3 | CP1 | | | | PLANNED |
| V09-011 | Configuração por usuário e por projeto com precedência documentada (flag > projeto > usuário > padrão) | precedência testada; nenhum segredo lido de arquivo de projeto | GAP-19 | P3 | CP1 | | | | PLANNED |
| V09-012 | Instalação limpa: wheel fora do checkout em Windows 3.11/3.12 e Linux 3.11–3.13 | gate de pacote por plataforma | — | P2 | CP1/CP9 | | | | PLANNED |
| V09-013 | Documentação sem afirmações desatualizadas | validador e teste do README | GAP-20 | P3 | CP1 | | | | PLANNED |
| V09-020 | Contrato de provider com capacidades, chamadas, custo observado e erros tipados, sem contornar gates | adapters existentes e novos passam pelo mesmo contrato; testes de erro | GAP-15 | P2 | CP2 | | | | PLANNED |
| V09-021 | Adapter HTTP para servidores locais compatíveis com a API de chat (Ollama, llama.cpp, LM Studio) | conexão recusada, modelo inexistente, timeout, resposta inválida tratados; execução real com um modelo local, se viável | GAP-15 | P2 | CP2 | | | | PLANNED |
| V09-022 | Fluxo agent-led real com host de verdade (Claude Code) usando a CLI do produto | registro da sessão com comandos, desfechos e custo | GAP-17 | P2 | CP2 | | | | PLANNED |
| V09-023 | Hosts Codex, Gemini CLI e Emulate com estado verificável | `NOT_RUN`/`BLOCKED` com motivo quando não executados | GAP-16/17 | P3 | CP2 | | | | PLANNED |
| V09-030 | Memória editorial entre unidades e guard de convergência de estilo | repetição introduzida pela reescrita vira sinal; repetição do original não; replay real antes × depois | GAP-09 | P2 | CP3 | | | | PLANNED |
| V09-031 | Teste de tempo estável e sem afrouxar o limite | método do CP0; sem falha sob carga da suíte | GAP-14 | P2 | CP3 | | | | PLANNED |
| V09-040 | Qualificador operacional apagado vira sinal sem tornar crítica toda remoção de adjetivo | pares positivos e negativos congelados antes da regra | GAP-01 | P1 | CP4 | | | | PLANNED |
| V09-041 | Troca de evento e de estado do fato vira sinal | conjunto prospectivo congelado antes; predicados sem piora | GAP-02/03/04 | P1 | CP4 | | | | PLANNED |
| V09-042 | Diagnóstico gramatical de alta confiança (concordância nominal, regência frequente) | controles de variante legítima e de DF-06 | GAP-08 | P2 | CP4 | | | | PLANNED |
| V09-043 | Termos técnicos consagrados preservados; grafia consistente | sem regressão nos benches | GAP-10 | P2 | CP4 | | | | PLANNED |
| V09-044 | Siglas de letras internas; Router com mais pistas sem perder precisão | curva cobertura × precisão | GAP-11/12 | P3 | CP4 | | | | PLANNED |
| V09-050 | Representação intermediária reversível e DOCX seguro | ida e volta sem edição equivalente por parte; original intocado; elementos protegidos com hash | GAP-13 | P2 | CP5 | | | | PLANNED |
| V09-051 | PDF: extração rastreável e anotação, sem prometer reconstrução | palavras com posição; equações e código protegidos | GAP-13 | P2 | CP5 | | | | PLANNED |
| V09-060 | Contrato e validador de packs; política de contribuição; pack exercitado no fluxo | pack inválido recusado; pack nunca relaxa guards | GAP-21 | P2 | CP6 | | | | PLANNED |
| V09-070 | Relatório antes × depois por eixo, com método e incerteza | v0.8.1 e v0.9 medidos pelo mesmo runner | — | P2 | CP7 | | | | PLANNED |
| V09-080 | Dogfood real com o engine, auditorias Assertiva e Derivanta, segurança | registros e testes de regressão | — | P2 | CP8 | | | | PLANNED |
| V09-090 | Release `v0.9.0` qualificada | critérios R1–R10 do [`PLAN.md`](PLAN.md) | — | — | CP9 | | | | PLANNED |
