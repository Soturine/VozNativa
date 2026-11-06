# CP12 — garantia e dogfood da v0.6 (2026-11-05)

Ferramentas usadas:
- Derivanta Engine 0.1.0@17fa564;
- Assertiva 0.10.1;
- Cosmic Ray, rodado diretamente: a opção `--mutate-tests` da Assertiva continua com o problema AXF-VN-01, cuja correção está no PR #8, aberto e não integrado.

O Engine tem o PR #3 aberto. Nenhum registro novo foi enviado aos repositórios das ferramentas.

## Derivanta Engine (`inspect --maintainability`, depois `compare`)

O Engine reportou 98 achados, todos INFO. São **candidatos**, não defeitos:
- 65 de complexidade (orientam refatoração);
- 31 de duplicação;
- 2 de definição sem referência.

Triagem:
- **Corrigido:** a escala de evidência E0–E4 estava duplicada em `temporal.py` e em `community.py`. Agora tem um dono só (`community` importa `EVIDENCE` e `GENERATION_MIN_EVIDENCE` de `temporal`). Sem ciclo de import, porque `temporal` não importa nada do pacote.
- **Mantido:** as outras duplicações são tabelas parecidas por coincidência, como listas de campos obrigatórios de esquemas diferentes ou casos de teste. A complexidade de validadores e de `segment` foi aceita: cada ramo corresponde a uma regra testada.
- **Comparação depois da correção:** 0 NEW, 97 PERSISTING, 1 ABSENT (a duplicação corrigida).

## Assertiva

| Modo | Revisão | Resultado |
|---|---|---|
| estático | `f5f2d30` + mudanças locais | sem execução; os limites são declarados pela própria ferramenta |
| `--execute` (cópia isolada) | `4035104` (árvore limpa) | unittest nativo: **PASS, 456 invocações**; wheel: build, install e import PASS; testes contra o wheel: NOT_RUN (não há adaptador) |

Achados:
- **`FALSE_GREEN_CANDIDATE` (médio): confirmado e corrigido.** Dois testes só faziam asserções sob condição:
  - `test_citation_only_sources_never_claim_verification` passaria vazio se não houvesse fonte do tipo citação;
  - `test_independent_claims_need_the_protocol_fields` não afirmava nada hoje, porque nenhuma suíte declara independência.

  O primeiro agora exige ao menos uma fonte de citação. O segundo aplica a regra também a uma declaração plantada, que precisa ser pega.
- **`UNCLASSIFIED_VERIFICATION` (info):** passos do CI que a ferramenta não classifica. Sem ação.

## Mutação (Cosmic Ray, diretamente)

Comando dos testes: `evals.test_temporal`, `evals.test_community_and_stuffing` e, depois, `evals.test_mutation_gaps_v06`. Números em `mutation-summary.json`.

| Módulo | Mutantes | Sobreviventes antes | Depois |
|---|---|---|---|
| `voznativa/stuffing.py` | 72 | 32 | **5** |
| `voznativa/temporal.py` | 701 | 264 (165 em linhas de assinatura, 99 em outras) | rodada 1: 236 (165 + 71); rodada 2: **198 (165 + 33)** |

- **Mutantes equivalentes:**
  - **Linhas de assinatura (165):** mutações em anotações de tipo (`str | None` → `str + None`), que nunca são avaliadas sob `from __future__ import annotations`.
  - **`stuffing.py` (os 5 restantes):**
    - em `compare`, a condição `!= "low"` já é implicada pela comparação de ordem que vem depois;
    - em `level`, o ramo médio só é alcançado com repetição ≤ 3, então `== 3` e `is 3` equivalem a `>= 3`.
- **Os 33 restantes em `temporal.py` não foram confirmados um a um como equivalentes.** Os inspecionados são de dois tipos:
  - `is` / `is not` no lugar de `==` / `!=` com inteiros pequenos ou strings internadas;
  - comparações de status com strings, em que nenhum status válido ordena antes de "active".

  Ficam como sobreviventes não triados, não como equivalentes provados.
- **Testes novos** (`evals/test_mutation_gaps_v06.py`):
  - fronteiras exatas de densidade e repetição;
  - densidade calculada e arredondamento;
  - queda de nível que não é stuffing;
  - época que termina no ano corrente;
  - limite de 548 dias e data ausente;
  - força negativa e arredondamento da força;
  - contagem das causas de abstenção;
  - formas repetidas;
  - cabeçalho do léxico, campo obrigatório e contagem 1;
  - erro de carga e metadados preservados;
  - E3 permite geração;
  - registro abaixo do máximo;
  - entrada datada.

## Controles negativos

Os controles negativos nesta rodada:
- **A mutação.** Cada mutante morto é uma quebra deliberada que a suíte pegou.
- **Os casos `expectedFailure`** de `evals/test_known_gaps_v06.py`. Se um gap for corrigido sem atualizar o teste, a suíte falha com "unexpected success".
