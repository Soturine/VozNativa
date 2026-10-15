# VozNativa Benchmarks

Benchmarking is split into:

- `cases/`: frozen inputs and expected invariants;
- `outputs/<system>/`: generated candidates;
- `results/`: generated reports (normally ignored/versioned selectively);
- `manifest.json`: system/version metadata.

The runner does **not** call detectors.

Basic flow:

```bash
python scripts/benchmark_runner.py   benchmarks/cases/smoke.jsonl   benchmarks/outputs
```

Each output file uses the case id as filename:

```text
benchmarks/outputs/
  raw/
    tech-001.txt
  one-line/
    tech-001.txt
  blader/
    tech-001.txt
  work-humanizer/
    tech-001.txt
  emulate/
    tech-001.txt
  voznativa/
    tech-001.txt
```

The deterministic report currently measures protected-span preservation and length change. Claim-level semantics, voice and human pairwise review are later layers.
