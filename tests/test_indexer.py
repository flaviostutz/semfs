from pathlib import Path

import pytest

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


def test_index_returns_initialized_state(tmp_path: Path) -> None:
    state = index(str(tmp_path), _config_payload())

    assert state.status is IndexStatus.READY
    assert state.index_name == "index0"
    assert state.database_path.endswith(".semfs/index0/index.db")
    assert state.schema_version == "1"
    assert state.embedding_dimensions == 0


def test_missing_directory_raises() -> None:
    missing_directory = Path("/tmp") / "this-path-should-not-exist-semfs"

    with pytest.raises(FileProcessingError):
        index(str(missing_directory), _config_payload())


def test_embedding_model_loader_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    load_embedding_model.cache_clear()
    calls: list[str] = []

    class FakeModel:
        def __init__(self, model_name: str) -> None:
            calls.append(model_name)

        def get_sentence_embedding_dimension(self) -> int:
            return 384

    monkeypatch.setattr("sentence_transformers.SentenceTransformer", FakeModel)

    first = load_embedding_model("fake-model")
    second = load_embedding_model("fake-model")

    assert first is second
    assert calls == ["fake-model"]
    assert embedding_dimensions("fake-model") == 384
