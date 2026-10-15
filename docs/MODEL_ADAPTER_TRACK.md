# Optional Model / Adapter Track

## Motivação

VozNativa começa como engine/orquestrador em torno de LLMs existentes. Isso mantém o projeto provider-agnostic e permite evoluir rápido.

Entretanto, um prompt/skill tem limite: ele condiciona um modelo cuja distribuição base continua sendo a mesma. Uma trilha opcional de adapter/modelo permite testar se parte da voz pode ser aprendida diretamente.

Esta trilha é **opcional e paralela**. Não bloqueia o Rewrite Engine principal.

## Princípio

Treinar um adapter não substitui:
- Semantic Ledger;
- Fact Guard;
- corpus/evidência;
- Voice Profile;
- evals;
- validation gates.

Modelo especializado continua sujeito aos mesmos gates.

## R0 — Provider adapters

Primeiro passo: padronizar provedores por contrato.

```python
rewrite(text, voice_contract, context) -> Candidate
```

Providers podem ser:
- LLM geral;
- Emulate API;
- modelo local;
- endpoint customizado.

Isto é integração, não treinamento.

## R1 — Candidate generation + reranking

Gerar N candidatas e ranquear por:
1. hard semantic invariants;
2. semantic judge;
3. voice match;
4. register;
5. naturalness.

Nunca ranquear por detector como função objetivo.

## R2 — Lightweight personal adapter

Pesquisa futura com LoRA/PEFT ou mecanismo equivalente.

Dados permitidos:
- amostras autorizadas do próprio usuário;
- pares sintéticos controlados;
- exemplos licenciados para treinamento;
- features derivadas de corpus quando juridicamente compatíveis.

Não usar silenciosamente histórico pessoal inteiro.

### Dataset

Separar:
- train;
- validation;
- frozen test;
- channel holdout.

Evitar vazamento de frases idênticas entre splits.

### Objetivo

Aprender tendências como:
- ritmo;
- pontuação;
- escolha lexical;
- estrutura discursiva;
- preferência de conectores;
- grau de concisão.

Não memorizar dados pessoais/fatos das amostras.

## R3 — Domain adapters

Adapters por gênero/comunidade podem ser investigados:
- technical;
- academic;
- professional-natural;
- conversational.

Só criar quando houver ganho medido sobre prompt + Voice Contract.

## R4 — Specialized PT-BR writing model

Somente considerar se:
- adapters mostrarem ganho consistente;
- houver dataset licenciado suficiente;
- custo operacional justificar;
- semantics não piorar;
- benchmarks humanos mostrarem ganho real.

Treinar modelo próprio por prestígio não é objetivo.

## Gates

Um adapter/modelo novo só avança se:
- hard-invariant pass rate não piorar;
- semantic error rate não piorar;
- voice match melhorar em holdout;
- naturalness melhorar em blind review;
- não houver ganho apenas em detector;
- privacidade/licença estiver documentada.

## Privacidade

Voice adapters podem revelar características de escrita do usuário. Portanto:
- opt-in explícito;
- separação por usuário;
- criptografia/controle de acesso quando persistido;
- política de deleção;
- evitar retenção do texto bruto quando um perfil derivado bastar;
- não inferir atributos sensíveis.

## Relação com Emulate

A API pública do Emulate demonstra uma interface útil para inspiração arquitetural:
- humanize;
- write;
- style contract.

VozNativa pode adotar um provider adapter para benchmarking sem copiar o produto nem fazer detector-evasion seu objetivo.

## Decisão de engenharia

Ordem recomendada:
```text
provider contract
-> benchmark harness
-> semantic ledger
-> rewrite engine
-> robust evals
-> reranking
-> only then adapters/training
```

Isso evita gastar esforço treinando antes de termos métricas confiáveis.
