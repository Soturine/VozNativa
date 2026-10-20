# Exemplos reais

Gerado por `scripts/make_examples.py` a partir de execuções gravadas com `claude-sonnet-5-5`. Os textos de entrada são sintéticos (escritos para os benchmarks). O relatório semântico é recalculado com o código atual; o veredito do juiz é o registrado na execução. Nada aqui é revisão humana.

## Reescrita aceita (e-mail corporativo)

Fonte: `evals/integration/20261020T060212Z-claude-sonnet-5-5-ptbr-ai-drafts-v1.json`, caso `ai-corp-001`.

**Antes**

> Prezados, espero que esta mensagem os encontre bem. Gostaria de informar que estaremos realizando a atualização do sistema de faturamento na próxima terça-feira, a partir das 19h. Nesse sentido, é importante destacar que o sistema poderá apresentar instabilidade por até 40 minutos. Além disso, vale ressaltar que os pedidos feitos nesse período só serão processados após a conclusão da atualização. Desde já, agradecemos a compreensão de todos.

**Depois**

> Prezados, espero que estejam bem.
>
> Vamos atualizar o sistema de faturamento na próxima terça-feira, a partir das 19h. O sistema poderá apresentar instabilidade por até 40 minutos, e os pedidos feitos nesse período só serão processados após a conclusão da atualização.
>
> Desde já, agradecemos a compreensão de todos.

**O que foi verificado**

- Gate determinístico: `no_deterministic_issues`
- Achados editoriais: 5 fortes + 4 fracos → 0 fortes + 1 fracos
- Desfecho do engine: `accepted`
- Juiz LLM (registrado): `equivalent`

## Nova tentativa depois da recusa do juiz (LinkedIn)

Fonte: `benchmarks/runs/ptbr-bench-v1-20261020T061509Z.json`, caso `pb-04`, braço `B5b-voznativa-engine`.

**Antes**

> Ninguém te conta isso, mas produtividade não é sobre fazer mais. É sobre fazer o que importa. No último trimestre, reduzi minhas reuniões semanais de 14 para 6. Foi uma mudança transformadora. E isso muda tudo. Você já fez esse exercício?

**Depois**

> Ninguém te conta isso, mas produtividade não é sobre fazer mais. É sobre fazer o que importa. No último trimestre, reduzi minhas reuniões semanais de 14 para 6. Foi uma mudança transformadora. Você já fez esse exercício?

**O que foi verificado**

- Gate determinístico: `no_deterministic_issues`
- Achados editoriais: 1 fortes + 1 fracos → 0 fortes + 1 fracos
- Desfecho do engine: `accepted`
- Juiz LLM (registrado): `equivalent`
- Nota: Na primeira tentativa o juiz recusou a saída; o engine refez a reescrita com o motivo da recusa.

## Texto natural: nenhuma chamada ao modelo (WhatsApp)

Fonte: `benchmarks/runs/ptbr-bench-v1-20261020T060615Z.json`, caso `pb-08`, braço `B5b-voznativa-engine`.

**Antes**

> gente, o churrasco de sábado vai ser na casa da Bia, às 13h. cada um leva uma bebida, a carne fica por minha conta. quem não puder ir me avisa até sexta, blz?

**Depois**

> gente, o churrasco de sábado vai ser na casa da Bia, às 13h. cada um leva uma bebida, a carne fica por minha conta. quem não puder ir me avisa até sexta, blz?

**O que foi verificado**

- Gate determinístico: `identical` (texto inalterado)
- Achados editoriais: 0 fortes + 0 fracos → 0 fortes + 0 fracos
- Desfecho do engine: `no_change`
- Nota: Sem achados editoriais, o engine devolve NO_CHANGE sem chamar o modelo.

## Saída de outra skill barrada: hedge removido (acadêmico)

Fonte: `benchmarks/runs/ptbr-bench-v1-20261020T060615Z.json`, caso `pb-03`, braço `B2-blader`.

**Antes**

> Em um mundo cada vez mais digitalizado, a leitura em telas tem se tornado cada vez mais frequente. Nesse contexto, o presente estudo investigou a compreensão leitora de 96 universitários em textos impressos e digitais. Os resultados sugerem que a compreensão foi ligeiramente maior no impresso, embora a diferença não tenha sido estatisticamente significativa (p = 0,08).

**Depois**

> A leitura em telas está cada vez mais comum. Este estudo comparou a compreensão leitora de 96 universitários em textos impressos e digitais. A compreensão foi um pouco maior no impresso, mas a diferença não foi estatisticamente significativa (p = 0,08).

**O que foi verificado**

- Gate determinístico: `fail`
- Achados editoriais: 1 fortes + 1 fracos → 0 fortes + 0 fracos
- `modality_changed` (critical): modality.evidential marker removed (1 -> 0)
- Juiz LLM (registrado): `not_equivalent`
- Nota: "Os resultados sugerem" virou afirmação categórica: mudança real de grau de certeza.

## Saída de outra skill barrada (jurídico)

Fonte: `benchmarks/runs/ptbr-bench-v1-20261020T060615Z.json`, caso `pb-10`, braço `B2-blader`.

**Antes**

> O contratante poderá rescindir o presente contrato mediante aviso prévio de 30 dias, sem prejuízo das obrigações já vencidas. A rescisão sem aviso prévio sujeitará a parte infratora à multa prevista na cláusula 11.

**Depois**

> O contratante pode rescindir este contrato com aviso prévio de 30 dias, mantidas as obrigações já vencidas. Se a rescisão ocorrer sem esse aviso, a parte que a causou paga a multa prevista na cláusula 11.

**O que foi verificado**

- Gate determinístico: `fail`
- Achados editoriais: 0 fortes + 0 fracos → 0 fortes + 0 fracos
- `causality_changed` (major): causality.causal marker added (0 -> 1)
- `condition_changed` (major): condition.conditional marker added (0 -> 1)
- `negation_changed` (critical): negation marker removed (2 -> 1)
- Juiz LLM (registrado): `not_equivalent`
- Nota: Nem todo alerta aqui é mudança real: "sem prejuízo das obrigações" → "mantidas as obrigações" é paráfrase fiel, e o gate é conservador nesse ponto. O juiz também recusou a saída.
