"""Chunking helpers for semfs."""

from bisect import bisect_right
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from semfs.errors import ConfigError
from semfs.models import ChunkFinding, ChunkingConfig, ChunkingEdges

MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown"}


@dataclass(slots=True)
class ChunkSpan:
    """A chunked text span with stable line ranges."""

    text: str
    start_line: int
    end_line: int


def chunking_description(edges: str) -> str:
    """Describe the configured chunking strategy."""
    if edges == ChunkingEdges.AUTO.value:
        return "markdown-aware for markdown files, fixed otherwise"
    return "fixed overlapping windows"


def _line_offsets(text: str) -> list[int]:
    offsets = [0]
    total = 0
    for line in text.splitlines(keepends=True):
        total += len(line)
        offsets.append(total)
    if len(offsets) == 1:
        offsets.append(0)
    return offsets


def _line_number_for_offset(offset: int, offsets: list[int]) -> int:
    if offsets[-1] == 0:
        return 1
    normalized = min(max(offset, 0), offsets[-1] - 1)
    return bisect_right(offsets, normalized) - 1 + 1


def chunk_fixed_windows(text: str, chunking: ChunkingConfig) -> list[ChunkSpan]:
    """Split text into overlapping fixed-size windows with stable line ranges."""
    if chunking.overlap >= chunking.size:
        message = (
            "Failed action `chunk_text`: chunking.overlap must be smaller than chunking.size. "
            "Next step: reduce overlap and retry."
        )
        raise ConfigError(message)

    if not text:
        return []

    offsets = _line_offsets(text)
    step = chunking.size - chunking.overlap
    spans: list[ChunkSpan] = []
    start = 0
    while start < len(text):
        end = min(start + chunking.size, len(text))
        slice_text = text[start:end]
        start_line = _line_number_for_offset(start, offsets)
        end_line = _line_number_for_offset(max(end - 1, start), offsets)
        spans.append(ChunkSpan(text=slice_text, start_line=start_line, end_line=end_line))
        if end >= len(text):
            break
        start += step
    return spans


def _markdown_blocks(text: str) -> list[ChunkSpan]:
    lines = text.splitlines(keepends=True)
    if not any(line.lstrip().startswith("#") for line in lines):
        return []

    blocks: list[ChunkSpan] = []
    current_lines: list[str] = []
    block_start = 1

    for line_number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("#") and current_lines:
            blocks.append(ChunkSpan("".join(current_lines), block_start, line_number - 1))
            current_lines = [line]
            block_start = line_number
            continue

        current_lines.append(line)
        if not line.strip():
            blocks.append(ChunkSpan("".join(current_lines), block_start, line_number))
            current_lines = []
            block_start = line_number + 1

    if current_lines:
        blocks.append(ChunkSpan("".join(current_lines), block_start, len(lines) or 1))

    return [block for block in blocks if block.text]


def _split_large_block(block: ChunkSpan, chunking: ChunkingConfig) -> list[ChunkSpan]:
    fixed_chunks = chunk_fixed_windows(block.text, chunking)
    offset = block.start_line - 1
    return [
        ChunkSpan(text=chunk.text, start_line=chunk.start_line + offset, end_line=chunk.end_line + offset)
        for chunk in fixed_chunks
    ]


def chunk_markdown(text: str, chunking: ChunkingConfig) -> list[ChunkSpan]:
    """Split markdown text into heading-aware blocks with a soft size target."""
    blocks = _markdown_blocks(text)
    if not blocks:
        return chunk_fixed_windows(text, chunking)

    spans: list[ChunkSpan] = []
    current_text = ""
    start_line = blocks[0].start_line
    end_line = blocks[0].end_line

    for block in blocks:
        if len(block.text) > chunking.size:
            if current_text:
                spans.append(ChunkSpan(text=current_text, start_line=start_line, end_line=end_line))
                current_text = ""
            spans.extend(_split_large_block(block, chunking))
            start_line = block.end_line + 1
            end_line = block.end_line
            continue

        starts_new_heading = block.text.lstrip().startswith("#") and current_text
        exceeds_target = current_text and len(current_text) + len(block.text) > chunking.size
        if starts_new_heading or exceeds_target:
            spans.append(ChunkSpan(text=current_text, start_line=start_line, end_line=end_line))
            current_text = block.text
            start_line = block.start_line
            end_line = block.end_line
            continue

        if not current_text:
            current_text = block.text
            start_line = block.start_line
            end_line = block.end_line
        else:
            current_text += block.text
            end_line = block.end_line

    if current_text:
        spans.append(ChunkSpan(text=current_text, start_line=start_line, end_line=end_line))

    return spans


def chunk_text(text: str, path: str | Path, chunking: ChunkingConfig) -> list[ChunkSpan]:
    """Chunk text using the configured strategy and the file suffix when needed."""
    suffix = Path(path).suffix.lower()
    if chunking.edges == ChunkingEdges.AUTO and suffix in MARKDOWN_SUFFIXES:
        return chunk_markdown(text, chunking)
    return chunk_fixed_windows(text, chunking)


def merge_contiguous_findings(findings: Iterable[ChunkFinding]) -> list[ChunkFinding]:
    """Merge overlapping or directly adjacent chunk findings from the same file."""
    ordered = sorted(findings, key=lambda finding: (finding.file, finding.from_line, finding.to_line))
    if not ordered:
        return []

    merged = [ordered[0]]
    for finding in ordered[1:]:
        current = merged[-1]
        if finding.file == current.file and finding.from_line <= current.to_line + 1:
            new_contents = current.contents or finding.contents
            if current.contents and finding.contents and finding.contents not in current.contents:
                new_contents = f"{current.contents}\n{finding.contents}"
            merged[-1] = current.model_copy(
                update={
                    "to_line": max(current.to_line, finding.to_line),
                    "score": max(current.score, finding.score),
                    "contents": new_contents,
                }
            )
            continue
        merged.append(finding)

    return merged
