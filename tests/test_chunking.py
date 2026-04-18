from semfs.chunking import chunk_text, merge_contiguous_findings
from semfs.models import ChunkFinding, ChunkingConfig, ChunkingEdges


def test_fixed_chunking_tracks_line_ranges() -> None:
    text = "line1\nline2\nline3\nline4\nline5\nline6\n"
    config = ChunkingConfig(size=12, overlap=4, edges=ChunkingEdges.FIXED)

    chunks = chunk_text(text, "notes.txt", config)

    assert len(chunks) >= 2
    assert chunks[0].start_line == 1
    assert chunks[0].end_line >= 2
    assert chunks[-1].end_line == 6


def test_auto_chunking_uses_markdown_headings() -> None:
    text = "# Title\nintro\n\n## Details\nmore text\n"
    config = ChunkingConfig(size=80, overlap=20, edges=ChunkingEdges.AUTO)

    chunks = chunk_text(text, "README.md", config)

    assert len(chunks) == 2
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 3
    assert chunks[1].start_line == 4


def test_merge_contiguous_findings_combines_adjacent_ranges() -> None:
    findings = [
        ChunkFinding.model_validate({"file": "docs/a.md", "from": 1, "to": 3, "score": 0.7}),
        ChunkFinding.model_validate({"file": "docs/a.md", "from": 4, "to": 5, "score": 0.9}),
        ChunkFinding.model_validate({"file": "docs/b.md", "from": 2, "to": 2, "score": 0.5}),
    ]

    merged = merge_contiguous_findings(findings)

    assert len(merged) == 2
    assert merged[0].file == "docs/a.md"
    assert merged[0].from_line == 1
    assert merged[0].to_line == 5
    assert merged[0].score == 0.9
