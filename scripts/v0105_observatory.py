#!/usr/bin/env python3
"""VozNativa Observatory (v0.10.5, R18): a static site that shows what the fire trial measured.

Two steps, so the page is reproducible from the repository alone:

* ``data``: reads the run files kept **outside** the repository (offline campaign, live arms, blind judgment,
  document flows) and writes ``evals/v0105/observatory_data.json``: aggregates and per-run records with every
  local path and raw command removed, plus the texts of live tasks whose source allows publishing excerpts
  (public domain; CC BY with attribution, outputs marked as changed by a model). ``local_only`` texts never
  enter it; for them only id, genre, length band and rights are kept.
* ``render``: reads that JSON, ``PLAN.md``, ``GAP_REGISTER.md``, ``RELEASE_QUALIFICATION.md`` and
  ``evals/v0105/tracks.json`` and writes one self-contained page (no network, no external script or font file,
  no storage of texts) to ``docs/observatory/index.html``.

Every number the page shows is computed here (and tested in ``evals/test_v0105_observatory.py``); the page only
filters and draws. Missing measurements stay ``null`` and are drawn as missing, never as zero.

    python scripts/v0105_observatory.py data --work <dir with the runs> --items ~/.voznativa/fire-trial/items.jsonl
    python scripts/v0105_observatory.py render
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

GENERATOR_VERSION = "2"
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "evals" / "v0105" / "observatory_data.json"
OUT = ROOT / "docs" / "observatory" / "index.html"
REL = ROOT / "docs" / "releases" / "v0.10.5"
TEMPLATE_PATH = Path(__file__).resolve().parent / "observatory_template.html"
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from v0105_live_arms import ABLATION, ARMS  # noqa: E402  (one owner for the arm list; Derivanta Engine duplication)

LABELS = ("v0100", "v0105")
# prospective holdout labels: the direct LLM is version-independent; v0105a is the candidate the development
# campaign measured (8f5ffc1), v0105b the code after the continuation fixes
PROSPECTIVE_LABELS = ("direct", "v0100", "v0105a", "v0105b")
VERSION_NAME = {"v0100": "v0.10.0", "v0105": "v0.10.5", "direct": "sem VozNativa", "v0105a": "v0.10.5 inicial",
                "v0105b": "v0.10.5 final"}
ARM_LABEL = {"A0_original": "Original", "A1_direct": "LLM direto", "A2_skill": "Skill no host",
             "A3_engine": "Engine", "A3_bare": "Engine sem pedido nem contexto (ablação antiga)",
             "A3_noattrs": "Engine sem atributos", "A3_noknow": "Engine sem conhecimento",
             "A3_neither": "Engine sem atributos nem conhecimento"}
KIND_LABEL = {"negation_added": "Negação acrescentada", "negation_removed": "Negação removida",
              "number_changed": "Número trocado", "contrast_to_consequence": "Contraste virou consequência",
              "exception_deleted": "Exceção apagada", "sentence_deleted": "Frase do meio apagada",
              "rewrapped": "Linhas reunidas", "unicode_nfd": "Unicode decomposto (NFD)"}
FAMILY_LABEL = {"literario": "Literário", "academico": "Acadêmico", "institucional_juridico": "Institucional e jurídico",
                "jornalistico": "Jornalístico", "jornalistico_blog": "Jornalístico (blog)",
                "comercial_consumidor": "Avaliações de consumidor", "redes_sociais": "Redes sociais"}
BANDS = ("micro", "curto", "medio", "longo", "documento")
# families the trial wanted and could not source lawfully (PLAN.md, CORPUS_AND_LICENSES.md)
MISSING_FAMILIES = ("Mensagens e WhatsApp", "Correspondência e e-mail", "Documentação técnica PT-BR",
                    "Saúde e orientação", "Criativo e comercial", "Fala regional transcrita")
CLI_SUBCOMMAND = re.compile(r"voznativa(?:_cli\.py)?\"?\s+([a-z][a-z-]+)|\$VN\s+([a-z][a-z-]+)")


# --------------------------------------------------------------------------- pure helpers (tested)

def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    """95% Wilson score interval for k successes in n trials, as fractions; None when n == 0."""
    if n <= 0:
        return None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def decision(expect: str, changed: bool | None) -> str:
    """Whether a run's edit/no-edit decision matches the expectation frozen with the task (CP0).

    ``unnecessary_edit``: the task expected the text back and it changed. ``missed_edit``: the task required an
    edit and the text came back. ``ok`` otherwise; ``open`` when the expectation allows both; ``failed`` when the
    run produced no output at all.
    """
    if changed is None:
        return "failed"
    if expect == "no_change_expected":
        return "unnecessary_edit" if changed else "ok"
    if expect == "edit_required":
        return "ok" if changed else "missed_edit"
    return "open"


def cli_steps(calls: list[str] | None) -> list[str]:
    """Only the VozNativa subcommand names of an agent's shell calls: the raw commands carry local paths."""
    steps = []
    for call in calls or []:
        for a, b in CLI_SUBCOMMAND.findall(call):
            name = a or b
            if name and (not steps or steps[-1] != name):
                steps.append(name)
    return steps


def same_text(a: str | None, b: str | None) -> bool:
    return (a or "").strip() == (b or "").strip()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- data

def _offline(rep: dict) -> dict:
    kinds = defaultdict(lambda: {"correct": 0, "total": 0, "expected": None})
    fams = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in rep["rows"]:
        for m in r["metamorphic"]:
            k = kinds[m["kind"]]
            k["correct"] += bool(m["correct"])
            k["total"] += 1
            k["expected"] = m["expected"]
            fams[r["family"]]["correct"] += bool(m["correct"])
            fams[r["family"]]["total"] += 1
    for d in list(kinds.values()) + list(fams.values()):
        d["ci"] = wilson(d["correct"], d["total"])
    return {"cpu_s": rep["cpu_s"], "items": len(rep["rows"]), "kinds": dict(kinds), "families": dict(fams),
            "confirmed_items": sum(1 for r in rep["rows"] if r["confirmed_types"]),
            "confirmed_types": dict(Counter(t for r in rep["rows"] for t in r["confirmed_types"])),
            "plans": dict(Counter(r["plan"] for r in rep["rows"])),
            "routed": dict(Counter(r["routed_genre"] for r in rep["rows"]))}


def _run_record(r: dict, original: str, expect: str) -> dict:
    out = r.get("output")
    produced = bool((out or "").strip())
    changed = (not same_text(out, original)) if produced else None
    if r["arm"].startswith("A3") and not produced:
        changed = None
    elif r["arm"].startswith("A3") and r.get("outcome") in ("no_change", "returned_original"):
        changed = False
    return {"label": r["label"], "task": r["task"], "rep": r["rep"], "arm": r["arm"], "order": r.get("order"),
            "exit_code": r.get("exit_code"), "outcome": r.get("outcome"), "status": r.get("status"),
            "changed": changed, "decision": decision(expect, changed), "expect": expect,
            "cost_usd": round(r.get("cost_usd") or 0, 6), "seconds": r.get("seconds"),
            "calls": r.get("calls"), "turns": r.get("turns"),
            "skill_invoked": r.get("skill_invoked"), "final_written": r.get("final_written"),
            "tools": r.get("tools") if r["arm"] == "A2_skill" else None,
            "cli_steps": cli_steps(r.get("cli_calls")) if r["arm"] == "A2_skill" else None,
            "knowledge": r.get("knowledge"), "output_sha256": sha256_text(out) if produced else None}


def _judge(path: Path) -> dict | None:
    if not path.exists():
        return None
    jr = json.loads(path.read_text(encoding="utf-8"))
    per_run = {}
    for row in jr["rows"]:
        for c in row["candidates"]:
            for arm in c["arms"]:
                label, a = arm.split(":") if ":" in arm else ("original", arm)
                per_run[f"{label}|{row['task']}|{row['rep']}|{a}"] = {
                    **{k: c["scores"].get(k) for k in ("fidelity", "request", "naturalness")},
                    "critical_error": c.get("critical_error"), "oracle_lost": len(c.get("oracle_lost") or []),
                    "identical_to_original": c.get("identical_to_original")}
    return {"model": jr.get("judge_model"), "relation": jr.get("relation"), "evidence": jr.get("evidence"),
            "rows": len(jr["rows"]), "cost_usd": round(sum(r["cost_usd"] for r in jr["rows"]), 4),
            "per_run": per_run}


def _arm_summary(runs: list[dict], judge: dict | None, labels=LABELS, arms=ARMS) -> dict:
    """Per (version, arm): counts over the runs that produced a result, judge means, cost."""
    out = {}
    for label in labels:
        for arm in arms:
            rs = [r for r in runs if r["label"] == label and r["arm"] == arm]
            if not rs:
                continue
            dec = Counter(r["decision"] for r in rs)
            s = {"runs": len(rs), "changed": sum(1 for r in rs if r["changed"]),
                 "failed": dec.get("failed", 0), "unnecessary_edit": dec.get("unnecessary_edit", 0),
                 "missed_edit": dec.get("missed_edit", 0),
                 "decided": sum(dec.get(k, 0) for k in ("ok", "unnecessary_edit", "missed_edit")),
                 "decision_ok": dec.get("ok", 0),
                 "cost_usd": round(sum(r["cost_usd"] for r in rs), 4),
                 "seconds_median": statistics.median([r["seconds"] for r in rs if r["seconds"] is not None] or [0])}
            if arm == "A2_skill":
                s["skill_invoked"] = sum(1 for r in rs if r["skill_invoked"])
                s["ran_compare"] = sum(1 for r in rs if "compare" in (r["cli_steps"] or []))
                s["ran_before_writing"] = sum(1 for r in rs if set(r["cli_steps"] or []) &
                                              {"route", "diagnose", "plan", "rewrite-prompt", "context"})
            if judge:
                js = [judge["per_run"].get(f"{label}|{r['task']}|{r['rep']}|{arm}") for r in rs]
                js = [j for j in js if j]
                s["judged"] = len(js)
                for axis in ("fidelity", "request", "naturalness"):
                    vals = [j[axis] for j in js if isinstance(j[axis], (int, float))]
                    s[axis] = round(statistics.mean(vals), 2) if vals else None
                # the judge reads "revise" as "change": a correct NO_CHANGE scores low on "request". The request
                # axis is therefore also reported only over tasks whose frozen expectation requires an edit.
                req = [j["request"] for r, j in ((r, judge["per_run"].get(f"{label}|{r['task']}|{r['rep']}|{arm}"))
                                                 for r in rs) if j and r.get("expect") == "edit_required"
                       and isinstance(j.get("request"), (int, float))]
                s["request_edit_required"] = round(statistics.mean(req), 2) if req else None
                s["request_edit_required_n"] = len(req)
                s["critical"] = sum(1 for j in js if j["critical_error"])
            out[f"{label}|{arm}"] = s
    return out


def judge_r6(runs: list[dict], reps: int = 3) -> dict:
    """R6 per arm and axis: a task counts as GAIN (LOSS) when v0.10.5 scores above (below) v0.10.0 in at least two
    of the repetitions judged for both; otherwise TIE. Tasks without both judgments are left out (not ties)."""
    by = {(r["label"], r["task"], r["rep"], r["arm"]): (r.get("judge") or {}) for r in runs}
    out = {}
    for arm in ARMS:
        tasks = sorted({r["task"] for r in runs if r["arm"] == arm})
        for axis in ("fidelity", "request", "naturalness"):
            res = {"gain": [], "loss": [], "tie": []}
            for t in tasks:
                win = loss = n = 0
                for rep in range(1, reps + 1):
                    a, b = by.get(("v0100", t, rep, arm), {}).get(axis), by.get(("v0105", t, rep, arm), {}).get(axis)
                    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                        continue
                    n += 1
                    win, loss = win + (b > a), loss + (b < a)
                if n:
                    res["gain" if win >= 2 else "loss" if loss >= 2 else "tie"].append(t)
            out[f"{arm}|{axis}"] = res
    return out


def _headline(data: dict) -> dict:
    """The four statements of the 'in one minute' block, each a list of facts with numbers, computed here."""
    off = data["offline"]
    b, c = off.get("v0.10.0"), off.get("v0.10.5")
    improved, worse, same = [], [], []
    if b and c:
        for kind, kb in b["kinds"].items():
            kc = c["kinds"].get(kind)
            if not kc:
                continue
            row = {"kind": kind, "label": KIND_LABEL.get(kind, kind), "expected": kb["expected"],
                   "base": [kb["correct"], kb["total"]], "cand": [kc["correct"], kc["total"]]}
            (improved if kc["correct"] > kb["correct"] else worse if kc["correct"] < kb["correct"] else same).append(row)
    miss = lambda o: sum(k["total"] - k["correct"] for k in o["kinds"].values() if k["expected"] == "flag")
    alarm = lambda o: sum(k["total"] - k["correct"] for k in o["kinds"].values() if k["expected"] == "clean")
    summ = data["live"]["arms"]
    live_cmp = []
    for arm in ARMS:
        x, y = summ.get(f"v0100|{arm}"), summ.get(f"v0105|{arm}")
        if x and y:
            live_cmp.append({"arm": arm, "label": ARM_LABEL[arm],
                             "base_unnecessary": x["unnecessary_edit"], "cand_unnecessary": y["unnecessary_edit"],
                             "base_missed": x["missed_edit"], "cand_missed": y["missed_edit"],
                             "base_decided": x["decided"], "cand_decided": y["decided"],
                             "base_failed": x["failed"], "cand_failed": y["failed"]})
    perf = data.get("perf_17600_cpu_min_s") or {}
    ratio = (round(min(perf["cand"]) / min(perf["base"]), 3) if perf.get("base") and perf.get("cand") else None)
    r6 = judge_r6(data["live"]["runs"]) if data.get("judge") else None
    return {"judge_r6": r6,
            "offline_missed": [miss(b), miss(c)] if b and c else None,
            "offline_false_alarms": [alarm(b), alarm(c)] if b and c else None,
            "offline_cases": sum(k["total"] for k in c["kinds"].values()) if c else None,
            "kinds_improved": improved, "kinds_worse": worse, "kinds_same": same,
            "confirmed_on_real_text": [b["confirmed_items"], c["confirmed_items"]] if b and c else None,
            "edit_plans_on_real_text": [b["plans"].get("edit", 0), c["plans"].get("edit", 0)] if b and c else None,
            "live": live_cmp, "perf_ratio_17600": ratio}


def ablation_pairs(runs: list[dict], base_arm: str = "A3_engine", label: str = "v0105b") -> dict:
    """Paired judge differences of each ablation arm against the full engine, same task and repetition, same
    request. Only pairs judged on both sides count; ``n`` is the number of pairs."""
    by = {(r["task"], r["rep"], r["arm"]): (r.get("judge") or {}) for r in runs if r["label"] == label}
    out = {}
    for arm in ABLATION:
        diffs = {"fidelity": [], "request": [], "naturalness": []}
        changed = [0, 0]
        for (task, rep, a), j in by.items():
            if a != arm or (task, rep, base_arm) not in by:
                continue
            full = by[(task, rep, base_arm)]
            for axis in diffs:
                if isinstance(j.get(axis), (int, float)) and isinstance(full.get(axis), (int, float)):
                    diffs[axis].append(j[axis] - full[axis])
        for r in runs:
            if r["label"] == label and r["arm"] in (arm, base_arm):
                changed[0 if r["arm"] == base_arm else 1] += bool(r["changed"])
        out[arm] = {axis: ({"n": len(v), "mean": round(statistics.mean(v), 2), "better": sum(1 for x in v if x > 0),
                            "worse": sum(1 for x in v if x < 0)} if v else {"n": 0, "mean": None, "better": 0,
                                                                             "worse": 0})
                    for axis, v in diffs.items()}
        out[arm]["changed_full_vs_arm"] = changed
    return out


def _prospective(work: Path) -> dict | None:
    """The prospective holdout of the continuation: frozen before measuring, texts outside the repository."""
    tf = ROOT / "evals" / "v0105" / "prospective_tasks.json"
    items_path = Path.home() / ".voznativa" / "fire-trial" / "prospective.jsonl"
    runs_dir = work / "live-prosp"
    if not (tf.exists() and items_path.exists() and runs_dir.exists()):
        return None
    spec = json.loads(tf.read_text(encoding="utf-8"))
    manifest = {i["id"]: i for i in spec["items"]}
    texts = {json.loads(x)["id"]: json.loads(x)["text"] for x in items_path.read_text(encoding="utf-8").splitlines()
             if x.strip()}
    tasks = {t["task"]: t for t in spec["tasks"]}
    runs = []
    for label in PROSPECTIVE_LABELS:
        for f in sorted((runs_dir / label).glob("*.json")) if (runs_dir / label).exists() else []:
            r = json.loads(f.read_text(encoding="utf-8"))
            t = tasks[r["task"]]
            rec = _run_record(r, texts[t["item"]], t["expect"])
            rec["cli_denied"] = len(r.get("cli_denied") or []) if r["arm"] == "A2_skill" else None
            runs.append(rec)
    judge = _judge(work / "judged-prosp.json")
    if judge:
        for r in runs:
            r["judge"] = judge["per_run"].get(f"{r['label']}|{r['task']}|{r['rep']}|{r['arm']}")
    arms_all = ARMS + tuple(ABLATION)
    out = {"frozen_sha256": sha256_text(tf.read_text(encoding="utf-8")), "note": spec.get("note"),
           "tasks": [{"task": t["task"], "genre": t["genre"], "words": t["words"], "request": t["request"],
                      "expect": t["expect"], "mode": t["engine_mode"], "source": manifest[t["item"]]["work"],
                      "rights": manifest[t["item"]]["rights"],
                      "publishable": manifest[t["item"]]["rights_by_operation"]["publish_excerpts"]}
                     for t in spec["tasks"]],
           "runs": runs, "judge": ({k: v for k, v in judge.items() if k != "per_run"} if judge else None),
           "arms": _arm_summary(runs, judge, PROSPECTIVE_LABELS, arms_all),
           "ablation": ablation_pairs(runs) if judge else None, "texts": {}}
    for t in spec["tasks"]:
        m = manifest[t["item"]]
        if not m["rights_by_operation"]["publish_excerpts"]:
            continue
        entry = {"original": texts[m["id"]], "outputs": {}}
        for label in PROSPECTIVE_LABELS:
            for f in sorted((runs_dir / label).glob(f"{t['task']}-r*-*.json")) if (runs_dir / label).exists() else []:
                r = json.loads(f.read_text(encoding="utf-8"))
                o = (r.get("output") or "").strip()
                if o:
                    entry["outputs"][f"{label}|{r['rep']}|{r['arm']}"] = o
        out["texts"][t["task"]] = entry
    return out


def build_data(work: Path, items_path: Path) -> dict:
    tasks_all = json.loads((ROOT / "evals" / "v0105" / "live_tasks.json").read_text(encoding="utf-8"))["tasks"]
    manifest = {i["id"]: i for i in json.loads((ROOT / "evals" / "v0105" / "corpus_manifest.json")
                                               .read_text(encoding="utf-8"))["items"]}
    texts = {}
    for line in items_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            it = json.loads(line)
            texts[it["id"]] = it["text"]
    data = {"kind": "voznativa.observatory_data", "schema_version": 2, "release": "0.10.5"}
    items = list(manifest.values())
    data["corpus"] = {"items": len(items), "genres": len({i["genre"] for i in items}),
                      "families": dict(Counter(i["family"] for i in items)),
                      "bands": dict(Counter(i["band"] for i in items)),
                      "rights": dict(Counter(i["rights"] for i in items)),
                      "missing_families": list(MISSING_FAMILIES),
                      "list": [{"id": i["id"], "family": i["family"], "genre": i["genre"], "band": i["band"],
                                "words": i["words"], "rights": i["rights"]} for i in items]}
    data["offline"] = {}
    for label, name in (("v0.10.0", "offline-base3.json"), ("v0.10.5", "offline-final.json")):
        f = work / name
        if f.exists():
            data["offline"][label] = _offline(json.loads(f.read_text(encoding="utf-8")))
    # live
    tasks = [t for t in tasks_all if t["split"] == "development"]
    expect = {t["task"]: t["expect"] for t in tasks}
    runs, failed = [], Counter()
    for label in LABELS:
        d = work / "live" / label
        for f in sorted(d.glob("*.json")) if d.exists() else []:
            r = json.loads(f.read_text(encoding="utf-8"))
            item = next(t["item"] for t in tasks if t["task"] == r["task"])
            runs.append(_run_record(r, texts[item], expect[r["task"]]))
        failed[label] = len(list((d / "failed").glob("*.json"))) if (d / "failed").exists() else 0
    judge = _judge(work / "judged-dev.json")
    data["judge"] = ({k: v for k, v in judge.items() if k != "per_run"} if judge else None)
    if judge:
        for r in runs:
            r["judge"] = judge["per_run"].get(f"{r['label']}|{r['task']}|{r['rep']}|{r['arm']}")
    data["live"] = {
        "model": "haiku", "reps": 3,
        "tasks": [{"task": t["task"], "genre": t["genre"], "words": t["words"], "request": t["request"],
                   "expect": t["expect"], "mode": t["engine_mode"], "source": manifest[t["item"]].get("work"),
                   "ref": manifest[t["item"]].get("ref"), "rights": manifest[t["item"]]["rights"],
                   "publishable": bool((manifest[t["item"]].get("rights_by_operation") or {}).get("publish_excerpts"))}
                  for t in tasks],
        "runs": runs, "provider_failures_retried": dict(failed), "arms": _arm_summary(runs, judge)}
    # frozen internal holdout: run once per version at the end (A2, A3), never used to repair anything
    hold_tasks = {t["task"]: t for t in tasks_all if t["split"] == "internal_holdout"}
    hold_runs = []
    for label in LABELS:
        for f in sorted((work / "live-holdout" / label).glob("*.json")) if (work / "live-holdout" / label).exists() else []:
            r = json.loads(f.read_text(encoding="utf-8"))
            t = hold_tasks[r["task"]]
            rec = _run_record(r, texts[t["item"]], t["expect"])
            rec.update({"genre": t["genre"], "expect": t["expect"]})
            hold_runs.append(rec)
    data["holdout"] = {"tasks": len(hold_tasks), "reps": 1, "runs": hold_runs,
                       "arms": _arm_summary(hold_runs, None)} if hold_runs else None
    data["prospective"] = _prospective(work)
    # texts: only what the source allows publishing
    data["texts"] = {}
    for t in tasks:
        m = manifest[t["item"]]
        if not (m.get("rights_by_operation") or {}).get("publish_excerpts"):
            continue
        entry = {"original": texts[m["id"]], "outputs": {}}
        for label in LABELS:
            for f in sorted((work / "live" / label).glob(f"{t['task']}-r*-*.json")):
                r = json.loads(f.read_text(encoding="utf-8"))
                out = (r.get("output") or "").strip()
                if out:
                    entry["outputs"][f"{label}|{r['rep']}|{r['arm']}"] = out
        data["texts"][t["task"]] = entry
    docs = work / "documents.json"
    data["documents"] = json.loads(docs.read_text(encoding="utf-8"))["flows"] if docs.exists() else None
    perf = {}
    for v in ("base", "cand"):
        mins = [json.loads((work / f"perf-{v}-{i}.json").read_text(encoding="utf-8"))["sizes"]["800"]["cpu_min"]
                for i in (1, 2) if (work / f"perf-{v}-{i}.json").exists()]
        if mins:
            perf[v] = mins
    data["perf_17600_cpu_min_s"] = perf or None
    data["headline"] = _headline(data)
    pr = data.get("prospective")
    if pr and pr.get("arms"):
        A = pr["arms"]
        pick = lambda k, f: (A.get(k) or {}).get(f)
        data["headline"]["prospective"] = {
            "engine_decision": [[pick("v0100|A3_engine", "decision_ok"), pick("v0100|A3_engine", "decided")],
                                [pick("v0105b|A3_engine", "decision_ok"), pick("v0105b|A3_engine", "decided")]],
            "skill_request_edit": [pick("v0100|A2_skill", "request_edit_required"),
                                   pick("v0105b|A2_skill", "request_edit_required")],
            "skill_fidelity": [pick("v0100|A2_skill", "fidelity"), pick("v0105b|A2_skill", "fidelity")],
            "direct_critical": [pick("direct|A1_direct", "critical"), pick("direct|A1_direct", "judged")]}
    return data


# --------------------------------------------------------------------------- render

def _md_table(path: Path, header_startswith: str | None = None) -> list[list[str]]:
    rows, on = [], header_startswith is None
    for line in path.read_text(encoding="utf-8").splitlines():
        if header_startswith and line.startswith("| " + header_startswith):
            on = True
        if not on:
            continue
        if line.startswith("|") and not re.match(r"^\|\s*-", line):
            rows.append([c.strip() for c in line.strip().strip("|").split(" | ")])
        elif rows and not line.startswith("|"):
            break
    return rows[1:] if rows else []


def _inline(md: str) -> str:
    s = html.escape(md)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", s)


def _status(cell: str) -> str:
    m = re.search(r"\b(PASS|FAIL|PARTIAL|NOT_RUN|BLOCKED|NO_MEASURABLE_GAIN|INCONCLUSIVE|FIXED|OPEN|REFUTED|"
                  r"ACCEPTED_RISK|PENDING)\b", cell)
    return m.group(1) if m else "PENDING"


def _git_head() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def payload() -> dict:
    raw = DATA.read_text(encoding="utf-8")
    data = json.loads(raw)
    gaps = [{"id": r[0], "gap": _inline(r[1]), "found": _inline(r[2]), "repro": _inline(r[3]), "sev": r[4],
             "state": _inline(r[5]), "status": _status(r[5])}
            for r in _md_table(REL / "GAP_REGISTER.md") if len(r) >= 6]
    results = {r[0]: r for r in _md_table(REL / "RELEASE_QUALIFICATION.md") if r and re.match(r"R\d+$", r[0])}
    gates = []
    for r in _md_table(REL / "PLAN.md", "# | Critério"):
        if len(r) >= 3 and re.match(r"R\d+$", r[0]):
            res = results.get(r[0])
            text = " | ".join(res[1:]) if res else ""
            gates.append({"id": r[0], "criterion": _inline(r[1]), "floor": _inline(r[2]),
                          "status": _status(text) if res else "PENDING", "result": _inline(text)})
    tracks = json.loads((ROOT / "evals" / "v0105" / "tracks.json").read_text(encoding="utf-8"))
    return {"data": data, "gaps": gaps, "gates": gates, "tracks": tracks,
            "labels": {"arm": ARM_LABEL, "kind": KIND_LABEL, "family": FAMILY_LABEL, "version": VERSION_NAME,
                       "bands": list(BANDS)},
            "provenance": {"generator": f"scripts/v0105_observatory.py v{GENERATOR_VERSION}",
                           "data_file": "evals/v0105/observatory_data.json", "data_sha256": sha256_text(raw),
                           "repository_head": _git_head(), "schema_version": data.get("schema_version")}}


def render() -> str:
    body = json.dumps(payload(), ensure_ascii=False)
    # the payload sits in a <script type="application/json">: neutralise every sequence that could close it
    body = body.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return TEMPLATE_PATH.read_text(encoding="utf-8").replace("__PAYLOAD__", body)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("data")
    d.add_argument("--work", required=True)
    d.add_argument("--items", required=True)
    sub.add_parser("render")
    args = ap.parse_args(argv)
    if args.cmd == "data":
        DATA.write_text(json.dumps(build_data(Path(args.work), Path(args.items).expanduser()), ensure_ascii=False,
                                   indent=1) + "\n", encoding="utf-8")
        print(DATA)
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(render(), encoding="utf-8", newline="\n")
        print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
