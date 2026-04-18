# Quickstart

## Goal

Verify the planned feature end-to-end once implementation is complete: configure the project, create a named index, query chunks and files, and run both benchmark scenarios.

## 1. Install project dependencies

```sh
make install
```

## 2. Create a local `.semfsrc`

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

`chunking.edges: "auto"` uses markdown-aware chunking for markdown files and fixed chunking for all other files. `"fixed"` always uses fixed chunking.

## 3. Build or refresh an index

```sh
uv run semfs index docs/
```

Expected behavior:

- Returned paths are relative to `docs/`.
- The CLI prints a start message for the named index.
- The CLI prints a success message with indexed file and chunk counts.

## 4. Query chunk results

```sh
uv run semfs chunks docs/ "what is x?" --top 5
```

To include excerpt contents:

```sh
uv run semfs chunks docs/ "what is x?" --top 5 --contents
```

If any selected file no longer matches the indexed snapshot or cannot be read, the whole `--contents` query fails with an actionable error.

## 5. Query file results

```sh
uv run semfs files docs/ "what is x?" --top 5
```

## 6. Use the library directly

```python
import semfs

config = {
    "name": "index0",
    "filter": "**/*.md",
    "mode": "auto",
  "chunking": {"size": 500, "overlap": 250, "edges": "auto"},
    "model": "sentence-transformers/all-MiniLM-L6-v2",
}

semfs.index("docs", config)
chunks = semfs.chunks({"text": "what is x?", "max_results": 5}, "docs", False, config)
files = semfs.files({"text": "what is x?", "max_results": 5}, "docs", config)
```

## 7. Run benchmark scenarios

```sh
make test
```

Expected behavior:

- Unit and integration tests pass.
- The small and large deterministic corpora are generated.
- Index and query timings are recorded for both benchmark datasets.
- Benchmark artifacts are written under the repository-level `benchmarks/` directory.