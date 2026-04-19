"""CLI-owned configuration helpers and validators for semfs."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from semfs.errors import ConfigError
from semfs.models import IndexConfig, QueryRequest

DEFAULT_CONFIG_FILE = ".semfsrc"
DEFAULT_INDEX_NAME = "index0"
DEFAULT_INDEX_FILTER = "**/*"
DEFAULT_INDEX_MODE = "auto"
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 250
DEFAULT_CHUNK_EDGES = "auto"


def resolve_config_path(config_path: Path | None = None, cwd: Path | None = None) -> Path:
    """Resolve the explicit config path or the default file under the selected cwd."""
    if config_path is not None:
        return config_path
    return (cwd or Path.cwd()) / DEFAULT_CONFIG_FILE


def default_index_config() -> IndexConfig:
    """Return the CLI default index configuration used when no config file is present."""
    return IndexConfig.model_validate(
        {
            "name": DEFAULT_INDEX_NAME,
            "filter": DEFAULT_INDEX_FILTER,
            "mode": DEFAULT_INDEX_MODE,
            "chunking": {
                "size": DEFAULT_CHUNK_SIZE,
                "overlap": DEFAULT_CHUNK_OVERLAP,
                "edges": DEFAULT_CHUNK_EDGES,
            },
        }
    )


def parse_index_config(config: IndexConfig | Mapping[str, Any] | None) -> IndexConfig:
    """Validate caller-supplied config data."""
    if isinstance(config, IndexConfig):
        return config
    if config is None:
        message = (
            "Failed action `load_config`: missing index configuration. Next step: create .semfsrc or provide --config."
        )
        raise ConfigError(message)
    try:
        return IndexConfig.model_validate(config)
    except ValidationError as exc:
        message = (
            "Failed action `load_config`: invalid index configuration. "
            "Next step: fix the config values and retry. "
            f"Details: {exc}"
        )
        raise ConfigError(message) from exc


def parse_query_request(query: QueryRequest | Mapping[str, Any]) -> QueryRequest:
    """Validate caller-supplied query data."""
    if isinstance(query, QueryRequest):
        return query
    try:
        return QueryRequest.model_validate(query)
    except ValidationError as exc:
        message = (
            "Failed action `query`: invalid query request. "
            "Next step: provide valid text and limits, then retry. "
            f"Details: {exc}"
        )
        raise ConfigError(message) from exc


def load_config(
    config_path: Path | None = None, cwd: Path | None = None, allow_missing: bool = False
) -> IndexConfig | None:
    """Load and validate JSON config from disk."""
    candidate = resolve_config_path(config_path, cwd)
    if not candidate.exists():
        if allow_missing:
            return None
        message = (
            f"Failed action `load_config` for {candidate}: config file not found. "
            "Next step: create .semfsrc or provide --config."
        )
        raise ConfigError(message)

    try:
        raw_config = json.loads(candidate.read_text(encoding="utf-8"))
    except OSError as exc:
        message = (
            f"Failed action `load_config` for {candidate}: config file could not be read. "
            "Next step: fix file permissions and retry."
        )
        raise ConfigError(message) from exc
    except json.JSONDecodeError as exc:
        message = (
            f"Failed action `load_config` for {candidate}: config file is not valid JSON. "
            "Next step: fix the JSON syntax and retry."
        )
        raise ConfigError(message) from exc

    return parse_index_config(raw_config)
