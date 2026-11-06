# Registro de descobertas da v0.7.0

Cada item: origem, evidência reproduzível, severidade, decisão (correção obrigatória / melhoria de baixo risco / pesquisa / fora do escopo) e estado. Achados de ferramentas de dogfood ficam em `docs/V07_DOGFOOD.md` (`VN07-DF-###`).

| ID | Origem | Evidência | Sev. | Decisão | Estado |
|---|---|---|---|---|---|
| VN07-DISC-001 | auditoria CP0 de `scripts/qualify.py` | `classify_ci` dá PASS a partir de um registro em `evals/qualification/external.json`; nada confere o run no GitHub. Commitar o registro cria um HEAD novo, que deixa de bater com o run | P2 | correção obrigatória (CP1) | aberto |
| VN07-DISC-002 | auditoria CP0 | qualificação local no Windows nunca chega a PASS: `review:pty` é obrigatório no escopo local e NOT_RUN fora de POSIX. Correto como regra (não é PASS), mas o veredito local do Windows é sempre INCOMPLETE; o fechamento precisa de WSL | P3 | registrar; manter a regra | registrado |
| VN07-DISC-003 | memória do agente × `gh run list` | registro anterior dizia "Actions bloqueado por cobrança"; `gh` mostra runs executados #107–#123 em 2026-11-05. O estado de cobrança atual é desconhecido até o disparo do CP16 | P3 | o CP16 registra o que de fato acontecer | aberto |
| VN07-DISC-004 | pesquisa CP0 (API GitHub, README/LICENSE lidos 2026-11-06) | UD Portuguese-GSD (CC BY-SA 4.0, blog/notícia), PetroGold (CC BY-SA 4.0, acadêmico), PUD (CC BY-SA 3.0, notícia/wiki), DANTEStocks (CC BY 4.0, social) têm licença aberta e CoNLL-U; CINTIL é CC BY-NC-ND 4.0 e PT-PT | — | integrar os quatro no CP3; CINTIL só catálogo | aberto |
