"""Storage helpers for semfs."""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import sqlite_vec

from semfs.errors import IndexStateError
from semfs.models import FileSnapshot, IndexConfig

SCHEMA_VERSION = "1"
REQUIRED_TABLES = {"index_meta", "file_snapshots", "chunk_index"}


def default_index_path(directory: str, index_name: str = "index0") -> Path:
    """Return the planned on-disk index location for a named index."""
    return Path(directory) / ".semfs" / index_name / "index.db"


def connect_database(database_path: str | Path, load_vector_extension: bool = True) -> sqlite3.Connection:
    """Open a SQLite connection and optionally load sqlite-vec."""
    resolved_path = Path(database_path) if database_path != ":memory:" else None
    if resolved_path is not None:
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    if load_vector_extension:
        try:
            connection.enable_load_extension(True)
            sqlite_vec.load(connection)
            connection.enable_load_extension(False)
        except sqlite3.Error as exc:
            message = (
                f"Failed action `open_index` for {database_path}: sqlite-vec extension could not be loaded. "
                "Next step: reinstall sqlite-vec and retry."
            )
            raise IndexStateError(message) from exc

    return connection


def ensure_schema(connection: sqlite3.Connection, dimensions: int) -> None:
    """Create the baseline metadata and vector tables for one index."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS index_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS file_snapshots (
            file_path TEXT PRIMARY KEY,
            size_bytes INTEGER NOT NULL,
            modified_time TEXT NOT NULL,
            content_digest TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            last_indexed_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunk_index USING vec0(
            chunk_id INTEGER PRIMARY KEY,
            embedding FLOAT[{dimensions}] DISTANCE_METRIC=cosine,
            +file_path TEXT,
            +start_line INTEGER,
            +end_line INTEGER
        )
        """
    )
    connection.commit()


def serialize_embedding(vector: list[float]) -> bytes:
    """Serialize an embedding for sqlite-vec storage."""
    return sqlite_vec.serialize_float32(vector)


def chunking_fingerprint(config: IndexConfig) -> str:
    """Return a stable fingerprint for the configured chunking settings."""
    payload = {
        "size": config.chunking.size,
        "overlap": config.chunking.overlap,
        "edges": config.chunking.edges.value,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_index_metadata(connection: sqlite3.Connection, config: IndexConfig, embedding_dimensions: int) -> None:
    """Persist the index metadata required to validate a reusable index."""
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "model_name": config.model,
        "embedding_dimensions": str(embedding_dimensions),
        "chunking_fingerprint": chunking_fingerprint(config),
    }
    connection.executemany("INSERT OR REPLACE INTO index_meta(key, value) VALUES(?, ?)", metadata.items())
    connection.commit()


def read_index_metadata(connection: sqlite3.Connection) -> dict[str, str]:
    """Return persisted index metadata as a dictionary."""
    rows = connection.execute("SELECT key, value FROM index_meta").fetchall()
    return {str(row["key"]): str(row["value"]) for row in rows}


def _storage_tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')").fetchall()
    return {str(row[0]) for row in rows}


def index_is_usable(connection: sqlite3.Connection, config: IndexConfig) -> bool:
    """Check whether an existing persisted index matches the requested configuration."""
    if not REQUIRED_TABLES.issubset(_storage_tables(connection)):
        return False

    metadata = read_index_metadata(connection)
    return (
        metadata.get("schema_version") == SCHEMA_VERSION
        and metadata.get("model_name") == config.model
        and metadata.get("chunking_fingerprint") == chunking_fingerprint(config)
    )


def digest_contents(contents: bytes | str) -> str:
    """Return a stable digest for file contents."""
    payload = contents.encode("utf-8") if isinstance(contents, str) else contents
    return hashlib.sha256(payload).hexdigest()


def build_file_snapshot(root: Path, file_path: Path, chunk_count: int) -> FileSnapshot:
    """Build a stored file snapshot from a path on disk."""
    contents = file_path.read_text(encoding="utf-8")
    stat = file_path.stat()
    timestamp = datetime.fromtimestamp(stat.st_mtime_ns / 1_000_000_000, UTC)
    now = datetime.now(UTC)
    return FileSnapshot(
        file_path=str(file_path.relative_to(root)),
        size_bytes=stat.st_size,
        modified_time=timestamp,
        content_digest=digest_contents(contents),
        chunk_count=chunk_count,
        last_indexed_at=now,
    )


def write_file_snapshots(connection: sqlite3.Connection, snapshots: list[FileSnapshot]) -> None:
    """Persist file snapshots used for freshness and digest checks."""
    connection.executemany(
        """
        INSERT OR REPLACE INTO file_snapshots(
            file_path,
            size_bytes,
            modified_time,
            content_digest,
            chunk_count,
            last_indexed_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                snapshot.file_path,
                snapshot.size_bytes,
                snapshot.modified_time.isoformat(),
                snapshot.content_digest,
                snapshot.chunk_count,
                snapshot.last_indexed_at.isoformat(),
            )
            for snapshot in snapshots
        ],
    )
    connection.commit()


def detect_snapshot_drift(connection: sqlite3.Connection, root: Path, files: list[Path]) -> bool:
    """Return true when the current file set differs from stored snapshot metadata."""
    stored_rows = connection.execute("SELECT file_path, size_bytes, modified_time FROM file_snapshots").fetchall()
    stored = {str(row["file_path"]): (int(row["size_bytes"]), str(row["modified_time"])) for row in stored_rows}

    current: dict[str, tuple[int, str]] = {}
    for file_path in files:
        stat = file_path.stat()
        timestamp = datetime.fromtimestamp(stat.st_mtime_ns / 1_000_000_000, UTC).isoformat()
        current[str(file_path.relative_to(root))] = (stat.st_size, timestamp)

    return stored != current


def sqlite_vec_version(connection: sqlite3.Connection) -> str:
    """Return the loaded sqlite-vec version string."""
    row = connection.execute("SELECT vec_version()").fetchone()
    return str(row[0])
