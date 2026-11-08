# Regional Evidence (v0.5.0)

Regionalidade sustentada por evidência, não por listas de estereótipos. Decisão de arquitetura: `docs/architecture/adr/ADR-0001-regional-evidence-packs.md`. Código: `voznativa/regional.py`. Packs: `voznativa/data/regional_packs/`.

## Regras

1. **Abstenção é o padrão.** Sem região pedida explicitamente, sem pack que cubra a região, fora dos contextos que a evidência cobre, sem o referente no texto, ou num estado registrado como exceção: força efetiva 0 e o motivo vai no relatório.
2. **A região nunca é inferida** do texto nem do autor. Só vale a região que o pedido nomeia (`--region`).
3. **A voz observada do autor vence.** Uma forma que o Voice Profile registra nas amostras do autor (`regional_form.<forma>`, só contagem) é mantida; o pack não sugere outra.
4. **Pack não insere marcador.** Ele diz: quais formas do mesmo referente pertencem ao escopo, qual troca pode mudar o referente, e qual forma pode ser oferecida como opção para leitores da região pedida.
5. **Força limitada**: pack não calibrado ≤ 0,25; a efetiva é o mínimo entre a pedida e a do pack.
6. **Nada de texto bruto de corpus** no repositório: o pack guarda formas, contagens, proporções e citações.

## Contrato `voznativa.regional_evidence_pack` (schema_version 1)

| Campo | Conteúdo | Validação (`regional.validate_pack`) |
|---|---|---|
| `id`, `version`, `status` | identificador estável; versão do pack; `pilot` / `experimental` / `calibrated` | obrigatórios; status do conjunto fechado |
| `human_reviewed` | se uma pessoa (não o desenvolvedor) revisou | obrigatório |
| `scope` | país, macrorregião, estados (UF), localidades, capital/interior | UFs válidas |
| `epoch` | ano inicial e final da coleta; nota sobre uso atual | anos inteiros |
| `modality`, `data_type`, `genre_channel`, `informants` | fala/escrita; tipo de dado; gênero e canal da coleta; perfil dos informantes | `modality` obrigatório |
| `sources[]` | citação, URL, tipo (primária/secundária), data de acesso | citação e URL em toda fonte |
| `license` | o que o pack reproduz e sob quais termos da fonte | obrigatório |
| `features[]` | `referent`, `forms` (forma, contagem, proporção), `total_answers`, `preferred_in_scope`, `exceptions`, `contexts_legitimate`, `contexts_not`, `confusions` (pares que mudam o referente), `confidence`, `evidence_level`, `limitations` | contagens somam `total_answers`; confusões só com formas listadas |
| `activation` | `requires_explicit_region` e `author_form_wins` (ambos obrigatoriamente verdadeiros), `requires_referent_in_text`, `max_strength`, `allowed_genres` | força ≤ 0,25 se não calibrado |

Um pack inválido não é carregado: `load_packs` levanta erro em vez de usar dados parciais.

## Integração

| Camada | O que faz com o pack |
|---|---|
| Context Router | `targets.region` vem só do pedido (`--region`, `--region-strength`) |
| Voice Contract | `regional_strength.effective` = força da ativação; `regional` com status, motivos e decisões; avisos quando fica 0 |
| Voice Profile | hábito `regional_form.<forma>` (contagem e suporte, sem texto) para formas dos packs nas amostras |
| Rewrite Planner | bloco `regional` no plano; no prompt, "manter X" ou "opcional: Y pode substituir X" com o motivo |
| Semantic Ledger (`compare`) | `regional_referent_changed` (major) quando uma troca está nas `confusions` de um pack (ex.: macaxeira → mandioca) |
| Regional Overfit / Dialect Mixing | `regional_form_introduced` (major) quando a candidata acrescenta forma de pack que a fonte não tinha e a ativação não ofereceu; o guard antigo de marcadores (E0) continua para "uai uai uai" |
| CLI | `voznativa regional packs`; `voznativa regional check TEXTO --region norte [--profile perfil.json]` |
| Agent Skill | `SKILL.md`: pedir a região explicitamente; relatar a abstenção; nunca inventar traço regional |

## Piloto: `br-norte-lex-mandioca` (0.1.0, pilot, sem revisão humana)

Um referente (a mandioca de mesa, QSL 50 do ALiB), na Região Norte, a partir de Romano (2020), análise publicada dos dados do ALiB: 24 localidades, 96 informantes com até o ensino fundamental, duas faixas etárias, coleta 2001–2013. Respostas: macaxeira 92/110 (83,6%), mandioca 13 (11,8%), aipim 5 (4,5%). Tocantins diverge (mandioca predomina; aipim 15,38%) e é tratado como exceção. Na região, "mandioca" é sobretudo a mandioca brava (QSL 51), por isso macaxeira/aipim → mandioca é marcado como possível mudança de referente.

Efeito real: em reescrita, o pack **protege** (mantém a forma do autor, bloqueia troca que muda o referente, bloqueia forma regional não pedida) e, com região pedida e uma forma de outra região no texto ("aipim"), **oferece** "macaxeira" como opção de força baixa. Sem o pedido, nada muda.

Limitações: fonte secundária; fala de inquérito, não escrita; um único referente; sem contraste quantitativo com outras regiões nesta fonte; confiança baixa; nenhuma avaliação humana regional (CP7 prepara o instrumento). A troca com ajuste de concordância ("aipim frito" → "macaxeira frita") ainda gera `possible_addition` (revisão) em frases curtas.

## Registro de fontes (consultado em 2026-11-05)

"Não verificado" = o campo não foi confirmado numa fonte oficial nesta rodada.

| Fonte | Instituição | URL | Versão / período | Variedade e dado | Gênero / canal | Localização e amostragem | Licença / condições de uso | Confiança para regionalidade | Limitações | Decisão |
|---|---|---|---|---|---|---|---|---|---|---|
| ALiB | UFBA e rede de universidades (Comitê Nacional) | https://alib.ufba.br/ (certificado TLS inválido na consulta) | Atlas v. 1–2 (2014); coleta 2001–2013 | PB falado; fonético, semântico-lexical, morfossintático | inquérito dialetal (questionários 2001) | 250 pontos (capitais e interior); informantes nativos, 2 sexos, 2 faixas etárias, escolaridade fundamental (+ superior nas capitais) | publicação científica; dados primários não abertos para download verificado | **alta** para léxico diatópico com metadados e contraste | fala de inquérito; não mede escrita nem uso atual | **usada** (via análise publicada) no piloto |
| SP2010 | GESOL / FFLCH-USP | https://projetosp2010.fflch.usp.br/corpus | gravações 2012–2013 | fala paulistana | entrevista sociolinguística | 60 falantes, 12 perfis (sexo; 20–34, 35–59, 60+; até médio / superior), zonas da cidade | gratuito para pesquisa mediante cadastro e pedido por e-mail; licença não declarada | média para **cidade de São Paulo** apenas | não representa o estado; sem pack até haver achado publicado com contraste | monitorar |
| C-ORAL-BRASIL | UFMG | https://periodicos.ufmg.br/index.php/relin/article/view/28683 | não verificado nesta rodada | fala espontânea, sobretudo mineira | diálogos e monólogos espontâneos | Minas Gerais (BH) principalmente | CC BY-NC-SA 4.0 reportada (arXiv 2110.15731; `docs/policy/LICENSING.md`) | baixa como fonte regional isolada (pouco contraste) | foco em oralidade e prosódia | oralidade, não regionalidade |
| ALIP (Iboruna) | UNESP / IBILCE | alip.ibilce.unesp.br (citado; não acessado) | coleta 2004–2005 (CORAA, arXiv 2110.15731) | fala do interior paulista (região de São José do Rio Preto) | entrevistas e diálogos | noroeste paulista; número de cidades e estratificação não verificados | uso acadêmico com cadastro; sem licença definida (CORAA) | média para o noroeste paulista | sem licença clara para derivados; não acessado | candidato a pack futuro só com achado publicado e termos verificados |
| PHPB | rede nacional (coordenação histórica USP) | equipes regionais (ex.: https://phpp.fflch.usp.br/) | séc. XVIII–XX | PB escrito histórico | cartas, documentos | por estado/equipe | não verificado | **não aplicável** a regionalidade contemporânea | diacrônico | rejeitado para packs atuais |
| Corpus Carolina | C4AI / USP | https://sites.usp.br/corpuscarolina/ | 1.3 Ada; 2.0.1 Bea | PB escrito contemporâneo, vários gêneros | web, wiki, jurídico etc. | sem metadado geográfico confiável por documento | conflito de licença entre portal (CC BY-NC-SA) e card (CC BY); licença por documento (`docs/policy/LICENSING.md`) | **nenhuma** para regionalidade | sem localização | rejeitado como fonte regional (útil para gênero e frequência) |
| NURC | UFRJ e outras capitais | https://nurcrj.letras.ufrj.br/ | anos 1970 e 1990 | fala culta urbana | elocuções formais, diálogos | 5 capitais; falantes com nível superior | por acervo; não verificado | média para fala culta de capitais, datada | época | monitorar |

Fontes aceitas nesta rodada: só os achados publicados do ALiB, por terem escopo, época, perfil de informante e contraste interno documentados. As demais ficam registradas com o motivo.
