"""Blind pairwise human review of benchmark outputs (v0.3.0 M4.4).

A reviewer sees the original and two outputs labeled only "A" and "B"
(order drawn from a recorded seed) and answers three separate questions:
which keeps the meaning better, which reads more natural for the genre,
and which they would send. Each answer is bound to the texts and signed
with the reviewer key (see voznativa.review). The summary counts only
answers whose signature verifies on this machine.

Limits: the task file names the arms so results can be decoded; a reviewer
who opens it is no longer blind. Signatures prove the key holder answered,
not who they are.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Callable

from .review import _load_key, content_hash, sign, verify

QUESTIONS = (
    ("meaning", "Qual preserva melhor o que o original diz (fatos, prazos, certeza, compromissos)?"),
    ("natural", "Qual soa mais natural para este gênero e canal?"),
    ("send", "Se você fosse o autor, qual enviaria?"),
)
ANSWERS = {"a": "A", "b": "B", "e": "equal", "n": "neither"}


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
            "note": "arm names are stored for decoding; do not open this file while reviewing"}


def review(tasks: dict, reviewer: str, ask: Callable[[str], str] = input,
           show: Callable[[str], None] = print, limit: int | None = None) -> list[dict]:
    key = _load_key(create=True)
    answers = []
    for task in tasks["tasks"][:limit]:
        show("\n=== ORIGINAL ===\n" + task["original"])
        show("\n=== TEXTO A ===\n" + task["a"]["text"])
        show("\n=== TEXTO B ===\n" + task["b"]["text"])
        record = {"kind": "voznativa.blind_answer", "task": task["task"], "judge_id": reviewer,
                  "original_sha256": content_hash(task["original"]),
                  "a_sha256": content_hash(task["a"]["text"]), "b_sha256": content_hash(task["b"]["text"]),
                  "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        for qid, question in QUESTIONS:
            choice = ""
            while choice not in ANSWERS:
                choice = ask(f"{question} [a/b/e=empate/n=nenhum] ").strip().lower()[:1]
            record[qid] = ANSWERS[choice]
        answers.append(sign(record, key))
    return answers


def summarize(tasks: dict, answers: list[dict]) -> dict:
    """Wins per arm and question, from verified answers only."""
    index = {t["task"]: t for t in tasks["tasks"]}
    table: dict[str, dict[str, dict[str, int]]] = {}
    counted = rejected = 0
    for answer in answers:
        task = index.get(answer.get("task"))
        if (not task or verify(answer) != "verified"
                or answer.get("a_sha256") != content_hash(task["a"]["text"])
                or answer.get("b_sha256") != content_hash(task["b"]["text"])):
            rejected += 1
            continue
        counted += 1
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
    return {"kind": "voznativa.blind_summary", "answers_counted": counted, "answers_rejected": rejected,
            "by_arm": table,
            "note": "human judgments only; empty until real reviewers answer"}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
