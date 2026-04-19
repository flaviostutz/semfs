from pathlib import Path

import semfs
from semfs.benchmark import run_benchmark
from semfs.synthetic_data import dataset_spec


def _config_payload() -> dict[str, object]:
    return {
        "name": "small-index",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 240, "overlap": 40, "edges": "auto"},
    }


def test_small_corpus_index_and_query_flow(small_corpus: Path, fake_model: object) -> None:
    _ = fake_model

    state = semfs.index(str(small_corpus), _config_payload())
    chunk_results = semfs.chunks({"text": "alpha", "max_results": 5}, str(small_corpus), config=_config_payload())
    file_results = semfs.files({"text": "alpha", "max_results": 5}, str(small_corpus), _config_payload())

    assert state.indexed_files == dataset_spec("small").file_count
    assert state.indexed_chunks >= dataset_spec("small").file_count
    assert chunk_results
    assert file_results


def test_small_benchmark_persists_artifact(small_corpus: Path, fake_model: object, tmp_path: Path) -> None:
    _ = fake_model
    spec = dataset_spec("small")

    result = run_benchmark(
        dataset_name="small",
        dataset_root=small_corpus,
        config=_config_payload(),
        query_text="alpha",
        output_dir=tmp_path / "benchmarks",
    )

    assert result.dataset_name == "small"
    assert result.folder_count == spec.folder_count
    assert result.file_count == spec.file_count
    assert result.max_depth == spec.max_depth
    assert Path(result.artifact_path).exists()
