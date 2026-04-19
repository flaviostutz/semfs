from pathlib import Path

import pytest

import semfs
from semfs.config import parse_index_config
from semfs.errors import FileProcessingError
from semfs.storage import (
    build_file_snapshot,
    chromadb_version,
    chunking_fingerprint,
    detect_snapshot_drift,
    index_is_usable,
    open_index_store,
    write_file_snapshots,
    write_index_metadata,
)


def _config_payload() -> dict[str, object]:
    return {
        "name": "index0",
        "filter": "**/*.md",
        "mode": "auto",
        "chunking": {"size": 120, "overlap": 30, "edges": "auto"},
    }


def test_chromadb_connection_and_schema(tmp_path: Path) -> None:
    store_path = tmp_path / "test_store"
    store = open_index_store(store_path)

    assert chromadb_version() != ""
    assert store.chunks is not None
    assert store.snapshots is not None
    assert store.index_meta is not None


def test_index_metadata_and_snapshot_drift(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    file_path = root / "a.md"
    file_path.write_text("# Title\nbody\n", encoding="utf-8")

    store = open_index_store(tmp_path / "store")
    config = parse_index_config(_config_payload())

    write_index_metadata(store, config)

    snapshot = build_file_snapshot(root, file_path, chunk_count=1)
    write_file_snapshots(store, [snapshot])

    assert index_is_usable(store, config)
    assert chunking_fingerprint(config)
    assert not detect_snapshot_drift(store, root, [file_path])

    file_path.write_text("# Title\nchanged\n", encoding="utf-8")
    assert detect_snapshot_drift(store, root, [file_path])


def test_chunks_query_merges_contiguous_ranges(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config(_config_payload())

    findings = semfs.chunks({"text": "alpha", "max_results": 1}, str(sample_docs), config=config)

    assert len(findings) == 1
    assert findings[0].file == "alpha.md"
    assert findings[0].from_line == 1
    assert findings[0].to_line >= 6
    assert findings[0].score > 0.5


def test_chunks_returns_verified_contents(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config(_config_payload())

    findings = semfs.chunks({"text": "alpha", "max_results": 1}, str(sample_docs), fetch_contents=True, config=config)

    assert len(findings) == 1
    assert findings[0].contents is not None
    assert "alpha concept" in findings[0].contents


def test_chunks_fail_when_contents_digest_mismatches(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config({**_config_payload(), "mode": "stale"})

    semfs.index(str(sample_docs), config)
    (sample_docs / "alpha.md").write_text("# Intro\nchanged\n", encoding="utf-8")

    with pytest.raises(FileProcessingError):
        semfs.chunks({"text": "alpha", "max_results": 5}, str(sample_docs), fetch_contents=True, config=config)


def test_files_query_deduplicates_and_ranks_by_best_match(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config(_config_payload())

    findings = semfs.files({"text": "alpha", "max_results": 5}, str(sample_docs), config=config)

    assert [finding.file for finding in findings] == ["alpha.md", "beta.md"]
    assert findings[0].best_score > findings[1].best_score


def test_files_query_breaks_score_ties_by_path(sample_docs: Path, fake_model: object) -> None:
    _ = fake_model
    config = parse_index_config(_config_payload())
    (sample_docs / "aardvark.md").write_text("# Aardvark\nalpha\n", encoding="utf-8")
    (sample_docs / "zebra.md").write_text("# Zebra\nalpha\n", encoding="utf-8")

    findings = semfs.files({"text": "alpha", "max_results": 2}, str(sample_docs), config=config)

    assert [finding.file for finding in findings] == ["aardvark.md", "zebra.md"]
    assert findings[0].best_score == findings[1].best_score
