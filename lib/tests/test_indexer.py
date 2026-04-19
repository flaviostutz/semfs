from pathlib import Path

import pytest

import semfs
from semfs.errors import FileProcessingError
from semfs.indexer import embedding_dimensions, index, load_embedding_model
from semfs.models import IndexStatus


def _config_payload() -> dict[str, object]:
    return {
        "name": "index0",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 120, "overlap": 30, "edges": "auto"},
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    }


def test_index_returns_initialized_state(tmp_path: Path, fake_model: object) -> None:
    _ = fake_model
    file_path = tmp_path / "doc.md"
    file_path.write_text("# Title\nalpha body\n", encoding="utf-8")

    state = index(str(tmp_path), _config_payload())

    assert state.status is IndexStatus.READY
    assert state.index_name == "index0"
    assert state.database_path.endswith(".semfs/index0")
    assert state.schema_version == "1"
    assert state.embedding_dimensions == 3
    assert state.indexed_files == 1
    assert state.indexed_chunks >= 1


def test_missing_directory_raises() -> None:
    missing_directory = Path("/tmp") / "this-path-should-not-exist-semfs"

    with pytest.raises(FileProcessingError):
        index(str(missing_directory), _config_payload())


def test_embedding_model_loader_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    load_embedding_model.cache_clear()
    calls: list[str] = []

    class FakeModel:
        def __init__(self, model_name: str, *, local_files_only: bool = False) -> None:
            calls.append(model_name)
            assert local_files_only is True

        def get_sentence_embedding_dimension(self) -> int:
            return 384

    monkeypatch.setattr("sentence_transformers.SentenceTransformer", FakeModel)

    first = load_embedding_model("fake-model")
    second = load_embedding_model("fake-model")

    assert first is second
    assert calls == ["fake-model"]
    assert embedding_dimensions("fake-model") == 384


def test_stale_mode_reuses_existing_index_when_files_change(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = {**_config_payload(), "mode": "stale"}

    initial = index(str(sample_docs), config)
    (sample_docs / "alpha.md").write_text("# Intro\nbeta only\n", encoding="utf-8")

    findings = semfs.files({"text": "alpha", "max_results": 5}, str(sample_docs), config)

    assert initial.status is IndexStatus.READY
    assert findings[0].file == "alpha.md"


def test_auto_mode_rebuilds_when_files_change(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = {**_config_payload(), "mode": "auto"}

    index(str(sample_docs), config)
    (sample_docs / "alpha.md").write_text("# Intro\nbeta beta beta\n", encoding="utf-8")

    findings = semfs.chunks({"text": "alpha", "max_results": 5}, str(sample_docs), fetch_contents=True, config=config)

    alpha_finding = next(finding for finding in findings if finding.file == "alpha.md")
    assert alpha_finding.contents is not None
    assert "beta beta beta" in alpha_finding.contents


def test_refresh_mode_rebuilds_before_query(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    stale_config = {**_config_payload(), "mode": "stale"}
    refresh_config = {**_config_payload(), "mode": "refresh"}

    index(str(sample_docs), stale_config)
    (sample_docs / "alpha.md").write_text("# Intro\nbeta beta beta\n", encoding="utf-8")

    findings = semfs.chunks(
        {"text": "alpha", "max_results": 5}, str(sample_docs), fetch_contents=True, config=refresh_config
    )

    alpha_finding = next(finding for finding in findings if finding.file == "alpha.md")
    assert alpha_finding.contents is not None
    assert "beta beta beta" in alpha_finding.contents


def test_inmemory_mode_keeps_index_off_disk(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model

    state = index(str(sample_docs), {**_config_payload(), "mode": "inmemory"})

    assert state.status is IndexStatus.EPHEMERAL
    assert state.database_path == ":memory:"
    assert not (sample_docs / ".semfs").exists()


def test_transient_mode_discards_temp_index_after_operation(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model

    state = index(str(sample_docs), {**_config_payload(), "mode": "transient"})

    assert state.status is IndexStatus.EPHEMERAL
    assert state.database_path != ":memory:"
    assert not Path(state.database_path).exists()
    assert not (sample_docs / ".semfs").exists()
