# Documentos: DOCX, PDF e normas (v0.9 CP5)

Os dois dogfoods da v0.8.1 converteram DOCX e PDF **fora** do produto. A v0.9 traz um subconjunto real, testado e com limites declarados. Nada aqui edita o arquivo original: toda saída é um arquivo novo, e escrever por cima do original ou de um arquivo existente é recusado.

## Representação intermediária

`voznativa.document_ir` (schema 1): fonte (formato, nome, sha256), elementos com id, tipo, texto, `editable` e o motivo de cada proteção; no DOCX, também o sha256 do XML de cada parágrafo e a lista de partes que não são tocadas. Headings entram no texto enviado ao motor como contexto (`## ...`); mudanças neles nunca são aplicadas.

## DOCX (`voznativa docx`, `rewrite ARQUIVO.docx --docx-out NOVO.docx`)

| Operação | O que faz |
|---|---|
| `docx extract` | parágrafos do corpo (inclui células de tabela) com tipo: título, parágrafo, item de lista, célula |
| `docx apply` | grava um arquivo novo com o texto dos parágrafos editados |
| `docx check` | compara original e cópia: mesmas partes, bytes iguais fora de `word/document.xml`, mesmos parágrafos, XML fora dos parágrafos idêntico, parágrafos protegidos idênticos, XML bem-formado |
| `rewrite X.docx --docx-out Y.docx` | os parágrafos editáveis passam pelo `rewrite --long-form` (mesmos gates, orçamento e proveniência); o resultado só é aplicado se todos os blocos voltarem; o relatório traz o `check` |

**Editável** é só o parágrafo cujas *runs* têm apenas texto e a mesma formatação. Hiperlink, campo, tabulação, quebra de linha, imagem, objeto, nota, equação, caixa de texto, marcador, alteração controlada, comentário, controle de conteúdo e formatação mista protegem o parágrafo, com o motivo. A reinjeção troca só o XML dos parágrafos editados (mantém as propriedades do parágrafo e a formatação da primeira *run*; o texto vira uma *run*) e copia todo o resto do pacote byte a byte. Nenhuma biblioteca de XML reserializa o documento: o `ElementTree` da biblioteca padrão renomeia prefixos de namespace, o que quebra `mc:Ignorable` e faz o Word acusar arquivo corrompido.

**Evidência:**

- `evals/test_v09_docx.py` (12 testes) com um DOCX sintético montado no teste: tipos e motivos de proteção, ida e volta sem edição com todas as partes byte-idênticas, edição que muda só o parágrafo alvo e preserva `mc:Ignorable` e o escape de `&`/`<`, formatação mantida, recusas (protegido, quebra de linha, id desconhecido, sobrescrever original ou arquivo existente, arquivo que não é DOCX), `check` reprovando parágrafo protegido alterado e XML fora dos parágrafos alterado, e o `rewrite` de ponta a ponta com o stub.
- **Documento real** (o DOCX do primeiro dogfood, privado, fora do repositório; só contagens): 485 parágrafos (202 de corpo, 252 células, 31 títulos), 76 protegidos com motivo; ida e volta sem edição: **27 de 27 partes byte-idênticas**; uma edição numa cópia: `check` PASS, só o parágrafo alvo mudou, XML fora dos parágrafos idêntico, a cópia abre no python-docx (233 parágrafos, 12 tabelas), original intacto; edição de parágrafo protegido recusada.

**Não suportado** (relatado, nunca alterado em silêncio): texto em cabeçalho, rodapé, nota de rodapé, comentário e caixa de texto; parágrafo com formatação mista ou elementos acima; controle de alterações (não implementado: só faria sentido com integridade completa das marcas de revisão). **Renderização no Word ou LibreOffice: NOT_RUN** (nenhum dos dois nesta máquina); a validação foi estrutural e por uma segunda biblioteca de leitura. O contêiner ZIP não é idêntico byte a byte (compressão e datas são regravadas); a igualdade é provada parte por parte.

## PDF (`voznativa pdf`, dependência opcional `pypdf`)

| Operação | O que faz | O que não faz |
|---|---|---|
| `pdf extract [--text]` | texto por página; parágrafos reconstruídos; hifenização de fim de linha desfeita só quando a palavra unida aparece no documento (senão fica, e é listada); ligaduras normalizadas; linhas com cara de equação ou código viram marcadores protegidos (`[[EQ-3-1]]`, `[[CODE-5-2]]`) com o texto original guardado | caixas por palavra, OCR, ordem de leitura confiável em várias colunas, matemática dentro da frase |
| `pdf annotate NOTAS.json --out NOVO.pdf` | uma nota por página num arquivo novo | destacar palavras, editar ou recompor o PDF |

Instalação: `python -m pip install "voznativa[pdf]"` (ou `pypdf` à parte). Sem o `pypdf`, os comandos saem com código 69 e dizem o que instalar. A CI instala o extra; a suíte contra o wheel instala só as dependências declaradas, então lá os testes de PDF são pulados com motivo.

**Evidência:** `evals/test_v09_pdf.py` (6 testes) com um PDF sintético montado só com objetos do `pypdf`: páginas, hifenização conhecida e desconhecida, equação e código protegidos, ligaduras, anotação numa cópia, recusas, dependência ausente. **PDF real** (o do segundo dogfood, privado; só contagens): 58 páginas, cerca de 12,6 mil palavras extraídas, 294 parágrafos, 152 linhas protegidas (113 de código, 39 de equação); uma nota adicionada numa cópia e lida de volta. A **precisão das proteções não foi medida** contra uma referência: proteger demais tira texto do modelo, mas não altera nada.

## Normas (CP5.4)

O Standards Registry, o Applicability Resolver e o Rubric Engine da v0.8 não mudaram. O piloto com a norma institucional usada nos dogfoods ficou **NOT_RUN**: não há fonte oficial conferida por URL e hash nesta rodada, e o texto da norma não pode ser copiado. O registro continua aceitando a ficha quando o mantenedor conferir a fonte ([`../v0.8/DOCUMENT_STANDARDS.md`](../v0.8/DOCUMENT_STANDARDS.md)).
