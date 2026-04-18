# semfs

Semantic file queries for local folders via a Python library and CLI.

## Getting Started

```sh
uv lock
make test
```

```sh
uv run semfs --help
```

Create `.semfsrc` as UTF-8 JSON before running indexed commands. The configured embedding model must be available locally before offline indexing, querying, or benchmark runs.

## CLI Examples

```sh
uv run semfs --version
```

```sh
uv run semfs index docs
```

```sh
uv run semfs chunks docs "what is x?" --top 5
```

```sh
uv run semfs files docs "what is x?" --top 5
```

```sh
uv run semfs index docs --config .semfsrc
```

Benchmark artifacts are written as JSON files under `benchmarks/` and preserved across planned runs unless they are removed explicitly.

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

## Layout

- `src/semfs/` contains the library and CLI scaffold.
- `tests/` contains unit tests for the scaffolded package surface.
- `examples/` contains runnable usage scenarios executed by `make test`.
- `specs/001-semantic-file-query/` contains the active feature artifacts.
