"""Indexing entry point and embedding-model loading utilities for semfs."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from semfs.chunking import chunk_text
from semfs.config import parse_index_config
from semfs.errors import FileProcessingError, ModelUnavailableError
from semfs.models import ChunkRecord, FileSnapshot, IndexConfig, IndexMode, IndexState, IndexStatus
from semfs.storage import (
    SCHEMA_VERSION,
    build_file_snapshot_from_contents,
    chunking_fingerprint,
    connect_database,
    default_index_path,
    detect_snapshot_drift,
    index_counts,
    index_is_usable,
    metadata_value,
    read_index_metadata,
    replace_index_data,
    reset_schema,
    write_index_metadata,
)


@dataclass(slots=True)
class PreparedIndex:
    """Open index resources prepared for one operation."""

    root: Path
    config: IndexConfig
    connection: sqlite3.Connection
    state: IndexState
    cleanup: Any | None = None


@cache
def load_embedding_model(model_name: str) -> Any:
    """Load and cache one sentence-transformers model per configured model name."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        message = (
            f"Failed action `load_model` for model {model_name}: sentence-transformers is unavailable. "
            "Next step: install dependencies and retry."
        )
        raise ModelUnavailableError(message) from exc

    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except (OSError, RuntimeError, ValueError) as exc:
        message = (
            f"Failed action `load_model` for model {model_name}: the embedding model could not be loaded. "
            "Next step: install or download the model locally and retry."
        )
        raise ModelUnavailableError(message) from exc


def embedding_dimensions(model_name: str) -> int:
    """Return the embedding dimension reported by the configured model."""
    model = load_embedding_model(model_name)
    dimensions = model.get_sentence_embedding_dimension()
    if not isinstance(dimensions, int) or dimensions <= 0:
        message = (
            f"Failed action `load_model` for model {model_name}: invalid embedding dimensions were reported. "
            "Next step: verify the model and retry."
        )
        raise ModelUnavailableError(message)
    return dimensions


def _validate_directory(directory: str) -> Path:
    target = Path(directory).resolve()
    if not target.exists() or not target.is_dir():
        message = (
            f"Failed action `index` for {target}: target directory does not exist. "
            "Next step: provide an existing directory and retry."
        )
        raise FileProcessingError(message)
    return target


def _candidate_files(root: Path, pattern: str) -> list[Path]:
    matched = []
    for path in root.glob(pattern):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if ".semfs" in relative_parts:
            continue
        matched.append(path)
    return sorted(set(matched))


def _load_indexable_sources(root: Path, pattern: str) -> list[tuple[Path, str]]:
    sources: list[tuple[Path, str]] = []
    for path in _candidate_files(root, pattern):
        try:
            contents = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        sources.append((path, contents))
    return sources


def _build_chunk_records(root: Path, config: IndexConfig) -> tuple[int, list[ChunkRecord], list[FileSnapshot]]:
    model = load_embedding_model(config.model)
    dimensions = embedding_dimensions(config.model)
    next_chunk_id = 1
    chunk_records: list[ChunkRecord] = []
    snapshots: list[FileSnapshot] = []

    for file_path, contents in _load_indexable_sources(root, config.filter):
        spans = chunk_text(contents, file_path.relative_to(root), config.chunking)
        snapshots.append(build_file_snapshot_from_contents(root, file_path, contents, len(spans)))
        if not spans:
            continue

        embeddings = model.encode([span.text for span in spans], normalize_embeddings=True)
        for span, embedding in zip(spans, embeddings, strict=True):
            chunk_records.append(
                ChunkRecord(
                    chunk_id=str(next_chunk_id),
                    file_path=str(file_path.relative_to(root)),
                    start_line=span.start_line,
                    end_line=span.end_line,
                    embedding=[float(value) for value in embedding],
                )
            )
            next_chunk_id += 1

    return dimensions, chunk_records, snapshots


def _build_state(
    root: Path,
    config: IndexConfig,
    database_path: str,
    status: IndexStatus,
    connection: sqlite3.Connection,
) -> IndexState:
    metadata = read_index_metadata(connection)
    indexed_files, indexed_chunks = index_counts(connection)
    now = datetime.now(UTC)
    return IndexState(
        directory_path=str(root),
        index_name=config.name,
        database_path=database_path,
        schema_version=metadata_value(metadata, "schema_version", SCHEMA_VERSION),
        model_name=metadata_value(metadata, "model_name", config.model),
        embedding_dimensions=int(metadata_value(metadata, "embedding_dimensions", "0") or "0"),
        chunking_fingerprint=metadata_value(metadata, "chunking_fingerprint", chunking_fingerprint(config)),
        status=status,
        created_at=now,
        updated_at=now,
        indexed_files=indexed_files,
        indexed_chunks=indexed_chunks,
    )


def _rebuild_index(connection: sqlite3.Connection, root: Path, config: IndexConfig) -> None:
    dimensions, chunk_records, snapshots = _build_chunk_records(root, config)
    reset_schema(connection, dimensions)
    write_index_metadata(connection, config, dimensions)
    replace_index_data(connection, snapshots, chunk_records)


def _prepare_persistent_index(root: Path, config: IndexConfig) -> PreparedIndex:
    database_path = default_index_path(str(root), config.name)
    connection = connect_database(database_path)
    try:
        usable = index_is_usable(connection, config)
        source_paths = [path for path, _contents in _load_indexable_sources(root, config.filter)]
        drift = detect_snapshot_drift(connection, root, source_paths) if usable else False

        rebuild = config.mode is IndexMode.REFRESH or not usable or (config.mode is IndexMode.AUTO and drift)
        if rebuild:
            _rebuild_index(connection, root, config)
            status = IndexStatus.READY
        else:
            status = IndexStatus.STALE if drift else IndexStatus.READY

        state = _build_state(root, config, str(database_path), status, connection)
        return PreparedIndex(root=root, config=config, connection=connection, state=state)
    except Exception:
        connection.close()
        raise


def _prepare_ephemeral_index(root: Path, config: IndexConfig) -> PreparedIndex:
    connection = connect_database(":memory:")
    try:
        _rebuild_index(connection, root, config)
        state = _build_state(root, config, ":memory:", IndexStatus.EPHEMERAL, connection)
        return PreparedIndex(root=root, config=config, connection=connection, state=state)
    except Exception:
        connection.close()
        raise


def _prepare_transient_index(root: Path, config: IndexConfig) -> PreparedIndex:
    temporary_directory = TemporaryDirectory(prefix="semfs-transient-")
    database_path = Path(temporary_directory.name) / "index.db"
    connection = connect_database(database_path)
    try:
        _rebuild_index(connection, root, config)
        state = _build_state(root, config, str(database_path), IndexStatus.EPHEMERAL, connection)
        return PreparedIndex(
            root=root,
            config=config,
            connection=connection,
            state=state,
            cleanup=temporary_directory.cleanup,
        )
    except Exception:
        connection.close()
        temporary_directory.cleanup()
        raise


@contextmanager
def open_prepared_index(directory: str, config: IndexConfig | dict[str, Any] | None) -> Iterator[PreparedIndex]:
    """Yield a ready-to-query index connection for one operation."""
    parsed_config = parse_index_config(config)
    root = _validate_directory(directory)
    if parsed_config.mode is IndexMode.INMEMORY:
        prepared = _prepare_ephemeral_index(root, parsed_config)
    elif parsed_config.mode is IndexMode.TRANSIENT:
        prepared = _prepare_transient_index(root, parsed_config)
    else:
        prepared = _prepare_persistent_index(root, parsed_config)
    try:
        yield prepared
    finally:
        prepared.connection.close()
        if prepared.cleanup is not None:
            prepared.cleanup()


def index(directory: str, config: IndexConfig | dict[str, Any] | None = None) -> IndexState:
    """Create or refresh one index and return the resulting state summary."""
    with open_prepared_index(directory, config) as prepared:
        return prepared.state
