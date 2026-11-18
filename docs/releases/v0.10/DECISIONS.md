# Decisões da v0.10 (ADRs curtos)

## D-01 — TaskContext estende o contrato do router; não é um segundo motor (CP0)

**Contexto.** O router já emite um contrato de contexto v3 com dimensões que carregam `source`, `confidence` e `evidence`. O prompt pede contexto aberto, extensível, com proveniência e conflitos.
**Decisão.** Um módulo `task_context` constrói, a partir do contrato do router, uma visão aberta: atributos com nome livre (validado), valor, proveniência (`explicit`, `inferred`, `agent_proposed`, `document`, `standard`, `none`), confiança e conflitos. Campos de segurança (fatos protegidos, trechos protegidos, autorização de fontes) não podem ser criados nem afrouxados por atributo livre. O engine continua lendo o contrato v3; o TaskContext entra no prompt e no relatório.
**Alternativas.** (a) Trocar o router por classificação por modelo: perde o modo sem modelo e a reprodutibilidade. (b) Enum maior: é o que o prompt pede para evitar.

## D-02 — Relação do juiz: só independência demonstrada aceita (CP0, a implementar no CP6)

**Contexto.** `unknown` aceita hoje. Nomes diferentes de comando não provam modelo diferente.
**Decisão.** Taxonomia `same_agent`, `same_model`, `same_vendor`, `different_model`, `different_provider`, `independence_verified`, `unknown`. Aceitação automática (`accepted_by_llm`) só com `different_model`, `different_provider` ou `independence_verified`; `same_vendor` é registrado como tal (aceita, com `independence: partial` visível — a mesma política da v0.9 para modelos distintos do mesmo fornecedor, agora explícita); `unknown`, `same_model` e `same_agent` não aceitam. Migração: julgamentos antigos com `different_model` continuam válidos; quem precisa do comportamento anterior declara o modelo do juiz.
**Alternativas.** Aceitar `unknown` com aviso: mantém o falso verde que o prompt manda auditar.

## D-03 — Conhecimento sem banco vetorial (CP0)

Volume pequeno e metadados ricos: seleção por necessidade declarada (fenômeno, gênero, período, região) com orçamento, sem embeddings. Revisável com medição de recall.

## D-04 — Watcher propõe, não aplica (CP0)

Modos `report` e `propose`; nenhum modo altera código, regras semânticas, dependências ou modelos. Agendamento: comando local pronto (`SCHEDULER_READY`); workflow hospedado só com consentimento de custo.
