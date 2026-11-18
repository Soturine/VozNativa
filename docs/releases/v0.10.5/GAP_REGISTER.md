# Registro de gaps da v0.10.5

| ID | Gap | Instrumento que achou | Reprodução | Sev. | Estado |
|---|---|---|---|---|---|
| V105-GAP-01 | Agente com a Skill pula o fluxo: ativa a Skill, não roda `route`/`diagnose`/`rewrite-prompt`, escreve a candidata direto e só depois chama `compare` | sessão real de host (piloto, Claude Code 2.1.317 + Haiku) | `docs/releases/v0.10.5/SKILL_LIVE_DOGFOOD.md`, piloto 1 | P1 | OPEN |
| V105-GAP-02 | `SKILL.md` não menciona contexto aberto (`--attr`, `context`) nem conhecimento (`knowledge`): as capacidades da v0.10 não chegam a quem usa a Skill | leitura + piloto | `SKILL.md` em `v0.10.0` | P2 | OPEN |
| V105-GAP-03 | `EXECUTION_STATE.md` da v0.10 sem a linha da CI final; `EVIDENCE_PATHS` não lista os registros da v0.10 | relatório final da v0.10 | `scripts/ci_evidence.py` | P3 | OPEN |
| V105-GAP-04 | Quantificador `{2,60}` trocado por `{2,63}` no Watcher só para não coincidir com um número de documento privado no gate | auditoria pedida | `voznativa/watcher.py` | P3 | OPEN |
| V105-HARNESS-01 | Harness de sessão sem a ferramenta `Edit`: o agente não pôde corrigir a candidata | piloto | corrigido antes da campanha; não é defeito do produto | — | FIXED (harness) |
