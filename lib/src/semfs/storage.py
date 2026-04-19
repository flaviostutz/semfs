"""Storage helpers for semfs - ChromaDB backend."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from semfs.errors import IndexStateError
from semfs.models import ChunkRecord, FileSnapshot, IndexConfig
from semfs.verbose import emit_verbose, format_seconds

SCHEMA_VERSION = "2"
DEFAULT_EMBEDDING_BACKEND = "chromadb-default"
_DUMMY_EMBEDDING: list[float] = [0.0]
_CHROMA_BATCH_SIZE = 500


@dataclass
class IndexStore:
    """Open ChromaDB store resources for one index."""

    client: Any
    chunks: Any
    snapshots: Any
    index_meta: Any
    store_path: str
    _closed: bool = field(default=False, init=False, repr=False)


def _batched(items: list[Any], batch_size: int = _CHROMA_BATCH_SIZE) -> list[list[Any]]:
    """Split a list into contiguous batches with a stable maximum size."""
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]


def default_index_path(directory: str, index_name: str = "index0") -> Path:
    """Return the planned on-disk index location for a named index."""
    return Path(directory) / ".semfs" / index_name


def default_embedding_function() -> Any:
    """Return the default ChromaDB embedding function for text documents."""
    try:
        from chromadb.utils.embedding_functions import (
            DefaultEmbeddingFunction,  # pyright: ignore[reportMissingTypeStubs]
        )
    except ImportError as exc:
        message = (
            "Failed action `open_index`: ChromaDB default embedding support is unavailable. "
            "Next step: install chromadb embedding dependencies and retry."
        )
        raise IndexStateError(message) from exc
    return DefaultEmbeddingFunction()


def open_index_store(store_path: str | Path, *, in_memory: bool = False, verbose: bool = False) -> IndexStore:
    """Open a ChromaDB store at the given path or in memory."""
    import chromadb  # pyright: ignore[reportMissingTypeStubs]

    target_path = ":memory:" if in_memory else str(Path(store_path))
    open_started = perf_counter()
    emit_verbose(verbose, f"Opening Chroma store at {target_path}")
    if in_memory:
        try:
            client = chromadb.EphemeralClient()
        except Exception as exc:
            message = (
                "Failed action `open_index` for ephemeral store: ChromaDB EphemeralClient could not be initialized. "
                "Next step: install chromadb and retry."
            )
            raise IndexStateError(message) from exc
        path_str = ":memory:"
    else:
        resolved = Path(store_path)
        resolved.mkdir(parents=True, exist_ok=True)
        try:
            client = chromadb.PersistentClient(path=str(resolved))
        except Exception as exc:
            message = (
                f"Failed action `open_index` for {store_path}: ChromaDB PersistentClient could not be initialized. "
                "Next step: install chromadb and retry."
            )
            raise IndexStateError(message) from exc
        path_str = str(resolved)

    chunks = client.get_or_create_collection(
        name="chunks",
        metadata={"hnsw:space": "cosine"},
        embedding_function=default_embedding_function(),
    )
    snapshots = client.get_or_create_collection(name="snapshots")
    index_meta = client.get_or_create_collection(name="index_meta")
    emit_verbose(verbose, f"Opened Chroma store at {path_str} in {format_seconds(perf_counter() - open_started)}")
    return IndexStore(
        client=client,
        chunks=chunks,
        snapshots=snapshots,
        index_meta=index_meta,
        store_path=path_str,
    )


def reset_store(store: IndexStore) -> None:
    """Delete and recreate all collections."""
    store.client.delete_collection("chunks")
    store.client.delete_collection("snapshots")
    store.client.delete_collection("index_meta")
    store.chunks = store.client.create_collection(
        name="chunks",
        metadata={"hnsw:space": "cosine"},
        embedding_function=default_embedding_function(),
    )
    store.snapshots = store.client.create_collection(name="snapshots")
    store.index_meta = store.client.create_collection(name="index_meta")


def chunking_fingerprint(config: IndexConfig) -> str:
    """Return a stable fingerprint for the configured chunking settings."""
    payload = {
        "size": config.chunking.size,
        "overlap": config.chunking.overlap,
        "edges": config.chunking.edges.value,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_index_metadata(store: IndexStore, config: IndexConfig) -> None:
    """Persist the index metadata required to validate a reusable index."""
    metadata_items = {
        "schema_version": SCHEMA_VERSION,
        "model_name": DEFAULT_EMBEDDING_BACKEND,
        "embedding_dimensions": "0",
        "chunking_fingerprint": chunking_fingerprint(config),
    }
    store.index_meta.upsert(
        ids=list(metadata_items.keys()),
        embeddings=[_DUMMY_EMBEDDING for _ in metadata_items],
        metadatas=[{"value": v} for v in metadata_items.values()],
    )


def metadata_value(metadata: dict[str, str], key: str, default: str = "") -> str:
    """Return one metadata value with a stable default."""
    return metadata.get(key, default)


def read_index_metadata(store: IndexStore) -> dict[str, str]:
    """Return persisted index metadata as a dictionary."""
    result = store.index_meta.get(include=["metadatas"])
    if not result["ids"]:
        return {}
    return {item_id: str(meta["value"]) for item_id, meta in zip(result["ids"], result["metadatas"], strict=True)}


def index_is_usable(store: IndexStore, config: IndexConfig) -> bool:
    """Check whether an existing persisted index matches the requested configuration."""
    metadata = read_index_metadata(store)
    if not metadata:
        return False
    return (
        metadata.get("schema_version") == SCHEMA_VERSION
        and metadata.get("model_name") == DEFAULT_EMBEDDING_BACKEND
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


def build_file_snapshot_from_contents(root: Path, file_path: Path, contents: str, chunk_count: int) -> FileSnapshot:
    """Build a stored file snapshot using already-loaded UTF-8 contents."""
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


def write_file_snapshots(store: IndexStore, snapshots: list[FileSnapshot], *, verbose: bool = False) -> None:
    """Persist file snapshots."""
    if not snapshots:
        return

    write_started = perf_counter()
    emit_verbose(verbose, f"Writing {len(snapshots)} file snapshots to Chroma")
    batch_count = 0
    for batch in _batched(snapshots):
        batch_count += 1
        store.snapshots.upsert(
            ids=[snapshot.file_path for snapshot in batch],
            embeddings=[_DUMMY_EMBEDDING for _ in batch],
            metadatas=[
                {
                    "size_bytes": snapshot.size_bytes,
                    "modified_time": snapshot.modified_time.isoformat(),
                    "content_digest": snapshot.content_digest,
                    "chunk_count": snapshot.chunk_count,
                    "last_indexed_at": snapshot.last_indexed_at.isoformat(),
                }
                for snapshot in batch
            ],
        )
    emit_verbose(
        verbose,
        (
            f"Wrote {len(snapshots)} file snapshots to Chroma in {batch_count} batches "
            f"in {format_seconds(perf_counter() - write_started)}"
        ),
    )


def replace_index_data(
    store: IndexStore,
    snapshots: list[FileSnapshot],
    chunk_records: list[ChunkRecord],
    *,
    verbose: bool = False,
) -> None:
    """Replace stored snapshots and chunks atomically."""
    existing_chunks = store.chunks.get(include=[])
    deleted_chunk_batches = 0
    existing_snapshots = store.snapshots.get(include=[])
    deleted_snapshot_batches = 0
    delete_started = perf_counter()
    emit_verbose(verbose, "Deleting existing index rows")
    for batch in _batched(existing_chunks["ids"]):
        deleted_chunk_batches += 1
        store.chunks.delete(ids=batch)

    for batch in _batched(existing_snapshots["ids"]):
        deleted_snapshot_batches += 1
        store.snapshots.delete(ids=batch)
    emit_verbose(
        verbose,
        (
            "Deleted existing index rows "
            f"({deleted_chunk_batches} chunk batches, {deleted_snapshot_batches} snapshot batches) in "
            f"{format_seconds(perf_counter() - delete_started)}"
        ),
    )

    if snapshots:
        write_file_snapshots(store, snapshots, verbose=verbose)

    chunk_batch_count = 0
    if chunk_records:
        chunk_write_started = perf_counter()
        emit_verbose(verbose, f"Writing {len(chunk_records)} chunk vectors to Chroma")
        try:
            for batch in _batched(chunk_records):
                chunk_batch_count += 1
                store.chunks.add(
                    ids=[record.chunk_id for record in batch],
                    documents=[record.document for record in batch],
                    metadatas=[
                        {
                            "file_path": record.file_path,
                            "start_line": record.start_line,
                            "end_line": record.end_line,
                        }
                        for record in batch
                    ],
                )
        except Exception as exc:
            message = (
                f"Failed action `index` for {store.store_path}: "
                "ChromaDB default embedding failed while indexing chunks. "
                "Next step: ensure the default Chroma embedding model can be downloaded or is cached locally, then retry."
            )
            raise IndexStateError(message) from exc
        emit_verbose(
            verbose,
            (
                f"Wrote {len(chunk_records)} chunk vectors to Chroma in {chunk_batch_count} batches in "
                f"{format_seconds(perf_counter() - chunk_write_started)}"
            ),
        )


def index_counts(store: IndexStore) -> tuple[int, int]:
    """Return the stored file and chunk counts for one index."""
    file_count = store.snapshots.count()
    chunk_count = store.chunks.count()
    return file_count, chunk_count


def read_file_snapshot(store: IndexStore, file_path: str) -> FileSnapshot | None:
    """Return one stored file snapshot when present."""
    result = store.snapshots.get(ids=[file_path], include=["metadatas"])
    if not result["ids"]:
        return None
    meta = result["metadatas"][0]
    return FileSnapshot(
        file_path=file_path,
        size_bytes=int(meta["size_bytes"]),
        modified_time=datetime.fromisoformat(str(meta["modified_time"])),
        content_digest=str(meta["content_digest"]),
        chunk_count=int(meta["chunk_count"]),
        last_indexed_at=datetime.fromisoformat(str(meta["last_indexed_at"])),
    )


def fetch_chunk_candidates(
    store: IndexStore,
    query_text: str,
    candidate_k: int,
    *,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Return deterministic chunk candidates from ChromaDB KNN search."""
    total_chunks = store.chunks.count()
    if total_chunks == 0:
        return []

    k = min(candidate_k, total_chunks)
    query_started = perf_counter()
    emit_verbose(verbose, f"Querying Chroma for up to {k} chunk candidates")
    try:
        results = store.chunks.query(
            query_texts=[query_text],
            n_results=k,
            include=["distances", "metadatas"],
        )
    except Exception as exc:
        message = (
            f"Failed action `query` for {store.store_path}: "
            "ChromaDB default embedding failed while processing the query. "
            "Next step: ensure the default Chroma embedding model can be downloaded or is cached locally, then retry."
        )
        raise IndexStateError(message) from exc
    rows: list[dict[str, Any]] = [
        {
            "chunk_id": chunk_id,
            "file_path": meta["file_path"],
            "start_line": meta["start_line"],
            "end_line": meta["end_line"],
            "distance": distance,
        }
        for chunk_id, meta, distance in zip(
            results["ids"][0],
            results["metadatas"][0],
            results["distances"][0],
            strict=True,
        )
    ]
    ranked = sorted(rows, key=lambda row: (float(row["distance"]), str(row["file_path"]), int(row["start_line"])))
    emit_verbose(
        verbose,
        (
            f"Queried Chroma across {total_chunks} chunks and received {len(ranked)} rows in "
            f"{format_seconds(perf_counter() - query_started)}"
        ),
    )
    return ranked


def detect_snapshot_drift(store: IndexStore, root: Path, files: list[Path], *, verbose: bool = False) -> bool:
    """Return true when the current file set differs from stored snapshot metadata."""
    drift_started = perf_counter()
    emit_verbose(verbose, f"Checking snapshot drift across {len(files)} files")
    has_drift = False
    result = store.snapshots.get(include=["metadatas"])
    stored = {
        item_id: (int(meta["size_bytes"]), str(meta["modified_time"]))
        for item_id, meta in zip(result["ids"], result["metadatas"], strict=True)
    }

    current: dict[str, tuple[int, str]] = {}
    for file_path in files:
        stat = file_path.stat()
        timestamp = datetime.fromtimestamp(stat.st_mtime_ns / 1_000_000_000, UTC).isoformat()
        current[str(file_path.relative_to(root))] = (stat.st_size, timestamp)

    has_drift = stored != current
    emit_verbose(
        verbose,
        (
            f"Checked snapshot drift across {len(files)} files; drift={has_drift} in "
            f"{format_seconds(perf_counter() - drift_started)}"
        ),
    )
    return has_drift


def chromadb_version() -> str:
    """Return the installed chromadb version string."""
    import chromadb  # pyright: ignore[reportMissingTypeStubs]

    return str(chromadb.__version__)
