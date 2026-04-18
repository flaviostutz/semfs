"""CLI-owned configuration helpers for the semfs scaffold."""

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_FILE = ".semfsrc"


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load JSON config from the explicit path or the default cwd file when present."""
    candidate = config_path or Path.cwd() / DEFAULT_CONFIG_FILE
    if not candidate.exists():
        return {}
    return dict(json.loads(candidate.read_text(encoding="utf-8")))
