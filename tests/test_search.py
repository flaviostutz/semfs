from pathlib import Path

from semfs.config import parse_index_config
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
