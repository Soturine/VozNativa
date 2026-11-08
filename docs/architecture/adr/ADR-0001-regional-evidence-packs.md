# ADR-0001 — Regional Evidence Packs como única fonte de regionalidade

- Status: aceito (v0.5.0.dev0, 2026-11-05)
- Contexto: v0.1–v0.4 tinham um rascunho de pack (`assets/regional-pack.yml`) sem uso, uma lista E0 de marcadores (`analyzer_pt_br.json`) usada só para pegar exagero, e força regional efetiva fixa em 0 no Voice Contract. A v0.5.0 precisa de regionalidade real sem caricatura, sem inferir origem e sem copiar corpus.

## Decisão

1. Regionalidade só entra por um **Regional Evidence Pack** versionado (`voznativa/data/regional_packs/*.yml`, contrato em `docs/evidence/REGIONAL_EVIDENCE.md`), validado ao carregar; pack inválido não é usado.
2. Um único ponto de decisão, `regional.activate(context, text, profile)`, consultado por Voice Contract, planejador e engine. Ele devolve `active` com decisões por feature ou `abstain` com motivos.
3. Ordem de decisão por feature: forma do autor (Voice Profile) > forma que pode mudar o referente (mantida) > forma da região já presente > opção da forma mais frequente na evidência. Nunca inserção.
4. Os guards são determinísticos e independem do pedido: `regional_referent_changed` no `compare` e `regional_form_introduced` no engine.
5. O pack guarda formas, contagens, proporções e citações; nunca texto de corpus.

## Alternativas rejeitadas

- **Listas de marcadores por região** (o caminho das skills "humanizer" regionais): sem escopo, época nem contraste; produz caricatura. A lista E0 fica só como detector de exagero.
- **Classificador de região a partir do texto do autor**: infere origem da pessoa, contra o princípio 5 do README.
- **Ingerir corpora (Carolina, SP2010, ALIP)**: licenças incertas ou ausentes para derivados, e sem metadado geográfico (Carolina); custo de privacidade sem ganho comprovado.
- **Deixar o modelo decidir a regionalização pelo prompt**: não auditável e não testável.

## Consequências

- Com um pack piloto (um referente, Região Norte), o efeito prático é pequeno e majoritariamente protetivo; é a escala honesta da evidência disponível.
- Cada pack novo exige fonte com escopo, época, perfil e contraste, e casos de teste; a cobertura cresce devagar.
- O guard de referente pode marcar para revisão trocas legítimas fora do escopo do pack (major, nunca fail).
- Revisão humana regional continua pendente (instrumento no CP7).
