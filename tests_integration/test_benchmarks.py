from __future__ import annotations

import random
import time
from pathlib import Path

import semfs


def test_small_corpus_benchmark(tmp_path: Path) -> None:
    corpus = _build_corpus(
        tmp_path / "small", folder_count=5, file_count=30, total_words=2000, max_depth=3
    )

    start = time.perf_counter()
    semfs.index(str(corpus), {"mode": "refresh"})
    index_seconds = time.perf_counter() - start

    start = time.perf_counter()
    results = semfs.files(
        {"text": "semantic index", "max_results": 5}, str(corpus), {"mode": "stale"}
    )
    query_seconds = time.perf_counter() - start

    assert results
    print(f"small corpus index seconds={index_seconds:.4f} query seconds={query_seconds:.4f}")


def test_large_corpus_benchmark(tmp_path: Path) -> None:
    corpus = _build_corpus(
        tmp_path / "large", folder_count=300, file_count=5000, total_words=20000, max_depth=7
    )

    start = time.perf_counter()
    semfs.index(str(corpus), {"mode": "refresh", "chunking": {"size": 300, "overlap": 100}})
    index_seconds = time.perf_counter() - start

    start = time.perf_counter()
    results = semfs.chunks(
        {"text": "vector search", "max_results": 10}, str(corpus), False, {"mode": "stale"}
    )
    query_seconds = time.perf_counter() - start

    assert results
    print(f"large corpus index seconds={index_seconds:.4f} query seconds={query_seconds:.4f}")


def _build_corpus(
    root: Path, folder_count: int, file_count: int, total_words: int, max_depth: int
) -> Path:
    random.seed(42)
    root.mkdir(parents=True, exist_ok=True)
    folders = []
    for index in range(folder_count):
        depth = (index % max_depth) + 1
        folder = root
        for level in range(depth):
            folder /= f"group-{index % folder_count}-d{level + 1}"
        folder.mkdir(parents=True, exist_ok=True)
        folders.append(folder)

    words_per_file = max(20, total_words // file_count)
    vocabulary = [
        "semantic",
        "query",
        "index",
        "vector",
        "chunk",
        "refresh",
        "configuration",
        "markdown",
        "search",
        "content",
    ]
    for file_index in range(file_count):
        folder = folders[file_index % len(folders)]
        words = [random.choice(vocabulary) for _ in range(words_per_file)]
        text = "# Synthetic\n\n" + " ".join(words)
        (folder / f"doc-{file_index}.md").write_text(text, encoding="utf-8")
    return root
