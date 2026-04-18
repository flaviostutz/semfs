from __future__ import annotations

from pathlib import Path

from .config import ChunkingConfig
from .models import ChunkDocument


def chunk_text(path: Path, text: str, config: ChunkingConfig) -> list[ChunkDocument]:
    lines = text.splitlines()
    if not lines:
        return []
    if config.mode == "auto" and path.suffix.lower() == ".md":
        return _chunk_markdown(path, lines, config)
    return _chunk_line_window(path, lines, config, 1)


def _chunk_markdown(path: Path, lines: list[str], config: ChunkingConfig) -> list[ChunkDocument]:
    sections: list[tuple[int, int]] = []
    section_start = 0
    for index, line in enumerate(lines):
        if index and line.startswith("#"):
            sections.append((section_start, index))
            section_start = index
    sections.append((section_start, len(lines)))

    chunks: list[ChunkDocument] = []
    for start, end in sections:
        section_lines = lines[start:end]
        char_count = sum(len(line) + 1 for line in section_lines)
        if char_count <= config.size:
            chunks.append(
                ChunkDocument(
                    file=str(path),
                    start_line=start + 1,
                    end_line=end,
                    text="\n".join(section_lines).strip(),
                )
            )
            continue
        chunks.extend(_chunk_line_window(path, section_lines, config, start + 1))
    return [chunk for chunk in chunks if chunk.text]


def _chunk_line_window(
    path: Path,
    lines: list[str],
    config: ChunkingConfig,
    base_line: int,
) -> list[ChunkDocument]:
    chunks: list[ChunkDocument] = []
    start = 0
    while start < len(lines):
        end = start
        char_count = 0
        while end < len(lines) and (char_count < config.size or end == start):
            char_count += len(lines[end]) + 1
            end += 1
        chunk_lines = lines[start:end]
        chunks.append(
            ChunkDocument(
                file=str(path),
                start_line=base_line + start,
                end_line=base_line + end - 1,
                text="\n".join(chunk_lines).strip(),
            )
        )
        if end >= len(lines):
            break
        next_start = _start_for_overlap(lines, end, config.overlap)
        start = max(next_start, start + 1)
    return [chunk for chunk in chunks if chunk.text]


def _start_for_overlap(lines: list[str], end_index: int, overlap_chars: int) -> int:
    if overlap_chars == 0:
        return end_index
    current = end_index
    consumed = 0
    while current > 0 and consumed < overlap_chars:
        current -= 1
        consumed += len(lines[current]) + 1
    return current
