# Library API Contract

## Public Module

The public module remains `semfs` and exposes one indexing entry point plus one entry point for each query shape.

## Function Contracts

### `semfs.index(dir, config)`

- **Purpose**: Create or refresh the named semantic index for `dir` according to `config`.
- **Inputs**:
  - `dir`: filesystem path to the indexed directory
  - `config`: validated `IndexConfig`
- **Returns**: `IndexState` summary containing index name, storage path, indexed file count, chunk count, and update timestamp
- **Behavior**:
  - Honors the selected index mode
  - Persists reusable index metadata for `refresh`, `auto`, and `stale`
  - Keeps `inmemory` and `transient` runs non-persistent
  - Treats an index as unusable when required metadata or storage structures are missing or unreadable, when the schema version is incompatible, or when the stored model or chunking fingerprint does not match the requested configuration

### `semfs.chunks(query, dir, fetch_contents, config)`

- **Purpose**: Return ranked chunk-level findings for a natural-language query.
- **Inputs**:
  - `query`: validated `QueryRequest`
  - `dir`: filesystem path to search
  - `fetch_contents`: boolean, default `False`
  - `config`: validated `IndexConfig`
- **Returns**: ordered list of `ChunkFinding`
- **Behavior**:
  - Honors the configured index mode, including building or refreshing the index on demand when the query requires it
  - Defaults to 10 results when `query.max_results` is omitted
  - Applies no distance filtering when `query.max_distance` is omitted
  - Exposes `ChunkFinding` fields as `file`, `from`, `to`, `score`, and optional `contents`, with `from` and `to` as inclusive merged line numbers
  - Merges directly contiguous findings from the same file before returning results
  - Returns file paths relative to the indexed directory
  - Includes `contents` only when `fetch_contents=True`
  - Fails the whole query with an actionable error if `fetch_contents=True` and any selected file no longer matches the indexed snapshot or cannot be read
  - Fails with an actionable error if the configured model is not available locally, including when a reusable index references that model

### `semfs.files(query, dir, config)`

- **Purpose**: Return deduplicated file-level results derived from semantic chunk matches.
- **Inputs**:
  - `query`: validated `QueryRequest`
  - `dir`: filesystem path to search
  - `config`: validated `IndexConfig`
- **Returns**: ordered list of `FileFinding`
- **Behavior**:
  - Honors the configured index mode, including building or refreshing the index on demand when the query requires it
  - Uses the same ranking and optional distance filter as `chunks()`
  - Deduplicates multiple matches from the same file
  - Returns file paths relative to the indexed directory
  - Orders files by highest semantic relevance after deduplication, with ties broken by relative path ascending

## Error Contract

The library raises typed domain exceptions for invalid config, missing indexes in unsupported states, unavailable models, including reusable indexes whose stored model is not available locally, or unreadable files.

Library exception messages are actionable only when they include all of the following that are known at the failure point:

- the failed action such as `index`, `chunks`, or `files`
- the relevant directory path, index name, or file path
- the specific reason the action failed
- the next corrective step such as rebuild the index, provide `--config`, install the model, or rerun without `fetch_contents`

The CLI is responsible for turning these exceptions into concise user-facing messages and exit code `1`.