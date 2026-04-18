"""Typed models used by the scaffolded public API."""

from dataclasses import dataclass


@dataclass(slots=True)
class IndexState:
    """Minimal index state returned by the scaffolded index API."""

    index_name: str
    status: str
    database_path: str
    indexed_files: int
    indexed_chunks: int


@dataclass(slots=True)
class ChunkFinding:
    """Minimal chunk-level result shape for the scaffold."""

    file: str
    start_line: int
    end_line: int


@dataclass(slots=True)
class FileFinding:
    """Minimal file-level result shape for the scaffold."""

    file: str
    best_score: float
