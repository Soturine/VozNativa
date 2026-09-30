# VozNativa

> Motor de voz escrita para português brasileiro: humanização contextual, preservação semântica, variação regional responsável e modelagem de idioleto.

VozNativa não tenta responder à pergunta genérica "como um humano escreve?". O objetivo é responder a uma pergunta mais útil:

> **Como esta pessoa escreveria este conteúdo, neste canal, para este público, sem perder fatos, intenção ou registro?**

O projeto nasce como uma Agent Skill PT-BR, mas a arquitetura foi desenhada para evoluir para um **Brazilian Portuguese Voice Engine** reutilizável por agentes, CLIs e pipelines de escrita.

## Por que existe

Humanizers tradicionais funcionam principalmente como catálogos de padrões: detectam expressões associadas a texto mecânico e pedem ao LLM que reescreva. Isso ajuda, mas cria alguns problemas:

- uma blacklist de palavras pode apagar marcas legítimas do autor;
- naturalidade pode vir às custas de fatos, números, modalidade ou termos técnicos;
- "português brasileiro" costuma ser tratado como um único registro;
- regionalidade vira caricatura quando é reduzida a meia dúzia de gírias;
- uma voz pessoal não é a mesma coisa que um dialeto, um sotaque ou um gênero textual;
- métricas estilísticas não provam autoria humana ou artificial.

VozNativa separa esses problemas em camadas independentes e verificáveis.

## Princípios

1. **Significado antes de estilo.** Nomes, números, datas, citações, código, causalidade, modalidade e afirmações protegidas não podem mudar silenciosamente.
2. **Voz antes de "humanidade".** A amostra do autor tem precedência sobre defaults genéricos.
3. **Contexto antes de regra.** Travessão, conectivo formal, repetição ou gíria não são erros isoladamente.
4. **Regionalidade sem caricatura.** Região influencia distribuição de escolhas linguísticas; não injeta bordões obrigatórios.
5. **Observação não é identidade.** O sistema pode observar "usa vc" ou "mistura inglês técnico"; não deve inferir idade, gênero, origem ou personalidade sem base explícita.
6. **Código para o determinístico.** Contagens, spans protegidos, comparação de invariantes e métricas simples devem ser executadas por scripts, não "estimadas" pelo modelo.
7. **LLM para o semântico.** Intenção, tom, ironia, registro, coerência e reescrita ficam na camada generativa.
8. **Sem promessa de burlar detectores.** VozNativa melhora escrita; não fornece probabilidade de autoria por IA nem promete evasão de detector.
9. **Progressive disclosure.** `SKILL.md` roteia o trabalho; detalhes vivem em `references/`, scripts e evals.
10. **Evidência e regressão.** Mudança de regra precisa sobreviver a casos factuais, de voz, de falso positivo, de gênero e de regionalidade.

## Arquitetura

```text
texto
  |
  v
Context Router
  |-- genero
  |-- canal
  |-- objetivo
  |-- publico
  v
Semantic Ledger / Fact Lock
  v
Deterministic Analyzer
  v
Voice Stack
  |-- locale
  |-- registro
  |-- genero
  |-- comunidade
  |-- regionalidade
  |-- temporalidade
  '-- idioleto
  v
Rewrite Engine
  v
Validation Gates
  |-- semantic preservation
  |-- register consistency
  |-- regional overfit
  |-- dialect mixing
  '-- voice drift
  v
saida
```

A precedência padrão de voz é:

```text
amostras do autor
    >
canal e contexto
    >
comunidade/socioleto
    >
regionalidade
    >
default PT-BR
```

## Estrutura do repositório

```text
VozNativa/
├── SKILL.md
├── README.md
├── ROADMAP.md
├── CHANGELOG.md
├── pyproject.toml
├── docs/
├── references/
│   ├── patterns/
│   ├── genres/
│   ├── regions/
│   ├── communities/
│   ├── slang/
│   └── voice/
├── scripts/
├── evals/
└── .github/workflows/
```

## Modos previstos

- **rewrite**: reescreve um texto existente preservando o Semantic Ledger.
- **audit**: diagnostica mecanicidade, perda de voz, desalinhamento de registro e riscos de reescrita.
- **create**: escreve do zero usando somente material fornecido/verificado e o Voice Stack.
- **profile**: extrai características de voz de amostras fornecidas pelo autor.
- **compare**: compara original e candidata em significado, voz e registro.

## O que VozNativa mede

Não existe `AI probability`. O projeto usa dimensões operacionais:

- `mechanicality`
- `formulaicity`
- `voice_drift`
- `regional_overfit`
- `register_mismatch`
- `semantic_loss`

Esses valores descrevem sinais dentro do próprio framework; não determinam quem escreveu o texto.

## Regionalidade e "sotaque escrito"

Sotaque, no sentido estrito, é fonético/fonológico. Em escrita, VozNativa modela sobretudo variação lexical, morfossintática, pragmático-discursiva, registro, marcadores conversacionais e ortografia estilizada quando ela já fizer parte da voz desejada.

Um pedido como "mineiro informal" não significa inserir `uai` ou `trem` em toda frase. O sistema deve usar evidência, intensidade configurável e um **Regional Overfit Guard**.

## Idioleto

Dialeto é compartilhado por um grupo; **idioleto** descreve padrões particulares de uma pessoa. Amostras autorizadas podem alimentar um Voice Profile com características como:

- comprimento e variação de frases;
- tamanho típico de parágrafo;
- pontuação;
- conectores;
- abreviações;
- contrações;
- estrangeirismos;
- palavras recorrentes;
- palavras evitadas;
- estilo de capitalização;
- emojis;
- autocorreções;
- ritmo e abertura/fechamento de parágrafos.

O perfil descreve padrões linguísticos. Ele não deve inferir atributos pessoais.

## Fontes e projetos estudados

O design inicial foi informado por uma auditoria de projetos existentes, sem tornar nenhum deles dependência ou fonte única de verdade:

- `blader/humanizer`
- `mackswendhell/humanizer-pt-br`
- `opaulomarcondes/humanizador-pt`
- `gabrielkashimarki/humanizer-ptbr`
- `fabricioctelles/skills` (`humanizar`)
- Projeto Atlas Linguístico do Brasil (ALiB)
- Projeto NURC
- Corpus Carolina / USP

Veja `docs/RESEARCH.md` para princípios de uso, atribuição e limites.

## Estado

**v0.1.0 — foundation.** A baseline inclui especificação da skill, arquitetura, schemas de voz/região/gíria, analisadores determinísticos iniciais, Fact Guard, guards de regionalidade e suíte inicial de evals.

O roadmap separa claramente o que já é implementado do que ainda depende de corpus, calibração ou validação humana.

## Uso inicial

Os scripts foram mantidos sem dependências externas na fundação:

```bash
python scripts/analyze.py caminho/para/texto.txt
python scripts/protect_spans.py caminho/para/texto.txt
python scripts/voice_profile.py sample1.txt sample2.txt
python scripts/fact_guard.py original.txt candidata.txt
python scripts/region_consistency.py texto.txt
```

Para validar o pacote:

```bash
python scripts/validate_package.py
python -m unittest discover -s evals -p "test_*.py"
```

## Licença

A licença pública do VozNativa ainda não foi definida. Antes de abrir o repositório ou incorporar material externo, revisar as licenças e condições de atribuição de cada fonte. O projeto deve preferir regras e implementação próprias em vez de copiar conteúdo de terceiros.
