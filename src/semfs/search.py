"""Search entry points for semfs."""

from collections.abc import Mapping
from typing import Any

from semfs.config import parse_index_config, parse_query_request
from semfs.models import ChunkFinding, FileFinding, IndexConfig, QueryRequest


def chunks(
    query: QueryRequest | Mapping[str, Any],
    directory: str,
    fetch_contents: bool = False,
    config: IndexConfig | Mapping[str, Any] | None = None,
) -> list[ChunkFinding]:
    """Validate inputs and return an empty chunk result set until search is implemented."""
    _ = (directory, fetch_contents)
    parse_query_request(query)
    parse_index_config(config)
    return []


def files(
    query: QueryRequest | Mapping[str, Any],
    directory: str,
    config: IndexConfig | Mapping[str, Any] | None = None,
) -> list[FileFinding]:
    """Validate inputs and return an empty file result set until search is implemented."""
    _ = directory
    parse_query_request(query)
    parse_index_config(config)
    return []
