# Estado de execução da v0.9.0 (retomada de sessão)

Retome por este arquivo **e** pelo Git (`git fetch --prune; git log --oneline origin/dev/v0.9.0 -20`). Se divergirem, o Git vence e este arquivo é corrigido.

- Branch: `dev/v0.9.0`, criada de `main` = `17d1f10` (tag `v0.8.1`) em 2026-11-18.
- Plano e critérios de release: [`PLAN.md`](PLAN.md). Gaps: [`GAP_REGISTER.md`](GAP_REGISTER.md). Rastreabilidade: [`TRACEABILITY.md`](TRACEABILITY.md).
- Política: commit por CP; antes de cada push, `scripts/privacy_gate.py` sobre os commits não publicados, lido como comando separado; nenhuma Action até o CP9.

## Checkpoints

| CP | Título | Estado | Commit | Verificação |
|---|---|---|---|---|
| CP0 | Estado, baseline, gate de privacidade, plano | concluído | `ac5c4de` | baseline abaixo; gate de privacidade com 8 testes (o primeiro push foi bloqueado pelo próprio gate: valores plantados no teste; e o gate lia só o diff líquido, corrigido para o patch de cada commit antes do push); critérios R1–R10 congelados |
| CP1 | Instalação, `doctor`, configuração, `--dry-run`, docs | concluído | `bdb23c0` | primeiro uso pelo wheel em venv limpo em CPython 3.11.18 e 3.12.6 (Windows); instalação pela tag; gates locais + pacote PASS; Linux BLOCKED (Docker sem resposta) |
| CP2 | Providers, relação gerador × juiz, hosts | concluído | `0118396` | provider real ponta a ponta (US$ 0,049); autojulgamento com linhas diferentes corrigido e provado com chamadas reais (GAP-24, P1); sessão agent-led real do Claude Code (US$ 0,21); adapter HTTP testado contra servidor local; modelo local real NOT_RUN (permissão); Codex/Gemini NOT_RUN; Emulate BLOCKED. [`INTEGRATIONS.md`](INTEGRATIONS.md) |
| CP3 | Consistência editorial em documento longo, método do teste de tempo | concluído | `2d96c27` | guard `style_convergence` e memória editorial: caso real do dogfood sinalizado (3 → 11), controle real quieto; 4 execuções reais (US$ 0,65), efeito da memória inconclusivo com n = 1; R9 sem regressão (17.600 palavras 4,95 s CPU); v4 22/22, v5 36/36, predicados 17/20 e 1/18. [`EDITORIAL.md`](EDITORIAL.md) |
| CP4 | Robustez semântica, diagnóstico gramatical, termos técnicos, siglas | concluído | `e5b134c` (conjuntos congelados antes das regras), `f81cbf1` | development 4/31 → 31/31 e 7/20 → 4/20; holdout (uma vez) 4/18 → 18/18 e 1/10 → 2/10; diagnóstico 0 → 11/11 e 6/6 sem falso alarme; predicados 19/20 e 1/18; v4 22/22, v5 36/36; testes de defeito falham em `17d1f10`. Suítes congeladas pegaram 4 falsos vermelhos de uma versão intermediária (moeda "reais", "em produção", "voltou ao"), corrigidos antes do commit; o gate de privacidade bloqueou um exemplo de comentário que coincidia com um documento privado, removido antes do push. [`SEMANTICS.md`](SEMANTICS.md) |
| CP5 | DOCX, PDF, normas | concluído | `47504a5` | DOCX: subconjunto editável, cópia nova, `check` parte a parte; real: 27/27 partes idênticas na ida e volta, edição aberta no python-docx. PDF: extração rastreável e notas (extra `pypdf`). Renderização no Word e piloto de norma: NOT_RUN. [`DOCUMENTS.md`](DOCUMENTS.md) |
| CP6 | Packs, contribuição, corpora | concluído | ver `git log` | envelope v1 e validador; packs externos com licença e proveniência; exemplo executável com efeito no plano; recusas (gate, código, regex, caminho, licença, id, tag YAML, tamanho, regional externo, id embutido); 13 corpora reverificados ao vivo, nenhum estado mudou. [`../../guide/PACKS.md`](../../guide/PACKS.md) |

## Baseline (CP0)

Revisão `17d1f10` (tag `v0.8.1`), worktree limpa separada, Windows 10, CPython 3.12.6, 2026-11-18.

| Instrumento | Resultado |
|---|---|
| `qualify.py --scope release` (324 s) | validador, unittest (933: 931 PASS, 2 skips com motivo; 138 s), semântica dev 77/77, holdouts safety e strict, decisão 28/30, roteador 15/16, códigos de saída, gatilhos da CI, pacote (sdist → wheel → venv → smoke → suíte contra o wheel): **PASS**. `ci:github-actions` PASS ao vivo: run #128 (43893178929), `workflow_dispatch`, `17d1f10`, 8/8, relação `same`. Veredito INCOMPLETE (exit 3) só por `review:pty` (POSIX), holdout independente e revisão cega humana (NOT_RUN) |
| `ptbr-bench-v4` | 22/22 |
| `ptbr-bench-v5` | 36/36 (Wilson 95%: 0,904–1,0) |
| amostra de predicados | 17/20 riscos, 1/18 falsos alarmes |
| `scripts/perf_compare.py` (5 repetições) | 2.200 palavras: CPU mín. 0,41 s; 8.800: 2,09 s; 17.600: 5,84 s; razão 800/100 blocos = 14,4× |
| Reprodução sintética de gaps | ver [`GAP_REGISTER.md`](GAP_REGISTER.md) (V09-GAP-01 a 08) |

Ambiente disponível: CPython 3.12.6 e 3.11.18 (gerenciado pelo uv, fora do `py`), Docker 28.5.1, Claude Code 2.1.317, PyMuPDF e pypdf instalados no Python do usuário (não são dependências obrigatórias do pacote). Ausentes: Codex, Gemini CLI, Ollama, `EMULATE_API_KEY`. Assertiva 0.10.1 e Derivanta Engine 0.1.0 em clones locais.

## Regras desta rodada

- **Commits:** sem `Co-authored-by` nem trailer de IA; identidade local (`git config --local`): Rafael Souza, noreply Soturine. Sem force push, sem `reset --hard`.
- **Gate antes do commit:** `python scripts/qualify.py --scope local --only validator,unittest,semantic:dev,semantic:holdouts:safety,semantic:holdouts:strict,decision:regression,router:regression,cli:exit-codes,ci:workflow-triggers,package:sdist-wheel-smoke --out <scratch>/q.json` (o gate de pacote monta o sdist só com arquivos rastreados: `git add` antes).
- **Gate antes do push:** `python scripts/privacy_gate.py --base origin/<branch> --private <doc> ... --terms-file <fora do repo>`; ler o veredito; só então `git push` em comando separado.
- **Benches:** numa worktree descartável do commit (eles gravam em `benchmarks/runs/`).
- **Holdout do CP4:** já rodado uma vez; resultado oficial registrado em [`SEMANTICS.md`](SEMANTICS.md); não ajustar regras por ele.
- **Dados privados:** documentos e saídas dos dogfoods ficam fora do repositório; fixtures sintéticas de outro domínio.
- **Edição de arquivos:** nada de heredoc com barra invertida; usar a ferramenta de edição ou script em arquivo.

## Bloqueios conhecidos

- Execução de binários baixados (servidor de modelo local) negada pelo controle de permissões da sessão no CP2; os arquivos estão fora do repositório, prontos para o mantenedor rodar.
- Docker Desktop parou de responder no CP1 (`docker images` sem resposta em 60 s); não reiniciado (aplicativo do usuário). Linux local: nova tentativa no CP9; substituto previsto em R2 é a CI.

## Próximo passo

CP7.
