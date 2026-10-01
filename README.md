# VozNativa

> Motor de voz escrita para português brasileiro: humanização contextual, preservação semântica, variação regional responsável e modelagem de idioleto.

VozNativa não tenta responder apenas a "como um humano escreve?". O objetivo é responder melhor:

> **Como esta pessoa escreveria este conteúdo, neste canal, para este público, sem perder fatos, intenção ou registro?**

O projeto nasce como uma Agent Skill PT-BR e uma fundação para um futuro **Brazilian Portuguese Voice Engine** reutilizável por agentes, CLIs e pipelines.

## Por que existe

Humanizers tradicionais ajudam a remover padrões mecânicos, mas frequentemente:
- tratam palavras isoladas como erro;
- apagam marcas legítimas do autor;
- alteram números, modalidade ou precisão;
- reduzem PT-BR a um registro único;
- transformam regionalidade em caricatura;
- confundem dialeto, comunidade e idioleto;
- chamam métricas estilísticas de "probabilidade de IA".

VozNativa separa esses problemas.

## Princípios

1. **Significado antes de estilo.**
2. **Voz antes de "humanidade".**
3. **Contexto antes de regra.**
4. **Regionalidade sem caricatura.**
5. **Observação linguística não vira inferência de identidade.**
6. **Código para o determinístico.**
7. **LLM para semântica, pragmática, tom e reescrita.**
8. **Sem promessa de evasão de detectores.**
9. **Progressive disclosure.**
10. **Mudanças precisam de regressão/evidência.**

## Arquitetura

```text
Context Router
   |
Semantic Ledger / Fact Lock
   |
Deterministic Analyzer
   |
Voice Stack
   |-- author samples
   |-- channel/context
   |-- community
   |-- regionality
   '-- pt-BR default
   |
Rewrite Engine
   |
Validation Gates
   |-- Semantic Guard
   |-- False Positive Guard
   |-- Regional Overfit Guard
   |-- Dialect Mixing Guard
   '-- Voice Drift Guard
```

Detalhes: `docs/ARCHITECTURE_AND_RESEARCH.md`.

## O que já existe em v0.1.0

- `SKILL.md` enxuto como roteador;
- arquitetura e pesquisa comparativa documentadas;
- estratégia de corpus/evidência com Source Ledger e níveis E0–E4;
- referências operacionais para Carolina, ALiB, NURC, SP2010, CORAA e C-ORAL-BRASIL;
- padrões PT-BR iniciais;
- Voice Stack documentado;
- schema versionado de Voice Profile;
- schema de gíria temporal;
- analisador determinístico;
- Semantic Guard com spans protegidos e controle de multiplicidade;
- profiler inicial de idioleto;
- Regional Overfit/Dialect Mixing baseline guard;
- suíte de regressão e scaffolds de eval por domínio;
- Audit baseline e Voice Drift baseline;
- assets/templates e metadata inicial para agente;
- matriz de rastreabilidade design → implementação → roadmap;
- validação estrutural do pacote;
- CI em Python 3.11/3.12/3.13.

## Estrutura atual

```text
VozNativa/
├── README.md
├── SKILL.md
├── ROADMAP.md
├── CHANGELOG.md
├── pyproject.toml
├── agents/
│   └── openai.yaml
├── assets/
│   ├── voice-profile.yml
│   └── regional-pack.yml
├── docs/
│   ├── ARCHITECTURE_AND_RESEARCH.md
│   ├── DESIGN_SPEC.md
│   └── TRACEABILITY.md
├── references/
│   ├── VOICE_STACK.md
│   ├── registers.md
│   ├── corpora/
│   │   ├── carolina.md
│   │   ├── alib.md
│   │   ├── nurc.md
│   │   ├── sp2010.md
│   │   ├── coraa.md
│   │   └── c-oral-brasil.md
│   ├── patterns/
│   │   ├── pt-br.md
│   │   ├── structural.md
│   │   ├── rhetorical.md
│   │   ├── formatting.md
│   │   └── false-positives.md
│   ├── genres/
│   ├── regions/
│   ├── communities/
│   ├── slang/
│   └── voice/
├── scripts/
│   ├── analyze.py
│   ├── semantic_guard.py
│   ├── protect_spans.py
│   ├── fact_guard.py
│   ├── voice_profile.py
│   ├── region_consistency.py
│   ├── voice_drift.py
│   ├── audit.py
│   └── validate_package.py
├── evals/
│   ├── test_foundation.py
│   ├── academic/
│   ├── whatsapp/
│   ├── linkedin/
│   ├── corporate/
│   ├── technical/
│   ├── documentation/
│   ├── storytelling/
│   ├── regional/
│   ├── slang/
│   ├── false-positive/
│   └── adversarial/
└── .github/workflows/
    └── ci.yml
```

## Modos planejados da skill

- `rewrite`
- `audit`
- `create`
- `profile`
- `compare`

A especificação existe em `SKILL.md`; o motor generativo agnóstico de provedor ainda faz parte do roadmap.

## Voice Stack

Precedência padrão:

```text
amostra do autor
    >
canal/contexto
    >
comunidade/socioleto
    >
regionalidade
    >
default PT-BR
```

Amostras do próprio autor têm precedência porque o projeto tenta preservar **idioleto**, não empurrar todo mundo para uma "voz brasileira média".

## Regionalidade

"Sotaque escrito" é um atalho coloquial. Sotaque estrito é fonético/fonológico. Na escrita, VozNativa trabalha com léxico, morfossintaxe, pragmática, discurso, formas de tratamento e grafia estilizada quando apropriado.

Regionalidade é **distribuição, não decoração**.

Um pedido como "mineiro informal" não significa inserir `uai` ou `trem` em toda frase.

O guard atual é apenas uma **heurística de baseline para testar a arquitetura**. Não deve ser interpretado como classificador confiável de dialeto.

## Gírias e temporalidade

Gírias podem registrar:
- região;
- comunidade;
- contexto;
- período observado;
- registro mínimo/máximo;
- confiança;
- regra `do_not_force`;
- fontes.

Isso permite tratar linguagem de 2007, 2018 e 2026 de forma diferente sem transformar o resultado em coleção de bordões.

## Idioleto

`scripts/voice_profile.py` observa características como:
- comprimento/variação de frases;
- pontuação;
- abreviações;
- estrangeirismos;
- léxico recorrente;
- estrutura de parágrafos.

Ele declara explicitamente `infer_identity: false`.

## Métricas

VozNativa evita "AI probability". As dimensões futuras são operacionais:

- `mechanicality`
- `formulaicity`
- `voice_drift`
- `regional_overfit`
- `register_mismatch`
- `semantic_loss`

Elas descrevem comportamento do framework, não autoria.

## Pesquisa

O design inicial estudou:
- `blader/humanizer`;
- `mackswendhell/humanizer-pt-br`;
- `opaulomarcondes/humanizador-pt`;
- `gabrielkashimarki/humanizer-ptbr`;
- `fabricioctelles/skills` (`humanizar`);
- ALiB;
- NURC;
- Corpus Carolina / USP;
- Projeto SP2010 / USP;
- CORAA / TaRSila;
- C-ORAL-BRASIL / UFMG.

VozNativa deve manter taxonomia e implementação próprias. Material externo só entra após revisão de licença/atribuição.

## Rodando a baseline

```bash
python scripts/analyze.py texto.txt
python scripts/semantic_guard.py original.txt candidata.txt
python scripts/voice_profile.py amostra1.txt amostra2.txt
python scripts/region_consistency.py texto.txt
python scripts/validate_package.py
python -m unittest discover -s evals -p "test_*.py"
```

## Estado

**v0.1.0 — foundation.**

A fundação está implementada e testável. Semantic Ledger profundo, Voice Drift real, packs regionais baseados em corpus, community packs, engine de rewrite e evals humanos continuam deliberadamente nas próximas versões.

Veja `ROADMAP.md`.

## Licença

A licença pública ainda não foi definida. Antes de tornar o repo público ou incorporar material de terceiros, revisar compatibilidade e atribuição.
