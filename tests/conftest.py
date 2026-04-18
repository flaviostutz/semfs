from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_docs(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text(
        "# Guide\n\n"
        "Semfs uses a local index.\n\n"
        "## Refresh\n\n"
        "Auto mode rebuilds when files change.",
        encoding="utf-8",
    )
    (docs / "cli.md").write_text(
        "# CLI\n\n"
        "The semfs CLI loads configuration from .semfsrc and exposes "
        "index, files, and chunks commands.",
        encoding="utf-8",
    )
    return docs
