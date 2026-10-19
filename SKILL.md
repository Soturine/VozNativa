---
name: voznativa
description: Reescreve, audita, cria e perfila textos em português brasileiro com preservação semântica, voz contextual, variação regional responsável e modelagem de idioleto.
metadata:
  version: "0.2.0.dev0"
  language: pt-BR
---

# VozNativa

Use esta skill quando o usuário pedir para humanizar, naturalizar, reescrever, auditar, criar ou adaptar texto em português brasileiro, especialmente quando voz, registro, regionalidade, gírias, canal ou amostras do autor importarem.

## Objetivo

Não tente produzir "texto humano genérico". Produza texto coerente com o autor, o canal e o contexto, preservando conteúdo protegido.

## Pipeline

1. Classifique gênero, canal, público, objetivo, formalidade e restrições.
2. Crie o Semantic Ledger: preserve nomes, números, datas, citações, URLs, código, identificadores, causalidade e modalidade.
3. Analise propriedades determinísticas quando as ferramentas estiverem disponíveis.
4. Monte o Voice Stack: amostra do autor > canal/contexto > comunidade > regionalidade > default PT-BR.
5. Carregue apenas as referências necessárias.
6. Reescreva sem inventar experiência, fatos, dados ou gírias.
7. Valide significado, registro, regionalidade e drift de voz.
8. Entregue o texto; relatório só quando solicitado ou quando houver risco relevante.

## Modos

- rewrite: reescreve texto existente.
- audit: diagnostica sem exigir reescrita.
- create: escreve do zero com fatos fornecidos/verificados.
- profile: extrai Voice Profile de amostras.
- compare: compara original e candidata.

## Regras invioláveis

- Naturalidade nunca compensa perda semântica.
- "Pode" não vira "causa"; "17" não vira "alguns".
- Não invente vivência pessoal para dar "alma".
- Não use gíria regional só para sinalizar região.
- Não infira idade, gênero, origem, classe social, etnia ou personalidade a partir da escrita.
- Não trate palavra isolada, travessão ou gramática boa como prova de IA.
- Não produza "probabilidade de IA".
- Não prometa evasão de detectores.

## Guards

- Semantic Guard
- False Positive Guard
- Regional Overfit Guard
- Dialect Mixing Guard
- Voice Drift Guard


## Progressive disclosure

Carregue apenas o que a tarefa exigir:

- `references/patterns/`: padrões estruturais, retóricos, formatação, PT-BR e falsos positivos.
- `references/genres/`: acadêmico, técnico, corporativo, social, WhatsApp e literário.
- `references/registers.md`: registros linguísticos.
- `references/voice/`: schema e idioleto.
- `references/regions/`: política e futuros packs regionais.
- `references/communities/`: socioletos/comunidades.
- `references/slang/`: gírias com temporalidade.
- `docs/DESIGN_SPEC.md`: contrato completo da arquitetura.
- `docs/TRACEABILITY.md`: estado real de cada requisito.

Quando disponível, use:
- `scripts/audit.py` para diagnóstico baseline;
- `scripts/semantic_guard.py` para invariantes;
- `scripts/voice_profile.py` para amostras;
- `scripts/region_consistency.py` para overfit/mixing baseline;
- `scripts/voice_drift.py` para drift estilístico baseline.
