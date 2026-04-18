from __future__ import annotations

from pathlib import Path

import semfs


def test_index_creates_persistent_artifacts(sample_docs: Path) -> None:
    result = semfs.index(str(sample_docs), {"mode": "refresh", "name": "index0"})
    assert result["chunk_count"] >= 2
    assert (sample_docs / ".semfs" / "index0.json").exists()
    assert (sample_docs / ".semfs" / "index0.db").exists()


def test_files_deduplicate_chunk_hits(sample_docs: Path) -> None:
    result = semfs.files(
        {"text": "local index", "max_results": 5}, str(sample_docs), {"mode": "refresh"}
    )
    assert result[0] == "guide.md"
    assert len(result) == len(set(result))


def test_chunks_merge_adjacent_results(sample_docs: Path) -> None:
    results = semfs.chunks(
        {"text": "configuration commands", "max_results": 5},
        str(sample_docs),
        True,
        {"mode": "refresh", "chunking": {"size": 80, "overlap": 20, "mode": "fixed"}},
    )
    assert results
    assert results[0]["file"] == "cli.md"
    assert results[0]["from"] <= results[0]["to"]
    assert results[0]["contents"] is not None


def test_auto_mode_rebuilds_when_source_changes(sample_docs: Path) -> None:
    first = semfs.index(str(sample_docs), {"mode": "auto"})
    (sample_docs / "guide.md").write_text(
        "# Guide\n\nSemfs now stores metadata and line ranges in its local index.",
        encoding="utf-8",
    )
    second = semfs.index(str(sample_docs), {"mode": "auto"})
    assert first["fingerprint"] != second["fingerprint"]


def test_inmemory_mode_does_not_create_artifacts(sample_docs: Path) -> None:
    result = semfs.files({"text": "configuration"}, str(sample_docs), {"mode": "inmemory"})
    assert result == ["cli.md"]
    assert not (sample_docs / ".semfs").exists()
