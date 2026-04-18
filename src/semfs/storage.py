"""Storage helpers for the semfs scaffold."""

from pathlib import Path


def default_index_path(directory: str, index_name: str = "index0") -> Path:
    """Return the planned on-disk index location for a named index."""
    return Path(directory) / ".semfs" / index_name / "index.db"
