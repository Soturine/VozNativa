# Política de contribuição de dados linguísticos

Vale para packs de comunidade, packs regionais, listas de padrões, léxicos e classes semânticas (`voznativa/data/`). Contrato técnico: [`../guide/PACKS.md`](../guide/PACKS.md). Licenças de terceiros: [`LICENSING.md`](LICENSING.md).

## O que toda contribuição traz

| Item | Exigência |
|---|---|
| **Fonte** | de onde vem cada forma ou fato: corpus, atlas, artigo, documentação de comunidade, ou observação do autor declarada como tal (nível E0). Corpus citado pelo Corpus Registry (`voznativa corpus list`), com o estado que ele tem lá |
| **Licença** | a da contribuição (SPDX) e a da fonte. Texto de fonte com licença NC, ND, por documento ou desconhecida **não entra**: só fatos, contagens e citações (`proprietary-facts-only`) |
| **Período** | quando a forma foi observada; gíria e meme são temporais e dizem isso |
| **Região ou contexto** | onde a forma vale, com a abrangência da fonte (uma capital não representa um estado) |
| **Evidência** | nível E0–E4 conforme [`../evidence/CORPUS_AND_EVIDENCE_STRATEGY.md`](../evidence/CORPUS_AND_EVIDENCE_STRATEGY.md); pack não-rascunho exige E2 ou mais e fontes |
| **Teste** | um caso positivo (a forma é reconhecida no contexto) e um controle (fora do contexto, nada muda) em `evals/` |
| **Revisão** | `voznativa packs validate` limpo e revisão de outra pessoa antes do merge; `human_reviewed` só com revisão real |

## O que não aceitamos

- **Estereótipo.** Uma forma atestada numa região não vira marca de identidade de quem é de lá. Packs nunca são ativados por inferência a partir do texto ou do autor: só por pedido explícito (`--region`, `--community`).
- **Substituir o idioleto.** A forma que o autor já usa vence a do pack.
- **Gerar o que não foi atestado.** Pack rascunho só preserva; nenhuma contribuição liga geração sem evidência E2+.
- **Mexer nos gates.** Severidade, proteção, regras de comparação e código não entram em dado linguístico; o envelope recusa.
- **Texto de corpus no repositório.** Nem trechos curtos de corpora sem licença de redistribuição; nem textos de pessoas que não autorizaram.
- **Dados pessoais.** Nomes, contatos, documentos ou textos privados, mesmo como exemplo; use exemplos sintéticos de outro domínio.

## Como contribuir

1. Escreva o pack em `voznativa/data/community_packs/<id>.yml` (ou proponha um regional por issue antes, com a fonte).
2. `voznativa packs validate <arquivo>` e os testes (`python -m unittest discover -s evals`).
3. Abra o PR dizendo fonte, licença, período, região/contexto, nível de evidência e o que foi revisado por quem.
