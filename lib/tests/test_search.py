from pathlib import Path

import pytest

import semfs
from semfs.config import parse_index_config
from semfs.errors import FileProcessingError, IndexStateError
from semfs.storage import (
    build_file_snapshot,
    chromadb_version,
    chunking_fingerprint,
    detect_snapshot_drift,
    index_is_usable,
    load_embedding_model,
    open_index_store,
    write_file_snapshots,
    write_index_metadata,
)


def _config_payload() -> dict[str, object]:
    return {
        "name": "index0",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 120, "overlap": 30, "edges": "auto"},
    }


def test_chromadb_connection_and_schema(tmp_path: Path) -> None:
    store_path = tmp_path / "test_store"
    store = open_index_store(store_path)

    assert chromadb_version() != ""
    assert store.chunks is not None
    assert store.snapshots is not None
    assert store.index_meta is not None


def test_index_metadata_and_snapshot_drift(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    file_path = root / "a.md"
    file_path.write_text("# Title\nbody\n", encoding="utf-8")

    store = open_index_store(tmp_path / "store")
    config = parse_index_config(_config_payload())

    write_index_metadata(store, config, 3)

    snapshot = build_file_snapshot(root, file_path, chunk_count=1)
    write_file_snapshots(store, [snapshot])

    assert index_is_usable(store, config)
    assert chunking_fingerprint(config)
    assert not detect_snapshot_drift(store, root, [file_path])

    file_path.write_text("# Title\nchanged\n", encoding="utf-8")
    assert detect_snapshot_drift(store, root, [file_path])


def test_chunks_query_merges_contiguous_ranges(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config(_config_payload())

    findings = semfs.chunks({"text": "alpha", "max_results": 1}, str(sample_docs), config=config)

    assert len(findings) == 1
    assert findings[0].file == "alpha.md"
    assert findings[0].from_line == 1
    assert findings[0].to_line >= 6
    assert findings[0].score > 0.5


def test_index_metadata_records_resolved_embedding_model(tmp_path: Path, fake_model: object) -> None:
    _ = fake_model
    root = tmp_path / "docs"
    root.mkdir()
    file_path = root / "a.md"
    file_path.write_text("# Title\nbody\n", encoding="utf-8")

    store = open_index_store(tmp_path / "store")
    config = parse_index_config(_config_payload())

    write_index_metadata(store, config, 3)

    assert index_is_usable(store, config)


def test_chunks_returns_verified_contents(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config(_config_payload())

    findings = semfs.chunks({"text": "alpha", "max_results": 1}, str(sample_docs), fetch_contents=True, config=config)

    assert len(findings) == 1
    assert findings[0].contents is not None
    assert "alpha concept" in findings[0].contents


def test_chunks_fail_when_contents_digest_mismatches(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config({**_config_payload(), "mode": "stale"})

    semfs.index(str(sample_docs), config)
    (sample_docs / "alpha.md").write_text("# Intro\nchanged\n", encoding="utf-8")

    with pytest.raises(FileProcessingError):
        semfs.chunks({"text": "alpha", "max_results": 5}, str(sample_docs), fetch_contents=True, config=config)


def test_files_query_deduplicates_and_ranks_by_best_match(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config(_config_payload())

    findings = semfs.files({"text": "alpha", "max_results": 5}, str(sample_docs), config=config)

    assert [finding.file for finding in findings] == ["alpha.md", "beta.md"]
    assert findings[0].best_score > findings[1].best_score


def test_files_query_breaks_score_ties_by_path(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config(_config_payload())
    (sample_docs / "aardvark.md").write_text("# Aardvark\nalpha\n", encoding="utf-8")
    (sample_docs / "zebra.md").write_text("# Zebra\nalpha\n", encoding="utf-8")

    findings = semfs.files({"text": "alpha", "max_results": 2}, str(sample_docs), config=config)

    assert [finding.file for finding in findings] == ["aardvark.md", "zebra.md"]
    assert findings[0].best_score == findings[1].best_score


def test_load_embedding_model_requires_local_model_when_offline_only_is_enabled(tmp_path: Path) -> None:
    load_embedding_model.cache_clear()

    with pytest.raises(IndexStateError) as exc_info:
        load_embedding_model(
            "sentence-transformers/custom-model",
            str(tmp_path / "missing-model"),
            offline_only=True,
        )

    load_embedding_model.cache_clear()
    assert "offline-only mode is enabled" in str(exc_info.value)


def test_load_embedding_model_uses_bundled_path_for_default_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundled_path = tmp_path / "bundled-model"
    bundled_path.mkdir()
    calls: list[tuple[str, bool]] = []

    class FakeSentenceTransformer:
        def __init__(self, model_source: str, *, local_files_only: bool) -> None:
            calls.append((model_source, local_files_only))

    monkeypatch.setattr("semfs.storage.gt_all_minilm_l6_v2.get_model_path", lambda: bundled_path)
    monkeypatch.setattr("semfs.storage.SentenceTransformer", FakeSentenceTransformer)
    load_embedding_model.cache_clear()

    load_embedding_model("sentence-transformers/all-MiniLM-L6-v2", None, offline_only=False)

    load_embedding_model.cache_clear()
    assert calls == [(str(bundled_path), True)]


def test_load_embedding_model_uses_local_path_when_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, bool]] = []

    class FakeSentenceTransformer:
        def __init__(self, model_source: str, *, local_files_only: bool) -> None:
            calls.append((model_source, local_files_only))

    local_model = tmp_path / "model"
    local_model.mkdir()
    monkeypatch.setattr("semfs.storage.SentenceTransformer", FakeSentenceTransformer)
    load_embedding_model.cache_clear()

    load_embedding_model("sentence-transformers/all-MiniLM-L6-v2", str(local_model), offline_only=False)

    load_embedding_model.cache_clear()
    assert calls == [(str(local_model), False)]


def test_load_embedding_model_preserves_original_exception_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_message = "boom"

    class FakeSentenceTransformer:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise RuntimeError(original_message)

    monkeypatch.setattr("semfs.storage.SentenceTransformer", FakeSentenceTransformer)
    load_embedding_model.cache_clear()

    with pytest.raises(IndexStateError) as exc_info:
        load_embedding_model(
            "sentence-transformers/all-MiniLM-L6-v2",
            str(tmp_path / "missing-model"),
            offline_only=False,
        )

    load_embedding_model.cache_clear()
    assert original_message in str(exc_info.value)
