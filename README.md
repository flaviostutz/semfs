# semfs

Semantic file queries for local folders via a Python library and CLI.

This utility can be used in RAG applications to enrich the context sent to LLMs by retrieving the most semantically relevant file chunks for a given query by simply pointing it to an existing filesystem.

All the heavy lifting of preparing models, scanning and opening files, chunking, embedding, indexing and querying is performed by semfs.

All the embedding is performed locally.

## Getting Started

No install needed — run `semfs` directly with [uvx](https://docs.astral.sh/uv/):

### Search for relevant file chunks

```sh
# The all-MiniLM-L6-v2 model (~90MB) is bundled with the package — no download needed.
uvx semfs chunks ./docs "how do I configure authentication?" --top 3 --contents
```

```
docs/setup/auth.md[12:28]
---
To configure authentication, set the `AUTH_PROVIDER` environment variable to
one of the supported providers: `github`, `google`, or `local`. Then add the
corresponding client credentials to your `.env` file.
---
docs/reference/env-vars.md[45:51]
---
AUTH_PROVIDER – selects the authentication backend. Defaults to `local`.
---
docs/guides/quickstart.md[3:9]
---
Before running the server, complete the authentication setup described in
the setup guide.
---
```

### Search for relevant files

```sh
uvx semfs files ./docs "deployment and environment setup" --top 3
```

```
docs/setup/deployment.md
docs/setup/auth.md
docs/reference/env-vars.md
```

## CLI options

### Configuration

Place a `.semfsrc` JSON file in your working directory to control how `semfs` indexes and searches files. If no file is present, the built-in defaults are used.

```json
{
  "name": "index0",
  "filter": "**/*",
  "mode": "auto",
  "chunking": {
    "size": 500,
    "overlap": 250,
    "edges": "auto"
  },
  "model": {
    "name": "all-MiniLM-L6-v2"
  }
}
```

| Field | Default | Description |
|---|---|---|
| `name` | `index0` | Name of the index stored on disk. Use different names to maintain multiple indexes in the same directory. |
| `filter` | `**/*` | Glob pattern to select which files are indexed. Example: `**/*.md` to index only Markdown files. |
| `mode` | `auto` | Index lifecycle mode. `auto` rebuilds only when files change; `refresh` always rebuilds; `stale` uses an existing index without rebuilding; `inmemory` / `transient` never writes to disk. |
| `chunking.size` | `500` | Maximum number of tokens per chunk. |
| `chunking.overlap` | `250` | Number of tokens that overlap between consecutive chunks. Must be less than `size`. |
| `chunking.edges` | `auto` | Chunk boundary strategy. `auto` splits on natural text boundaries; `fixed` splits at a fixed token count. |
| `model.name` | `all-MiniLM-L6-v2` | Sentence-Transformers model name used for embedding. The default model is bundled with the package via `gt-all-minilm-l6-v2` and works fully offline with no additional setup. |
| `model.offlineOnly` | `false` | When `true`, the model is loaded only from `localPath` and no download is attempted. Required `localPath` for custom models; not needed for the default `all-MiniLM-L6-v2` model which is always loaded from the bundled package. |
| `model.localPath` | — | Path to a local model directory. Use this to override the bundled default or to specify a custom model location. |

You can also point to a custom config file with the `--config` CLI flag:

```sh
uvx semfs chunks ./docs "how do I configure auth?" --config ./my-config.json
```


### `semfs index <directory>`

Pre-builds or refreshes the index for a directory. Useful to warm up the index before querying.

```sh
uvx semfs index ./docs
uvx semfs index ./docs --config ./my-config.json --offline --verbose
```

### `semfs chunks <directory> <query>`

Returns the most relevant file chunks for a query, ranked by semantic similarity.

| Option | Default | Description |
|---|---|---|
| `--top` | `10` | Maximum number of chunk results to return. |
| `--distance` | — | Optional upper bound on the distance score. Lower values = stricter match. |
| `--contents` | `false` | Include the actual text excerpt in the output. |
| `--config` | — | Path to a `.semfsrc`-format JSON config file. |
| `--offline` | `false` | Disable model downloads; use only locally cached models. |
| `--verbose` | `false` | Print extra detail about index and query execution. |

### `semfs files <directory> <query>`

Returns the most relevant files for a query, deduplicated by best-matching chunk.

| Option | Default | Description |
|---|---|---|
| `--top` | `10` | Maximum number of file results to return. |
| `--distance` | — | Optional upper bound on the distance score. |
| `--config` | — | Path to a `.semfsrc`-format JSON config file. |
| `--offline` | `false` | Disable model downloads; use only locally cached models. |
| `--verbose` | `false` | Print extra detail about index and query execution. |

## Library API

Install the package:

```sh
pip install semfs
```

Three public functions are exported from the `semfs` package.

### `semfs.index(directory, config, *, verbose)`

Builds or refreshes the index for the given directory. Returns an `IndexState` with `indexed_files` and `indexed_chunks` counts.

```python
import semfs

state = semfs.index("./docs", {"name": "index0", "filter": "**/*.md", "mode": "auto"})
print(f"Indexed {state.indexed_files} files, {state.indexed_chunks} chunks")
```

### `semfs.chunks(query, directory, fetch_contents, config, *, verbose)`

Returns a list of `ChunkFinding` objects ranked by semantic similarity.

```python
results = semfs.chunks(
    {"text": "how do I configure authentication?", "max_results": 5},
    "./docs",
    fetch_contents=True,
)
for r in results:
    print(r.file, r.from_line, r.to_line, r.contents)
```

### `semfs.files(query, directory, config, *, verbose)`

Returns a list of `FileFinding` objects deduplicated by best chunk match.

```python
results = semfs.files(
    {"text": "deployment and environment setup", "max_results": 3},
    "./docs",
)
for r in results:
    print(r.file, r.best_score)
```

---

## Developer instructions

The published Python package lives in `lib/` and runnable consumer projects live in `examples/`.

The default embedding model (`all-MiniLM-L6-v2`) is bundled with the `semfs` package via the `gt-all-minilm-l6-v2` dependency. No pre-download or network access is required. Custom models can be configured via `model.name` and `model.localPath` in `.semfsrc`.

## Repository Layout

- `lib/` contains the package source, tests, package metadata, lockfile, and library-specific Makefile.
- `examples/` contains independent consumer projects that exercise the package as an installed dependency.
- `benchmarks/` stores benchmark timing artifacts written by benchmark flows.
- `specs/` and `.xdrs/` capture the active feature and decision records for the repository.

## Common Commands

```sh
make install
make build
make lint-fix
make test
make run
```

`make test` runs library unit tests and the consumer examples. `make test-integration` runs the integration test suite separately. Example verification builds the library and runs examples against the editable source install.

## Package Usage

User-facing CLI and library examples live in `lib/README.md`.

From a source checkout, prepare the shared environment once and then use the root Makefile targets:

```sh
make setup
make run
```

## Benchmark Example

Run the benchmark consumer project against the built wheel when you want fresh artifacts under `benchmarks/`:

```sh
make setup
make build
make -C examples/benchmark-corpora run
```
