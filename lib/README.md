# semfs

Semantic file queries for local folders via a Python library and CLI.

## Getting Started

Create a UTF-8 JSON `.semfsrc` in the working directory:

```json
{
  "name": "index0",
  "filter": "**/*.md",
  "mode": "auto",
  "chunking": {
    "size": 500,
    "overlap": 250,
    "edges": "auto"
  },
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

From a source checkout, install the shared environment and run the CLI through `lib/`:

```sh
make install
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv run --project lib semfs index docs
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv run --project lib semfs chunks docs "what is x?" --top 5
```

The configured embedding model must be available locally before offline indexing or querying.

## Using semfs

semfs is for searching local UTF-8 text folders with semantic queries. It supports two result shapes:

- Chunk results return relative file paths plus inclusive line ranges, with excerpt contents only when requested.
- File results return one deduplicated relative path per matching file, ordered by strongest match first.

Only UTF-8-readable text files matched by the configured filter are indexed. Binary files, unreadable files, and other unsupported non-text inputs are skipped.

`chunking.edges: "auto"` uses markdown-aware chunking for markdown files and fixed chunking for all other UTF-8 text files. `"fixed"` always uses fixed chunking.

Lifecycle modes:

- `refresh` rebuilds before every index or query operation.
- `auto` rebuilds when the index is missing or indexed files changed.
- `stale` reuses an existing index even when files changed and only builds when no usable index exists.
- `inmemory` avoids reusable on-disk index state.
- `transient` uses temporary on-disk state and deletes it after the operation completes.

## CLI Examples

Show the installed version:

```sh
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv run --project lib semfs --version
```

Build or refresh an index:

```sh
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv run --project lib semfs index docs
```

Return chunk matches with excerpt contents:

```sh
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv run --project lib semfs chunks docs "what is x?" --top 5 --contents
```

Return deduplicated matching files:

```sh
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv run --project lib semfs files docs "what is x?" --top 5
```

Use an explicit config file path:

```sh
UV_PROJECT_ENVIRONMENT="$PWD/.venv" UV_CACHE_DIR="$PWD/.cache/uv" uv run --project lib semfs index docs --config .semfsrc
```

Successful `index` runs print a start message and a completion message with indexed file and chunk counts. If the configured model is not available locally, semfs fails with an actionable error instead of falling back to online behavior.

## Library Examples

Create or refresh an index:

```python
import semfs

config = {
    "name": "index0",
    "filter": "**/*.md",
    "mode": "auto",
    "chunking": {"size": 500, "overlap": 250, "edges": "auto"},
    "model": "sentence-transformers/all-MiniLM-L6-v2",
}

state = semfs.index("docs", config)
print(state.indexed_files, state.indexed_chunks)
```

Query chunk and file results:

```python
import semfs

config = {
    "name": "index0",
    "filter": "**/*.md",
    "mode": "auto",
    "chunking": {"size": 500, "overlap": 250, "edges": "auto"},
    "model": "sentence-transformers/all-MiniLM-L6-v2",
}
query = {"text": "what is x?", "max_results": 5}

chunks = semfs.chunks(query, "docs", False, config)
files = semfs.files(query, "docs", config)

print(chunks)
print(files)
```

If excerpt contents are requested and any selected file no longer matches the indexed snapshot or cannot be read, the whole query fails with an actionable error.

## Development

```sh
make build
make lint
make test
```

Consumer examples under `examples/` are verified from the wheel built into `lib/dist/`, not by importing from `lib/src/` directly.