"""Blind pairwise human review of benchmark outputs (v0.3.0 M4.4).

A reviewer sees the original and two outputs labeled only "A" and "B"
(order drawn from a recorded seed) and answers three separate questions:
which keeps the meaning better, which reads more natural for the genre,
and which they would send. Each answer is bound to the texts and to the
whole task (including the hidden arm mapping, so relabeling the arms after
the fact is detected) and signed with the reviewer key (see
voznativa.review).

The summary counts each (task, signing key) once: a repeated answer is a
duplicate, and repeated answers that disagree are all left out. Several
``judge_id`` values under one key are one participant as far as the
evidence goes, because a declared name is not an identity.

Limits: the task file names the arms so results can be decoded; a reviewer
who opens it is no longer blind. Signatures prove the key holder answered,
not who they are (see ``review.assess``).
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Callable

from .review import _load_key, assess, content_hash, sign, sign_ssh, signer_key

QUESTIONS = (
    ("meaning", "Qual preserva melhor o que o original diz (fatos, prazos, certeza, compromissos)?"),
    ("natural", "Qual soa mais natural para este gênero e canal?"),
    ("send", "Se você fosse o autor, qual enviaria?"),
)
ANSWERS = {"a": "A", "b": "B", "e": "equal", "n": "neither"}


def task_hash(task: dict) -> str:
    """sha256 of the whole task: texts and the arm behind each label."""
    return content_hash(json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def build_tasks(report: dict, focus: str | None = None, seed: int = 0) -> dict:
    """Pairs of arm outputs per case. With ``focus``, only pairs that include
    that arm; identical outputs and failed rows are skipped."""
    rng = random.Random(seed)
    by_case: dict[str, dict[str, str]] = {}
    for row in report["rows"]:
        if "output" not in row:
            continue
        by_case.setdefault(row["id"], {})[row["arm"]] = row["output"]
    tasks = []
    for case_id, outputs in sorted(by_case.items()):
        original = outputs.get("B0-original")  # the B0 arm is the input text itself
        if original is None:
            continue
        for x, y in combinations(sorted(outputs), 2):
            if focus and focus not in (x, y):
                continue
            if outputs[x].strip() == outputs[y].strip():
                continue
            a, b = (x, y) if rng.random() < 0.5 else (y, x)
            tasks.append({"task": f"{case_id}:{a}:{b}", "case": case_id, "original": original,
                          "a": {"arm": a, "text": outputs[a]}, "b": {"arm": b, "text": outputs[b]}})
    rng.shuffle(tasks)
    return {"kind": "voznativa.blind_tasks", "seed": seed, "focus": focus, "tasks": tasks,
            "source_run_sha256": content_hash(json.dumps(report, ensure_ascii=False, sort_keys=True)),
            "note": "arm names are stored for decoding; do not open this file while reviewing"}


def review(tasks: dict, reviewer: str, ask: Callable[[str], str] = input,
           show: Callable[[str], None] = print, limit: int | None = None,
           ssh_key: str | None = None, principal: str | None = None) -> list[dict]:
    key = None if ssh_key else _load_key(create=True)
    answers = []
    for task in tasks["tasks"][:limit]:
        show("\n=== ORIGINAL ===\n" + task["original"])
        show("\n=== TEXTO A ===\n" + task["a"]["text"])
        show("\n=== TEXTO B ===\n" + task["b"]["text"])
        record = {"kind": "voznativa.blind_answer", "task": task["task"], "judge_id": reviewer,
                  "task_sha256": task_hash(task),
                  "original_sha256": content_hash(task["original"]),
                  "a_sha256": content_hash(task["a"]["text"]), "b_sha256": content_hash(task["b"]["text"]),
                  "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        for qid, question in QUESTIONS:
            choice = ""
            while choice not in ANSWERS:
                choice = ask(f"{question} [a/b/e=empate/n=nenhum] ").strip().lower()[:1]
            record[qid] = ANSWERS[choice]
        answers.append(sign_ssh(record, ssh_key, principal or reviewer) if ssh_key else sign(record, key))
    return answers


def _rejection(answer: dict, task: dict | None, assurance: dict) -> str | None:
    if answer.get("kind") != "voznativa.blind_answer":
        return "not a blind answer"
    if task is None:
        return "unknown task"
    if assurance["integrity"] != "valid":
        return f"signature {assurance['check']}"
    expected = {"task_sha256": task_hash(task), "original_sha256": content_hash(task["original"]),
                "a_sha256": content_hash(task["a"]["text"]), "b_sha256": content_hash(task["b"]["text"])}
    for field, value in expected.items():
        if answer.get(field) != value:
            return f"{field} does not match the task" if answer.get(field) else f"missing {field}"
    for qid, _ in QUESTIONS:
        if answer.get(qid) not in ANSWERS.values():
            return f"invalid answer for {qid}: {answer.get(qid)!r}"
    return None


def summarize(tasks: dict, answers: list[dict], registry: Path | None = None) -> dict:
    """Wins per arm and question, from valid, deduplicated answers only."""
    index = {t["task"]: t for t in tasks["tasks"]}
    rejected, valid = [], defaultdict(list)
    for position, answer in enumerate(answers):
        task = index.get(answer.get("task"))
        assurance = assess(answer, registry)
        reason = _rejection(answer, task, assurance)
        if reason:
            rejected.append({"position": position, "task": answer.get("task"), "judge_id": answer.get("judge_id"),
                             "reason": reason})
            continue
        valid[(answer["task"], signer_key(answer))].append((position, answer, assurance))

    names: dict[str, set] = defaultdict(set)  # every declared name seen under a key
    for (_, key), group in valid.items():
        names[key].update(a.get("judge_id") for _, a, _ in group)
    counted, duplicates, conflicts = [], 0, []
    for (task_id, key), group in valid.items():
        choices = {tuple(a[q] for q, _ in QUESTIONS) for _, a, _ in group}
        if len(choices) > 1:
            conflicts.append({"task": task_id, "key": key, "answers": len(group)})
            continue
        duplicates += len(group) - 1
        counted.append(group[0])

    table: dict[str, dict[str, dict[str, int]]] = {}
    participants: dict[str, dict] = {}
    for _, answer, assurance in counted:
        task = index[answer["task"]]
        person = participants.setdefault(signer_key(answer), {
            "key": signer_key(answer), "method": assurance["method"], "judge_ids": names[signer_key(answer)],
            "answers": 0, "independence": assurance["independence"],
            "independence_basis": assurance["independence_basis"]})
        person["answers"] += 1
        for qid, _ in QUESTIONS:
            for side in ("a", "b"):
                arm = task[side]["arm"]
                cell = table.setdefault(arm, {}).setdefault(qid, {"win": 0, "loss": 0, "tie": 0, "neither": 0})
                choice = answer[qid]
                if choice == "equal":
                    cell["tie"] += 1
                elif choice == "neither":
                    cell["neither"] += 1
                elif choice == side.upper():
                    cell["win"] += 1
                else:
                    cell["loss"] += 1
    people = [dict(p, judge_ids=sorted(p["judge_ids"]), shared_key=len(p["judge_ids"]) > 1)
              for p in sorted(participants.values(), key=lambda p: p["key"])]
    return {"kind": "voznativa.blind_summary", "answers_received": len(answers),
            "answers_counted": len(counted), "answers_rejected": len(rejected),
            "duplicates_ignored": duplicates, "conflicting_duplicates": conflicts,
            "participants": people,
            "independent_participants": sum(p["independence"] == "declared" for p in people),
            "by_arm": table,
            "counted": [{"position": pos, "task": a["task"], "key": signer_key(a), "judge_id": a.get("judge_id"),
                         "recorded_at": a.get("recorded_at")} for pos, a, _ in sorted(counted, key=lambda c: c[0])],
            "rejected": rejected,
            "note": "human judgments only; one answer per task and signing key; a participant is a key, "
                    "not a declared name; independence is at most declared in the reviewer registry"}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
