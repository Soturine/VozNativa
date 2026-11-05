#!/usr/bin/env python3
"""H4 probe of the Semantic Ledger (2026-11-05): hand-written pairs per category,
run before and after the H4 changes. Developer-written; not a holdout.

    python scripts/experiments/ledger_probe_h4.py evals/experiments/ledger_probe_h4.after.json
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json

from voznativa.compare import compare  # noqa: E402
U = {"fail", "review_required"}
# (category, original, candidate, should_block)
P = [
 ("temporal-equiv", "A reunião é às 14h.", "A reunião é às 2 da tarde.", False),
 ("temporal-equiv", "Entrego em 48 horas.", "Entrego em dois dias.", False),
 ("temporal-equiv", "O prazo é amanhã às 9h.", "O prazo é amanhã às 21h.", True),
 ("temporal-equiv", "Volto em 15 minutos.", "Volto em meia hora.", True),
 ("weekday", "O deploy é quinta.", "O deploy é na quinta-feira.", False),
 ("weekday", "Fechamos sexta, dia 12.", "Fechamos sábado, dia 12.", True),
 ("temporal-order", "Teste antes de publicar.", "Publique antes de testar.", True),
 ("temporal-order", "Primeiro a Ana revisa, depois o Caio aprova.", "Primeiro o Caio aprova, depois a Ana revisa.", True),
 ("causality", "O site caiu porque o certificado expirou.", "O certificado expirou porque o site caiu.", True),
 ("causality", "As vendas caíram e o preço subiu.", "As vendas caíram porque o preço subiu.", True),
 ("causality", "O uso de cache está associado a menos erros.", "O uso de cache reduz os erros.", True),
 ("agent-swap", "A Ana aprovou o orçamento do Caio.", "O Caio aprovou o orçamento da Ana.", True),
 ("agent-swap", "O cliente processou a empresa.", "A empresa processou o cliente.", True),
 ("agent-swap", "O gerente demitiu o analista.", "O analista demitiu o gerente.", True),
 ("pronoun", "A Ana ligou para a Bia porque ela estava atrasada.", "A Ana ligou para a Bia porque estava atrasada.", True),
 ("pronoun", "Pedimos ao fornecedor que ele mande a nota.", "O fornecedor pediu que nós mandássemos a nota.", True),
 ("cross-sentence", "O servidor A está estável. O servidor B caiu.", "O servidor A caiu. O servidor B está estável.", True),
 ("cross-sentence", "Contratamos a Lia em março. Ela lidera o time de dados.", "Contratamos a Lia em março. O time de dados é liderado por ela.", False),
 ("addition", "O app agora exporta CSV.", "O app agora exporta CSV e PDF.", True),
 ("addition", "Lançamos a versão 2.", "Lançamos a versão 2, a mais rápida do mercado.", True),
 ("omission", "Só administradores podem apagar projetos, exceto os arquivados.", "Só administradores podem apagar projetos.", True),
 ("omission", "O reembolso sai em até 5 dias úteis, se o pedido for aprovado.", "O reembolso sai em até 5 dias úteis.", True),
 ("pragmatic", "Você poderia revisar o contrato?", "Revise o contrato.", True),
 ("pragmatic", "Talvez a gente atrase a entrega.", "A gente vai atrasar a entrega.", True),
 ("pragmatic", "Sugiro adiar o lançamento.", "Vamos adiar o lançamento.", True),
 ("common-entity", "o fornecedor pagou a transportadora.", "a transportadora pagou o fornecedor.", True),
 ("common-entity", "o banco notificou o cliente sobre a fraude.", "o cliente notificou o banco sobre a fraude.", True),
 ("multiplier", "A receita cresceu.", "A receita triplicou.", True),
 # "duas vezes" also means "on two occasions": blocking is the safe reading.
 ("multiplier", "A receita dobrou.", "A receita cresceu duas vezes.", True),
]
rows = []
for cat, a, b, block in P:
    r = compare(a, b)
    ok = (r["status"] in U) == block
    rows.append({"category": cat, "original": a, "candidate": b, "should_block": block, "status": r["status"],
                 "codes": sorted({i["code"] for i in r["issues"]}), "ok": ok})
    print(("OK  " if ok else ("MISS" if block else "FRED")), cat, "|", r["status"], sorted({i["code"] for i in r["issues"]}), "|", b)
json.dump(rows, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(sum(r["ok"] for r in rows), "/", len(rows))
