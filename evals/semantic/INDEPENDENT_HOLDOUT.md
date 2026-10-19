# Protocolo de holdout independente

Nenhuma suíte atual é validação independente: todas foram escritas por quem escreveu o motor (ver `MANIFEST.json`). Um holdout só conta como independente se seguir estes passos.

1. **Autor:** alguém que não escreveu e não leu `voznativa/` nem os casos existentes. Registre quem é (nome ou identificador) e a relação com o projeto.
2. **Conteúdo:** pares `original` / `candidate` em PT-BR, no formato de `cases.jsonl`, com `expect.status` escrito **antes** de rodar. Inclua reescritas boas (que não devem falhar) e ruins. Texto sintético ou com licença verificada; nada de corpus sem licença.
3. **Congelamento:** um commit contendo **só** o arquivo do holdout e a entrada em `MANIFEST.json` (`role: "independent_holdout"`, `independent: true`, `frozen: true`, `sha256`, `author`, `written_without_reading_engine: true`). Esse commit precede a primeira execução.
4. **Execução única:** `voznativa eval evals/semantic/<arquivo> --require-frozen`. Registre o resultado em `first_run` num commit separado, mesmo que seja ruim.
5. **Depois:** correções motivadas pelas falhas tornam o holdout contaminado; anote em `contaminated` e não reporte números posteriores como independentes.

O teste `evals/test_eval_provenance.py` recusa uma suíte marcada como independente sem esses campos. Ele não consegue provar quem escreveu o arquivo: a autenticidade depende do histórico do Git e da palavra do autor.
