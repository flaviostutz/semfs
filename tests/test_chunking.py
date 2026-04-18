from __future__ import annotations

from pathlib import Path

from semfs.chunking import chunk_text
from semfs.config import ChunkingConfig


def test_markdown_auto_prefers_heading_sections() -> None:
    chunks = chunk_text(
        Path("notes.md"),
        "# One\n\nalpha\n\n# Two\n\nbeta\n",
        ChunkingConfig(size=100, overlap=20, mode="auto"),
    )
    assert [chunk.start_line for chunk in chunks] == [1, 5]


def test_fixed_chunking_applies_overlap() -> None:
    text = "\n".join(f"line {index}" for index in range(1, 9))
    chunks = chunk_text(Path("plain.txt"), text, ChunkingConfig(size=14, overlap=7, mode="fixed"))
    assert len(chunks) > 1
    assert chunks[1].start_line <= chunks[0].end_line
