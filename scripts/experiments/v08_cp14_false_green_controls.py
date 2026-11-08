"""v0.8 CP14: negative controls for the false-green leads of the Assertiva dogfood (AGENT_OBSERVED).

Each control breaks, in a disposable full copy of a source tree, the behaviour one test claims to
protect (usually by making the code produce nothing), then runs only that test. A test that still
passes is a confirmed false green for that break; a test that fails detects it. The unmutated test
runs first in the same copy kind (control): a lead is only judged when the control passes.

Leads come from Assertiva 0.10.1 (CONDITIONAL_ASSERTION) and from the local UNCHECKED_ALL patch
written during this dogfood (docs/releases/v0.8/upstream/). The judgement of each lead is the
agent's, recorded with this command; nothing here is independent review.

    python -B scripts/experiments/v08_cp14_false_green_controls.py --root <tree> --out <file.json>
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# (id, lead source, test, file, old, new)
CONTROLS = [
    ("events-detector-disabled", "CONDITIONAL_ASSERTION",
     "evals.test_v08_events.Recipients.test_new_codes_are_never_critical",
     "voznativa/compare.py", "    issues += _event_issues(src, out, alignment)\n", ""),
    ("semantic-risk-metric-removed", "CONDITIONAL_ASSERTION",
     "evals.test_v08_evaluation.RepositoryDataset.test_nothing_is_auto_accepted_without_identity",
     "voznativa/evaluation.py", '            entry["semantic_risk"] = _semantic_metrics(gate)\n', ""),
    ("run-records-no-results", "UNCHECKED_ALL",
     "evals.test_v08_evaluation.Metrics.test_the_record_keeps_hashes_not_texts",
     "voznativa/evaluation.py", "            results.append(row)\n", "            pass\n"),
    ("run-records-no-inputs", "UNCHECKED_ALL",
     "evals.test_v08_evaluation.RepositoryDataset.test_no_source_is_called_independent",
     "voznativa/evaluation.py", '        inputs.append({"path": src["path"],', '        [].append({"path": src["path"],'),
    ("no-frame-extracted", "UNCHECKED_ALL",
     "evals.test_v08_events.Frames.test_what_is_not_a_recipient",
     "voznativa/events.py", "    out = []\n    interesting", "    return []\n    out = []\n    interesting"),
    ("blind-focus-drops-all", "UNCHECKED_ALL",
     "evals.test_blind_review.Tasks.test_focus_and_seeded_order",
     "voznativa/blind.py", "if focus and focus not in (x, y):", "if focus:"),
    ("community-withdrawn-not-recorded", "UNCHECKED_ALL",
     "evals.test_community_and_stuffing.Activation."
     "test_keeps_the_texts_terms_and_withdraws_anglicism_findings_only_when_requested",
     "voznativa/community.py", "return with_findings(report, kept, withdrawn, text)",
     "return with_findings(report, kept, [], text)"),
    ("provenance-returns-nothing", "UNCHECKED_ALL",
     "evals.test_containment.MultiKeySplits.test_works_of_one_author_never_cross_a_split",
     "voznativa/corpus/processing.py", "extra_groups=group_keys(entry, r)[1:]))\n    return out\n",
     "extra_groups=group_keys(entry, r)[1:]))\n    return []\n"),
    ("policy-rows-missing-for-unknown-licence", "UNCHECKED_ALL",
     "evals.test_corpus_tei.ManifestAndCache.test_per_document_manifest_never_inherits_the_card",
     "voznativa/corpus/processing.py", "for op in MANIFEST_OPERATIONS}",
     "for op in MANIFEST_OPERATIONS if lic != 'unknown' or op == 'EXPORT_STATISTICS'}"),
    ("plan-without-sentence-rows", "UNCHECKED_ALL",
     "evals.test_longform.LiteraryPolicy.test_literary_notes_never_decide_or_get_acted_on",
     "voznativa/planner.py", '        "sentences": rows,\n', '        "sentences": [],\n'),
    ("case-loader-returns-nothing", "UNCHECKED_ALL",
     "evals.test_patterns.PatternSuite.test_separates_ai_style_drafts_from_natural_texts",
     "voznativa/benchmark.py", "        if not line:\n            continue\n", "        continue\n"),
    # Rejected lead: the outcome assertion already depends on the units, so this break is caught.
    ("timeout-units-dropped", "UNCHECKED_ALL",
     "evals.test_document_rewrite.SegmentedRewrite.test_timeout_returns_the_original",
     "voznativa/engine.py", '            units.append(dict(record, outcome="not_run", reason="document timeout"))\n', ""),
]


def _run(tree: Path, test: str) -> int:
    env = dict(os.environ, PYTHONPATH=str(tree), PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, "-B", "-m", "unittest", test], cwd=tree, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace").returncode


def _copy(root: Path, tmp: str, name: str) -> Path:
    dst = Path(tmp) / name
    shutil.copytree(root, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return dst


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        control = _copy(args.root, tmp, "control")
        for cid, lead, test, rel, old, new in CONTROLS:
            row = {"id": cid, "lead": lead, "test": test, "file": rel,
                   "control": "PASS" if _run(control, test) == 0 else "FAIL"}
            tree = _copy(args.root, tmp, cid)
            body = (tree / rel).read_text(encoding="utf-8")
            row["occurrences"] = body.count(old)
            if row["occurrences"] != 1 or row["control"] != "PASS":
                row["verdict"] = "NOT_JUDGED"
            else:
                (tree / rel).write_text(body.replace(old, new), encoding="utf-8")
                row["mutant"] = "PASS" if _run(tree, test) == 0 else "FAIL"
                row["verdict"] = "FALSE_GREEN_CONFIRMED" if row["mutant"] == "PASS" else "DETECTED"
            shutil.rmtree(tree, ignore_errors=True)
            rows.append(row)
            print(f"{cid:40s} control={row['control']} mutant={row.get('mutant', '-'):4s} {row['verdict']}")
    summary = {v: sum(r["verdict"] == v for r in rows) for v in ("FALSE_GREEN_CONFIRMED", "DETECTED", "NOT_JUDGED")}
    record = {"kind": "voznativa.v08_cp14_false_green_controls", "schema_version": 1, "evidence": "AGENT_OBSERVED",
              "python": platform.python_version(), "platform": platform.system(), "summary": summary, "controls": rows}
    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
