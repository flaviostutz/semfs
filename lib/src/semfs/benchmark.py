"""Benchmark execution helpers for semfs example corpora."""

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import semfs
from semfs.models import BenchmarkRun, IndexConfig
from semfs.synthetic_data import create_dataset, dataset_spec


def _artifact_path(output_dir: Path, dataset_name: str, recorded_at: datetime) -> Path:
    timestamp = recorded_at.strftime("%Y%m%dT%H%M%S%fZ")
    return output_dir / f"{dataset_name}-{timestamp}.json"


def run_benchmark(
    dataset_name: str,
    dataset_root: Path,
    config: IndexConfig | Mapping[str, Any],
    query_text: str,
    output_dir: Path | str = "benchmarks",
    *,
    verbose: bool = False,
) -> BenchmarkRun:
    """Run one benchmark scenario and persist its JSON artifact."""
    parsed_config = IndexConfig.model_validate(config)
    benchmark_query = {"text": query_text, "max_results": 10}
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    index_config = parsed_config.model_copy(update={"mode": "refresh"})
    query_config = parsed_config.model_copy(update={"mode": "stale"})

    index_started = perf_counter()
    semfs.index(str(dataset_root), index_config, verbose=verbose)
    index_seconds = perf_counter() - index_started

    query_started = perf_counter()
    semfs.chunks(benchmark_query, str(dataset_root), config=query_config, verbose=verbose)
    semfs.files(benchmark_query, str(dataset_root), query_config, verbose=verbose)
    query_seconds = perf_counter() - query_started

    spec = dataset_spec(dataset_name)
    recorded_at = datetime.now(UTC)
    artifact = _artifact_path(target_dir, dataset_name, recorded_at)
    result = BenchmarkRun(
        dataset_name=dataset_name,
        folder_count=spec.folder_count,
        file_count=spec.file_count,
        max_depth=spec.max_depth,
        index_seconds=index_seconds,
        query_seconds=query_seconds,
        artifact_path=str(artifact),
        recorded_at=recorded_at,
    )
    artifact.write_text(f"{json.dumps(result.model_dump(mode='json'), indent=2)}\n", encoding="utf-8")
    return result


def run_benchmark_suite(
    root: Path,
    config: IndexConfig | Mapping[str, Any],
    query_text: str,
    output_dir: Path | str = "benchmarks",
    *,
    verbose: bool = False,
) -> list[BenchmarkRun]:
    """Generate both benchmark corpora, run them, and persist one artifact per dataset."""
    results: list[BenchmarkRun] = []
    for dataset_name in ("small", "large"):
        dataset_root = root / dataset_name
        create_dataset(dataset_root, dataset_name)
        results.append(run_benchmark(dataset_name, dataset_root, config, query_text, output_dir, verbose=verbose))
    return results


def write_placeholder_benchmark(output_dir: str = "benchmarks") -> Path:
    """Preserve the scaffold benchmark command with a lightweight placeholder artifact."""
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
