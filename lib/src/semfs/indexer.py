"""Indexing entry point for semfs."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any

from semfs.chunking import chunk_text
from semfs.config import parse_index_config
from semfs.errors import FileProcessingError
from semfs.models import ChunkRecord, FileSnapshot, IndexConfig, IndexMode, IndexState, IndexStatus
from semfs.storage import (
    DEFAULT_EMBEDDING_BACKEND,
    SCHEMA_VERSION,
    IndexStore,
    build_file_snapshot_from_contents,
    chunking_fingerprint,
    default_index_path,
    detect_snapshot_drift,
    index_counts,
    index_is_usable,
    metadata_value,
    open_index_store,
    read_index_metadata,
    replace_index_data,
    reset_store,
    write_index_metadata,
)
from semfs.verbose import emit_verbose, format_seconds


@dataclass(slots=True)
class PreparedIndex:
    """Open index resources prepared for one operation."""

    root: Path
    config: IndexConfig
    store: IndexStore
    state: IndexState
    cleanup: Any | None = None


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


def _build_chunk_records(
    root: Path, config: IndexConfig, *, verbose: bool = False
) -> tuple[list[ChunkRecord], list[FileSnapshot]]:
    tree_walk_started = perf_counter()
    emit_verbose(verbose, f"Loading source files matching {config.filter}")
    sources = _load_indexable_sources(root, config.filter)
    emit_verbose(
        verbose,
        (
            f"Loaded {len(sources)} source files matching {config.filter} in "
            f"{format_seconds(perf_counter() - tree_walk_started)}"
        ),
    )

    next_chunk_id = 1
    chunk_records: list[ChunkRecord] = []
    snapshots: list[FileSnapshot] = []

    for file_path, contents in sources:
        spans = chunk_text(contents, file_path.relative_to(root), config.chunking)
        snapshots.append(build_file_snapshot_from_contents(root, file_path, contents, len(spans)))
        if not spans:
            continue

        for span in spans:
            chunk_records.append(
                ChunkRecord(
                    chunk_id=str(next_chunk_id),
                    file_path=str(file_path.relative_to(root)),
                    start_line=span.start_line,
                    end_line=span.end_line,
                    document=span.text,
                )
            )
            next_chunk_id += 1

    emit_verbose(
        verbose,
        f"Prepared {len(chunk_records)} chunks from {len(snapshots)} files for Chroma indexing",
    )

    return chunk_records, snapshots


def _build_state(
    root: Path,
    config: IndexConfig,
    store_path: str,
    status: IndexStatus,
    store: IndexStore,
) -> IndexState:
    metadata = read_index_metadata(store)
    indexed_files, indexed_chunks = index_counts(store)
    now = datetime.now(UTC)
    return IndexState(
        directory_path=str(root),
        index_name=config.name,
        database_path=store_path,
        schema_version=metadata_value(metadata, "schema_version", SCHEMA_VERSION),
        model_name=metadata_value(metadata, "model_name", DEFAULT_EMBEDDING_BACKEND),
        embedding_dimensions=int(metadata_value(metadata, "embedding_dimensions", "0") or "0"),
        chunking_fingerprint=metadata_value(metadata, "chunking_fingerprint", chunking_fingerprint(config)),
        status=status,
        created_at=now,
        updated_at=now,
        indexed_files=indexed_files,
        indexed_chunks=indexed_chunks,
    )


def _rebuild_index(store: IndexStore, root: Path, config: IndexConfig, *, verbose: bool = False) -> None:
    rebuild_started = perf_counter()
    emit_verbose(verbose, "Rebuilding index data")
    chunk_records, snapshots = _build_chunk_records(root, config, verbose=verbose)

    reset_started = perf_counter()
    emit_verbose(verbose, "Resetting Chroma collections")
    reset_store(store)
    emit_verbose(verbose, f"Reset Chroma collections in {format_seconds(perf_counter() - reset_started)}")

    metadata_started = perf_counter()
    emit_verbose(verbose, "Writing index metadata")
    write_index_metadata(store, config)
    emit_verbose(verbose, f"Wrote index metadata in {format_seconds(perf_counter() - metadata_started)}")

    write_started = perf_counter()
    emit_verbose(verbose, "Writing snapshot and chunk records")
    replace_index_data(store, snapshots, chunk_records, verbose=verbose)
    emit_verbose(verbose, f"Wrote snapshot and chunk records in {format_seconds(perf_counter() - write_started)}")
    emit_verbose(verbose, f"Rebuilt index data in {format_seconds(perf_counter() - rebuild_started)}")


def _prepare_persistent_index(root: Path, config: IndexConfig, *, verbose: bool = False) -> PreparedIndex:
    store_path = default_index_path(str(root), config.name)
    store = open_index_store(store_path, verbose=verbose)

    usability_started = perf_counter()
    emit_verbose(verbose, "Checking index compatibility")
    usable = False
    usable = index_is_usable(store, config)
    emit_verbose(verbose, f"Checked index compatibility in {format_seconds(perf_counter() - usability_started)}")

    source_scan_started = perf_counter()
    emit_verbose(verbose, f"Scanning current source files matching {config.filter}")
    source_paths: list[Path] = []
    source_paths = [path for path, _contents in _load_indexable_sources(root, config.filter)]
    emit_verbose(
        verbose,
        f"Scanned current source files ({len(source_paths)}) in {format_seconds(perf_counter() - source_scan_started)}",
    )

    drift = detect_snapshot_drift(store, root, source_paths, verbose=verbose) if usable else False

    rebuild = config.mode is IndexMode.REFRESH or not usable or (config.mode is IndexMode.AUTO and drift)
    if rebuild:
        _rebuild_index(store, root, config, verbose=verbose)
        status = IndexStatus.READY
    else:
        status = IndexStatus.STALE if drift else IndexStatus.READY

    state = _build_state(root, config, str(store_path), status, store)
    return PreparedIndex(root=root, config=config, store=store, state=state)


def _prepare_ephemeral_index(root: Path, config: IndexConfig, *, verbose: bool = False) -> PreparedIndex:
    store = open_index_store(":memory:", in_memory=True, verbose=verbose)
    _rebuild_index(store, root, config, verbose=verbose)
    state = _build_state(root, config, ":memory:", IndexStatus.EPHEMERAL, store)
    return PreparedIndex(root=root, config=config, store=store, state=state)


def _prepare_transient_index(root: Path, config: IndexConfig, *, verbose: bool = False) -> PreparedIndex:
    temporary_directory = TemporaryDirectory(prefix="semfs-transient-")
    transient_path = Path(temporary_directory.name) / "chromadb"
    store = open_index_store(transient_path, verbose=verbose)
    try:
        _rebuild_index(store, root, config, verbose=verbose)
        state = _build_state(root, config, str(transient_path), IndexStatus.EPHEMERAL, store)
        return PreparedIndex(
            root=root,
            config=config,
            store=store,
            state=state,
            cleanup=temporary_directory.cleanup,
        )
    except Exception:
        temporary_directory.cleanup()
        raise


@contextmanager
def open_prepared_index(
    directory: str,
    config: IndexConfig | dict[str, Any] | None,
    *,
    verbose: bool = False,
) -> Iterator[PreparedIndex]:
    """Yield a ready-to-query index store for one operation."""
    parsed_config = parse_index_config(config)
    root = _validate_directory(directory)
    prepare_started = perf_counter()
    emit_verbose(verbose, f"Preparing index '{parsed_config.name}' in mode '{parsed_config.mode.value}' for {root}")
    if parsed_config.mode is IndexMode.INMEMORY:
        prepared = _prepare_ephemeral_index(root, parsed_config, verbose=verbose)
    elif parsed_config.mode is IndexMode.TRANSIENT:
        prepared = _prepare_transient_index(root, parsed_config, verbose=verbose)
    else:
        prepared = _prepare_persistent_index(root, parsed_config, verbose=verbose)
    emit_verbose(
        verbose,
        (
            f"Prepared index '{parsed_config.name}' in mode '{parsed_config.mode.value}' for {root} in "
            f"{format_seconds(perf_counter() - prepare_started)}"
        ),
    )
    try:
        yield prepared
    finally:
        if prepared.cleanup is not None:
            prepared.cleanup()


def index(
    directory: str,
    config: IndexConfig | dict[str, Any] | None = None,
    *,
    verbose: bool = False,
) -> IndexState:
    """Create or refresh one index and return the resulting state summary."""
    with open_prepared_index(directory, config, verbose=verbose) as prepared:
        return prepared.state
