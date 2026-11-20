"""Self-contained HTML for a local editorial delivery."""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from html import escape
from importlib.resources import files
from pathlib import Path
from string import Template

from . import __version__

_TOKENS = re.compile(r"\w+|[^\w\s]|\s+")
_STATUS = {
    "identical": ("Sem alterações", "Os dois textos comparados são idênticos.", "plain"),
    "no_change": ("Original mantido", "A revisão terminou sem alterações.", "plain"),
    "returned_original": ("Original mantido", "O fluxo devolveu o texto de partida.", "review"),
    "no_deterministic_issues": ("Equivalência a verificar", "As checagens automáticas não apontaram impeditivos. O resultado não comprova equivalência de sentido nem fundamentação.", "review"),
    "review_required": ("Revisão necessária", "Confira os sinais abaixo antes de tratar a candidata como versão final.", "review"),
    "human_review_claimed": ("Revisão humana pendente", "A assinatura da revisão declarada não foi validada.", "review"),
    "accepted_by_llm": ("Aceita pelo fluxo de julgamento", "O resultado inclui um julgamento executado pelo motor. Consulte a evidência registrada.", "good"),
    "accepted_by_human": ("Revisão assinada registrada", "A assinatura vincula a revisão ao par de textos e à chave usada.", "good"),
    "fail": ("Candidata reprovada", "Os sinais registrados impedem a entrega desta candidata como revisão aprovada.", "bad"),
    "provider_error": ("Geração interrompida", "O provedor falhou. Nenhuma revisão foi entregue.", "bad"),
    "needs_review": ("Revisão necessária", "A execução terminou com uma etapa de revisão pendente.", "review"),
}
_SEVERITY = {"critical": "Crítico", "major": "Revisar", "info": "Informativo"}


def _opcodes(before, after, max_pairs):
    if before == after:
        return [("equal", 0, len(before), 0, len(after))]
    if not before:
        return [("insert", 0, 0, 0, len(after))]
    if not after:
        return [("delete", 0, len(before), 0, 0)]
    if len(before) * len(after) <= max_pairs:
        return SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
    # Long documents with a local edit should still show the shared text as context.
    start, left_end, right_end = 0, len(before), len(after)
    while start < min(left_end, right_end) and before[start] == after[start]:
        start += 1
    while left_end > start and right_end > start and before[left_end - 1] == after[right_end - 1]:
        left_end -= 1
        right_end -= 1
    result = [("equal", 0, start, 0, start)] if start else []
    if start or left_end < len(before):
        result.extend((tag, i + start, j + start, k + start, end + start)
                      for tag, i, j, k, end in _opcodes(before[start:left_end], after[start:right_end], max_pairs))
    else:
        result.append(("replace", start, left_end, start, right_end))
    if left_end < len(before):
        result.append(("equal", left_end, len(before), right_end, len(after)))
    return result


def _word_diff(before: str, after: str) -> tuple[str, str]:
    a, b = _TOKENS.findall(before), _TOKENS.findall(after)
    left, right = [], []
    for tag, i, j, k, end in _opcodes(a, b, 250_000):
        old, new = escape("".join(a[i:j])), escape("".join(b[k:end]))
        left.append(f"<del>{old}</del>" if tag != "equal" and old else old)
        right.append(f"<ins>{new}</ins>" if tag != "equal" and new else new)
    return "".join(left), "".join(right)


def _diff(original: str, candidate: str, notes: list[dict]) -> tuple[str, int, dict[int, int]]:
    before, after = original.splitlines(keepends=True), candidate.splitlines(keepends=True)
    rows, changes, links = [], 0, {}
    for tag, i, j, k, end in _opcodes(before, after, 600_000):
        if tag == "equal":
            block = escape("".join(before[i:j]))
            if block:
                rows.append(_row(block, block))
            continue
        # Group adjacent inserts/deletes together and align the words within the group.
        changes += 1
        source, target = "".join(before[i:j]), "".join(after[k:end])
        linked = []
        for number, note in enumerate(notes):
            if number not in links and note["before"] in source and note["after"] in target:
                links[number] = changes
                linked.append(number + 1)
        old, new = _word_diff(source, target)
        rows.append(_row(old, new, changes, linked))
    return "".join(rows), changes, links


def _row(old: str, new: str, index: int = 0, notes: list[int] | None = None) -> str:
    attrs = f' class="pair change" id="mudanca-{index}" tabindex="-1"' if index else ' class="pair same"'
    reason = ""
    if notes:
        count = f"{len(notes)} motivos" if len(notes) > 1 else "Ver motivo"
        reason = f'<a class="jump" href="#motivo-{notes[0]}">{count} ↓</a>'
    label = f'<div class="change-id"><span>Alteração {index:02}</span>{reason}</div>' if index else ""
    empty = '<span class="blank">Sem trecho</span>'
    return (f'<div{attrs}>{label}'
            f'<div class="pane before" role="group" aria-label="Antes"><div class="mobile-label" aria-hidden="true">Antes</div>'
            f'<pre><span class="text">{old}</span>{"" if old else empty}</pre></div>'
            f'<div class="pane after" role="group" aria-label="Depois"><div class="mobile-label" aria-hidden="true">Depois</div>'
            f'<pre><span class="text">{new}</span>{"" if new else empty}</pre></div></div>')


def validate_notes(notes, original: str, candidate: str) -> list[dict]:
    """Editorial explanations cite literal excerpts from the delivered pair."""
    if not isinstance(notes, list) or len(notes) > 30:
        raise ValueError("notas editoriais: passe uma lista JSON com até 30 itens")
    valid, seen = [], set()
    for note in notes:
        if not isinstance(note, dict) or any(not isinstance(note.get(key), str)
                                             for key in ("before", "after", "reason")):
            raise ValueError("cada nota editorial exige before, after e reason (texto)")
        before, after, reason = note["before"], note["after"], note["reason"]
        if (not reason.strip() or max(map(len, (before, after, reason))) > 1000
                or before == after or before not in original or after not in candidate):
            raise ValueError("cada nota deve citar trechos literais diferentes e explicar a mudança (até 1000 caracteres por campo)")
        key = before, after, reason.strip()
        if key not in seen:
            seen.add(key)
            valid.append({"before": before, "after": after, "reason": key[2]})
    return valid


def _editorial(notes: list[dict], reason: str, links: dict[int, int]) -> str:
    cards = []
    for number, note in enumerate(notes):
        old = f'<del>{escape(note["before"])}</del>' if note["before"] else ""
        new = f'<ins>{escape(note["after"])}</ins>' if note["after"] else ""
        block = links.get(number)
        link = f'<a class="jump" href="#mudanca-{block}">Ir à alteração {block:02} ↑</a>' if block else ""
        cards.append(f'<li id="motivo-{number + 1}"><p>{escape(note["reason"])}</p>'
                     f'<div class="excerpts">{old}{new}</div>{link}</li>')
    fallback = "Nenhuma justificativa editorial foi registrada para esta versão."
    intro = f"<p>{escape(reason)}</p>" if reason else ""
    if cards:
        return intro + '<ol class="reasons">' + "".join(cards) + "</ol>"
    return intro or f'<p class="muted">{fallback}</p>'


def _evidence(report: dict) -> str:
    items = []
    summary = report.get("summary", {})
    checked = summary.get("protected_in_original")
    lead = f'<p class="coverage">{checked} ocorrências protegidas no original</p>' if type(checked) is int else ""
    for item in report.get("issues", []):
        severity = item.get("severity", "")
        label = _SEVERITY.get(severity, "Sinal")
        items.append(f'<li><b>{label}</b> <code>{escape(str(item.get("code", "")))}</code>'
                     f'<p>{escape(str(item.get("message", "")))}</p></li>')
    for judgment in report.get("evidence", {}).get("judgments", []):
        fields = ("kind", "verdict", "generator_relation", "relation_evidence")
        detail = " · ".join(str(judgment[key]) for key in fields if judgment.get(key))
        if detail:
            items.append(f'<li><b>Julgamento registrado</b><p>{escape(detail)}</p></li>')
    if items:
        return lead + '<ul class="signals">' + "".join(items) + "</ul>"
    return lead + '<p class="muted">Nenhum sinal individual foi registrado.</p>'


def _activity(attempts, units) -> str:
    if not attempts and not units:
        return ""
    events = []
    for index, attempt in enumerate(attempts, 1):
        state = attempt.get("judge") or attempt.get("status", "")
        codes = " · ".join(attempt.get("codes", []))
        events.append(f'<li>Candidata {index:02} <code>{escape(state)}</code>'
                      f'{f"<p>{escape(codes)}</p>" if codes else ""}</li>')
    for unit in units:
        outcome = unit.get("outcome")
        if outcome in {"returned_original", "provider_error", "not_run", "needs_review"}:
            detail = escape(str(unit.get("reason") or ""))
            label = escape(str(unit.get("index", "")))
            events.append(f'<li>Unidade {label} <code>{outcome}</code><p>{detail}</p></li>')
    return ('<details class="activity"><summary>Histórico do processamento</summary><ul class="signals">'
            + "".join(events) + "</ul></details>") if events else ""


def render(original: str | None, candidate: str, report: dict, *, notes=None,
           reason: str = "", outcome: str = "", kept_original: bool = False, attempts=(), units=()) -> str:
    compared = original if original is not None else ""
    notes = validate_notes([] if notes is None else notes, compared, candidate)
    rows, changes, links = _diff(compared, candidate, notes)
    status = report.get("status") or outcome
    title, message, tone = _STATUS.get(status, ("Resultado registrado", "Consulte a saída da operação.", "plain"))
    if outcome == "needs_review" and status != "fail":
        title, message, tone = _STATUS["needs_review"]
    if status == "identical" and changes:
        title, message = "Variação de superfície", "O comparador normalizou a variação. Os realces mostram a diferença literal."
    view_note = ""
    if kept_original:
        view_note = "Entrega: original mantido. A seção de checagens descreve o resultado da tentativa."
    elif status == "fail":
        view_note = "A coluna Depois mostra a candidata reprovada para inspeção."
    if original is None:
        view_note += " A criação parte de fontes autorizadas e não tem um texto anterior."
    label = f"{changes} {'bloco alterado' if changes == 1 else 'blocos alterados'}"
    sizes = len(compared.split()), len(candidate.split())
    words = f"{sizes[0]} → {sizes[1]} palavras" if original is not None and changes else ""
    template = Template(files("voznativa").joinpath("data/editorial_report.html").read_text(encoding="utf-8"))
    return template.substitute(
        title=title, message=message, tone=tone, status=escape(str(status or "sem_status")),
        view_note=f"<p>{escape(view_note.strip())}</p>" if view_note else "",
        layout=" reading" if original is None else "",
        heading="Texto gerado" if original is None else "Comparação",
        label=(("Candidata de criação" if candidate else "Sem texto gerado") if original is None else label),
        words=f'<span class="length">{words}</span>' if words else "",
        rows=rows or _row("", ""),
        copy_side="before" if kept_original else "after",
        copy_allowed="false" if not candidate or (status in ("fail", "provider_error") and not kept_original) else "true",
        controls="" if not changes or original is None else (
            '<button type="button" id="changes" aria-pressed="false">Só mudanças</button>'
            '<button type="button" id="reading" aria-pressed="false">Só depois</button>'
            '<button type="button" id="previous" aria-label="Alteração anterior" disabled>←</button>'
            '<button type="button" id="next" aria-label="Próxima alteração">→</button>'),
        editorial=_editorial(notes, reason, links), evidence=_evidence(report) + _activity(attempts, units),
        version=escape(__version__),
    )


def check_destination(path: str) -> Path:
    destination = Path(path)
    if destination.suffix.lower() != ".html":
        raise ValueError("--html-out exige um caminho terminado em .html")
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"o relatório já existe: {destination}. Escolha um caminho novo.")
    if not destination.parent.is_dir():
        raise ValueError(f"a pasta do relatório não existe: {destination.parent}")
    return destination


def write(path: str, html: str) -> None:
    destination = check_destination(path)
    # Each report is a snapshot. Exclusive creation also protects inputs and existing reports.
    data = html.encode("utf-8")
    with destination.open("xb") as stream:
        try:
            stream.write(data)
            stream.flush()
        except OSError:
            stream.close()
            destination.unlink(missing_ok=True)
            raise
