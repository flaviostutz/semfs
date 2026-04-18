"""Indexing entry point and embedding-model loading utilities for semfs."""

from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any

from semfs.config import parse_index_config
from semfs.errors import FileProcessingError, ModelUnavailableError
from semfs.models import IndexConfig, IndexMode, IndexState, IndexStatus
from semfs.storage import SCHEMA_VERSION, chunking_fingerprint, default_index_path


@cache
def load_embedding_model(model_name: str) -> Any:
    """Load and cache one sentence-transformers model per configured model name."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        message = (
            f"Failed action `load_model` for model {model_name}: sentence-transformers is unavailable. "
            "Next step: install dependencies and retry."
        )
        raise ModelUnavailableError(message) from exc

    try:
        return SentenceTransformer(model_name)
    except (OSError, RuntimeError, ValueError) as exc:
        message = (
            f"Failed action `load_model` for model {model_name}: the embedding model could not be loaded. "
            "Next step: install or download the model locally and retry."
        )
        raise ModelUnavailableError(message) from exc


def embedding_dimensions(model_name: str) -> int:
    """Return the embedding dimension reported by the configured model."""
    model = load_embedding_model(model_name)
    dimensions = model.get_sentence_embedding_dimension()
    if not isinstance(dimensions, int) or dimensions <= 0:
        message = (
            f"Failed action `load_model` for model {model_name}: invalid embedding dimensions were reported. "
            "Next step: verify the model and retry."
        )
        raise ModelUnavailableError(message)
    return dimensions


def index(directory: str, config: IndexConfig | dict[str, Any] | None = None) -> IndexState:
    """Validate the directory and config, then return an initialized index state summary."""
    parsed_config = parse_index_config(config)
    target = Path(directory).resolve()
    if not target.exists() or not target.is_dir():
        message = (
            f"Failed action `index` for {target}: target directory does not exist. "
            "Next step: provide an existing directory and retry."
        )
        raise FileProcessingError(message)

    database_path = ":memory:"
    status = IndexStatus.EPHEMERAL
    if parsed_config.mode not in {IndexMode.INMEMORY, IndexMode.TRANSIENT}:
        database_path = str(default_index_path(str(target), parsed_config.name))
        status = IndexStatus.READY

    now = datetime.now(UTC)
    return IndexState(
        directory_path=str(target),
        index_name=parsed_config.name,
        database_path=database_path,
        schema_version=SCHEMA_VERSION,
        model_name=parsed_config.model,
        embedding_dimensions=0,
        chunking_fingerprint=chunking_fingerprint(parsed_config),
        status=status,
        created_at=now,
        updated_at=now,
        indexed_files=0,
        indexed_chunks=0,
    )
