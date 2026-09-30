#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = [
    "README.md",
    "SKILL.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "pyproject.toml",
    "agents/openai.yaml",
    "assets/voice-profile.yml",
    "assets/regional-pack.yml",
    "docs/ARCHITECTURE_AND_RESEARCH.md",
    "docs/DESIGN_SPEC.md",
    "docs/TRACEABILITY.md",
    "references/VOICE_STACK.md",
    "references/registers.md",
    "references/voice/schema.yml",
    "references/voice/idiolect.md",
    "references/slang/schema.yml",
    "references/regions/README.md",
    "references/communities/tech.yml",
    "references/patterns/pt-br.md",
    "references/patterns/structural.md",
    "references/patterns/rhetorical.md",
    "references/patterns/formatting.md",
    "references/patterns/false-positives.md",
    "references/genres/academic.md",
    "references/genres/technical.md",
    "references/genres/corporate.md",
    "references/genres/social.md",
    "references/genres/whatsapp.md",
    "references/genres/literary.md",
    "scripts/analyze.py",
    "scripts/semantic_guard.py",
    "scripts/protect_spans.py",
    "scripts/fact_guard.py",
    "scripts/voice_profile.py",
    "scripts/region_consistency.py",
    "scripts/voice_drift.py",
    "scripts/audit.py",
    "evals/test_foundation.py",
    "evals/academic/README.md",
    "evals/whatsapp/README.md",
    "evals/linkedin/README.md",
    "evals/corporate/README.md",
    "evals/technical/README.md",
    "evals/documentation/README.md",
    "evals/storytelling/README.md",
    "evals/regional/README.md",
    "evals/slang/README.md",
    "evals/false-positive/README.md",
    "evals/adversarial/README.md",
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

trace = (ROOT / "docs" / "TRACEABILITY.md").read_text(encoding="utf-8")
for must_have in ("Semantic/factual lock", "Voice Drift Guard", "Regional Overfit Guard", "Rewrite engine"):
    if must_have not in trace:
        raise SystemExit(f"traceability missing: {must_have}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for forbidden in ("probabilidade de IA:", "AI probability:"):
    if forbidden.lower() in readme.lower():
        raise SystemExit("README must not advertise AI-authorship probability")

print("VozNativa package v0.1.0 is structurally valid")
