"""First use without a model or a key: ``voznativa doctor`` and ``voznativa demo`` (v0.8 CP3).

* ``doctor`` checks the installation and says what to do about each problem.
  It never uses the network, never reads the user's texts and never prints
  the value of an environment variable (only whether a known one is set).
* ``demo`` runs the quickstart offline on texts bundled here, so it works
  from an installed wheel as well as from a checkout. It changes no file and
  calls no model. The texts are the same as ``examples/quickstart/`` (a test
  keeps them identical).
"""
from __future__ import annotations

import importlib.util
import os
import platform
import sys
import tempfile
from pathlib import Path

from . import __version__

DEMO_ORIGINAL = ("É importante destacar que o relatório trimestral será enviado até sexta-feira, 14/11/2025. "
                 "Vale ressaltar que o orçamento não pode ultrapassar R$ 12.000,00.")
DEMO_CANDIDATES = (
    ("candidata-boa", "O relatório trimestral será encaminhado até sexta-feira, 14/11/2025. "
                      "O orçamento não pode passar de R$ 12.000,00."),
    ("candidata-ruim", "O relatório trimestral será encaminhado até sexta-feira, 14/11/2025. "
                       "O orçamento pode passar de R$ 12.000,00."),
    ("candidata-perde-acao", "O relatório trimestral vai até sexta-feira, 14/11/2025. "
                             "O orçamento não pode passar de R$ 12.000,00."),
)
DEMO_ERRORS = "O relatório foi enviado para o o cliente na terça-feira, 13/11/2026."

STATUS_PT = {
    "identical": "idêntico",
    "no_deterministic_issues": "nenhum problema determinístico (não prova equivalência: falta juiz ou pessoa)",
    "review_required": "precisa de revisão humana",
    "fail": "reprovada",
}
# Variables a provider command commonly reads; doctor reports only whether they are set.
KNOWN_PROVIDER_VARIABLES = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "VOZNATIVA_HOME")


def _check(name: str, status: str, detail: str, hint: str | None = None) -> dict:
    return {"check": name, "status": status, "detail": detail, **({"hint": hint} if hint else {})}


def doctor() -> dict:
    """Installation checks. ``status`` per check: OK, WARN (works, with a
    caveat) or FAIL (a command will not work). No network, no user text."""
    checks = []
    py = sys.version_info
    checks.append(_check("python", "OK" if py >= (3, 11) else "FAIL", platform.python_version(),
                         None if py >= (3, 11) else "VozNativa precisa de Python 3.11 ou mais novo"))
    package_dir = Path(__file__).resolve().parent
    checkout = (package_dir.parent / "pyproject.toml").is_file() and (package_dir.parent / ".git").exists()
    checks.append(_check("voznativa", "OK", f"{__version__} em {package_dir}",
                         None if not checkout else "rodando de um checkout (desenvolvimento); "
                                                   "para uso isolado, instale o wheel num venv"))
    if importlib.util.find_spec("yaml") is None:
        checks.append(_check("pyyaml", "FAIL", "não instalado",
                             "instale as dependências: python -m pip install ."))
    else:
        import yaml
        checks.append(_check("pyyaml", "OK", getattr(yaml, "__version__", "?")))
    from .paths import HomeNotFound, home
    try:
        root = home()
        checks.append(_check("references", "OK", str(root / "references")))
    except HomeNotFound as error:
        checks.append(_check("references", "FAIL", str(error),
                             "reinstale a partir do repositório (python -m pip install .) ou defina VOZNATIVA_HOME"))
    data = package_dir / "data"
    packs = sorted(p.name for p in (data / "regional_packs").glob("*.yml")) if (data / "regional_packs").is_dir() else []
    checks.append(_check("dados do pacote", "OK" if packs else "FAIL", f"{len(packs)} packs regionais",
                         None if packs else "o pacote foi instalado sem os dados; reinstale com pip install ."))
    try:
        with tempfile.TemporaryDirectory(prefix="vn-doctor-") as tmp:
            (Path(tmp) / "probe").write_text("ok", encoding="utf-8")
        checks.append(_check("diretório temporário", "OK", tempfile.gettempdir()))
    except OSError as error:
        checks.append(_check("diretório temporário", "FAIL", str(error),
                             "o rewrite roda o provider num diretório temporário; libere a escrita em TEMP"))
    present = [name for name in KNOWN_PROVIDER_VARIABLES if os.environ.get(name)]
    checks.append(_check("provider", "OK",
                         "nenhum é necessário para compare, plan, diagnose, route e demo; "
                         + (f"variáveis definidas (valores não exibidos): {', '.join(present)}" if present
                            else "nenhuma variável de provider definida"),
                         "para reescrever com um modelo, passe --cmd; veja o README, seção 'Com um provider'"))
    worst = "FAIL" if any(c["status"] == "FAIL" for c in checks) else \
        "WARN" if any(c["status"] == "WARN" for c in checks) else "OK"
    return {"kind": "voznativa.doctor", "schema_version": 1, "status": worst, "network": "not used",
            "checks": checks}


def render_doctor(report: dict) -> str:
    lines = [f"VozNativa doctor: {report['status']} (sem rede, sem ler textos)"]
    for c in report["checks"]:
        lines.append(f"  [{c['status']:<4}] {c['check']}: {c['detail']}")
        if c.get("hint") and c["status"] != "OK":
            lines.append(f"         -> {c['hint']}")
    return "\n".join(lines)


def demo() -> dict:
    """The quickstart, offline: three candidates through the gate, the plan of
    the original and the diagnosis of a text with errors."""
    from .compare import compare
    from .diagnose import diagnose
    from .planner import plan
    from .router import route
    comparisons = []
    for name, candidate in DEMO_CANDIDATES:
        report = compare(DEMO_ORIGINAL, candidate)
        comparisons.append({"candidate": name, "text": candidate, "status": report["status"],
                            "semantic_equivalence": report["semantic_equivalence"],
                            "issues": [{"code": i["code"], "severity": i["severity"]} for i in report["issues"]]})
    the_plan = plan(DEMO_ORIGINAL, route(DEMO_ORIGINAL))
    diagnosis = diagnose(DEMO_ERRORS, route(DEMO_ERRORS))
    return {"kind": "voznativa.demo", "schema_version": 1, "model_called": False, "files_written": 0,
            "original": DEMO_ORIGINAL, "comparisons": comparisons,
            "plan": {"decision": the_plan["decision"], "summary": the_plan.get("summary")},
            "diagnosis": {"text": DEMO_ERRORS,
                          "diagnostics": [{"class": d.get("class"), "message": d.get("message")}
                                          for d in diagnosis["diagnostics"]]}}


def render_demo(result: dict) -> str:
    lines = ["VozNativa demo: tudo local, sem modelo e sem chave; nenhum arquivo é alterado.", "",
             "Original:", f"  {result['original']}", "",
             "1) Três reescritas candidatas passam pelo gate semântico (voznativa compare):"]
    for c in result["comparisons"]:
        codes = ", ".join(f"{i['code']} ({i['severity']})" for i in c["issues"] if i["severity"] != "info") or "nenhum"
        lines += [f"  - {c['candidate']}: {STATUS_PT.get(c['status'], c['status'])}",
                  f"      {c['text']}", f"      sinais: {codes}"]
    lines += ["", "   Nenhum desfecho prova que o sentido foi mantido: o melhor caso sem juiz é 'unverified'.", "",
              f"2) Plano para o original (voznativa plan): decisão '{result['plan']['decision']}'",
              "", "3) Diagnóstico de um texto com erros (voznativa diagnose):", f"  {result['diagnosis']['text']}"]
    for d in result["diagnosis"]["diagnostics"]:
        lines.append(f"  - {d['class']}: {d['message']}")
    lines += ["", "Próximos passos:",
              "  voznativa compare ORIGINAL.txt CANDIDATA.txt   # o gate com os seus textos",
              "  voznativa diagnose TEXTO.txt                    # erros e escolhas legítimas do original",
              "  voznativa doctor                                # conferir a instalação",
              "  voznativa demo --json                           # esta demonstração em JSON"]
    return "\n".join(lines)
