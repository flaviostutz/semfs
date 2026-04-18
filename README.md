# semfs

Semantic file queries for local folders via a Python library and CLI.

## Getting Started

```sh
make install
```

```sh
cat > .semfsrc <<'EOF'
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
EOF
```

```sh
uv run semfs index docs
```

Create `.semfsrc` as UTF-8 JSON before running indexed commands. The configured embedding model must be available locally before offline indexing, querying, or benchmark runs.

`chunking.edges: "auto"` uses markdown-aware chunking for markdown files and fixed chunking for other UTF-8 text files. `"fixed"` always uses fixed chunking.

Only UTF-8-readable text files matched by the filter are indexed. Binary files, unreadable files, and other unsupported non-text inputs are skipped.

## CLI Examples

```sh
uv run semfs --version
```

```sh
uv run semfs index docs
```

```sh
uv run semfs chunks docs "what is x?" --top 5 --contents
```

```sh
uv run semfs files docs "what is x?" --top 5
```

```sh
uv run semfs index docs --config .semfsrc
```

```sh
uv run python examples/benchmark-corpora/run.py
```

Successful `index` runs print a start message and a completion message with indexed file and chunk counts. Benchmark artifacts are written as JSON files under `benchmarks/` and preserved across planned runs unless they are removed explicitly.

If the configured model is not available locally, semfs fails with an actionable error instead of silently falling back to online behavior.

## Library Examples

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
print(state.status)
```

```python
import semfs

query = {"text": "what is x?", "max_results": 5}
config = {
    "name": "index0",
    "filter": "**/*.md",
    "mode": "auto",
    "chunking": {"size": 500, "overlap": 250, "edges": "auto"},
    "model": "sentence-transformers/all-MiniLM-L6-v2",
}
print(semfs.chunks(query, "docs", False, config))
print(semfs.files(query, "docs", config))
```

## Benchmark Flow

Run the benchmark example directly when you want fresh timing artifacts without running the full test suite:

```sh
uv run python examples/benchmark-corpora/run.py
```

Run the full suite, including the runnable examples, with:

```sh
make test
```

Each planned benchmark run writes one JSON artifact per dataset under `benchmarks/`. Small and large corpora are generated deterministically during the benchmark run and integration tests.

## Layout

- `src/semfs/` contains the library and CLI implementation.
- `tests/` contains unit tests for config, indexing, search, and CLI behavior.
- `tests_integration/` contains deterministic corpus and benchmark integration coverage.
- `examples/` contains runnable usage scenarios executed by `make test`.
- `specs/001-semantic-file-query/` contains the active feature artifacts.
