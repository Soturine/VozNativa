"""Evaluation Core (v0.8 CP4): datasets with splits, axes, provenance and integrity.

The older runners stay as they are (``evals.run`` for one semantic suite,
``evals.run_decisions``, ``benchmark.run`` for frozen benchmark outputs). This
module reads the same suites through adapters, without copying or editing
them, and adds what a reproducible evaluation needs:

* **dataset spec** (``voznativa.eval_dataset``): which files, read by which
  adapter, in which split. The split must agree with the suite's own
  ``MANIFEST.json`` (a suite its manifest calls non-independent can never be
  an independent holdout) and a frozen file must still have its hash;
  otherwise the run is ``INVALID``, never a PASS.
* **axes** reported separately, never folded into one score:
  ``semantic_risk`` (did the gate flag a candidate that changed meaning, and
  leave a clean one alone), ``status_agreement`` (the exact status the case
  expects) and ``decision`` (did the planner call the model only when it
  should). Each outcome is counted with its denominator and a 95% Wilson
  interval; ``abstained`` and ``not_applicable`` are counted, not dropped.
* **run record** (``voznativa.eval_run``): revision, dirty flag, versions,
  input hashes, the dataset spec, per-case results without the texts (their
  sha256 only), and a digest of the results so an edited record is detected
  by ``verify_run``.
* **evidence**: what this module executes is ``ENGINE_EXECUTED``. Arms that
  need a model, a person or an external service are listed as ``NOT_RUN``
  with the reason; they never count as passed.

Every number here comes from cases written by the engine's developer unless a
source says otherwise; the report says so per split.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .benchmark import wilson
from .evals import CLEARED, UNSAFE, check_decision, sha256_lf

DATASET_KIND = "voznativa.eval_dataset"
RUN_KIND = "voznativa.eval_run"
SCHEMA_VERSION = 1
SPLITS = ("frozen_regression", "development", "prospective_holdout", "external_independent_holdout",
          "adversarial", "real_provider_study")
INDEPENDENT_SPLITS = {"external_independent_holdout"}
EVIDENCE = ("ENGINE_EXECUTED", "AGENT_OBSERVED", "EXTERNAL_VERIFIED", "EXTERNAL_UNVERIFIED", "DECLARED", "INFERRED",
            "HUMAN_OBSERVED", "NOT_RUN")
ADAPTERS = ("semantic_suite", "risk_sample", "decision_suite")
AXES = ("semantic_risk", "status_agreement", "decision")


class DatasetError(ValueError):
    """The dataset spec or one of its cases is malformed."""


# --- dataset spec -------------------------------------------------------------------------

def _manifest_entry(path: Path) -> dict:
    """What the suite's own MANIFEST.json says about ``path`` (two layouts exist)."""
    manifest = path.parent / "MANIFEST.json"
    if not manifest.is_file():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if path.name in data.get("suites", {}):
        return dict(data["suites"][path.name])
    if Path(str(data.get("file", ""))).name == path.name:          # single-sample layout (evals/predicates)
        return {"frozen": "sha256" in data, **{k: data[k] for k in ("sha256", "independent", "author") if k in data}}
    return {}


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


INDEPENDENCE_FIELDS = ("prepared_by", "custodian", "frozen_commit", "attestation")


def independence_problems(entry: dict, path: Path, root: Path) -> list[str]:
    """``independent: true`` is a claim, not evidence (v0.8 CP5). An
    independent holdout needs an ``independence_evidence`` block:

    * ``prepared_by`` and ``custodian``: who wrote and who kept the cases (not
      the engine's developer; this is declared, the run cannot check people);
    * ``frozen_commit``: the commit that froze the file; it must exist in this
      repository and the file there must have the MANIFEST's sha256, so the
      cases provably existed before any later code;
    * ``attestation``: a file in the repository with the custody record.

    What can be checked is checked; the rest stays labelled DECLARED in the
    run record. Passing this does not make a set independent, it only stops
    a bare flag from being enough."""
    evidence = entry.get("independence_evidence")
    if not isinstance(evidence, dict):
        return [f"{path.name}: independent: true without independence_evidence ({', '.join(INDEPENDENCE_FIELDS)})"]
    problems = [f"{path.name}: independence_evidence.{k} missing" for k in INDEPENDENCE_FIELDS
                if not isinstance(evidence.get(k), str) or not evidence.get(k).strip()]
    if problems:
        return problems
    developer = {"voznativa developer", "the engine's developer", "agent", "claude"}
    if evidence["prepared_by"].strip().lower() in developer:
        problems.append(f"{path.name}: prepared_by names the engine's developer")
    attestation = root / evidence["attestation"]
    if Path(evidence["attestation"]).is_absolute() or not _inside(root, attestation) or not attestation.is_file():
        problems.append(f"{path.name}: attestation {evidence['attestation']} not found inside the repository")
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    frozen = _git_bytes(root, "show", f"{evidence['frozen_commit']}:{rel}")
    if frozen is None:
        problems.append(f"{path.name}: frozen_commit {evidence['frozen_commit']} does not contain {rel}")
    elif hashlib.sha256(frozen.replace(b"\r\n", b"\n")).hexdigest() != entry.get("sha256"):
        problems.append(f"{path.name}: the file at frozen_commit does not have the MANIFEST sha256")
    return problems


def _git_bytes(root: Path, *args: str) -> bytes | None:
    try:
        done = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout if done.returncode == 0 else None


def validate_dataset(spec: dict, root: Path) -> list[str]:
    """Problems that make the spec unusable (empty = usable)."""
    problems = []
    if spec.get("kind") != DATASET_KIND or spec.get("schema_version") != SCHEMA_VERSION:
        problems.append("unsupported dataset kind or schema_version")
    if not isinstance(spec.get("id"), str) or not spec.get("id"):
        problems.append("dataset id missing")
    sources = spec.get("sources")
    if not isinstance(sources, list) or not sources:
        return problems + ["sources must be a non-empty list"]
    seen = set()
    for n, src in enumerate(sources):
        where = f"source {n}"
        if not isinstance(src, dict):
            problems.append(f"{where} is not an object")
            continue
        path = src.get("path")
        if not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts:
            problems.append(f"{where}: path must be relative to the repository and stay inside it")
            continue
        # A link (symlink or junction) can point outside the root while its own path looks inside (v0.8 CP5).
        if not _inside(root, root / path):
            problems.append(f"{where}: {path} resolves outside the repository (link?)")
            continue
        if path in seen:
            problems.append(f"{where}: {path} listed twice")
        seen.add(path)
        if src.get("adapter") not in ADAPTERS:
            problems.append(f"{where}: adapter must be one of {ADAPTERS}")
        if src.get("split") not in SPLITS:
            problems.append(f"{where}: split must be one of {SPLITS}")
        full = root / path
        if not full.is_file():
            problems.append(f"{where}: {path} not found")
            continue
        entry = _manifest_entry(full)
        if src.get("split") in INDEPENDENT_SPLITS:
            if not entry.get("independent"):
                problems.append(f"{where}: {path} is not independent per its MANIFEST; it cannot be split "
                                f"{src.get('split')!r}")
            else:
                problems += [f"{where}: {p}" for p in independence_problems(entry, full, root)]
        if entry.get("frozen") and entry.get("sha256") and sha256_lf(full) != entry["sha256"]:
            problems.append(f"{where}: frozen file {path} changed (sha256 differs from its MANIFEST)")
    return problems


# --- adapters: suite rows -> normalised cases ---------------------------------------------

def _semantic_rows(rows, source):
    for r in rows:
        statuses = (r.get("expect") or {}).get("status")
        if not isinstance(statuses, list) or not statuses:
            raise DatasetError(f"{source}:{r.get('id')}: expect.status must be a non-empty list")
        risk = True if set(statuses) <= UNSAFE else False if set(statuses) <= CLEARED else None
        yield {"id": r["id"], "original": r["original"], "candidate": r["candidate"], "expect_risk": risk,
               "expect_status": statuses, "kind": r.get("category"), "genre": r.get("genre")}


def _risk_rows(rows, source):
    for r in rows:
        if r.get("expect") not in ("risk", "clean"):
            raise DatasetError(f"{source}:{r.get('id')}: expect must be 'risk' or 'clean'")
        yield {"id": r["id"], "original": r["original"], "candidate": r["candidate"],
               "expect_risk": r["expect"] == "risk", "expect_status": None, "kind": r.get("kind"), "genre": None}


def load_cases(src: dict, root: Path) -> list[dict]:
    path = root / src["path"]
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise DatasetError(f"{src['path']}:{number}: invalid JSON ({error.msg})") from None
    required = {"semantic_suite": ("id", "original", "candidate"), "risk_sample": ("id", "original", "candidate"),
                "decision_suite": ("id", "text")}[src["adapter"]]
    for r in rows:
        missing = [k for k in required if not isinstance(r.get(k), str)]
        if missing:
            raise DatasetError(f"{src['path']}:{r.get('id', '?')}: missing or non-text {missing}")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise DatasetError(f"{src['path']}: duplicate case ids")
    if src["adapter"] == "decision_suite":
        return [dict(r, _adapter="decision_suite") for r in rows]
    gen = _semantic_rows if src["adapter"] == "semantic_suite" else _risk_rows
    return [dict(c, _adapter=src["adapter"]) for c in gen(rows, src["path"])]


# --- running --------------------------------------------------------------------------------

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _gate_result(case: dict) -> dict:
    from .compare import compare
    report = compare(case["original"], case["candidate"])
    flagged = report["status"] in UNSAFE
    expect = case["expect_risk"]
    outcome = ("not_applicable" if expect is None else
               "detected" if expect and flagged else "missed" if expect else
               "false_alarm" if flagged else "correct_clear")
    return {"status": report["status"], "codes": sorted({i["code"] for i in report["issues"]}),
            "semantic_risk": outcome,
            "status_agreement": ("not_applicable" if case["expect_status"] is None else
                                 "agree" if report["status"] in case["expect_status"] else "disagree"),
            "auto_accepted_without_identity": bool(report["safe_to_auto_accept"] and report["status"] != "identical"),
            "original_sha256": _sha(case["original"]), "candidate_sha256": _sha(case["candidate"])}


def _decision_result(case: dict) -> dict:
    r = check_decision(case)
    should_call = case["expect"]["decision"] != "no_change"
    called = r["decision"] != "no_change"
    outcome = ("called_when_needed" if called and should_call else "stayed_out_correctly" if not called
               and not should_call else "unnecessary_call" if called else "missed_call")
    return {"decision": r["decision"], "expected": case["expect"]["decision"], "passed": r["passed"],
            "decision_outcome": outcome, "text_sha256": _sha(case["text"])}


def _git(root: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


HOLDOUT_SPLITS = {"prospective_holdout", "external_independent_holdout"}
NEAR_DUPLICATE = 0.8


def _norm(text: str) -> str:
    """Words only, folded: punctuation, case, accents and spacing do not make two copies different."""
    import re
    from .text import fold
    return " ".join(re.findall(r"\w+", fold(text)))


def _trigrams(key: str) -> set:
    words = key.split()
    return {" ".join(words[i:i + 3]) for i in range(len(words) - 2)}


def leakage(entries: list[dict]) -> dict:
    """Texts shared between different sources (V08-GAP-08). ``entries``:
    ``{"id", "source", "split", "text"}``, one per source text (original or
    decision text). Exact = same text after folding case, accents and spaces;
    near = word-trigram Jaccard >= 0.8 for texts of 6+ words; ``same_pair``
    when the candidate (``pair``) is the same too, i.e. the very same case. A link that
    touches a holdout split from another source makes that holdout unusable."""
    keys = [_norm(e["text"]) for e in entries]
    grams = [_trigrams(k) if len(k.split()) >= 6 else set() for k in keys]
    links = []
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            if entries[i]["source"] == entries[j]["source"]:
                continue
            if keys[i] == keys[j]:
                kind, score = "exact", 1.0
            elif grams[i] and grams[j]:
                score = len(grams[i] & grams[j]) / len(grams[i] | grams[j])
                if score < NEAR_DUPLICATE:
                    continue
                kind = "near"
            else:
                continue
            same_pair = (kind == "exact" and entries[i].get("pair") is not None
                         and _norm(entries[i]["pair"]) == _norm(entries[j].get("pair") or ""))
            links.append({"a": entries[i]["id"], "b": entries[j]["id"], "kind": kind, "score": round(score, 3),
                          "same_pair": same_pair, "splits": sorted({entries[i]["split"], entries[j]["split"]})})
    blocking = [l for l in links if set(l["splits"]) & HOLDOUT_SPLITS]
    return {"links": links, "cross_split": sum(len(l["splits"]) > 1 for l in links),
            "holdout_contaminated": blocking}


def results_digest(results: list[dict]) -> str:
    return _sha(json.dumps(results, ensure_ascii=False, sort_keys=True))


def run(spec: dict, root: Path, recorded_at: str | None = None) -> dict:
    """Run every source of ``spec``. Never raises for a bad case: the run is
    ``INVALID`` (spec or integrity problems) or ``INCOMPLETE`` (a source could
    not be read) and says why."""
    problems = validate_dataset(spec, root)
    revision = _git(root, "rev-parse", "HEAD")
    porcelain = _git(root, "status", "--porcelain")
    base = {"kind": RUN_KIND, "schema_version": SCHEMA_VERSION, "dataset": spec.get("id"),
            "dataset_sha256": _sha(json.dumps(spec, ensure_ascii=False, sort_keys=True)),
            "dataset_spec": spec,      # kept so the run can be replayed at its revision
            "authenticity": "not established: results_sha256 is an integrity digest, not a signature; anyone "
                            "who edits the results can recompute it. Use replay to re-execute at the revision.",
            "recorded_at": recorded_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "revision": revision, "dirty": None if porcelain is None else bool(porcelain),
            "package_version": __version__,
            "environment": {"python": platform.python_version(), "platform": platform.platform(terse=True)},
            "system_under_test": {"id": f"voznativa-gate@{__version__}", "evidence": "ENGINE_EXECUTED",
                                  "deterministic": True, "model": None, "seed": None},
            "arms_not_run": [
                {"arm": "rewrite arms B0-B6", "evidence": "NOT_RUN",
                 "reason": "this dataset evaluates the gate and the planner on fixed pairs; arms that generate "
                           "text need a provider and a budget (CP9)"},
                {"arm": "human review", "evidence": "NOT_RUN", "reason": "no human reviewers in this run"}]}
    if problems:
        return dict(base, status="INVALID", problems=problems, inputs=[], results=[], metrics={},
                    results_sha256=results_digest([]))
    inputs, results, errors, texts = [], [], [], []
    for src in spec["sources"]:
        path = root / src["path"]
        entry = _manifest_entry(path)
        inputs.append({"path": src["path"], "sha256_lf": sha256_lf(path), "adapter": src["adapter"],
                       "split": src["split"], "independent": bool(entry.get("independent")),
                       "independence": ("frozen_commit verified; people and custody DECLARED"
                                        if src["split"] in INDEPENDENT_SPLITS else "not claimed"),
                       "frozen": bool(entry.get("frozen")), "author": entry.get("author", "unknown")})
        try:
            cases = load_cases(src, root)
        except DatasetError as error:
            errors.append(str(error))
            continue
        for case in cases:
            texts.append({"id": f"{Path(src['path']).stem}:{case['id']}", "source": src["path"],
                          "split": src["split"], "text": case.get("original", case.get("text", "")),
                          "pair": case.get("candidate")})
        for case in cases:
            row = {"id": f"{Path(src['path']).stem}:{case['id']}", "source": src["path"], "split": src["split"],
                   "kind": case.get("kind"), "genre": case.get("genre")}
            row.update(_decision_result(case) if case["_adapter"] == "decision_suite" else _gate_result(case))
            results.append(row)
    leaks = leakage(texts)
    for link in leaks["holdout_contaminated"]:
        problems.append(f"holdout contaminated: {link['a']} and {link['b']} ({link['kind']}, {link['score']})")
    status = "INVALID" if problems else "INCOMPLETE" if errors else "COMPLETE"
    return dict(base, status=status, problems=problems + errors, inputs=inputs, results=results,
                metrics=metrics(results), results_sha256=results_digest(results),
                leakage={"links": len(leaks["links"]), "cross_split": leaks["cross_split"],
                         "same_pair": sum(l["same_pair"] for l in leaks["links"]),
                         "pairs": [{k: l[k] for k in ("a", "b", "kind", "score", "same_pair", "splits")}
                                   for l in leaks["links"]]})


# --- metrics ---------------------------------------------------------------------------------

def _rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "rate": round(k / n, 3) if n else None, "wilson95": wilson(k, n)}


def _semantic_metrics(rows: list[dict]) -> dict:
    c = Counter(r["semantic_risk"] for r in rows)
    risky = c["detected"] + c["missed"]
    clean = c["false_alarm"] + c["correct_clear"]
    return {"counts": {k: c.get(k, 0) for k in ("detected", "missed", "false_alarm", "correct_clear",
                                                 "abstained", "not_applicable")},
            "sensitivity": _rate(c["detected"], risky), "false_alarm_rate": _rate(c["false_alarm"], clean),
            "auto_accepted_without_identity": sum(r["auto_accepted_without_identity"] for r in rows)}


def metrics(results: list[dict]) -> dict:
    """Per split (never pooled across splits) and per kind inside a split."""
    out = {}
    by_split = defaultdict(list)
    for r in results:
        by_split[r["split"]].append(r)
    for split, rows in sorted(by_split.items()):
        gate = [r for r in rows if "semantic_risk" in r]
        dec = [r for r in rows if "decision_outcome" in r]
        entry = {"cases": len(rows)}
        if gate:
            entry["semantic_risk"] = _semantic_metrics(gate)
            agree = [r for r in gate if r["status_agreement"] != "not_applicable"]
            entry["status_agreement"] = _rate(sum(r["status_agreement"] == "agree" for r in agree), len(agree))
            kinds = defaultdict(list)
            for r in gate:
                kinds[r.get("kind") or "unspecified"].append(r)
            entry["semantic_risk_by_kind"] = {k: _semantic_metrics(v)["counts"] for k, v in sorted(kinds.items())}
        if dec:
            d = Counter(r["decision_outcome"] for r in dec)
            should = d["called_when_needed"] + d["missed_call"]
            should_not = d["stayed_out_correctly"] + d["unnecessary_call"]
            entry["decision"] = {"counts": dict(sorted(d.items())),
                                 "calls_when_needed": _rate(d["called_when_needed"], should),
                                 "unnecessary_calls": _rate(d["unnecessary_call"], should_not),
                                 "exact_decision": _rate(sum(r["passed"] for r in dec), len(dec))}
        out[split] = entry
    return out


def verify_run(record: dict) -> list[str]:
    """Problems that make a run record untrustworthy (empty = consistent):
    edited results, metrics that do not follow from them, or a status that
    claims more than the record shows."""
    problems = []
    if record.get("kind") != RUN_KIND or record.get("schema_version") != SCHEMA_VERSION:
        problems.append("not a voznativa.eval_run v1 record")
    results = record.get("results", [])
    if results_digest(results) != record.get("results_sha256"):
        problems.append("results do not match results_sha256 (the record was edited)")
    if metrics(results) != record.get("metrics"):
        problems.append("metrics do not follow from the results")
    if record.get("status") == "COMPLETE" and (record.get("problems") or not results):
        problems.append("status COMPLETE with problems or without results")
    for arm in record.get("arms_not_run", []):
        if arm.get("evidence") != "NOT_RUN":
            problems.append(f"arm {arm.get('arm')!r} listed as not run with evidence {arm.get('evidence')!r}")
    return problems


def replay_run(record: dict, root: Path) -> dict:
    """Re-execute a recorded run with the code and inputs of its revision
    (``git archive`` into a temporary directory, run there in a subprocess)
    and compare the results digest.

    ``REPRODUCED`` is evidence that the recorded results follow from that
    revision on this machine; it is not a signature, does not say who ran the
    original and does not make any dataset independent. ``NOT_REPLAYABLE``
    when the record came from a dirty tree, names no known revision, lacks
    its dataset spec, or the revision has no evaluation core."""
    import sys
    import tarfile
    import tempfile

    def outcome(status, reason, **extra):
        return {"kind": "voznativa.eval_run_replay", "status": status, "reason": reason,
                "revision": record.get("revision"), **extra}

    if record.get("dirty") is not False:
        return outcome("NOT_REPLAYABLE", "the run came from a dirty or unknown tree: its code is not in any commit")
    revision, spec = record.get("revision"), record.get("dataset_spec")
    if not isinstance(spec, dict) or _sha(json.dumps(spec, ensure_ascii=False, sort_keys=True)) != \
            record.get("dataset_sha256"):
        return outcome("NOT_REPLAYABLE", "the record has no dataset spec matching dataset_sha256")
    if not revision or _git_bytes(root, "cat-file", "-e", f"{revision}^{{commit}}") is None:
        return outcome("NOT_REPLAYABLE", f"revision {revision!r} is not in this repository")
    archive = _git_bytes(root, "archive", "--format=tar", revision)
    if archive is None:
        return outcome("NOT_REPLAYABLE", "git archive failed")
    with tempfile.TemporaryDirectory(prefix="vn-replay-") as tmp:
        tree = Path(tmp) / "tree"
        tree.mkdir()
        tar_path = Path(tmp) / "rev.tar"
        tar_path.write_bytes(archive)
        with tarfile.open(tar_path) as tar:
            tar.extractall(tree, filter="data")
        if not (tree / "voznativa" / "evaluation.py").is_file():
            return outcome("NOT_REPLAYABLE", "the revision has no evaluation core")
        changed = [i["path"] for i in record.get("inputs", [])
                   if not (tree / i["path"]).is_file() or sha256_lf(tree / i["path"]) != i.get("sha256_lf")]
        if changed:
            return outcome("DIFFERENT", "inputs at the revision differ from the recorded hashes", inputs=changed)
        (Path(tmp) / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        code = ("import json, sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
                "from voznativa import evaluation; "
                "spec = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')); "
                "r = evaluation.run(spec, Path(sys.argv[1]), recorded_at='replay'); "
                "print(json.dumps({'status': r['status'], 'results_sha256': r['results_sha256']}))")
        done = subprocess.run([sys.executable, "-B", "-E", "-s", "-c", code, str(tree), str(Path(tmp) / "spec.json")],
                              capture_output=True, timeout=1800)
        if done.returncode != 0:
            return outcome("NOT_REPLAYABLE", "the replay process failed",
                           stderr=done.stderr.decode("utf-8", "replace")[-800:])
        replayed = json.loads(done.stdout.decode("utf-8").strip().splitlines()[-1])
    same = replayed["results_sha256"] == record.get("results_sha256")
    return outcome("REPRODUCED" if same else "DIFFERENT",
                   "same results digest at the revision" if same else "the revision gives other results",
                   replayed=replayed, recorded_results_sha256=record.get("results_sha256"),
                   note="reproducibility on this machine; not a signature, not independence")


# --- report -----------------------------------------------------------------------------------

SPLIT_NOTE = {
    "frozen_regression": "regressão: casos congelados, mas escritos pelo desenvolvedor e já usados para corrigir; "
                         "não é generalização",
    "development": "desenvolvimento: o código foi ajustado até passar; não é generalização",
    "prospective_holdout": "holdout prospectivo: congelado antes da mudança; mesmo autor, então não é independente",
    "external_independent_holdout": "holdout independente externo",
    "adversarial": "adversarial/metamórfico",
    "real_provider_study": "estudo com provider real",
}


def _fmt(rate: dict) -> str:
    if not rate["n"]:
        return "sem casos"
    lo, hi = rate["wilson95"]
    return f"{rate['k']}/{rate['n']} ({rate['rate']:.1%}; IC95% {lo:.1%}–{hi:.1%})"


def render(record: dict) -> str:
    lines = [f"# Avaliação `{record['dataset']}`", "",
             f"- Estado: **{record['status']}**; revisão `{(record.get('revision') or '?')[:12]}`"
             f"{' (árvore suja)' if record.get('dirty') else ''}; VozNativa {record['package_version']}; "
             f"Python {record['environment']['python']}",
             f"- Sistema avaliado: `{record['system_under_test']['id']}` ({record['system_under_test']['evidence']}, "
             "determinístico, sem modelo)",
             f"- Integridade: `results_sha256` {record['results_sha256'][:16]}…"]
    if record.get("problems"):
        lines += ["", "## Problemas", ""] + [f"- {p}" for p in record["problems"]]
    lines += ["", "## Não executado", ""] + [f"- {a['arm']}: NOT_RUN — {a['reason']}" for a in record["arms_not_run"]]
    for split, m in record.get("metrics", {}).items():
        lines += ["", f"## {split} ({m['cases']} casos)", "", f"_{SPLIT_NOTE.get(split, split)}._", ""]
        if "semantic_risk" in m:
            s = m["semantic_risk"]
            lines += [f"- Sensibilidade a risco semântico: {_fmt(s['sensitivity'])}",
                      f"- Falso alarme em candidatas limpas: {_fmt(s['false_alarm_rate'])}",
                      f"- Status exato esperado: {_fmt(m['status_agreement'])}",
                      f"- Contagens: {', '.join(f'{k} {v}' for k, v in s['counts'].items())}",
                      f"- Aceitas sem identidade nem julgamento: {s['auto_accepted_without_identity']}"]
        if "decision" in m:
            d = m["decision"]
            lines += [f"- Chamou o modelo quando devia: {_fmt(d['calls_when_needed'])}",
                      f"- Chamadas desnecessárias: {_fmt(d['unnecessary_calls'])}",
                      f"- Decisão exata: {_fmt(d['exact_decision'])}"]
    lines += ["", "Nenhum número acima é validação independente: todos os conjuntos foram escritos pelo "
                  "desenvolvedor do engine, salvo indicação em contrário na tabela de entradas.", "",
              "| Entrada | Split | Adaptador | Congelado | Independente | sha256 (LF) |", "|---|---|---|---|---|---|"]
    for i in record.get("inputs", []):
        lines.append(f"| `{i['path']}` | {i['split']} | {i['adapter']} | {'sim' if i['frozen'] else 'não'} | "
                     f"{'sim' if i['independent'] else 'não'} | `{i['sha256_lf'][:12]}` |")
    return "\n".join(lines) + "\n"
