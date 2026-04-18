from __future__ import annotations

import fnmatch
import hashlib
import math
import re
from collections import Counter
from pathlib import Path

from .chunking import chunk_text
from .config import SearchConfig
from .models import ChunkDocument, IndexRow

TOKEN_RE = re.compile(r"[a-zA-Z0-9]{2,}")
SKIP_DIRS = {".git", ".semfs", ".venv", "node_modules", "dist", "build", "__pycache__"}


def discover_documents(
    directory: Path, config: SearchConfig
) -> tuple[list[ChunkDocument], str, int]:
    files = _discover_files(directory, config.filter)
    manifest_entries: list[str] = []
    chunks: list[ChunkDocument] = []
    for file_path in files:
        relative_path = file_path.relative_to(directory)
        stat = file_path.stat()
        manifest_entries.append(f"{relative_path}:{stat.st_size}:{stat.st_mtime_ns}")
        text = _read_text(file_path)
        if text is None:
            continue
        chunks.extend(chunk_text(relative_path, text, config.chunking))
    fingerprint = hashlib.sha256("\n".join(sorted(manifest_entries)).encode("utf-8")).hexdigest()
    return chunks, fingerprint, len(files)


def build_index_payload(chunks: list[ChunkDocument]) -> tuple[dict[str, float], list[IndexRow]]:
    document_frequency: Counter[str] = Counter()
    tokenized_chunks: list[tuple[ChunkDocument, Counter[str]]] = []

    for chunk in chunks:
        counts = Counter(tokenize(chunk.text))
        if not counts:
            continue
        tokenized_chunks.append((chunk, counts))
        document_frequency.update(counts.keys())

    chunk_count = len(tokenized_chunks)
    idf = {
        term: math.log((1 + chunk_count) / (1 + frequency)) + 1.0
        for term, frequency in document_frequency.items()
    }

    rows: list[IndexRow] = []
    for chunk, counts in tokenized_chunks:
        weights = {term: count * idf[term] for term, count in counts.items()}
        norm = math.sqrt(sum(weight * weight for weight in weights.values())) or 1.0
        rows.append(
            {
                "file": chunk.file,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "text": chunk.text,
                "weights": weights,
                "norm": norm,
            }
        )
    return idf, rows


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _discover_files(directory: Path, pattern: str) -> list[Path]:
    files: list[Path] = []
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        relative = path.relative_to(directory).as_posix()
        if _matches_pattern(relative, pattern):
            files.append(path)
    return sorted(files)


def _matches_pattern(relative_path: str, pattern: str) -> bool:
    if fnmatch.fnmatch(relative_path, pattern):
        return True
    if Path(relative_path).match(pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatch(relative_path, pattern[3:])
    return False


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
