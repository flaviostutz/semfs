# Data Model: Semantic File Query Library and CLI

## Entities

### IndexConfig

Represents the caller-supplied indexing and query settings for one named index.

| Field | Type | Required | Validation |
|---|---|---|---|
| `name` | string | Yes | Non-empty, filesystem-safe, unique per target directory |
| `filter` | string | Yes | Valid glob; defaults to `**/*` when omitted |
| `mode` | enum | Yes | One of `refresh`, `auto`, `stale`, `inmemory`, `transient` |
| `chunking.size` | integer | Yes | Greater than 0 |
| `chunking.overlap` | integer | Yes | Greater than or equal to 0 and strictly smaller than `size` |
| `chunking.edges` | enum | Yes | `auto` applies markdown-aware chunking to markdown files and fixed chunking otherwise; `fixed` always uses fixed chunking |
| `model` | string | Yes | Installed local embedding model identifier |

Supported indexed inputs are UTF-8-readable text files selected by the filter. Binary files, unreadable files, and other unsupported non-text inputs are skipped.

### IndexState

Represents one materialized index for one directory and one named configuration.

| Field | Type | Required | Notes |
|---|---|---|---|
| `directory_path` | string | Yes | Root directory being indexed |
| `index_name` | string | Yes | Derived from `IndexConfig.name` |
| `database_path` | string | Yes | On-disk path for reusable modes, including sqlite-vec-backed vector tables |
| `schema_version` | string | Yes | Used to force rebuilds when storage changes |
| `model_name` | string | Yes | Embedding model used for this index |
| `embedding_dimensions` | integer | Yes | Needed to validate stored vectors |
| `chunking_fingerprint` | string | Yes | Detects when chunking settings changed |
| `status` | enum | Yes | `ready`, `stale`, `ephemeral` |
| `created_at` | datetime | Yes | First materialization time |
| `updated_at` | datetime | Yes | Most recent rebuild time |

### FileSnapshot

Represents the last indexed state of one file.

| Field | Type | Required | Notes |
|---|---|---|---|
| `file_path` | string | Yes | Relative path within indexed directory |
| `size_bytes` | integer | Yes | Used for auto-mode drift detection |
| `modified_time` | datetime | Yes | Used for auto-mode drift detection |
| `content_digest` | string | Yes | Digest of the indexed file contents used to verify live-file excerpt consistency |
`content_digest` uses SHA-256 over the UTF-8 text contents that were indexed. Changing that compatibility rule requires a schema-version change.

| `chunk_count` | integer | Yes | Number of chunks emitted for this file |
| `last_indexed_at` | datetime | Yes | Audit field for rebuilds |

### ChunkRecord

Represents one stored searchable unit in the index.

| Field | Type | Required | Notes |
|---|---|---|---|
| `chunk_id` | string | Yes | Stable unique identifier inside one index |
| `file_path` | string | Yes | Stored alongside the vector row in `chunk_index` for direct result retrieval |
| `start_line` | integer | Yes | Inclusive start line |
| `end_line` | integer | Yes | Inclusive end line |
| `embedding` | float32[] | Yes | Vector persisted in the sqlite-vec `chunk_index` table |

### QueryRequest

Represents a semantic query submitted to either `chunks()` or `files()`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `text` | string | Yes | Non-empty after trimming |
| `max_results` | integer | No | Greater than 0; defaults to 10 |
| `max_distance` | float | No | Non-negative when provided; omitted means no distance filter |

### ChunkFinding

Represents a chunk-level query result returned to callers.

The public field names are `file`, `from`, `to`, `score`, and optional `contents`. CLI rendering may format the same range as `path[from:to]`, but the library result contract uses the field names below.

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | string | Yes | Relative path within the indexed directory |
| `from` | integer | Yes | Inclusive start line after merge |
| `to` | integer | Yes | Inclusive end line after merge |
| `score` | float | Yes | Ranking value derived from semantic similarity |
| `contents` | string | No | Present only when contents were requested |

### FileFinding

Represents a deduplicated file-level search result.

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | string | Yes | Relative path within the indexed directory |
| `best_score` | float | Yes | Highest score among that file's chunks |

### BenchmarkRun

Represents one recorded benchmark execution.

| Field | Type | Required | Notes |
|---|---|---|---|
| `dataset_name` | string | Yes | `small` or `large` |
| `folder_count` | integer | Yes | Corpus shape metadata |
| `file_count` | integer | Yes | Corpus shape metadata |
| `max_depth` | integer | Yes | Expected to be 7 for the large dataset |
| `index_seconds` | float | Yes | Elapsed index time |
| `query_seconds` | float | Yes | Elapsed query time |
| `artifact_path` | string | Yes | Persisted artifact path under the repository-level `benchmarks/` directory |
| `recorded_at` | datetime | Yes | Time of the benchmark run |

Benchmark artifacts are JSON records. Each planned run writes its own artifact and does not overwrite prior benchmark artifacts unless the caller explicitly removes them. The deterministic corpus generator rules for each dataset are part of the public benchmark contract.

## Relationships

- One `IndexConfig` materializes one `IndexState` per indexed directory.
- One `IndexState` contains many `FileSnapshot` records.
- One `FileSnapshot` contains many `ChunkRecord` rows.
- One `QueryRequest` yields many `ChunkFinding` results or many `FileFinding` results.
- One `BenchmarkRun` is associated with one synthetic dataset definition and one completed index/query execution.

## State Transitions

### IndexState lifecycle

`missing` -> `ready` when an index is created successfully.

`ready` -> `stale` when file metadata no longer matches the stored `FileSnapshot` set.

`stale` -> `ready` when `refresh` or `auto` rebuilds the index.

`ready` -> `ephemeral` when `inmemory` or `transient` materializes a non-persistent index for the current operation.

`ephemeral` -> `missing` when the operation completes and no reusable index artifact remains.