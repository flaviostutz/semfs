# Implementation Plan: Semantic File Query Library and CLI

**Branch**: `[001-semantic-file-query]` | **Date**: 2026-04-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-semantic-file-query/spec.md`

## Summary

Build `semfs` as a uv-managed Python library with a thin Typer CLI that indexes local directories into named SQLite plus sqlite-vec semantic indexes under `{dir}/.semfs/`, searches chunk and file results with local sentence-transformer embeddings and sqlite-vec nearest-neighbor queries, and ships deterministic benchmark scenarios for small and large markdown corpora.

## Technical Context

**Language/Version**: Python 3.11+ (current workspace: Python 3.14.3)  
**Primary Dependencies**: sentence-transformers, Typer, Pydantic, sqlite3, sqlite-vec, numpy, pytest  
**Storage**: Local filesystem plus SQLite index databases under `{dir}/.semfs/<index-name>/index.db`, with sqlite-vec tables for persisted embeddings and nearest-neighbor queries  
**Testing**: pytest, pytest-cov, integration tests over generated corpora  
**Target Platform**: Local macOS/Linux developer environments via uv and uvx  
**Project Type**: Python library + CLI  
**Performance Goals**: Complete indexing and query benchmark runs for 30-file and 5000-file corpora; keep top-k local queries interactive enough for manual CLI use. These goals are advisory planning guidance only; release acceptance for benchmark coverage depends on successful JSON artifact generation and completeness rather than any fixed timing threshold.  
**Constraints**: Offline-capable, no external services, named persistent indexes, embedded sqlite-vec deployment, CLI parity with library API, current repo lacks Python packaging and standard Make targets  
**Scale/Scope**: Semantic search across filtered text files, contiguous chunk merging, benchmark corpora of 5 folders/30 files and 300 folders/5000 files with max depth 7

## Storage And Query Design

Use one SQLite database per named index and keep `file_snapshots` as a regular SQLite table, but collapse chunk metadata and embeddings into a single `sqlite-vec` table. For the MVP, this single-table `chunk_index` shape is a required storage contract rather than an optional implementation detail.

Only UTF-8-readable text files selected by the configured filter are in scope for indexing. Binary files, unreadable files, and other unsupported non-text inputs are skipped.

`chunking.edges` controls chunk construction before vectors are written: `auto` applies markdown-aware chunking to markdown files and fixed overlapping chunking to all other files, while `fixed` always uses fixed overlapping chunking. If markdown-aware chunking finds no useful structure, it falls back to the same fixed overlapping chunking behavior.

Do not persist file contents in the index. The index should stay small, so chunk text is used only transiently during indexing to compute embeddings, and query-time excerpts are reconstructed from the live file only when contents are explicitly requested. Acceptable index-size growth for the MVP is defined by this rule rather than by a fixed database-size ceiling.

To avoid inconsistent excerpt output, only return live-file contents when the current file still matches the indexed snapshot.

If the configured filter matches files but none of them yield chunks, index creation still succeeds and leaves a usable index state whose queries return empty results.

`storage.py` owns connection setup, sqlite-vec extension loading, schema creation, and rebuild transactions. The planned schema is:

- `index_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)` for schema version, model name, embedding dimension, and chunking fingerprint.
- `file_snapshots(file_path TEXT PRIMARY KEY, size_bytes INTEGER NOT NULL, modified_time TEXT NOT NULL, content_digest TEXT NOT NULL, chunk_count INTEGER NOT NULL, last_indexed_at TEXT NOT NULL)` for `auto` freshness detection and live-file consistency checks before returning contents.
- `chunk_index` as one `vec0` table that stores both the embedding and the chunk result fields needed after KNN retrieval, for example:

    ```sql
    CREATE VIRTUAL TABLE chunk_index USING vec0(
        chunk_id INTEGER PRIMARY KEY,
        embedding FLOAT[{dimensions}] DISTANCE_METRIC=cosine,
        +file_path TEXT,
        +start_line INTEGER,
        +end_line INTEGER
    )
    ```

    The non-vector columns are auxiliary fields because they are returned in query results but are not part of KNN filtering.

`storage.py` inserts file metadata into `file_snapshots` and writes chunk rows directly into `chunk_index` in the same rebuild transaction. Rebuilds for `refresh` and `auto` replace both datasets atomically so metadata and vectors never drift.

`content_digest` compatibility is fixed to SHA-256 over the UTF-8 text contents used for indexing. Changing that rule requires a schema-version change.

`search.py` must embed the query once and execute KNN directly against `chunk_index`. The baseline query pattern is:

```sql
SELECT
        chunk_id,
        file_path,
        start_line,
        end_line,
        distance
FROM chunk_index
WHERE embedding MATCH :query_embedding
    AND k = :candidate_k
ORDER BY distance, file_path, start_line;
```

For `chunks()`, `search.py` applies the optional `max_distance` filter to the retrieved candidates, merges directly contiguous ranges from the same file in Python, and trims to `max_results` after merging so the public contract stays stable. When `fetch_contents=True`, `search.py` reads the live file, verifies that its digest matches `file_snapshots.content_digest`, and only then returns the requested excerpt for the merged line range.

For `files()`, `search.py` must reuse the same KNN candidate query, group returned chunk matches by `file_path` in Python, compute `MIN(distance)` as the file score, sort ascending by that score and then by relative `file_path` ascending for ties, and apply `max_results` after deduplication.

Use an over-fetch candidate count for both query modes so merging and file deduplication do not starve the final result set. The plan baseline is `candidate_k = max(max_results * 5, 25)`. This is a default internal heuristic, not a public behavior contract, and may change if benchmark evidence justifies a better default.

This keeps the index small while preventing silent mismatches between indexed vectors and returned excerpt text. In `stale` mode, passage ranking can still come from the existing index, but `fetch_contents=True` must fail with an actionable error if the live file no longer matches the indexed snapshot or cannot be read.

`benchmark.py` must persist benchmark timing artifacts as JSON records under the repository-level `benchmarks/` directory so each planned benchmark run leaves a reusable record for documentation updates without overwriting prior artifacts unless cleanup is requested explicitly.

Benchmark and indexing flows are expected to run incrementally on one local machine once the configured model is available locally; they should not depend on external services or on loading the full corpus into memory at once.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. XDR-First | Product and engineering decisions captured in `_local` XDRs before implementation | PASS |
| II. Preset Integrity | No filedist preset extraction changes are in scope for this feature | PASS |
| III. Consumer-First | New public library and CLI surface treated as a MINOR-version addition | PASS |
| IV. Self-Contained | New spec artifacts and local XDRs are concise and cross-linked | PASS |
| V. Simplicity | Chosen stack stays local and minimal; Milestone 1 adds missing `build`, `lint-fix`, and `test` workflow targets | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/001-semantic-file-query/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── library-api.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── semfs/
    ├── __init__.py
    ├── __main__.py
    ├── benchmark.py
    ├── chunking.py
    ├── cli.py
    ├── config.py
    ├── errors.py
    ├── indexer.py
    ├── models.py
    ├── search.py
    ├── storage.py
    └── synthetic_data.py

tests/
├── conftest.py
├── test_chunking.py
├── test_cli.py
├── test_config.py
├── test_indexer.py
└── test_search.py

tests_integration/
├── test_large_corpus.py
└── test_small_corpus.py

examples/
├── Makefile
├── basic-usage/
│   ├── Makefile
│   └── main.py
└── benchmark-corpora/
    ├── Makefile
    └── run.py
```

**Structure Decision**: Use a single Python package with a thin CLI adapter over library modules, dedicated integration tests, and runnable examples in `examples/` to satisfy agentme Python and CLI standards.
