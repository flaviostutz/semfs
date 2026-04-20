from pathlib import Path

from semfs.benchmark import run_benchmark
from semfs.synthetic_data import dataset_spec


def _config_payload() -> dict[str, object]:
    return {
        "name": "large-index",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 240, "overlap": 40, "edges": "auto"},
    }


def test_large_benchmark_persists_complete_artifact(large_corpus: Path, fake_model: object, tmp_path: Path) -> None:
    _ = fake_model
    spec = dataset_spec("large")

    result = run_benchmark(
        dataset_name="large",
        dataset_root=large_corpus,
        config=_config_payload(),
        query_text="gamma",
        output_dir=tmp_path / "benchmarks",
    )

    assert result.dataset_name == "large"
    assert result.folder_count == spec.folder_count
    assert result.file_count == spec.file_count
    assert result.max_depth == spec.max_depth
    assert result.index_seconds >= 0.0
    assert result.query_seconds >= 0.0
    artifact_path = Path(result.artifact_path)
    assert artifact_path.exists()
    assert artifact_path.parent == tmp_path / "benchmarks"


def test_large_dataset_shape_is_deterministic(large_corpus: Path) -> None:
    files = sorted(large_corpus.glob("**/*.md"))
    folders = {path.parent.relative_to(large_corpus) for path in files}
    max_depth = max(len(folder.parts) for folder in folders)

    assert len(files) == dataset_spec("large").file_count
    assert len(folders) == dataset_spec("large").folder_count
    assert max_depth == dataset_spec("large").max_depth
