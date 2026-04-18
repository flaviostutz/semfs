"""Indexing entry point for the semfs scaffold."""

from pathlib import Path
from typing import Any

from semfs.models import IndexState
from semfs.storage import default_index_path


def index(directory: str, config: dict[str, Any] | None = None) -> IndexState:
    """Return a placeholder index state for the requested directory."""
    target = Path(directory)
    index_name = str((config or {}).get("name", "index0"))
    database_path = default_index_path(str(target), index_name)
    return IndexState(
        index_name=index_name,
        status="scaffold",
        database_path=str(database_path),
        indexed_files=0,
        indexed_chunks=0,
    )
