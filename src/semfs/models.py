"""Typed models used by the semfs public API."""

import re
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

INDEX_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class IndexMode(StrEnum):
    """Supported index lifecycle modes."""

    REFRESH = "refresh"
    AUTO = "auto"
    STALE = "stale"
    INMEMORY = "inmemory"
    TRANSIENT = "transient"


class ChunkingEdges(StrEnum):
    """Supported chunk construction strategies."""

    AUTO = "auto"
    FIXED = "fixed"


class IndexStatus(StrEnum):
    """Lifecycle states for a materialized index."""

    READY = "ready"
    STALE = "stale"
    EPHEMERAL = "ephemeral"


class ChunkingConfig(BaseModel):
    """Chunking configuration used to build an index."""

    model_config = ConfigDict(extra="forbid")

    size: int = Field(gt=0)
    overlap: int = Field(ge=0)
    edges: ChunkingEdges

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkingConfig":
        """Ensure overlap stays smaller than chunk size."""
        if self.overlap >= self.size:
            raise ValueError("chunking.overlap must be strictly smaller than chunking.size")
        return self


class IndexConfig(BaseModel):
    """Validated caller-supplied index configuration."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    filter: str = Field(default="**/*", min_length=1)
    mode: IndexMode
    chunking: ChunkingConfig
    model: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Reject unsafe index names."""
        if not INDEX_NAME_PATTERN.fullmatch(value):
            raise ValueError("name must be filesystem-safe and use only letters, digits, '.', '_', or '-'")
        return value


class QueryRequest(BaseModel):
    """Validated semantic query request."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    max_results: int = Field(default=10, gt=0)
    max_distance: float | None = Field(default=None, ge=0)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """Reject blank query strings after trimming."""
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("text must be non-empty after trimming")
        return trimmed


class IndexState(BaseModel):
    """Materialized index state summary."""

    model_config = ConfigDict(extra="forbid")

    directory_path: str
    index_name: str
    database_path: str
    schema_version: str
    model_name: str
    embedding_dimensions: int = Field(ge=0)
    chunking_fingerprint: str
    status: IndexStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    indexed_files: int = Field(default=0, ge=0)
    indexed_chunks: int = Field(default=0, ge=0)


class FileSnapshot(BaseModel):
    """Stored snapshot metadata for one indexed file."""

    model_config = ConfigDict(extra="forbid")

    file_path: str
    size_bytes: int = Field(ge=0)
    modified_time: datetime
    content_digest: str = Field(min_length=1)
    chunk_count: int = Field(ge=0)
    last_indexed_at: datetime


class ChunkRecord(BaseModel):
    """Stored searchable unit in the vector index."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    embedding: list[float]

    @model_validator(mode="after")
    def validate_line_range(self) -> "ChunkRecord":
        """Ensure stored line ranges are coherent."""
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class ChunkFinding(BaseModel):
    """Chunk-level semantic query result."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    file: str
    from_line: int = Field(alias="from", serialization_alias="from", ge=1)
    to_line: int = Field(alias="to", serialization_alias="to", ge=1)
    score: float
    contents: str | None = None

    @model_validator(mode="after")
    def validate_line_range(self) -> "ChunkFinding":
        """Ensure result line ranges are coherent."""
        if self.to_line < self.from_line:
            raise ValueError("to must be greater than or equal to from")
        return self


class FileFinding(BaseModel):
    """File-level semantic query result."""

    model_config = ConfigDict(extra="forbid")

    file: str
    best_score: float
