# semfs

Semantic file queries for local folders via a Python library and CLI.

## Getting Started

Run semfs immediately with the built-in default config, or add a UTF-8 JSON `.semfsrc` in the working directory to override it.

Default CLI config:

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

Optional `.semfsrc` override:

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
  "model": {
    "name": "all-MiniLM-L6-v2"
  }
}
```

From a source checkout, prepare the shared environment once and run the installed CLI from the shared virtual environment:

```sh
make setup
./.venv/bin/semfs index docs
./.venv/bin/semfs chunks docs "what is x?" --top 5
```

The default `all-MiniLM-L6-v2` model is bundled with the package via `gt-all-minilm-l6-v2` and works fully offline with no pre-download or network access required. To use a custom model, set `model.name` and optionally `model.localPath` in `.semfsrc`; custom models with `model.offlineOnly: true` require `model.localPath`.

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
semfs --version
```

Build or refresh an index:

```sh
semfs index docs
```

Return chunk matches with excerpt contents:

```sh
semfs chunks docs "what is x?" --top 5 --contents
```

Return deduplicated matching files:

```sh
semfs files docs "what is x?" --top 5
```

Use an explicit config file path:

```sh
semfs index docs --config .semfsrc
```

When `.semfsrc` is absent, the CLI falls back to the default config shown above. When `--config` is provided, that file must exist and contain valid JSON.

Successful `index` runs print a start message and a completion message with indexed file and chunk counts.

### Sample directory walkthrough

The `examples/basic-usage/sample-corpus/` directory contains a ready-made corpus you can use to try the CLI immediately after setup.

```sh
# from the repository root, after running `make setup`

# index the sample corpus
cd examples/basic-usage
mise exec -- uv run --project . semfs index sample-corpus

# search for relevant chunks and print their file locations and text
mise exec -- uv run --project . semfs chunks sample-corpus \
  'how do installers recover an offline zigbee hub?' \
  --top 5 --contents
# expected: devices/zigbee-hub-recovery.txt[1:6] in results

# search for the most relevant files
mise exec -- uv run --project . semfs files sample-corpus \
  'steps to prepare a technician visit for thermostat or lock issues' \
  --top 5
# expected: support/field-visit-prep.md and devices/thermostat-onboarding.md in results
```

The sample corpus covers three top-level topics (`devices/`, `operations/`, `support/`) and is the same corpus used by `make test-cli` in `examples/basic-usage`.

## Library Examples

Create or refresh an index:

```python
import semfs

config = {
    "name": "index0",
    "filter": "**/*.md",
    "mode": "auto",
    "chunking": {"size": 500, "overlap": 250, "edges": "auto"},
    "model": {
        "name": "all-MiniLM-L6-v2",
    },
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
    "model": {
        "name": "all-MiniLM-L6-v2",
    },
}
query = {"text": "what is x?", "max_results": 5}

chunks = semfs.chunks(query, "docs", False, config)
files = semfs.files(query, "docs", config)

print(chunks)
print(files)
```

If excerpt contents are requested and any selected file no longer matches the indexed snapshot or cannot be read, the whole query fails with an actionable error.

If the configured local model directory is missing and `model.offlineOnly` is `true`, indexing and query operations fail with an actionable local-model error.

## Development

```sh
make setup
make build
make lint
make test
```

Consumer examples under `examples/` are verified against an editable install of the library source.