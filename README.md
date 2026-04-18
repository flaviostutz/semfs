# semfs

Semantic queries on files for local folders, exposed as both a Python library and a CLI.

## Getting Started

```sh
make setup
make test
mise exec -- uv run semfs files docs/ "configuration loading"
```

```python
import semfs

results = semfs.files({"text": "configuration loading"}, "docs")
print(results)
```

## Overview

`semfs` builds a local chunk index for text files, stores it under `.semfs/`, and lets you query files or merged line ranges using a vector-style TF-IDF backend. The CLI follows the same action-oriented API as the library.

## CLI Examples

```sh
uvx semfs index content/
```

```sh
uvx semfs files content/ "how do indexes refresh?"
```

```sh
uvx semfs chunks content/ "chunk overlap" --top 5 --distance 0.7
```

```sh
uvx semfs files --config .semfsrc content/ "cli configuration"
```

## Library Examples

```python
import semfs

summary = semfs.index("content", {"name": "index0", "mode": "refresh"})
print(summary["chunk_count"])
```

```python
import semfs

findings = semfs.chunks(
		{"text": "semantic queries", "max_results": 3},
		"content",
		True,
		{"name": "index0", "mode": "auto"},
)
for finding in findings:
		print(finding["file"], finding["from"], finding["to"])
```

## Config File

The CLI looks for a JSON config file at `.semfsrc` in the current working directory, or you can pass `--config path/to/file.json`.

```json
{
	"name": "index0",
	"mode": "auto",
	"filter": "**/*.md",
	"model": "tfidf",
	"chunking": {
		"size": 500,
		"overlap": 250,
		"mode": "auto"
	}
}
```

## Repository Layout

```text
.
├── src/semfs/            # Library and CLI implementation
├── tests/                # Unit tests
├── tests_integration/    # Benchmark-oriented integration tests
├── examples/             # Runnable consumer examples
├── .xdrs/                # Shared and local decision records
└── .github/workflows/    # CI, release, and publish automation
```

## Status

This initial implementation uses a built-in TF-IDF model named `tfidf`. The public config already includes a `model` field so additional embedding backends can be added later without changing the API shape.
