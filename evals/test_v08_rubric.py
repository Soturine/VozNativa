"""v0.8 CP11 (ST-05): Rubric Engine. Objective checks only where the source and
the criterion are verified enough; subjective criteria listed, never scored;
no total or grade. Synthetic sources are labelled; the Enem entry is real."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa import rubric  # noqa: E402

sys.path.insert(0, str(ROOT / "evals"))
from test_v08_standards import entry  # noqa: E402

CRITERIA = [
    {"id": "tamanho", "kind": "objective", "verification": "VERIFIED", "check": {"type": "word_range", "min": 5,
                                                                                 "max": 12}},
    {"id": "secoes", "kind": "objective", "verification": "SOURCE_CITED",
     "check": {"type": "required_sections", "sections": ["Introdução", "Conclusão"]}},
    {"id": "linhas", "kind": "objective", "verification": "CATALOGUED", "check": {"type": "line_range", "max": 2}},
    {"id": "argumento", "kind": "subjective", "verification": "VERIFIED", "statement": "argumenta com coerência"},
    {"id": "sem-check", "kind": "objective", "verification": "VERIFIED"},
]
SOURCE = (entry("manual-sintetico", "2025", "2025-02-01", None, criteria=CRITERIA),)
PROFILE = {"document_type": "tcc", "authority": "universidade-exemplo", "submission_date": "2026-01-10"}
GOOD = "# Introdução\n\nTexto curto do trabalho.\n\n# Conclusão\n\nFim do texto."


class Engine(unittest.TestCase):

    def statuses(self, text, entries=SOURCE, profile=PROFILE):
        return {c["criterion"]: c["status"] for c in rubric.evaluate(text, profile, entries)["criteria"]}

    def test_objective_checks_run_only_where_verified(self):
        s = self.statuses(GOOD)
        self.assertEqual(s, {"tamanho": "MET", "secoes": "MET", "linhas": "NOT_ENFORCED",
                             "argumento": "NEEDS_JUDGMENT", "sem-check": "NOT_ENFORCED"})

    def test_not_met_has_evidence(self):
        report = rubric.evaluate("# Introdução\n\n" + "palavra " * 30, PROFILE, SOURCE)
        by_id = {c["criterion"]: c for c in report["criteria"]}
        self.assertEqual(by_id["tamanho"]["status"], "NOT_MET")
        self.assertEqual(by_id["tamanho"]["evidence"]["max"], 12)
        self.assertEqual(by_id["secoes"]["evidence"]["missing"], ["Conclusão"])
        self.assertEqual(by_id["secoes"]["source"], "manual-sintetico")

    def test_nothing_applies_when_the_source_does_not(self):
        s = self.statuses(GOOD, profile=dict(PROFILE, submission_date="2024-01-10"))
        self.assertEqual(s, {})          # no edition valid then: no criterion at all, not the latest manual's
        unknown = (entry("manual-sintetico", "2025", "2025-02-01", None, status="CATALOGUED", criteria=CRITERIA),)
        self.assertEqual(set(self.statuses(GOOD, entries=unknown).values()), {"NOT_ENFORCED"})

    def test_no_score_anywhere(self):
        report = json.dumps(rubric.evaluate(GOOD, PROFILE, SOURCE)).lower()
        for word in ('"score"', '"grade"', '"nota"', '"total"', '"points"'):
            self.assertNotIn(word, report)


class EnemPilot(unittest.TestCase):

    def test_the_real_entry_enforces_nothing_it_cannot_prove(self):
        profile = {"document_type": "redacao-enem", "series": "enem-redacao-cartilha", "event_year": 2026,
                   "submission_date": "2026-11-08"}
        report = rubric.evaluate("Uma redação.", profile)
        self.assertEqual(report["counts"]["MET"] + report["counts"]["NOT_MET"], 0)
        by_id = {c["criterion"]: c["status"] for c in report["criteria"]}
        self.assertEqual(by_id["cinco-competencias"], "NOT_ENFORCED")
        self.assertEqual(by_id["limite-de-linhas"], "NOT_ENFORCED")
        self.assertEqual(by_id["proposta-de-intervencao-direitos-humanos"], "NEEDS_JUDGMENT")

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "perfil.json"
            path.write_text(json.dumps({"document_type": "redacao-enem", "series": "enem-redacao-cartilha",
                                        "event_year": 2026, "submission_date": "2026-11-08"}), encoding="utf-8")
            done = subprocess.run([sys.executable, "-B", "-m", "voznativa", "rubric",
                                   str(ROOT / "examples" / "quickstart" / "original.txt"),
                                   "--document-profile", str(path)], capture_output=True, cwd=ROOT)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["kind"], "voznativa.rubric_report")


if __name__ == "__main__":
    unittest.main()
