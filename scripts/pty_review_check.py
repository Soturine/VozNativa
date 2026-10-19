#!/usr/bin/env python3
"""Exercise `voznativa review` through a real pseudo-terminal (POSIX only).

This proves the interactive path works when a terminal exists and is
refused when it does not. It does not prove that a *person* typed the
answers: here the script types them. That limit is the point of the
signature design, documented in voznativa/review.py.
"""
import json
import os
import pty
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    os.environ["VOZNATIVA_REVIEW_KEY"] = str(tmp / "review.key")
    (tmp / "a.txt").write_text("Apenas admins apagam projetos.", encoding="utf-8")
    (tmp / "b.txt").write_text("Admins apagam projetos.", encoding="utf-8")
    out = tmp / "review.json"
    argv = [sys.executable, "-m", "voznativa", "review", str(tmp / "a.txt"), str(tmp / "b.txt"),
            "--reviewer", "pty-check", "--out", str(out)]

    pid, fd = pty.fork()
    if pid == 0:
        os.execv(sys.executable, argv)
    transcript = b""
    for answer in (b"e\n", b"conferi o quantificador apenas com cuidado\n"):
        time.sleep(1.5)
        os.write(fd, answer)
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        transcript += chunk
    _, status = os.waitpid(pid, 0)
    code = os.waitstatus_to_exitcode(status)

    judgment = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    compared = subprocess.run([*argv[:3], "compare", str(tmp / "a.txt"), str(tmp / "b.txt"), "--judgment", str(out)],
                              capture_output=True)
    final = json.loads(compared.stdout) if compared.stdout else {}
    refused = subprocess.run(argv, capture_output=True, stdin=subprocess.DEVNULL)
    result = {
        "tty_exit_code": code,
        "signed": bool(judgment.get("signature")),
        "method": (judgment.get("attestation") or {}).get("method"),
        "final_status_with_signed_review": final.get("status"),
        "non_tty_refused_exit_code": refused.returncode,
    }
    print(json.dumps(result, indent=2))
    ok = (result["signed"] and result["final_status_with_signed_review"] == "accepted_by_human"
          and result["non_tty_refused_exit_code"] == 64)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
