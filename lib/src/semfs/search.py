"""Search entry points for semfs."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from semfs.chunking import merge_contiguous_findings
from semfs.config import parse_index_config, parse_query_request
from semfs.errors import FileProcessingError
from semfs.indexer import open_prepared_index
from semfs.models import ChunkFinding, FileFinding, IndexConfig, QueryRequest
from semfs.storage import (
    IndexStore,
    digest_contents,
    embed_texts,
    fetch_chunk_candidates,
    read_file_snapshot,
)
from semfs.verbose import emit_verbose, timed_verbose


def _candidate_k(query: QueryRequest) -> int:
    return max(query.max_results * 5, 25)


def _score_from_distance(distance: float) -> float:
    return 1.0 / (1.0 + distance)


def _matching_chunk_rows(
    store: IndexStore,
    query: QueryRequest,
    model_config: IndexConfig,
    *,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    query_embedding = embed_texts([query.text], model_config.model, verbose=verbose)[0]
    rows = fetch_chunk_candidates(
        store,
        query_embedding,
        _candidate_k(query),
        verbose=verbose,
    )

    filtered: list[dict[str, Any]] = []
    with timed_verbose(
        verbose,
        "Applying distance filter",
        after_message=lambda: f"Applied distance filter; {len(filtered)} rows remain",
    ):
        filtered = [row for row in rows if query.max_distance is None or float(row["distance"]) <= query.max_distance]
    return filtered


def _chunk_findings_from_rows(rows: list[dict[str, Any]], *, verbose: bool = False) -> list[ChunkFinding]:
    findings: list[ChunkFinding] = []
    ranked: list[ChunkFinding] = []
    with timed_verbose(
        verbose,
        f"Parsing {len(rows)} candidate rows into chunk findings",
        after_message=lambda: (
            f"Parsed {len(rows)} rows into {len(findings)} chunk findings and {len(ranked)} merged results"
        ),
    ):
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
        ]
        merged = merge_contiguous_findings(findings)
        ranked = sorted(merged, key=lambda finding: (-finding.score, finding.file, finding.from_line))
    return ranked


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
    *,
    verbose: bool = False,
) -> list[ChunkFinding]:
    """Return ranked chunk findings for one semantic query."""
    parsed_query = parse_query_request(query)
    parsed_config = parse_index_config(config)

    emit_verbose(verbose, f"Querying: '{parsed_query.text}'")
    with open_prepared_index(directory, parsed_config, verbose=verbose) as prepared:
        rows = _matching_chunk_rows(prepared.store, parsed_query, parsed_config, verbose=verbose)
        ranked = _chunk_findings_from_rows(rows, verbose=verbose)
        final = ranked[: parsed_query.max_results]

        if not fetch_contents:
            return final

        with_contents: list[ChunkFinding] = []
        with timed_verbose(
            verbose,
            f"Reading and verifying excerpt contents for {len(final)} results",
            after_message=lambda: f"Read and verified excerpt contents for {len(with_contents)} results",
        ):
            for finding in final:
                snapshot = read_file_snapshot(prepared.store, finding.file)
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
    *,
    verbose: bool = False,
) -> list[FileFinding]:
    """Return ranked file findings derived from semantic chunk candidates."""
    parsed_query = parse_query_request(query)
    parsed_config = parse_index_config(config)

    emit_verbose(verbose, f"Querying: '{parsed_query.text}'")
    with open_prepared_index(directory, parsed_config, verbose=verbose) as prepared:
        rows = _matching_chunk_rows(prepared.store, parsed_query, parsed_config, verbose=verbose)

    best_distances: dict[str, float] = {}
    result: list[FileFinding] = []
    with timed_verbose(
        verbose,
        "Ranking file findings",
        after_message=lambda: f"Ranked file findings; returning {len(result)} files",
    ):
        for row in rows:
            file_path = str(row["file_path"])
            distance = float(row["distance"])
            best_distance = best_distances.get(file_path)
            if best_distance is None or distance < best_distance:
                best_distances[file_path] = distance

        ranked = sorted(best_distances.items(), key=lambda item: (item[1], item[0]))
        result = [
            FileFinding.model_validate({"file": file_path, "best_score": _score_from_distance(distance)})
            for file_path, distance in ranked[: parsed_query.max_results]
        ]
    return result
