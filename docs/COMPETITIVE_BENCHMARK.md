# Competitive Benchmark Protocol

## Objetivo

Comparar VozNativa com alternativas reais sem reduzir "qualidade" a um detector de IA.

O benchmark responde perguntas separadas:

1. O significado foi preservado?
2. Fatos, números, prazos, compromissos e modalidade foram preservados?
3. O texto ficou mais natural para leitores?
4. A voz do autor foi preservada quando havia amostras?
5. O registro e o gênero continuam adequados?
6. Quanto o sistema alterou o texto?
7. Qual custo/latência operacional?
8. Como métrica exploratória apenas: detectores mudaram de classificação?

Detector nunca é gate de aprovação.

## Sistemas comparados

### B0 — Raw model
Saída do modelo sem humanização específica.

### B1 — One-line prompt
`Reescreva para soar mais natural/humano sem alterar o significado.`

Serve para medir quanto o pipeline especializado acrescenta sobre uma instrução trivial.

### B2 — blader/humanizer
Agent Skill baseada em padrões estruturais e preservação de claims.

Referência:
- https://github.com/blader/humanizer
- versão/commit deve ser congelado no manifest da execução.

O projeto declara explicitamente que passar em AI detector não é objetivo.

### B3 — work-humanizer
Skill orientada a escrita profissional, compromissos e preservação de significado.

Referência:
- https://github.com/phuryn/work-humanizer

O benchmark publicado pelo próprio projeto inclui comparação com one-line prompt, blader e Emulate-1. Seus números são evidência produzida pelo autor da ferramenta e devem ser tratados como hipótese externa, não como resultado independente do VozNativa.

### B4 — Emulate-1
Sistema/modelo especializado em escrita.

Referências oficiais:
- https://www.tryemulate.ai/
- https://www.tryemulate.ai/docs/api
- https://www.tryemulate.ai/research/mode-collapse

A API expõe `/v1/humanize` e um objeto de estilo com dimensões como tipo, tom, formalidade, sentenças, nível, perspectiva e concisão.

O campo legado `reads_human` atualmente retorna `null`; portanto o benchmark VozNativa não deve depender dele.

### B5 — VozNativa
Versão/commit congelado, com profile/contexto explicitamente registrado.

## Duas classes de comparação

### Skill-only benchmark
Usa o **mesmo LLM base** para:
- raw;
- one-line prompt;
- blader;
- work-humanizer;
- VozNativa skill/prompt mode.

Isto isola o efeito da skill.

### System benchmark
Compara produtos completos:
- Emulate-1;
- VozNativa com provider escolhido;
- outros sistemas especializados.

Aqui o modelo-base pode ser diferente. Portanto não atribuir a diferença apenas ao prompt/skill.

## Conjuntos de casos

### Factual/semantic
- números;
- moeda;
- datas;
- versões;
- modalidade;
- negação;
- causalidade;
- condição;
- compromisso;
- atribuição.

### Technical
- README;
- documentação;
- API;
- incident/report;
- arquitetura.

### Academic
- hipótese;
- método;
- resultados;
- limitação;
- citação.

### Corporate/work
- prazo;
- ownership;
- compromisso;
- suporte;
- HR;
- status report.

### Social/LinkedIn
- opinião;
- hook;
- storytelling sem invenção.

### WhatsApp/chat
- abreviações;
- voz pessoal;
- compromisso/horário;
- baixa formalidade.

### Voice matching
Mesma pessoa em:
- chat;
- GitHub/docs;
- e-mail;
- artigo.

### Regional/temporal
Somente quando houver evidência e reviewers adequados.

## Métricas

### Tier 0 — hard invariants
Determinístico sempre que possível:
- protected span recall;
- número/data/moeda/URL/identifier preservation;
- multiplicidade;
- comprimento/estrutura;
- unexpected protected additions.

Falha crítica em Tier 0 reprova a candidata.

### Tier 1 — semantic fidelity
Avaliar separadamente:
- claim omission;
- claim addition;
- modality shift;
- negation flip;
- causal direction;
- commitment strength;
- scope/condition drift;
- attribution drift.

Human review tem precedência sobre judge automático em casos disputados.

### Tier 2 — voice/register
- author voice match;
- channel fit;
- genre fit;
- regional overfit;
- dialect mixing;
- voice drift.

### Tier 3 — reader quality
Blind pairwise:
- naturalness;
- clarity;
- specificity;
- send/publish preference.

### Tier 4 — operational
- latency;
- token/word cost;
- retries;
- failure rate.

### Tier X — detector research
Opcional, separado e nunca usado como objetivo:
- detector/version/date;
- raw score;
- classification.

Não agregar como "human probability" do VozNativa.

## Protocolo

1. congelar dataset antes de gerar;
2. congelar versão/commit de cada sistema;
3. registrar modelo-base e configuração;
4. usar fresh context quando aplicável;
5. gerar múltiplas seeds/runs quando o provider permitir;
6. ocultar rótulos dos candidatos;
7. randomizar ordem;
8. separar pergunta de naturalidade da pergunta "você publicaria/enviaria?";
9. fazer fact-check contra o original;
10. publicar failures, não só médias;
11. manter detector fora do gate.

## Estatística mínima

Por sistema:
- número de casos;
- número de runs;
- hard-invariant pass rate;
- semantic error count por categoria;
- blind preference rate;
- voice-match score;
- register-fit score;
- latency mediana;
- custo mediano.

Intervalos de confiança devem acompanhar percentuais quando a amostra permitir.

## Fairness

Emulate-1 é um sistema treinado próprio; blader/work-humanizer são skills. Portanto existem dois placares separados: **skill-only** e **system**.

Não é válido concluir "skill X é melhor modelo" a partir de um benchmark que mistura classes sem declarar isso.

## Version manifest

Cada execução deve gravar algo como:

```json
{
  "benchmark_version": "0.1",
  "dataset_hash": "...",
  "systems": {
    "blader": {"commit": "..."},
    "work_humanizer": {"commit": "..."},
    "emulate": {"api": "v1", "date": "..."},
    "voznativa": {"commit": "..."}
  }
}
```
