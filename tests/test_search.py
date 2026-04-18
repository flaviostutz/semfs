from pathlib import Path

import pytest

import semfs
from semfs.config import parse_index_config
from semfs.errors import FileProcessingError
from semfs.storage import (
    build_file_snapshot,
    chunking_fingerprint,
    connect_database,
    detect_snapshot_drift,
    ensure_schema,
    index_is_usable,
    sqlite_vec_version,
    write_file_snapshots,
    write_index_metadata,
)


def _config_payload() -> dict[str, object]:
    return {
        "name": "index0",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 120, "overlap": 30, "edges": "auto"},
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    }


def test_sqlite_vec_connection_and_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "index.db"
    connection = connect_database(database_path)

    try:
        ensure_schema(connection, dimensions=8)
        assert sqlite_vec_version(connection).startswith("v")
    finally:
        connection.close()


def test_index_metadata_and_snapshot_drift(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    file_path = root / "a.md"
    file_path.write_text("# Title\nbody\n", encoding="utf-8")

    connection = connect_database(tmp_path / "index.db")
    config = parse_index_config(_config_payload())

    try:
        ensure_schema(connection, dimensions=8)
        write_index_metadata(connection, config, embedding_dimensions=8)

        snapshot = build_file_snapshot(root, file_path, chunk_count=1)
        write_file_snapshots(connection, [snapshot])

        assert index_is_usable(connection, config)
        assert chunking_fingerprint(config)
        assert not detect_snapshot_drift(connection, root, [file_path])

        file_path.write_text("# Title\nchanged\n", encoding="utf-8")
        assert detect_snapshot_drift(connection, root, [file_path])
    finally:
        connection.close()


def test_chunks_query_merges_contiguous_ranges(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config(_config_payload())

    findings = semfs.chunks({"text": "alpha", "max_results": 1}, str(sample_docs), config=config)

    assert len(findings) == 1
    assert findings[0].file == "alpha.md"
    assert findings[0].from_line == 1
    assert findings[0].to_line >= 6
    assert findings[0].score > 0.5


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
