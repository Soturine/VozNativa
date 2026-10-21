"""v0.4.0 M0.4/M0.5: blind-summary counting and what a review signature shows.

v0.3.0 defects pinned here:
* blind-summary did not check original_sha256, counted repeated answers,
  accepted any signed value as a choice and could not tell participants
  apart, so counts could be inflated;
* the arm mapping lived only in the unsigned task file, so relabeling arms
  after the answers flipped the results without breaking any signature;
* a "verified" review said nothing about who held the key or whether the
  reviewer was independent.
No human result is produced here: the tests type answers to exercise the mechanism.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voznativa.blind import build_tasks, review, summarize
from voznativa.compare import apply_judgment, compare
from voznativa.judge import validate
from voznativa.review import _load_key, assess, interactive_review, sign

RUN = {"rows": [
    {"arm": "B0-original", "id": "c1", "output": "Original um."},
    {"arm": "X", "id": "c1", "output": "Texto do X."},
    {"arm": "B0-original", "id": "c2", "output": "Original dois."},
    {"arm": "X", "id": "c2", "output": "Outro do X."},
]}


class TempEnv:
    """A temporary HMAC key (and optionally a reviewer registry)."""

    def __init__(self, **extra):
        self.extra = extra

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = {k: os.environ.get(k) for k in ("VOZNATIVA_REVIEW_KEY", "VOZNATIVA_REVIEWERS")}
        os.environ["VOZNATIVA_REVIEW_KEY"] = str(Path(self.tmp.name) / "k")
        os.environ["VOZNATIVA_REVIEWERS"] = str(Path(self.tmp.name) / "no-registry")
        os.environ.update(self.extra)
        return Path(self.tmp.name)

    def __exit__(self, *exc):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()


def answer_all(tasks, reviewer, choice="a", **kwargs):
    typed = iter([choice] * 3 * len(tasks["tasks"]))
    return review(tasks, reviewer, ask=lambda _: next(typed), show=lambda _: None, **kwargs)


class BlindSummaryCounting(unittest.TestCase):
    def setUp(self):
        self.tasks = build_tasks(RUN, seed=1)

    def test_repeated_answers_count_once(self):
        with TempEnv():
            answers = answer_all(self.tasks, "ana")
            summary = summarize(self.tasks, answers + answers)
        self.assertEqual(summary["answers_received"], 4)
        self.assertEqual(summary["answers_counted"], 2)
        self.assertEqual(summary["duplicates_ignored"], 2)

    def test_disagreeing_repeats_are_left_out(self):
        with TempEnv():
            first = answer_all(self.tasks, "ana", "a")
            second = answer_all(self.tasks, "ana", "b")
            summary = summarize(self.tasks, first + second)
        self.assertEqual(summary["answers_counted"], 0)
        self.assertEqual(len(summary["conflicting_duplicates"]), 2)

    def test_a_new_name_under_the_same_key_is_not_a_new_participant(self):
        with TempEnv():
            summary = summarize(self.tasks, answer_all(self.tasks, "ana") + answer_all(self.tasks, "bia"))
        self.assertEqual(summary["answers_counted"], 2)
        self.assertEqual(len(summary["participants"]), 1)
        self.assertTrue(summary["participants"][0]["shared_key"])
        self.assertEqual(summary["participants"][0]["judge_ids"], ["ana", "bia"])

    def test_every_hash_is_checked(self):
        with TempEnv():
            answers = answer_all(self.tasks, "ana")
            edited = json.loads(json.dumps(self.tasks))
            edited["tasks"][0]["original"] = "Outro original."
            summary = summarize(edited, answers)
        self.assertEqual(summary["answers_counted"], 1)
        self.assertIn("does not match the task", summary["rejected"][0]["reason"])

    def test_relabeling_the_arms_after_answering_is_detected(self):
        with TempEnv():
            answers = answer_all(self.tasks, "ana")
            swapped = json.loads(json.dumps(self.tasks))
            swapped["tasks"][0]["a"]["arm"], swapped["tasks"][0]["b"]["arm"] = \
                swapped["tasks"][0]["b"]["arm"], swapped["tasks"][0]["a"]["arm"]
            summary = summarize(swapped, answers)
        self.assertEqual(summary["rejected"][0]["reason"], "task_sha256 does not match the task")

    def test_a_signed_but_invalid_choice_is_rejected(self):
        with TempEnv():
            answers = answer_all(self.tasks, "ana")
            bogus = sign(dict({k: v for k, v in answers[0].items() if k != "signature"}, meaning="X"),
                         _load_key())
            summary = summarize(self.tasks, [bogus])
        self.assertEqual(summary["answers_counted"], 0)
        self.assertIn("invalid answer for meaning", summary["rejected"][0]["reason"])

    def test_counted_answers_are_traceable(self):
        with TempEnv():
            summary = summarize(self.tasks, answer_all(self.tasks, "ana"))
        self.assertEqual([c["position"] for c in summary["counted"]], [0, 1])
        self.assertTrue(all(c["key"].startswith("hmac:") for c in summary["counted"]))
        self.assertEqual(summary["independent_participants"], 0)


class ReviewAssurance(unittest.TestCase):
    TEXTS = ("O relatório sai na sexta.", "O relatório sai sexta-feira.")

    def signed(self, verdict="e", **kwargs):
        typed = iter([verdict, "conferi prazo e dia da semana"])
        return interactive_review(*self.TEXTS, compare(*self.TEXTS), "ana", ask=lambda _: next(typed),
                                  show=lambda _: None, **kwargs)

    def test_hmac_review_separates_the_four_properties(self):
        with TempEnv():
            report = assess(self.signed())
        self.assertEqual(report["integrity"], "valid")
        self.assertIn("shared HMAC secret", report["key_possession"])
        self.assertEqual(report["declared_identity"]["judge_id"], "ana")
        self.assertFalse(report["declared_identity"]["verified"])
        self.assertEqual(report["independence"], "not_established")

    def test_accepted_review_carries_its_assurance(self):
        with TempEnv():
            judgment = validate(self.signed(), *self.TEXTS)
            merged = apply_judgment(compare(*self.TEXTS), judgment)
        self.assertEqual(merged["status"], "accepted_by_human")
        self.assertEqual(merged["human_review"]["assurance"]["independence"], "not_established")

    def test_tampered_review_has_no_integrity(self):
        with TempEnv():
            forged = dict(self.signed(), verdict="not_equivalent")
            self.assertEqual(assess(forged)["integrity"], "invalid")


@unittest.skipUnless(shutil.which("ssh-keygen"), "ssh-keygen not installed")
class SshSignedReviews(unittest.TestCase):
    """The reviewer signs with a private key the project never holds."""

    def make_registry(self, directory: Path, principal: str, relationship: str) -> Path:
        key = directory / "id_reviewer"
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", principal, "-f", str(key)],
                       check=True, stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
        registry = directory / "reviewers"
        registry.mkdir()
        public = (directory / "id_reviewer.pub").read_text(encoding="ascii").strip()
        (registry / "allowed_signers").write_text(f"{principal} {public}\n", encoding="ascii")
        (registry / "registry.json").write_text(json.dumps({"reviewers": {principal: {
            "declared_name": "Revisora Externa", "relationship": relationship}}}), encoding="utf-8")
        return key

    def test_registered_independent_key(self):
        with TempEnv() as tmp:
            key = self.make_registry(tmp, "rev@example.org", "independent")
            os.environ["VOZNATIVA_REVIEWERS"] = str(tmp / "reviewers")
            tasks = build_tasks(RUN, seed=1)
            answers = answer_all(tasks, "rev", ssh_key=str(key), principal="rev@example.org")
            summary = summarize(tasks, answers)
            judgment = ReviewAssurance.signed(ReviewAssurance(), ssh_key=str(key), principal="rev@example.org")
            report = assess(judgment)
            forged = dict(judgment, verdict="not_equivalent")
            swapped = json.loads(json.dumps(judgment))
            swapped["signature"]["principal"] = "other@example.org"
            states = (assess(forged)["integrity"], assess(swapped)["integrity"])
        self.assertEqual(summary["answers_counted"], 2)
        self.assertEqual(summary["independent_participants"], 1)
        self.assertEqual(report["integrity"], "valid")
        self.assertEqual(report["independence"], "declared")
        self.assertIn("private SSH key", report["key_possession"])
        self.assertEqual(states, ("invalid", "invalid"))

    def test_developer_key_is_never_independent(self):
        with TempEnv() as tmp:
            key = self.make_registry(tmp, "dev@example.org", "developer")
            os.environ["VOZNATIVA_REVIEWERS"] = str(tmp / "reviewers")
            report = assess(ReviewAssurance.signed(ReviewAssurance(), ssh_key=str(key), principal="dev@example.org"))
        self.assertEqual(report["independence"], "none")

    def test_unregistered_principal_cannot_be_verified(self):
        with TempEnv() as tmp:
            key = self.make_registry(tmp, "rev@example.org", "independent")
            os.environ["VOZNATIVA_REVIEWERS"] = str(tmp / "reviewers")
            report = assess(ReviewAssurance.signed(ReviewAssurance(), ssh_key=str(key), principal="ghost@example.org"))
        self.assertEqual((report["integrity"], report["check"]), ("unverifiable", "unknown_signer"))


if __name__ == "__main__":
    unittest.main()
