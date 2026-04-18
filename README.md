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
print(semfs.chunks(query, "docs", False, {}))
print(semfs.files(query, "docs", {}))
```

## Layout

- `src/semfs/` contains the library and CLI scaffold.
- `tests/` contains unit tests for the scaffolded package surface.
- `examples/` contains runnable usage scenarios executed by `make test`.
- `specs/001-semantic-file-query/` contains the active feature artifacts.
