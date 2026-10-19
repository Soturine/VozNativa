# Idioleto

## Definição operacional

No VozNativa, idioleto é o conjunto de **tendências observáveis e recorrentes** na escrita de um autor em amostras autorizadas.

O objetivo não é identificar a pessoa. É preservar características de escrita relevantes para a tarefa atual.

## Escopo

O perfil pode observar:

### Ritmo
- comprimento mediano de sentença;
- variância;
- fragmentos;
- alternância curta/longa;
- tamanho dos parágrafos.

### Pontuação
- vírgulas;
- ponto e vírgula;
- dois-pontos;
- travessões;
- reticências;
- exclamações;
- interrogações;
- parênteses.

### Léxico
- palavras recorrentes;
- termos técnicos;
- estrangeirismos;
- abreviações;
- contrações;
- intensificadores;
- formas evitadas quando houver amostra suficiente.

### Discurso
- aberturas;
- conectores;
- formas de discordar;
- formas de explicar;
- preferência por exemplo antes/depois da regra;
- uso de perguntas;
- conclusões.

### Formatação
- Markdown;
- listas;
- headings;
- emoji;
- caixa alta;
- blocos curtos/longos.

### Canal
O mesmo autor pode ter perfis diferentes em:
- WhatsApp;
- e-mail;
- GitHub/docs;
- artigo/TCC;
- LinkedIn;
- chat corporativo.

Não colapsar tudo em uma média única.

## Quantidade de amostra

Pouca amostra -> perfil conservador.

Heurística de produto:
- 1 trecho curto: apenas sinais explícitos;
- 3–5 textos: tendências provisórias;
- múltiplos textos no mesmo canal: perfil por canal;
- histórico amplo: somente usar se autorizado e com provenance.

Esses limites são heurísticos e precisam de eval/calibração.

## Confiança por feature

Cada observação deveria conter:
```yaml
feature: abbreviations.nn
observed: true
count: 18
sample_count: 6
channels:
  - whatsapp
confidence: 0.84
stability: medium
```

Não tratar uma ocorrência como hábito.

## Precedência

A ordem canônica está em `references/VOICE_STACK.md` (implementada por `voznativa contract`). O ponto que importa para idioleto: a amostra do autor no mesmo canal vem logo depois da preservação semântica, das convenções obrigatórias do gênero e da instrução explícita, e acima do perfil geral do autor.

## Voice drift

Em textos longos, comparar janelas:
- ritmo;
- formalidade;
- pontuação;
- léxico;
- estrutura;
- marcadores discursivos.

Uma mudança pode ser legítima por seção/gênero. O drift só importa quando não é explicado pelo conteúdo.

## Negative evidence

"Palavras evitadas" exigem muito mais evidência do que palavras usadas. Ausência em poucas amostras não significa preferência negativa.

## Privacidade e inferência

Permitido:
- "usa frases curtas";
- "abrevia 'não' como 'nn' nesta amostra";
- "usa inglês técnico";
- "quase não usa emoji neste canal".

Não permitido como inferência do Voice Profile:
- idade;
- gênero;
- etnia;
- classe social;
- localização;
- religião;
- saúde;
- personalidade;
- diagnóstico;
- orientação política.

## Evals

O perfil deve ser testado com:
- amostras do mesmo autor em canais diferentes;
- duas pessoas com registro parecido;
- pouca amostra;
- amostra contraditória;
- mudança temporal;
- texto deliberadamente formal do mesmo autor;
- caso em que a melhor decisão é não aplicar um hábito observado.
