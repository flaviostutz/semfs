"""Benchmark artifact helpers for the semfs scaffold."""

import json
from datetime import UTC, datetime
from pathlib import Path


def write_placeholder_benchmark(output_dir: str = "benchmarks") -> Path:
    """Write a placeholder benchmark artifact to the configured output directory."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    artifact = target_dir / "scaffold-benchmark.json"
    payload = {
        "dataset": "scaffold",
        "index_seconds": 0.0,
        "query_seconds": 0.0,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    artifact.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")
    return artifact
