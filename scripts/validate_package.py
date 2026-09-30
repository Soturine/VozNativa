#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = [
    "README.md",
    "SKILL.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "pyproject.toml",
    "docs/ARCHITECTURE_AND_RESEARCH.md",
    "references/VOICE_STACK.md",
    "references/voice/schema.yml",
    "references/slang/schema.yml",
    "references/patterns/pt-br.md",
    "scripts/analyze.py",
    "scripts/semantic_guard.py",
    "scripts/voice_profile.py",
    "scripts/region_consistency.py",
    "evals/test_foundation.py",
    ".github/workflows/ci.yml",
]

missing = [path for path in REQUIRED if not (ROOT / path).exists()]
if missing:
    raise SystemExit("missing required files: " + ", ".join(missing))

skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
if not skill.startswith("---\n"):
    raise SystemExit("SKILL.md must start with YAML frontmatter")
if "name: voznativa" not in skill:
    raise SystemExit("SKILL.md name must be voznativa")
if 'version: "0.1.0"' not in skill:
    raise SystemExit("SKILL.md version must match foundation release")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for forbidden in ("probabilidade de IA:", "AI probability:"):
    if forbidden.lower() in readme.lower():
        raise SystemExit("README must not advertise AI-authorship probability")

print("VozNativa package v0.1.0 is structurally valid")
