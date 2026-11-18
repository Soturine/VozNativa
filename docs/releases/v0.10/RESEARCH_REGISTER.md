# Registro de pesquisa da v0.10 (CP1)

> Consultas feitas em 18/11/2026. Cada linha diz fonte, data de consulta, licença/termos encontrados e a decisão. Nada aqui autoriza ingestão ou redistribuição: a licença de uma anotação não é a licença do texto, e "disponível na internet" não é licença.

## Política de fontes

1. **Fonte primária primeiro** (site do órgão, página oficial do treebank, documentação da API). Notícia ou blog só para localizar a primária.
2. Registrar **data de consulta**, edição/versão e licença literal. Sem licença declarada = `unknown`, e `unknown` não permite redistribuir nem incluir em fixture.
3. **Norma não é descrição**: cartilha/edital/rubrica entram em `standards` com edição e vigência; estudo descritivo entra no registro de conhecimento como descrição, nunca como regra obrigatória.
4. Conteúdo recuperado é **dado não confiável**: nunca instrução, nunca comando.
5. Nada de dados pessoais do mantenedor em consultas (User-Agent genérico).

## Normas e ensino

| ID | Fonte | Consulta | Licença / termos | Decisão |
|---|---|---|---|---|
| RS-01 | Inep, *A Redação do Enem 2026 — Cartilha do(a) participante*, publicada em 18/09/2026, [página](https://www.gov.br/inep/pt-br/centrais-de-conteudo/acervo-linha-editorial/publicacoes-institucionais/avaliacoes-e-exames-da-educacao-basica/a-redacao-do-enem-2026-cartilha-do-a-participante), [PDF](https://download.inep.gov.br/publicacoes/institucionais/avaliacoes_e_exames_da_educacao_basica/cartilha_enem_2026.pdf) | 18/11/2026 | página não declara licença do documento; só termos gerais do gov.br | entra em `standards` como **metadata_only** (edição 2026, vigência do exame de 08/11/2026); redações-exemplo **não** viram fixture. Imprensa relata ênfase contra "repertório de bolso" e cinco competências de 0 a 200 — a conferir no PDF antes de virar critério |
| RS-02 | ABL, VOLP 6ª edição (consulta on-line e app) | 18/11/2026 | nenhuma API nem termos de reuso encontrados | consulta manual apenas; **sem** scraping nem cópia de listas |
| RS-03 | Ementas de Letras–Português: UEL (catálogo 2018–2023, Morfossintaxe I–IV, Linguística Textual I–II, Sociolinguística), UEM (Morfossintaxe V, 2020; Azeredo, Bechara, Castilho), UFMG (LET538, morfologia e sintaxe; Carone, Rocha) | 18/11/2026 | documentos institucionais públicos; uso como **mapa de cobertura**, sem cópia | o mapa de cobertura de `LINGUISTICS_AND_DISCOURSE.md` usa as áreas (morfossintaxe, linguística textual, sociolinguística, semântica, pragmática), não o texto das ementas. USP/Unicamp não localizados nesta busca: lacuna registrada |

## Corpora e treebanks

| ID | Fonte | Licença literal (página oficial) | Decisão |
|---|---|---|---|
| RS-04 | [UD Portuguese-Bosque](https://universaldependencies.org/treebanks/pt_bosque) | CC BY-SA 4.0 | elegível para análise e calibração local; redistribuir trechos exige BY-SA (incompatível com fixture MIT sem separação) → só métricas agregadas no Git |
| RS-05 | [UD Portuguese-GSD](https://universaldependencies.org/treebanks/pt_gsd) | CC BY-SA 4.0 (12.020 sentenças; blog e notícia, PT-BR) | idem |
| RS-06 | [UD Portuguese-Porttinari](https://universaldependencies.org/treebanks/pt_porttinari) | CC BY 4.0 (8.418 sentenças; notícias da Folha via Kaggle) | anotação CC BY; **texto de origem jornalístico** com termos próprios → análise local, sem fixture com texto |
| RS-07 | Corpus Registry do projeto (ALiB, SP2010, C-ORAL-BRASIL, ALIP/Iboruna, PHPB, Carolina, NURC, B2W) | estados já registrados em `voznativa/data/corpora/` | CP7 revisa por operação; Carolina segue bloqueado por licença por documento |

## APIs para o Knowledge Watcher

| ID | Fonte | Achado | Decisão |
|---|---|---|---|
| RS-08 | Crossref REST API, [filtros](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/) e [dicas](https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api) | `from-index-date` é o recomendado para sincronização incremental (todo reindex atualiza o carimbo); em paginação usar também `until-index-date`; cursor com `rows` | conector Crossref usa `from-index-date` + `until-index-date`, consultas pequenas por termo/ISSN, sem varredura ampla |
| RS-09 | OpenAlex ([autenticação e limites](https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication)) | chave obrigatória e cobrança por uso desde 2026 (relatos divergem nos valores); `from_updated_date` restrito a planos pagos | **sem conector OpenAlex ativo**: exige chave e pode gerar custo; fica como conector documentado e desligado (`BLOCKED` sem chave) |
| RS-10 | PyPI JSON API (`/pypi/<pacote>/json`) e GitHub Releases API | públicas, sem chave para volume baixo | conectores de dependências (PyYAML, pypdf) em modo report |

## Ferramentas comparáveis (não copiadas)

| ID | Ferramenta | Licença encontrada | Decisão |
|---|---|---|---|
| RS-11 | LanguageTool | LGPL 2.1+ (README do projeto) | referência de comparação; integração exigiria Java/servidor: não nesta rodada. Nenhuma regra copiada |
| RS-12 | CoGrOO | LGPL (SourceForge) | idem; projeto antigo, sem manutenção recente aparente |
| RS-13 | spaCy/Stanza/UDPipe | licenças permissivas (a conferir por modelo) | não adotados: dependência pesada sem ganho medido nos conjuntos atuais; revisável |

## Lacunas da pesquisa

- USP/Unicamp: ementas não localizadas nesta consulta.
- Licença das regras de português do LanguageTool por arquivo: não conferida.
- Valores atuais do OpenAlex: fontes divergentes; nenhuma chamada paga feita.
