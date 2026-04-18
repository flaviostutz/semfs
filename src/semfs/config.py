from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

IndexMode = Literal["refresh", "auto", "stale", "inmemory", "transient"]
ChunkMode = Literal["auto", "fixed"]


@dataclass(frozen=True)
class ChunkingConfig:
    size: int = 500
    overlap: int = 250
    mode: ChunkMode = "auto"


@dataclass(frozen=True)
class SearchConfig:
    name: str = "index0"
    filter: str = "**/*"
    mode: IndexMode = "auto"
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    model: str = "tfidf"


@dataclass(frozen=True)
class Query:
    text: str
    max_results: int = 10
    max_distance: float | None = None


def normalize_dir(directory: str | Path) -> Path:
    return Path(directory).expanduser().resolve()


def normalize_query(raw_query: Query | Mapping[str, Any]) -> Query:
    if isinstance(raw_query, Query):
        query = raw_query
    else:
        text = str(raw_query.get("text", "")).strip()
        if not text:
            raise ValueError("query.text is required")
        query = Query(
            text=text,
            max_results=int(raw_query.get("max_results", 10)),
            max_distance=(
                float(raw_query["max_distance"])
                if raw_query.get("max_distance") is not None
                else None
            ),
        )
    if query.max_results < 1:
        raise ValueError("query.max_results must be at least 1")
    if query.max_distance is not None and query.max_distance < 0:
        raise ValueError("query.max_distance must be non-negative")
    return query


def normalize_config(raw_config: SearchConfig | Mapping[str, Any] | None) -> SearchConfig:
    if raw_config is None:
        config = SearchConfig()
    elif isinstance(raw_config, SearchConfig):
        config = raw_config
    else:
        chunking_raw = raw_config.get("chunking", {})
        config = SearchConfig(
            name=str(raw_config.get("name", "index0")),
            filter=str(raw_config.get("filter", "**/*")),
            mode=cast(IndexMode, str(raw_config.get("mode", "auto"))),
            chunking=ChunkingConfig(
                size=int(chunking_raw.get("size", 500)),
                overlap=int(chunking_raw.get("overlap", 250)),
                mode=cast(ChunkMode, str(chunking_raw.get("mode", "auto"))),
            ),
            model=str(raw_config.get("model", "tfidf")),
        )
    if config.chunking.size < 1:
        raise ValueError("chunking.size must be at least 1")
    if config.chunking.overlap < 0:
        raise ValueError("chunking.overlap must be non-negative")
    if config.chunking.overlap >= config.chunking.size:
        raise ValueError("chunking.overlap must be smaller than chunking.size")
    if config.mode not in {"refresh", "auto", "stale", "inmemory", "transient"}:
        raise ValueError(f"unsupported mode: {config.mode}")
    if config.chunking.mode not in {"auto", "fixed"}:
        raise ValueError(f"unsupported chunking mode: {config.chunking.mode}")
    if config.model != "tfidf":
        raise ValueError(f"unsupported model: {config.model}")
    return config


def config_to_dict(config: SearchConfig) -> dict[str, Any]:
    return {
        "name": config.name,
        "filter": config.filter,
        "mode": config.mode,
        "model": config.model,
        "chunking": {
            "size": config.chunking.size,
            "overlap": config.chunking.overlap,
            "mode": config.chunking.mode,
        },
    }
