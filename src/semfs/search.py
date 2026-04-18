"""Search entry points for the semfs scaffold."""

from typing import Any

from semfs.models import ChunkFinding, FileFinding


def chunks(
    query: dict[str, Any],
    directory: str,
    fetch_contents: bool = False,
    config: dict[str, Any] | None = None,
) -> list[ChunkFinding]:
    """Return an empty chunk result set for the scaffold."""
    _ = (query, directory, fetch_contents, config)
    return []


def files(query: dict[str, Any], directory: str, config: dict[str, Any] | None = None) -> list[FileFinding]:
    """Return an empty file result set for the scaffold."""
    _ = (query, directory, config)
    return []
