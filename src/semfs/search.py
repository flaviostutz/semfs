"""Search entry points for semfs."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from semfs.chunking import merge_contiguous_findings
from semfs.config import parse_index_config, parse_query_request
from semfs.errors import FileProcessingError
from semfs.indexer import load_embedding_model, open_prepared_index
from semfs.models import ChunkFinding, FileFinding, IndexConfig, QueryRequest
from semfs.storage import digest_contents, fetch_chunk_candidates, read_file_snapshot, serialize_embedding


def _candidate_k(query: QueryRequest) -> int:
    return max(query.max_results * 5, 25)


def _score_from_distance(distance: float) -> float:
    return 1.0 / (1.0 + distance)


def _read_excerpt(root: Path, finding: ChunkFinding, expected_digest: str) -> str:
    file_path = root / finding.file
    try:
        contents = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        message = (
            f"Failed action `chunks` for {file_path}: file could not be read for contents verification. "
            "Next step: rebuild the index or rerun without fetch_contents."
        )
        raise FileProcessingError(message) from exc

    if digest_contents(contents) != expected_digest:
        message = (
            f"Failed action `chunks` for {file_path}: live file no longer matches the indexed snapshot. "
            "Next step: rebuild the index or rerun without fetch_contents."
        )
        raise FileProcessingError(message)

    lines = contents.splitlines()
    return "\n".join(lines[finding.from_line - 1 : finding.to_line])


def chunks(
    query: QueryRequest | Mapping[str, Any],
    directory: str,
    fetch_contents: bool = False,
    config: IndexConfig | Mapping[str, Any] | None = None,
) -> list[ChunkFinding]:
    """Return ranked chunk findings for one semantic query."""
    parsed_query = parse_query_request(query)
    parsed_config = parse_index_config(config)

    with open_prepared_index(directory, parsed_config) as prepared:
        model = load_embedding_model(parsed_config.model)
        query_vector = model.encode([parsed_query.text], normalize_embeddings=True)[0]
        rows = fetch_chunk_candidates(
            prepared.connection,
            serialize_embedding([float(value) for value in query_vector]),
            _candidate_k(parsed_query),
        )

        findings = [
            ChunkFinding.model_validate(
                {
                    "file": str(row["file_path"]),
                    "from": int(row["start_line"]),
                    "to": int(row["end_line"]),
                    "score": _score_from_distance(float(row["distance"])),
                }
            )
            for row in rows
            if parsed_query.max_distance is None or float(row["distance"]) <= parsed_query.max_distance
        ]

        merged = merge_contiguous_findings(findings)
        ranked = sorted(merged, key=lambda finding: (-finding.score, finding.file, finding.from_line))
        final = ranked[: parsed_query.max_results]

        if not fetch_contents:
            return final

        with_contents: list[ChunkFinding] = []
        for finding in final:
            snapshot = read_file_snapshot(prepared.connection, finding.file)
            if snapshot is None:
                message = (
                    f"Failed action `chunks` for {finding.file}: indexed snapshot metadata is missing. "
                    "Next step: rebuild the index or rerun without fetch_contents."
                )
                raise FileProcessingError(message)

            contents_text = _read_excerpt(prepared.root, finding, snapshot.content_digest)
            with_contents.append(finding.model_copy(update={"contents": contents_text}))

        return with_contents


def files(
    query: QueryRequest | Mapping[str, Any],
    directory: str,
    config: IndexConfig | Mapping[str, Any] | None = None,
) -> list[FileFinding]:
    """Validate inputs and return an empty file result set until search is implemented."""
    _ = directory
    parse_query_request(query)
    parse_index_config(config)
    return []
