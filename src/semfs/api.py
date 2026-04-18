from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .config import Query, SearchConfig, normalize_config, normalize_dir, normalize_query
from .indexer import build_index_payload, discover_documents
from .models import ChunkFinding, IndexRow
from .querying import deduplicate_files, merge_chunk_scores, search_chunks
from .storage import load_chunk_rows, load_metadata, save_index


def index(directory: str, config: SearchConfig | Mapping[str, Any] | None = None) -> dict[str, Any]:
    normalized_dir = normalize_dir(directory)
    normalized_config = normalize_config(config)
    metadata, _ = _ensure_index(normalized_dir, normalized_config)
    return metadata


def files(
    query: Query | Mapping[str, Any],
    directory: str,
    config: SearchConfig | Mapping[str, Any] | None = None,
) -> list[str]:
    normalized_dir = normalize_dir(directory)
    normalized_config = normalize_config(config)
    normalized_query = normalize_query(query)
    metadata, rows = _ensure_index(normalized_dir, normalized_config)
    scores = search_chunks(rows, metadata["idf"], normalized_query)
    return deduplicate_files(scores)


def chunks(
    query: Query | Mapping[str, Any],
    directory: str,
    fetch_contents: bool = True,
    config: SearchConfig | Mapping[str, Any] | None = None,
) -> list[ChunkFinding]:
    normalized_dir = normalize_dir(directory)
    normalized_config = normalize_config(config)
    normalized_query = normalize_query(query)
    metadata, rows = _ensure_index(normalized_dir, normalized_config)
    scores = search_chunks(rows, metadata["idf"], normalized_query)
    return merge_chunk_scores(scores, fetch_contents)


def _ensure_index(directory, config: SearchConfig) -> tuple[dict[str, Any], list[IndexRow]]:
    metadata = load_metadata(directory, config)
    should_persist = config.mode in {"refresh", "auto", "stale"}
    if config.mode == "refresh":
        return _build_index(directory, config, should_persist)
    if config.mode == "stale" and metadata is not None:
        return metadata, load_chunk_rows(directory, config)

    if config.mode == "auto" and metadata is not None:
        current_chunks, current_fingerprint, file_count = discover_documents(directory, config)
        if metadata.get("fingerprint") == current_fingerprint:
            return metadata, load_chunk_rows(directory, config)
        return _build_from_chunks(
            directory, config, current_chunks, current_fingerprint, file_count, True
        )

    if config.mode in {"inmemory", "transient"}:
        return _build_index(directory, config, False)

    if metadata is not None:
        return metadata, load_chunk_rows(directory, config)
    return _build_index(directory, config, should_persist)


def _build_index(
    directory, config: SearchConfig, persist: bool
) -> tuple[dict[str, Any], list[IndexRow]]:
    chunks_found, fingerprint, file_count = discover_documents(directory, config)
    return _build_from_chunks(directory, config, chunks_found, fingerprint, file_count, persist)


def _build_from_chunks(directory, config, chunks_found, fingerprint, file_count, persist):
    idf, rows = build_index_payload(chunks_found)
    metadata = {
        "schema_version": 1,
        "name": config.name,
        "file_count": file_count,
        "chunk_count": len(rows),
        "fingerprint": fingerprint,
        "idf": idf,
        "persisted": persist,
    }
    if persist:
        metadata = save_index(
            directory,
            config,
            fingerprint,
            file_count,
            len(rows),
            idf,
            rows,
        ) | {"persisted": True}
    return metadata, rows
