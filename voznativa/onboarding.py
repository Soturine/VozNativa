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

import importlib
import importlib.util
import json
import os
import platform
import sys
import tempfile
import time
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


# v0.9 CP1: every check names the kind of problem, so a FAIL says what to fix, not only that something broke.
CATEGORIES = ("python_version", "package", "dependency", "package_data", "permission", "config",
              "provider_not_configured", "provider_not_found", "provider_unsafe", "credential", "provider_call",
              "timeout", "ok")


def _check(name: str, status: str, detail: str, hint: str | None = None, category: str = "ok") -> dict:
    assert category in CATEGORIES, category
    return {"check": name, "status": status, "category": category if status != "OK" else "ok", "detail": detail,
            **({"hint": hint} if hint else {})}


def _provider_checks(probe: bool) -> list[dict]:
    """The provider the configuration names: found on PATH, started safely,
    credentials it was allowed to see present. No call unless ``probe``."""
    import shutil
    from .config import ConfigError, resolve
    try:
        cfg = resolve({})
    except ConfigError as error:
        return [_check("configuração", "FAIL", str(error), "corrija ou remova o arquivo indicado; "
                       "veja `voznativa config`", "config")]
    sources = {k: v["source"] for k, v in cfg.items() if v["source"] != "default"}
    out = [_check("configuração", "OK", "valores vindos de arquivo: " + (
        ", ".join(f"{k} ({s})" for k, s in sorted(sources.items())) if sources else "nenhum (só padrões)"))]
    cmd = cfg["cmd"]["value"]
    if not cmd:
        out.append(_check("provider", "OK",
                          "nenhum configurado; compare, plan, diagnose, route e demo não precisam de modelo",
                          "para reescrever com um modelo, passe --cmd ou defina 'cmd' em [rewrite] no arquivo do "
                          "usuário (voznativa config mostra o caminho)", "provider_not_configured"))
        return out
    from .providers import CommandProvider, ProviderError, agent_cli_warnings  # only with a provider configured
    try:
        provider = CommandProvider.from_string(cmd, 60.0, env=cfg["provider_env"]["value"],
                                               env_allow=tuple(cfg["provider_env_allow"]["value"]))
    except (ValueError, json.JSONDecodeError) as error:
        return out + [_check("provider", "FAIL", f"comando inválido: {error}",
                             "use uma string de comando ou um array JSON de strings", "config")]
    program = provider.argv[0]
    if shutil.which(program) is None and not Path(program).is_file():
        out.append(_check("provider", "FAIL", f"programa não encontrado: {program}",
                          "instale o programa, confira o PATH ou use o caminho absoluto no 'cmd'",
                          "provider_not_found"))
        return out
    out.append(_check("provider", "OK", f"programa encontrado: {Path(program).name} ({provider.id})"))
    for warning in agent_cli_warnings(provider.argv):
        out.append(_check("isolamento do provider", "WARN", warning,
                          "desligue as ferramentas do agente no comando", "provider_unsafe"))
    if cfg["provider_env"]["value"] == "minimal":
        missing = [n for n in cfg["provider_env_allow"]["value"] if not os.environ.get(n)]
        if missing:
            out.append(_check("credenciais do provider", "WARN",
                              f"liberadas mas não definidas (valores nunca exibidos): {', '.join(missing)}",
                              "defina as variáveis no ambiente ou tire-as de provider_env_allow; um CLI que "
                              "guarda a própria sessão pode não precisar delas", "credential"))
    if probe:
        started = time.perf_counter()
        try:
            answer = provider.generate("Responda apenas com a palavra: ok")[0]
            out.append(_check("chamada de teste", "OK",
                              f"respondeu em {time.perf_counter() - started:.1f} s ({len(answer)} caracteres)"))
        except ProviderError as error:
            message = str(error)
            category = ("provider_not_found" if "cannot start" in message else
                        "timeout" if "no answer after" in message else "provider_call")
            out.append(_check("chamada de teste", "FAIL", message[:300],
                              {"provider_not_found": "confira o caminho do programa",
                               "timeout": "o provider não respondeu em 60 s: rede, fila do serviço ou modelo local "
                                          "sem memória; tente de novo ou aumente --timeout no rewrite",
                               "provider_call": "o programa saiu com erro: confira login/credencial, rede, nome "
                                                "do modelo e a mensagem acima"}[category], category))
    return out


def doctor(probe_provider: bool = False) -> dict:
    """Installation checks. ``status`` per check: OK, WARN (works, with a
    caveat) or FAIL (a command will not work); ``category`` names the kind of
    problem. No network and no user text, unless ``probe_provider`` asks for
    one real call to the configured provider."""
    checks = []
    py = sys.version_info
    checks.append(_check("python", "OK" if py >= (3, 11) else "FAIL", platform.python_version(),
                         None if py >= (3, 11) else "VozNativa precisa de Python 3.11 ou mais novo",
                         "python_version"))
    package_dir = Path(__file__).resolve().parent
    checkout = (package_dir.parent / "pyproject.toml").is_file() and (package_dir.parent / ".git").exists()
    checks.append(_check("voznativa", "OK", f"{__version__} em {package_dir}",
                         None if not checkout else "rodando de um checkout (desenvolvimento); "
                                                   "para uso isolado, instale o wheel num venv"))
    broken = []
    # Core modules only: engine/providers import urllib (and ssl), and doctor must not load network code.
    for module in ("compare", "planner", "router", "diagnose", "document", "config"):
        try:
            importlib.import_module(f"voznativa.{module}")
        except Exception as error:  # noqa: BLE001 - any import failure means a broken install
            broken.append(f"{module}: {type(error).__name__}")
    checks.append(_check("módulos", "OK" if not broken else "FAIL",
                         "núcleo importável" if not broken else "falha ao importar " + "; ".join(broken),
                         None if not broken else "pacote quebrado: reinstale num venv limpo "
                                                 "(python -m pip install --force-reinstall .)", "package"))
    if importlib.util.find_spec("yaml") is None:
        checks.append(_check("pyyaml", "FAIL", "não instalado",
                             "instale as dependências: python -m pip install .", "dependency"))
    else:
        import yaml
        checks.append(_check("pyyaml", "OK", getattr(yaml, "__version__", "?")))
    from .paths import HomeNotFound, home
    try:
        root = home()
        checks.append(_check("references", "OK", str(root / "references")))
    except HomeNotFound as error:
        checks.append(_check("references", "FAIL", str(error),
                             "reinstale a partir do repositório (python -m pip install .) ou defina VOZNATIVA_HOME",
                             "package_data"))
    data = package_dir / "data"
    packs = sorted(p.name for p in (data / "regional_packs").glob("*.yml")) if (data / "regional_packs").is_dir() else []
    checks.append(_check("dados do pacote", "OK" if packs else "FAIL", f"{len(packs)} packs regionais",
                         None if packs else "o pacote foi instalado sem os dados; reinstale com pip install .",
                         "package_data"))
    try:
        with tempfile.TemporaryDirectory(prefix="vn-doctor-") as tmp:
            (Path(tmp) / "probe").write_text("ok", encoding="utf-8")
        checks.append(_check("diretório temporário", "OK", tempfile.gettempdir()))
    except OSError as error:
        checks.append(_check("diretório temporário", "FAIL", str(error),
                             "o rewrite roda o provider num diretório temporário; libere a escrita em TEMP",
                             "permission"))
    present = [name for name in KNOWN_PROVIDER_VARIABLES if os.environ.get(name)]
    checks.append(_check("variáveis de provider", "OK",
                         f"definidas (valores não exibidos): {', '.join(present)}" if present
                         else "nenhuma definida (um CLI com login próprio não precisa delas)"))
    checks += _provider_checks(probe_provider)
    worst = "FAIL" if any(c["status"] == "FAIL" for c in checks) else \
        "WARN" if any(c["status"] == "WARN" for c in checks) else "OK"
    return {"kind": "voznativa.doctor", "schema_version": 2, "status": worst,
            "network": "used by the provider probe" if probe_provider else "not used",
            "checks": checks}


def render_doctor(report: dict) -> str:
    probe = report.get("network") != "not used"
    lines = [f"VozNativa doctor: {report['status']} "
             + ("(com uma chamada de teste ao provider)" if probe else "(sem rede, sem ler textos)")]
    for c in report["checks"]:
        kind = f" [{c['category']}]" if c.get("category", "ok") != "ok" else ""
        lines.append(f"  [{c['status']:<4}] {c['check']}: {c['detail']}{kind}")
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
