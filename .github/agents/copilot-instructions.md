# semfs Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-18

## Active Technologies
- Python 3.11+ (current workspace: Python 3.14.3)
- sentence-transformers, Typer, Pydantic, sqlite3, sqlite-vec, numpy, pytest
- Local filesystem plus SQLite index databases under `{dir}/.semfs/<index-name>/index.db`
- sqlite-vec-backed nearest-neighbor queries in the persisted `chunk_index` table

## Project Structure

```text
src/
tests/
tests_integration/
examples/
```

## Commands

- `make install`
- `make lint`
- `make lint-fix`
- `make test`
- `make build`
- `uv run semfs --help`

## Code Style

- Keep CLI argument parsing and config discovery in `src/semfs/cli.py`.
- Keep storage setup and sqlite-vec schema ownership in `src/semfs/storage.py`.
- Keep direct KNN retrieval and result post-processing in `src/semfs/search.py`.
- Keep benchmark corpus generation deterministic and local-only.

## Recent Changes
- 001-semantic-file-query: Implemented chunk and file semantic search through library and CLI flows.
- 001-semantic-file-query: Implemented named index lifecycle modes `refresh`, `auto`, `stale`, `inmemory`, and `transient`.
- 001-semantic-file-query: Implemented deterministic benchmark corpora and JSON timing artifacts under `benchmarks/`.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
